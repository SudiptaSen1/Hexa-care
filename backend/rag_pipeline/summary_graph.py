import os
from typing import TypedDict, List, Annotated, Dict, Optional, Union
from datetime import datetime
from dotenv import load_dotenv

# Ensure environment variables are loaded as early as possible
load_dotenv()

# Import google.generativeai BEFORE it's used for configuration
import google.generativeai as genai

# LangChain Imports for LLM and Embeddings
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

# LangChain Imports for Vector Store (Qdrant)
from langchain_qdrant import QdrantVectorStore
from langchain_core.documents import Document
from qdrant_client import QdrantClient
from qdrant_client.http import models

# LangGraph Imports
from langgraph.graph import StateGraph, END

# Pydantic for data models
from pydantic import BaseModel, Field, ValidationError
import json

# --- Configuration ---
# Retrieve API key from environment variables
gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if gemini_api_key:
    genai.configure(api_key=gemini_api_key)
else:
    print("WARNING: Gemini API key not found. Please set GEMINI_API_KEY or GOOGLE_API_KEY environment variable.")

llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.2)
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

# Qdrant Configuration
QDRANT_URL = os.getenv("QDRANT_URL", "https://your-cluster-url.qdrant.tech")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = "medical_prescriptions"

# Initialize Qdrant client
qdrant_client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
)

# Initialize vector store
vector_store = QdrantVectorStore(
    client=qdrant_client,
    collection_name=COLLECTION_NAME,
    embedding=embeddings,
)

# Ensure collection exists
try:
    qdrant_client.get_collection(COLLECTION_NAME)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Qdrant collection '{COLLECTION_NAME}' exists.")
except Exception:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Creating Qdrant collection '{COLLECTION_NAME}'.")
    qdrant_client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE),
    )

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
        # First try to parse as JSON
        try:
            prescription_data = json.loads(prescription_json_str)
        except json.JSONDecodeError:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Invalid JSON, treating as raw text")
            return {"ingestion_status": "parsing_failed: Invalid JSON format"}
        
        # Validate with Pydantic
        parsed_data = PatientPrescriptionRecord.model_validate(prescription_data)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Prescription parsed successfully for patient: {parsed_data.patient_name}")
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
        documents_to_add = []
        
        # Create comprehensive prescription summary document
        prescription_summary = (
            f"Patient: {parsed_prescription.patient_name} (Age: {parsed_prescription.age}). "
            f"Prescription Date: {parsed_prescription.date}. "
            f"Diagnosis: {parsed_prescription.diagnosis or 'Not specified'}. "
            f"Doctor Instructions: {'; '.join(parsed_prescription.doctor_instructions) if parsed_prescription.doctor_instructions else 'None'}. "
        )
        
        # Add medication information to summary
        medication_info = []
        for med in parsed_prescription.medicines:
            med_text = f"{med.name} - Dosage: {med.dosage}"
            if med.duration:
                med_text += f", Duration: {med.duration}"
            if med.notes:
                med_text += f", Notes: {med.notes}"
            medication_info.append(med_text)
        
        if medication_info:
            prescription_summary += f"Medications prescribed: {'; '.join(medication_info)}."
        
        # Create main prescription document
        summary_doc = Document(
            page_content=prescription_summary,
            metadata={
                "type": "prescription_summary",
                "patient_name": parsed_prescription.patient_name,
                "user_id": user_id,
                "date_issued": parsed_prescription.date,
                "diagnosis": parsed_prescription.diagnosis,
                "medication_count": len(parsed_prescription.medicines),
                "medications": [med.name for med in parsed_prescription.medicines]
            }
        )
        documents_to_add.append(summary_doc)
        
        # Create individual medication documents for detailed queries
        for i, med in enumerate(parsed_prescription.medicines):
            med_content = (
                f"Patient {parsed_prescription.patient_name} has been prescribed {med.name}. "
                f"Dosage: {med.dosage}. "
                f"Duration: {med.duration or 'Not specified'}. "
                f"Additional notes: {med.notes or 'None'}. "
                f"This medication is part of treatment for: {parsed_prescription.diagnosis}."
            )
            
            med_doc = Document(
                page_content=med_content,
                metadata={
                    "type": "medication_detail",
                    "patient_name": parsed_prescription.patient_name,
                    "user_id": user_id,
                    "medication_name": med.name,
                    "medication_dosage": med.dosage,
                    "medication_duration": med.duration,
                    "prescription_date": parsed_prescription.date,
                    "diagnosis": parsed_prescription.diagnosis
                }
            )
            documents_to_add.append(med_doc)
        
        # Create diagnosis-specific document
        if parsed_prescription.diagnosis:
            diagnosis_content = (
                f"Patient {parsed_prescription.patient_name} has been diagnosed with: {parsed_prescription.diagnosis}. "
                f"Treatment includes the following medications: {', '.join([med.name for med in parsed_prescription.medicines])}. "
                f"Doctor's instructions: {'; '.join(parsed_prescription.doctor_instructions) if parsed_prescription.doctor_instructions else 'None provided'}."
            )
            
            diagnosis_doc = Document(
                page_content=diagnosis_content,
                metadata={
                    "type": "diagnosis_info",
                    "patient_name": parsed_prescription.patient_name,
                    "user_id": user_id,
                    "diagnosis": parsed_prescription.diagnosis,
                    "prescription_date": parsed_prescription.date
                }
            )
            documents_to_add.append(diagnosis_doc)
        
        # Add all documents to vector store
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Adding {len(documents_to_add)} documents to Qdrant...")
        vector_store.add_documents(documents_to_add)
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Successfully stored {len(documents_to_add)} documents in Qdrant for user {user_id}")
        
        # Verify storage by doing a quick search
        try:
            test_results = vector_store.similarity_search(
                f"medications for {parsed_prescription.patient_name}",
                k=1,
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="metadata.user_id",
                            match=models.MatchValue(value=user_id)
                        )
                    ]
                )
            )
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Verification search returned {len(test_results)} results")
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Verification search failed: {e}")
        
        return {"ingestion_status": "completed"}
        
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Error storing prescription data: {e}")
        import traceback
        traceback.print_exc()
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
    
    try:
        # Create filter for user-specific data
        filter_condition = models.Filter(
            must=[
                models.FieldCondition(
                    key="metadata.user_id",
                    match=models.MatchValue(value=user_id)
                )
            ]
        )
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Searching with filter for user_id: {user_id}")
        
        # Search with user filter
        retrieved_docs = vector_store.similarity_search(
            query, 
            k=5,
            filter=filter_condition
        )
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Retrieved {len(retrieved_docs)} documents for user {user_id}")
        
        # Log retrieved documents for debugging
        for i, doc in enumerate(retrieved_docs):
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Doc {i+1}: {doc.metadata.get('type', 'unknown')} - {doc.page_content[:100]}...")
        
        return {"retrieved_info": retrieved_docs}
        
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Error retrieving documents: {e}")
        import traceback
        traceback.print_exc()
        return {"retrieved_info": []}

