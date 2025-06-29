import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import HTTPException
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from utils.db import db

# Import the compiled graphs from summary_graph
from rag_pipeline.summary_graph import query_graph, PrescriptionIngestionState

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

        # Retrieve existing chat history
        chat_sessions_collection = db["chat_sessions"]
        existing_session = await chat_sessions_collection.find_one({"user_id": user_id, "session_id": session_id})
        
        existing_chat_history = []
        if existing_session and "chat_history" in existing_session:
            # Convert dict back to BaseMessage objects
            for msg_dict in existing_session["chat_history"]:
                if msg_dict.get("type") == "human":
                    existing_chat_history.append(HumanMessage(content=msg_dict["content"]))
                elif msg_dict.get("type") == "ai":
                    existing_chat_history.append(AIMessage(content=msg_dict["content"]))

        # Build the initial state for the graph
        initial_state: PrescriptionIngestionState = {
            "user_id": user_id,
            "session_id": session_id,
            "question": message,
            "chat_history": existing_chat_history,
            "answer": "",
            "retrieved_info": [],
            "parsed_prescription": None,
            "user_summary": None,
            "ingestion_status": "started",
            "prescription_text": "",
        }

        try:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Invoking query graph for user {user_id}")
            final_state = await query_graph.ainvoke(initial_state)
            response_content = final_state.get("answer", "No answer generated.")
            updated_chat_history = final_state.get("chat_history", [])

            # Convert BaseMessage objects to dict for storage
            chat_history_dicts = []
            for msg in updated_chat_history:
                if isinstance(msg, HumanMessage):
                    chat_history_dicts.append({"type": "human", "content": msg.content})
                elif isinstance(msg, AIMessage):
                    chat_history_dicts.append({"type": "ai", "content": msg.content})

            # Persist chat history in MongoDB
            await chat_sessions_collection.update_one(
                {"user_id": user_id, "session_id": session_id},
                {"$set": {"chat_history": chat_history_dicts}},
                upsert=True
            )

            print(f"[{datetime.now().strftime('%H:%M:%S')}] Response generated for thread {thread_id}.")
            return {
                "user_id": user_id,
                "session_id": session_id,
                "question": message,
                "answer": response_content,
                "chat_history": chat_history_dicts
            }
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Error in send_chat_message for thread {thread_id}: {e}")
            import traceback
            traceback.print_exc()
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