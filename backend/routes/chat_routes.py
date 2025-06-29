from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel
from typing import List, Dict, Any

from controllers.chat_controller import chat_controller # Import the new controller

router = APIRouter()

# Pydantic models for request/response
class StartChatResponse(BaseModel):
    user_id: str
    session_id: str
    message: str

class ChatMessageRequest(BaseModel):
    message: str

class ChatMessageResponse(BaseModel):
    user_id: str
    session_id: str
    question: str
    answer: str
    chat_history: List[Dict[str, Any]] # history will be a list of dicts from BaseMessage.dict()

class ChatHistoryResponse(BaseModel):
    user_id: str
    session_id: str
    chat_history: List[Dict[str, Any]]

class UserSessionsResponse(BaseModel):
    user_id: str
    sessions: List[Dict[str, str]]


@router.post("/sessions/start/{user_id}", response_model=StartChatResponse, summary="Start a new chat session for a user")
async def start_new_chat(
    user_id: str = Path(..., description="The ID of the user starting the chat session")
):
    """
    Starts a new chat session for the given user, generating a unique session ID.
    """
    try:
        return await chat_controller.create_chat_session(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start new chat session: {e}")

@router.post("/sessions/{user_id}/{session_id}/message", response_model=ChatMessageResponse, summary="Send a message to a chat session")
async def send_message_to_chat(
    chat_message: ChatMessageRequest,
    user_id: str = Path(..., description="The ID of the user"),
    session_id: str = Path(..., description="The ID of the chat session")
):
    """
    Sends a message to an ongoing chat session and retrieves the AI's response.
    The chat history for this session is maintained persistently.
    """
    try:
        return await chat_controller.send_chat_message(user_id, session_id, chat_message.message)
    except HTTPException as e:
        raise e # Re-raise HTTPExceptions from controller
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message: {e}")

@router.get("/history/{user_id}/{session_id}", response_model=ChatHistoryResponse, summary="Get chat history for a specific session")
async def get_session_history(
    user_id: str = Path(..., description="The ID of the user"),
    session_id: str = Path(..., description="The ID of the chat session")
):
    """
    Retrieves the complete chat history for a given user and session ID.
    """
    try:
        return await chat_controller.get_chat_history(user_id, session_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve chat history: {e}")

@router.get("/sessions/{user_id}", response_model=UserSessionsResponse, summary="Get all chat sessions for a user")
async def get_all_sessions_for_user(
    user_id: str = Path(..., description="The ID of the user")
):
    """
    Retrieves a list of all chat sessions associated with a specific user ID.
    """
    try:
        return await chat_controller.get_all_user_sessions(user_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve user sessions: {e}")