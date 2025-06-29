import os
from typing import TypedDict, List, Annotated, Dict, Optional, Union
from datetime import datetime
from dotenv import load_dotenv
import uuid
import json

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

# --- Configuration ---
# Retrieve API key from environment variables
gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if gemini_api_key:
    genai.configure(api_key=gemini_api_key)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Gemini API configured successfully")
else:
    print("WARNING: Gemini API key not found. Please set GEMINI_API_KEY or GOOGLE_API_KEY environment variable.")

llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.2)
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

# Qdrant Configuration
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = "medical_prescriptions"

print(f"[{datetime.now().strftime('%H:%M:%S')}] Qdrant URL: {QDRANT_URL}")
print(f"[{datetime.now().strftime('%H:%M:%S')}] Qdrant API Key configured: {'Yes' if QDRANT_API_KEY else 'No'}")

# Initialize Qdrant client with error handling
qdrant_client = None
vector_store = None

try:
    if QDRANT_URL and QDRANT_API_KEY:
        qdrant_client = QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY,
        )
        
        # Test connection
        collections = qdrant_client.get_collections()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Successfully connected to Qdrant. Collections: {len(collections.collections)}")
        
        # Ensure collection exists
        try:
            collection_info = qdrant_client.get_collection(COLLECTION_NAME)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Collection '{COLLECTION_NAME}' exists with {collection_info.points_count} points")
        except Exception:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Creating collection '{COLLECTION_NAME}'")
            qdrant_client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE),
            )
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Collection '{COLLECTION_NAME}' created successfully")
        
        # Initialize vector store
        vector_store = QdrantVectorStore(
            client=qdrant_client,
            collection_name=COLLECTION_NAME,
            embedding=embeddings,
        )
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Vector store initialized successfully")
        
    else:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] WARNING: Qdrant not configured. Missing URL or API key.")
        
except Exception as e:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: Failed to initialize Qdrant: {e}")
    import traceback
    traceback.print_exc()

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

# --- Helper Functions ---
async def store_documents_directly(documents: List[Document], user_id: str) -> bool:
    """Store documents directly using Qdrant client for better control"""
    if not qdrant_client or not vector_store:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: Qdrant not available for storage")
        return False
    
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Storing {len(documents)} documents directly...")
        
        points = []
        for i, doc in enumerate(documents):
            # Generate embedding for the document
            embedding = await embeddings.aembed_query(doc.page_content)
            
            # Create point with proper structure
            point_id = str(uuid.uuid4())
            point = models.PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "page_content": doc.page_content,
                    "metadata": doc.metadata
                }
            )
            points.append(point)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Created point {i+1}: {point_id} for user {user_id}")
        
        # Upsert points to Qdrant
        operation_info = qdrant_client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Upsert operation status: {operation_info.status}")
        
        # Verify storage
        collection_info = qdrant_client.get_collection(COLLECTION_NAME)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Collection now has {collection_info.points_count} total points")
        
        # Test retrieval immediately
        test_query = f"medications for user {user_id}"
        test_embedding = await embeddings.aembed_query(test_query)
        
        search_result = qdrant_client.search(
            collection_name=COLLECTION_NAME,
            query_vector=test_embedding,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="metadata.user_id",
                        match=models.MatchValue(value=user_id)
                    )
                ]
            ),
            limit=3
        )
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Verification search returned {len(search_result)} results")
        for result in search_result:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Found: {result.payload.get('metadata', {}).get('type', 'unknown')} (score: {result.score})")
        
        return len(search_result) > 0
        
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR in direct storage: {e}")
        import traceback
        traceback.print_exc()
        return False

async def search_documents_directly(query: str, user_id: str, limit: int = 5) -> List[Document]:
    """Search documents directly using Qdrant client"""
    if not qdrant_client or not embeddings:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: Qdrant not available for search")
        return []
    
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Searching for: '{query}' for user: {user_id}")
        
        # Generate embedding for query
        query_embedding = await embeddings.aembed_query(query)
        
        # Search with user filter
        search_results = qdrant_client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_embedding,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="metadata.user_id",
                        match=models.MatchValue(value=user_id)
                    )
                ]
            ),
            limit=limit
        )
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Direct search returned {len(search_results)} results")
        
        # Convert to Document objects
        documents = []
        for result in search_results:
            doc = Document(
                page_content=result.payload.get("page_content", ""),
                metadata=result.payload.get("metadata", {})
            )
            documents.append(doc)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Retrieved doc: {doc.metadata.get('type', 'unknown')} (score: {result.score})")
        
        return documents
        
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR in direct search: {e}")
        import traceback
        traceback.print_exc()
        return []