async def generate_response(state: PrescriptionIngestionState) -> PrescriptionIngestionState:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Generating response...")
    
    retrieved_docs = state.get("retrieved_info", [])
    question = state.get("question", "")
    chat_history = state.get("chat_history", [])
    
    if not retrieved_docs:
        response_content = "I don't have any prescription information available for you yet. Please upload a prescription first, and then I'll be able to help you with questions about your medications, dosages, and treatment plans."
        print(f"[{datetime.now().strftime('%H:%M:%S')}] No documents retrieved, returning default response")
    else:
        system_message = (
            "You are a helpful medical assistant. Use the following retrieved prescription information "
            "to answer the user's question accurately and helpfully. Focus on the specific medications, "
            "dosages, and instructions mentioned in the prescription data. If the question cannot be "
            "answered from the provided prescription information, clearly state that and suggest "
            "consulting with a healthcare provider."
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("user", "Retrieved prescription information:\n{context}\n\nChat history:\n{chat_history}\n\nQuestion: {question}")
        ])
        
        context = "\n\n".join([f"Document {i+1}: {doc.page_content}" for i, doc in enumerate(retrieved_docs)])
        chat_history_str = "\n".join([f"{msg.type}: {msg.content}" for msg in chat_history])
        
        try:
            chain = prompt | llm
            response = await chain.ainvoke({
                "context": context,
                "chat_history": chat_history_str,
                "question": question
            })
            response_content = response.content
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Generated response using {len(retrieved_docs)} documents")
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Error generating response: {e}")
            response_content = "I encountered an error while processing your question. Please try again or rephrase your question."
    
    # Update chat history
    updated_chat_history = chat_history + [
        HumanMessage(content=question),
        AIMessage(content=response_content)
    ]
    
    return {
        "answer": response_content,
        "chat_history": updated_chat_history
    }

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