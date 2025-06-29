import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import HTTPException
import google.generativeai as genai
import os
from utils.db import db

# Configure Gemini
GENAI_API_KEY = os.getenv("GEMINI_API_KEY")
if GENAI_API_KEY:
    genai.configure(api_key=GENAI_API_KEY)

gemini_model = genai.GenerativeModel("gemini-1.5-flash")

class ChatController:
    async def create_chat_session(self, user_id: str) -> Dict[str, str]:
        session_id = str(uuid.uuid4())
        created_at = datetime.utcnow()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] New chat session created for user {user_id}: {session_id}")

        # Insert session metadata into the sessions_metadata collection
        sessions_metadata_collection = db["sessions_metadata"]
        await sessions_metadata_collection.insert_one({
            "user_id": user_id,
            "session_id": session_id,
            "session_name": f"Session {created_at.strftime('%Y-%m-%d %H:%M:%S')}",
            "created_at": created_at
        })

        return {"user_id": user_id, "session_id": session_id, "message": "New chat session started."}

    async def send_chat_message(self, user_id: str, session_id: str, message: str) -> Dict[str, Any]:
        thread_id = f"{user_id}_{session_id}"
        print(f"[{datetime.now().strftime('%H:%M:%S')}] User {user_id} sending message in session {session_id} (thread: {thread_id}): {message}")

        try:
            # Get user's prescription data for context
            prescriptions_collection = db["prescriptions"]
            user_prescriptions = []
            async for prescription in prescriptions_collection.find({"user_id": user_id}):
                user_prescriptions.append(prescription)

            # Retrieve existing chat history
            chat_sessions_collection = db["chat_sessions"]
            existing_session = await chat_sessions_collection.find_one({"user_id": user_id, "session_id": session_id})
            
            chat_history = []
            if existing_session and "chat_history" in existing_session:
                chat_history = existing_session["chat_history"]

            # Build context from user's prescriptions
            context = self._build_prescription_context(user_prescriptions)
            
            # Build chat history string
            chat_history_str = ""
            for msg in chat_history[-10:]:  # Last 10 messages for context
                chat_history_str += f"{msg['type']}: {msg['content']}\n"

            # Create prompt for Gemini
            prompt = f"""You are a helpful medical assistant. You have access to the user's prescription information below. 
Use this information to answer their questions about medications, dosages, treatments, and health advice.

User's Prescription Information:
{context}

Chat History:
{chat_history_str}

User Question: {message}

Please provide a helpful, accurate response based on the prescription information available. If the question cannot be answered from the prescription data, politely explain that and suggest consulting with a healthcare provider."""

            # Generate response using Gemini
            response = gemini_model.generate_content(prompt)
            response_content = response.text

            # Update chat history
            new_messages = [
                {"type": "human", "content": message},
                {"type": "ai", "content": response_content}
            ]
            
            updated_chat_history = chat_history + new_messages

            # Persist chat history in MongoDB
            await chat_sessions_collection.update_one(
                {"user_id": user_id, "session_id": session_id},
                {"$set": {"chat_history": updated_chat_history}},
                upsert=True
            )

            print(f"[{datetime.now().strftime('%H:%M:%S')}] Response generated for thread {thread_id}.")
            return {
                "user_id": user_id,
                "session_id": session_id,
                "question": message,
                "answer": response_content,
                "chat_history": updated_chat_history
            }
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Error in send_chat_message for thread {thread_id}: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Failed to process chat message: {e}")

    def _build_prescription_context(self, prescriptions: List[Dict]) -> str:
        """Build context string from user's prescriptions"""
        if not prescriptions:
            return "No prescription information available."
        
        context_parts = []
        for i, prescription in enumerate(prescriptions, 1):
            context_parts.append(f"Prescription {i}:")
            context_parts.append(f"  Patient: {prescription.get('patient_name', 'Unknown')}")
            context_parts.append(f"  Date: {prescription.get('date', 'Unknown')}")
            context_parts.append(f"  Diagnosis: {prescription.get('diagnosis', 'Not specified')}")
            
            medicines = prescription.get('medicines', [])
            if medicines:
                context_parts.append("  Medications:")
                for med in medicines:
                    med_info = f"    - {med.get('name', 'Unknown')}: {med.get('dosage', 'Unknown dosage')}"
                    if med.get('duration'):
                        med_info += f" for {med['duration']}"
                    if med.get('notes'):
                        med_info += f" ({med['notes']})"
                    context_parts.append(med_info)
            
            instructions = prescription.get('doctor_instructions', [])
            if instructions:
                context_parts.append("  Doctor's Instructions:")
                for instruction in instructions:
                    context_parts.append(f"    - {instruction}")
            
            context_parts.append("")  # Empty line between prescriptions
        
        return "\n".join(context_parts)

    async def get_chat_history(self, user_id: str, session_id: str) -> Dict[str, Any]:
        thread_id = f"{user_id}_{session_id}"
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Retrieving chat history for user {user_id}, session {session_id} (thread: {thread_id}).")
        try:
            chat_sessions_collection = db["chat_sessions"]
            session = await chat_sessions_collection.find_one({"user_id": user_id, "session_id": session_id})
            if session and "chat_history" in session:
                chat_history = session["chat_history"]
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Chat history retrieved for thread {thread_id}.")
                return {
                    "user_id": user_id,
                    "session_id": session_id,
                    "chat_history": chat_history
                }
            print(f"[{datetime.now().strftime('%H:%M:%S')}] No chat history found for thread {thread_id}.")
            return {"user_id": user_id, "session_id": session_id, "chat_history": []}
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Error retrieving chat history for thread {thread_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve chat history: {e}")

    async def get_all_user_sessions(self, user_id: str) -> Dict[str, Any]:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Getting all chat sessions for user {user_id}.")
        try:
            sessions_metadata_collection = db["sessions_metadata"]
            sessions_cursor = sessions_metadata_collection.find({"user_id": user_id})
            sessions = []
            async for session_doc in sessions_cursor:
                sessions.append({
                    "session_id": session_doc["session_id"],
                    "session_name": session_doc.get("session_name", "Unnamed Session"),
                    "created_at": session_doc.get("created_at").isoformat() if session_doc.get("created_at") else None
                })
            return {"user_id": user_id, "sessions": sessions}
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Error retrieving sessions for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve sessions: {e}")

chat_controller = ChatController()