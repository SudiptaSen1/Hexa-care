import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
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
            medications_collection = db["medications"]
            medication_logs_collection = db["medication_logs"]
            
            # Get user's prescriptions
            user_prescriptions = []
            async for prescription in prescriptions_collection.find({"user_id": user_id}):
                user_prescriptions.append(prescription)

            # Get user's active medications
            current_date = datetime.now()
            active_medications = []
            async for medication in medications_collection.find({
                "user_id": user_id,
                "start_date": {"$lte": current_date}
            }):
                # Check if medication is still active
                start_date = medication["start_date"]
                duration_days = medication["duration_days"]
                end_date = start_date + timedelta(days=duration_days)
                
                if current_date <= end_date:
                    active_medications.append(medication)

            # Get recent medication logs (last 7 days)
            week_ago = current_date - timedelta(days=7)
            recent_logs = []
            async for log in medication_logs_collection.find({
                "user_id": user_id,
                "sent_time": {"$gte": week_ago}
            }).sort("sent_time", -1).limit(20):
                recent_logs.append(log)

            # Retrieve existing chat history
            chat_sessions_collection = db["chat_sessions"]
            existing_session = await chat_sessions_collection.find_one({"user_id": user_id, "session_id": session_id})
            
            chat_history = []
            if existing_session and "chat_history" in existing_session:
                chat_history = existing_session["chat_history"]

            # Build comprehensive context
            context = self._build_comprehensive_context(user_prescriptions, active_medications, recent_logs)
            
            # Build chat history string
            chat_history_str = ""
            for msg in chat_history[-10:]:  # Last 10 messages for context
                chat_history_str += f"{msg['type']}: {msg['content']}\n"

            # Create prompt for Gemini
            prompt = f"""You are a helpful medical assistant with access to the user's complete medical information. 
You can answer questions about their medications, prescriptions, adherence, schedules, and provide health guidance.

IMPORTANT: Always base your responses on the actual data provided below. Be specific and reference the actual medications, times, and status when relevant.

User's Medical Information:
{context}

Chat History:
{chat_history_str}

User Question: {message}

Please provide a helpful, accurate response based on the medical information available. Include specific details from their prescriptions and medication history when relevant. If you need more information, ask specific questions. Always remind users to consult healthcare providers for medical decisions."""

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

    def _build_comprehensive_context(self, prescriptions: List[Dict], medications: List[Dict], logs: List[Dict]) -> str:
        """Build comprehensive context string from all user's medical data"""
        context_parts = []
        
        # Prescriptions section
        if prescriptions:
            context_parts.append("=== PRESCRIPTIONS ===")
            for i, prescription in enumerate(prescriptions, 1):
                parsed_data = prescription.get('parsed_data', {})
                upload_date = prescription.get('upload_date')
                upload_date_str = upload_date.strftime('%Y-%m-%d') if upload_date else 'Unknown'
                
                context_parts.append(f"Prescription {i} (Uploaded: {upload_date_str}):")
                context_parts.append(f"  Patient: {parsed_data.get('patient_name', prescription.get('patient_name', 'Unknown'))}")
                context_parts.append(f"  Date: {parsed_data.get('date', 'Unknown')}")
                context_parts.append(f"  Diagnosis: {parsed_data.get('diagnosis', 'Not specified')}")
                
                medicines = parsed_data.get('medicines', [])
                if medicines:
                    context_parts.append("  Medications:")
                    for med in medicines:
                        med_info = f"    - {med.get('name', 'Unknown')}: {med.get('dosage', 'Unknown dosage')}"
                        if med.get('duration'):
                            med_info += f" for {med['duration']}"
                        if med.get('notes'):
                            med_info += f" ({med['notes']})"
                        context_parts.append(med_info)
                
                instructions = parsed_data.get('doctor_instructions', [])
                if instructions:
                    context_parts.append("  Doctor's Instructions:")
                    for instruction in instructions:
                        context_parts.append(f"    - {instruction}")
                
                context_parts.append("")
        else:
            context_parts.append("=== PRESCRIPTIONS ===")
            context_parts.append("No prescriptions uploaded yet.")
            context_parts.append("")

        # Active medications section
        if medications:
            context_parts.append("=== ACTIVE MEDICATIONS ===")
            for i, medication in enumerate(medications, 1):
                start_date = medication.get('start_date')
                start_date_str = start_date.strftime('%Y-%m-%d') if start_date else 'Unknown'
                
                context_parts.append(f"Medication {i}:")
                context_parts.append(f"  Name: {medication.get('name', 'Unknown')}")
                context_parts.append(f"  Dosage: {medication.get('dosage', 'Unknown')}")
                context_parts.append(f"  Times: {', '.join(medication.get('times', []))}")
                context_parts.append(f"  Duration: {medication.get('duration_days', 0)} days")
                context_parts.append(f"  Started: {start_date_str}")
                if medication.get('message'):
                    context_parts.append(f"  Reminder Message: {medication['message']}")
                context_parts.append("")
        else:
            context_parts.append("=== ACTIVE MEDICATIONS ===")
            context_parts.append("No active medications scheduled.")
            context_parts.append("")

        # Recent medication logs section
        if logs:
            context_parts.append("=== RECENT MEDICATION HISTORY (Last 7 days) ===")
            for i, log in enumerate(logs, 1):
                sent_time = log.get('sent_time')
                sent_time_str = sent_time.strftime('%Y-%m-%d %H:%M') if sent_time else 'Unknown'
                response_time = log.get('response_time')
                response_time_str = response_time.strftime('%Y-%m-%d %H:%M') if response_time else None
                
                context_parts.append(f"Log {i}:")
                context_parts.append(f"  Time: {log.get('scheduled_time', 'Unknown')}")
                context_parts.append(f"  Status: {log.get('status', 'Unknown')}")
                context_parts.append(f"  Sent: {sent_time_str}")
                if log.get('response_message'):
                    context_parts.append(f"  Response: {log['response_message']}")
                if response_time_str:
                    context_parts.append(f"  Responded at: {response_time_str}")
                context_parts.append("")
        else:
            context_parts.append("=== RECENT MEDICATION HISTORY ===")
            context_parts.append("No recent medication logs available.")
            context_parts.append("")

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
                created_at = session_doc.get("created_at")
                created_at_str = created_at.isoformat() if created_at else None
                
                sessions.append({
                    "session_id": session_doc["session_id"],
                    "session_name": session_doc.get("session_name", "Unnamed Session"),
                    "created_at": created_at_str
                })
            return {"user_id": user_id, "sessions": sessions}
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Error retrieving sessions for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve sessions: {e}")

chat_controller = ChatController()