# --- Nodes and Functions ---
async def validate_and_parse_prescription(state: PrescriptionIngestionState) -> PrescriptionIngestionState:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Validating and parsing prescription record.")
    prescription_json_str = state["prescription_text"]
    try:
        # First try to parse as JSON
        try:
            prescription_data = json.loads(prescription_json_str)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Successfully parsed JSON")
        except json.JSONDecodeError as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Invalid JSON: {e}")
            return {"ingestion_status": f"parsing_failed: Invalid JSON format - {e}"}
        
        # Validate with Pydantic
        parsed_data = PatientPrescriptionRecord.model_validate(prescription_data)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Prescription parsed successfully for patient: {parsed_data.patient_name}")
        return {"parsed_prescription": parsed_data, "ingestion_status": "parsed"}
        
    except ValidationError as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Pydantic validation error: {e}")
        return {"ingestion_status": f"parsing_failed: {e}"}
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Unexpected parsing error: {e}")
        import traceback
        traceback.print_exc()
        return {"ingestion_status": f"parsing_failed_unexpected: {e}"}

async def store_prescription_data(state: PrescriptionIngestionState) -> PrescriptionIngestionState:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting prescription storage process.")
    parsed_prescription = state["parsed_prescription"]
    user_id = state["user_id"]
    
    if not parsed_prescription:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] No parsed prescription to store.")
        return {"ingestion_status": "no_parsed_data"}

    if not qdrant_client:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: Qdrant client not available")
        return {"ingestion_status": "storage_failed: Qdrant not configured"}

    try:
        documents_to_add = []
        
        # Create comprehensive prescription summary document
        prescription_summary = (
            f"Patient: {parsed_prescription.patient_name} (Age: {parsed_prescription.age}). "
            f"Prescription Date: {parsed_prescription.date}. "
            f"Diagnosis: {parsed_prescription.diagnosis or 'Not specified'}. "
        )
        
        # Add doctor instructions
        if parsed_prescription.doctor_instructions:
            prescription_summary += f"Doctor Instructions: {'; '.join(parsed_prescription.doctor_instructions)}. "
        
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
                "medications": [med.name for med in parsed_prescription.medicines],
                "document_id": str(uuid.uuid4())
            }
        )
        documents_to_add.append(summary_doc)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Created prescription summary document")
        
        # Create individual medication documents for detailed queries
        for i, med in enumerate(parsed_prescription.medicines):
            med_content = (
                f"Patient {parsed_prescription.patient_name} has been prescribed {med.name}. "
                f"Dosage: {med.dosage}. "
                f"Duration: {med.duration or 'Not specified'}. "
                f"Additional notes: {med.notes or 'None'}. "
                f"This medication is part of treatment for: {parsed_prescription.diagnosis}. "
                f"Prescription date: {parsed_prescription.date}."
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
                    "diagnosis": parsed_prescription.diagnosis,
                    "document_id": str(uuid.uuid4())
                }
            )
            documents_to_add.append(med_doc)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Created medication document for {med.name}")
        
        # Create diagnosis-specific document
        if parsed_prescription.diagnosis:
            diagnosis_content = (
                f"Patient {parsed_prescription.patient_name} has been diagnosed with: {parsed_prescription.diagnosis}. "
                f"Treatment includes the following medications: {', '.join([med.name for med in parsed_prescription.medicines])}. "
                f"Prescription date: {parsed_prescription.date}. "
            )
            
            if parsed_prescription.doctor_instructions:
                diagnosis_content += f"Doctor's instructions: {'; '.join(parsed_prescription.doctor_instructions)}."
            
            diagnosis_doc = Document(
                page_content=diagnosis_content,
                metadata={
                    "type": "diagnosis_info",
                    "patient_name": parsed_prescription.patient_name,
                    "user_id": user_id,
                    "diagnosis": parsed_prescription.diagnosis,
                    "prescription_date": parsed_prescription.date,
                    "document_id": str(uuid.uuid4())
                }
            )
            documents_to_add.append(diagnosis_doc)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Created diagnosis document")
        
        # Store documents using direct method
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Attempting to store {len(documents_to_add)} documents...")
        storage_success = await store_documents_directly(documents_to_add, user_id)
        
        if storage_success:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Successfully stored all documents for user {user_id}")
            return {"ingestion_status": "completed"}
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Failed to store documents")
            return {"ingestion_status": "storage_failed: Document storage verification failed"}
        
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR in store_prescription_data: {e}")
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
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Retrieving information for query: '{state['question']}'")
    query = state["question"]
    user_id = state["user_id"]
    
    try:
        # Use direct search method
        retrieved_docs = await search_documents_directly(query, user_id, limit=5)
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Retrieved {len(retrieved_docs)} documents for user {user_id}")
        
        # Log retrieved documents for debugging
        for i, doc in enumerate(retrieved_docs):
            doc_type = doc.metadata.get('type', 'unknown')
            content_preview = doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Doc {i+1} ({doc_type}): {content_preview}")
        
        return {"retrieved_info": retrieved_docs}
        
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR in retrieve_information: {e}")
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