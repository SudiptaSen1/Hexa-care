import os
from typing import TypedDict, List, Annotated, Dict, Optional, Union
from datetime import datetime
from dotenv import load_dotenv

# Ensure environment variables are loaded as early as possible
load_dotenv()

# Import google.generativeai BEFORE it's used for configuration
import google.generativeai as genai

# Correct checkpoint saver import
from pymongo import MongoClient
from langgraph.checkpoint.mongodb.aio import AsyncMongoDBSaver

# LangChain Imports for LLM and Embeddings
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

# LangChain Imports for Vector Store (ChromaDB)
from langchain_chroma import Chroma
from langchain_core.documents import Document

# LangGraph Imports
from langgraph.graph import StateGraph, END

# Pydantic for data models
from pydantic import BaseModel, Field, ValidationError

# --- Configuration ---
# Retrieve API key from environment variables
gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if gemini_api_key:
    genai.configure(api_key=gemini_api_key)
else:
    print("WARNING: Gemini API key not found. Please set GEMINI_API_KEY or GOOGLE_API_KEY environment variable.")

# MongoDB connection for Checkpoint Saver
MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "hexacare")

# Initialize MongoDB client and checkpoint saver
try:
    mongo_client = MongoClient(MONGO_URI)
    mongo_db = mongo_client[DB_NAME]
    saver = AsyncMongoDBSaver(mongo_db)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] MongoDB Checkpoint Saver initialized. Chat history will be persistent.")
except Exception as e:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: Could not connect to MongoDB for checkpointing: {e}")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Falling back to in-memory checkpointing. Chat history will NOT be persistent across restarts.")
    from langgraph.checkpoint.memory import MemorySaver
    saver = MemorySaver()

llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.2)
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

CHROMA_DB_DIRECTORY = "./chroma_db"
# Ensure the directory exists or will be created by Chroma
vector_store = Chroma(embedding_function=embeddings, persist_directory=CHROMA_DB_DIRECTORY)

# --- Data Models ---
class Medicine(BaseModel):
    name: str = Field(description="Name of the medicine.")
    dosage: str = Field(description="Dosage of the medicine (e.g., '2 TSF thrice daily').")
    duration: Optional[str] = Field(default=None, description="Duration of the prescription (e.g., '10 days').")
    notes: Optional[str] = Field(default=None, description="Any specific notes or additional instructions for the medication.")
    frequency: Optional[str] = Field(default=None, description="How often the medication should be taken (e.g., 'once daily', 'twice a day').")
    route: Optional[str] = Field(default=None, description="Route of administration (e.g., 'oral', 'topical', 'IV').")

class PatientPrescriptionRecord(BaseModel):
    patient_name: str = Field(description="Name of the patient.")
    age: str = Field(description="Age of the patient (e.g., '20 Years').")
    date: str = Field(description="Date of the record in YYYY-MM-DD format.")
    medicines: List[Medicine] = Field(description="List of prescribed medicines.")
    diagnosis: str = Field(description="Patient's diagnosis as a single string summary.")
    doctor_instructions: List[str] = Field(description="List of specific instructions from the doctor.")
    prescribing_doctor: Optional[str] = Field(default=None, description="Name of the prescribing doctor.")
    pharmacy_info: Optional[str] = Field(default=None, description="Information about the pharmacy.")
    allergies: List[str] = Field(default_factory=list, description="List of patient allergies.")

# --- LangGraph State ---
class PrescriptionIngestionState(TypedDict):
    user_id: str
    session_id: Optional[str]
    prescription_text: str
    parsed_prescription: Optional[PatientPrescriptionRecord]
    retrieved_info: List[Document]
    question: str
    answer: str
    chat_history: Annotated[List[BaseMessage], lambda x, y: x + y]
    ingestion_status: str
    user_summary: Optional[str]

# --- Nodes and Functions ---
async def validate_and_parse_prescription(state: PrescriptionIngestionState) -> PrescriptionIngestionState:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Validating and parsing prescription record.")
    prescription_json_str = state["prescription_text"]
    try:
        parsed_data = PatientPrescriptionRecord.model_validate_json(prescription_json_str)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Prescription parsed successfully.")
        return {"parsed_prescription": parsed_data, "ingestion_status": "parsed"}
    except ValidationError as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Error parsing prescription (Pydantic validation): {e}")
        return {"ingestion_status": f"parsing_failed: {e}"}
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Unexpected error parsing prescription: {e}")
        return {"ingestion_status": f"parsing_failed_unexpected: {e}"}

