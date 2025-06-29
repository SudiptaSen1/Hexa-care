import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import HTTPException
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from utils.db import db  # Make sure this provides your MongoDB client

# Import the compiled graphs from summary_graph
from rag_pipeline.summary_graph import query_graph, PrescriptionIngestionState

# If you have a separate db_service for managing session metadata
# (which is implied by your `chat_service.py` logic), import it here.
# For example:
# from services.database_service import db_service
# NOTE: The provided `chat_service.py` indicates `db_service` is used there,
# but `chat_controller.py` itself doesn't directly use it for session listing.
# If `get_all_user_sessions` is intended to list sessions from LangGraph's
# checkpoint store directly, that would require different logic.
# Based on the structure, `get_all_user_sessions` likely lists sessions
# from your custom `sessions_collection` managed by your application.


class ChatController:
    # Function to start a new chat session (generate session_id)
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

    # Function to send a message and get a response from the RAG pipeline
    async def send_chat_message(self, user_id: str, session_id: str, message: str) -> Dict[str, Any]:
        thread_id = f"{user_id}_{session_id}"
        print(f"[{datetime.now().strftime('%H:%M:%S')}] User {user_id} sending message in session {session_id} (thread: {thread_id}): {message}")

        # Build the initial state for the graph
        initial_state: PrescriptionIngestionState = {
            "user_id": user_id,
            "session_id": session_id,
            "question": message,
            "chat_history": [],
            "answer": "",
            "retrieved_info": [],
            "parsed_prescription": None,
            "user_summary": None,
            "ingestion_status": "started",
        }

        try:
            final_state = await query_graph.ainvoke(initial_state)
            response_content = final_state.get("answer", "No answer generated.")
            updated_chat_history = final_state.get("chat_history", [])

            # Persist chat history in MongoDB
            chat_sessions_collection = db["chat_sessions"]
            await chat_sessions_collection.update_one(
                {"user_id": user_id, "session_id": session_id},
                {"$set": {"chat_history": [msg.dict() for msg in updated_chat_history]}},
                upsert=True
            )

            print(f"[{datetime.now().strftime('%H:%M:%S')}] Response generated for thread {thread_id}.")
            return {
                "user_id": user_id,
                "session_id": session_id,
                "question": message,
                "answer": response_content,
                "chat_history": [msg.dict() for msg in updated_chat_history]
            }
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Error in send_chat_message for thread {thread_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to process chat message: {e}")

    # Function to retrieve chat history for a specific session
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
    # Function to get all chat sessions for a user
    # This assumes session metadata (like session_name, created_at) is stored
    # in a separate custom collection, not directly derived from LangGraph's raw checkpoints.
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