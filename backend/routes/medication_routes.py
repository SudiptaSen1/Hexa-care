from fastapi import APIRouter, HTTPException, Form
from controllers.medication_controller import (
    process_medication_response, 
    get_medication_adherence, 
    get_recent_confirmations
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
async def get_adherence(patient_name: str, days: int = 7):
    """
    Get medication adherence statistics for a patient
    """
    return await get_medication_adherence(patient_name, days)

@router.get("/medication-confirmations/{patient_name}")
async def get_confirmations(patient_name: str, limit: int = 10):
    """
    Get recent medication confirmations for a patient
    """
    return await get_recent_confirmations(patient_name, limit)

@router.get("/medication-status/{patient_name}")
async def get_medication_status(patient_name: str):
    """
    Get current medication status overview for a patient
    """
    try:
        from utils.db import db
        from datetime import datetime, timedelta
        
        medication_logs_collection = db["medication_logs"]
        
        # Get today's medication logs
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        
        today_logs = []
        async for log in medication_logs_collection.find({
            "patient_name": patient_name,
            "sent_time": {"$gte": today, "$lt": tomorrow}
        }).sort("sent_time", 1):
            log["_id"] = str(log["_id"])
            today_logs.append(log)
        
        taken_today = len([log for log in today_logs if log["status"] == "taken"])
        missed_today = len([log for log in today_logs if log["status"] == "missed"])
        pending_today = len([log for log in today_logs if log["status"] == "pending"])
        
        return {
            "status": "success",
            "patient_name": patient_name,
            "date": today.strftime("%Y-%m-%d"),
            "today_summary": {
                "total": len(today_logs),
                "taken": taken_today,
                "missed": missed_today,
                "pending": pending_today
            },
            "today_logs": today_logs
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting medication status: {str(e)}")