async def store_prescription_data(state: PrescriptionIngestionState) -> PrescriptionIngestionState:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Storing prescription for user.")
    parsed_prescription = state["parsed_prescription"]
    user_id = state["user_id"]
    if not parsed_prescription:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] No parsed prescription to store. Skipping storage.")
        return {"ingestion_status": "no_parsed_data"}

    try:
        prescription_doc_content = (
            f"Patient: {parsed_prescription.patient_name} (Age: {parsed_prescription.age}). "
            f"Record Date: {parsed_prescription.date}. "
            f"Diagnosis: {parsed_prescription.diagnosis or 'N/A'}. "
            f"Doctor's Instructions: {', '.join(parsed_prescription.doctor_instructions)}. "
            "Medications: "
        )
        for med in parsed_prescription.medicines:
            prescription_doc_content += f"{med.name} {med.dosage} (Duration: {med.duration or 'N/A'}); "
        
        medicine_docs = []
        for med in parsed_prescription.medicines:
            medicine_docs.append(Document(
                page_content=f"Patient: {parsed_prescription.patient_name}. Medication: {med.name}. Dosage: {med.dosage}. Duration: {med.duration or 'N/A'}. Notes: {med.notes or 'None'}.",
                metadata={
                    "type": "medicine_detail",
                    "patient_name": parsed_prescription.patient_name,
                    "date": parsed_prescription.date,
                    "user_id": user_id
                }
            ))

        medication_names_str = ", ".join([m.name for m in parsed_prescription.medicines])

        summary_doc = Document(
            page_content=prescription_doc_content,
            metadata={
                "type": "prescription_summary",
                "patient_name": parsed_prescription.patient_name,
                "date_issued": parsed_prescription.date,
                "medications": medication_names_str,
                "diagnosis_summary": parsed_prescription.diagnosis,
                "user_id": user_id
            }
        )
        
        documents_to_add = [summary_doc] + medicine_docs
        vector_store.add_documents(documents_to_add)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Prescription data stored in ChromaDB.")
        return {"ingestion_status": "completed"}
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Error storing prescription data: {e}")
        return {"ingestion_status": f"storage_failed: {e}"}

async def generate_user_summary(state: PrescriptionIngestionState) -> PrescriptionIngestionState:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Generating user-facing summary.")
    parsed_prescription = state["parsed_prescription"]

    if not parsed_prescription:
        user_summary_content = "Could not generate a summary as no prescription data was parsed."
    else:
        summary_parts = []
        summary_parts.append(f"**Patient:** {parsed_prescription.patient_name} (Age: {parsed_prescription.age})")
        summary_parts.append(f"**Date:** {parsed_prescription.date}")
        summary_parts.append(f"**Diagnosis:** {parsed_prescription.diagnosis}")

        if parsed_prescription.medicines:
            summary_parts.append("**Medications:**")
            for med in parsed_prescription.medicines:
                summary_parts.append(f"- {med.name}: {med.dosage} for {med.duration or 'an unspecified duration'}")
                if med.notes:
                    summary_parts.append(f"  (Notes: {med.notes})")
        
        if parsed_prescription.doctor_instructions:
            summary_parts.append("**Doctor's Instructions:**")
            for instr in parsed_prescription.doctor_instructions:
                summary_parts.append(f"- {instr}")

        user_summary_content = "\n".join(summary_parts)

    print(f"[{datetime.now().strftime('%H:%M:%S')}] User summary generated.")
    return {"user_summary": user_summary_content, "ingestion_status": "completed_with_summary"}

async def retrieve_information(state: PrescriptionIngestionState) -> PrescriptionIngestionState:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Retrieving information for query: {state['question']}")
    query = state["question"]
    user_id = state["user_id"]
    # Filter by user_id
    retrieved_docs = vector_store.similarity_search(query, k=5, filter={"user_id": user_id})
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Retrieved {len(retrieved_docs)} documents.")
    return {"retrieved_info": retrieved_docs}

async def generate_response(state: PrescriptionIngestionState) -> PrescriptionIngestionState:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Generating response...")
    system_message = (
        "You are a helpful medical assistant. Use the following retrieved information and chat history "
        "to answer the user's question. If you don't know the answer based on the provided context, "
        "state that you don't have enough information from the records. "
        "Be concise and directly answer the question."
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_message),
            ("user", "Retrieved context:\n{context}\n\nChat history:\n{chat_history}\n\nQuestion: {question}")
        ]
    )
    context = "\n".join([doc.page_content for doc in state["retrieved_info"]])
    chat_history_str = "\n".join([f"{msg.type}: {msg.content}" for msg in state["chat_history"]])
    chain = prompt | llm
    response = await chain.ainvoke({
        "context": context,
        "chat_history": chat_history_str,
        "question": state["question"]
    })
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Response generated.")
    return {"answer": response.content, "chat_history": state["chat_history"] + [HumanMessage(content=state["question"]), AIMessage(content=response.content)]}

# --- Graph Definitions ---
print("--- Prescription Ingestion Graph Compiled ---")
ingestion_graph_builder = StateGraph(PrescriptionIngestionState)
ingestion_graph_builder.add_node("parse", validate_and_parse_prescription)
ingestion_graph_builder.add_node("store", store_prescription_data)
ingestion_graph_builder.add_node("summarize", generate_user_summary)

def decide_ingestion_path(state: PrescriptionIngestionState) -> str:
    if state.get("parsed_prescription"):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Parsing successful, proceeding to store.")
        return "store"
    else:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Parsing failed, ending ingestion graph.")
        return "end_ingestion_failure"

ingestion_graph_builder.set_entry_point("parse")
ingestion_graph_builder.add_conditional_edges(
    "parse",
    decide_ingestion_path,
    {
        "store": "store",
        "end_ingestion_failure": END,
    }
)
ingestion_graph_builder.add_edge("store", "summarize")
ingestion_graph_builder.add_edge("summarize", END)

ingestion_graph = ingestion_graph_builder.compile()

print("--- Query Answering Graph Compiled ---")
query_graph_builder = StateGraph(PrescriptionIngestionState)
query_graph_builder.add_node("retrieve", retrieve_information)
query_graph_builder.add_node("generate", generate_response)
query_graph_builder.set_entry_point("retrieve")
query_graph_builder.add_edge("retrieve", "generate")
query_graph_builder.add_edge("generate", END)

query_graph = query_graph_builder.compile()

# --- Expose graphs for external use ---
__all__ = ["ingestion_graph", "query_graph", "PatientPrescriptionRecord"]