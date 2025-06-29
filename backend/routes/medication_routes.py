from fastapi import APIRouter, HTTPException, Form, Header
from controllers.medication_controller import (
    process_medication_response, 
    get_medication_adherence, 
    get_recent_confirmations,
    get_medication_status,
    create_test_medication_logs
)

router = APIRouter()

@router.post("/medication-response")
async def handle_medication_response(
    contact_number: str = Form(...),
    message: str = Form(...)
):
    """
    Handle incoming medication confirmation responses
    This endpoint can be called by Twilio webhooks or manual API calls
    """
    return await process_medication_response(contact_number, message)

@router.get("/medication-adherence/{patient_name}")
async def get_adherence(
    patient_name: str, 
    days: int = 7,
    user_id: str = Header(None, alias="X-User-ID")
):
    """
    Get medication adherence statistics for a patient
    """
    return await get_medication_adherence(patient_name, days, user_id)

@router.get("/medication-confirmations/{patient_name}")
async def get_confirmations(
    patient_name: str, 
    limit: int = 10,
    user_id: str = Header(None, alias="X-User-ID")
):
    """
    Get recent medication confirmations for a patient
    """
    return await get_recent_confirmations(patient_name, limit, user_id)

@router.get("/medication-status/{patient_name}")
async def get_medication_status_endpoint(
    patient_name: str,
    user_id: str = Header(None, alias="X-User-ID")
):
    """
    Get current medication status overview for a patient
    """
    return await get_medication_status(patient_name, user_id)

@router.post("/create-test-logs/{patient_name}")
async def create_test_logs(
    patient_name: str,
    user_id: str = Header(None, alias="X-User-ID")
):
    """
    Create test medication logs for demonstration purposes
    """
    return await create_test_medication_logs(patient_name, user_id)