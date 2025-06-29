from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Header
from controllers.prescription_controller import process_prescription, get_user_prescriptions, get_active_medications, delete_prescription
from controllers.upload_controller import upload_prescription_and_process
from models.prescription_model import UserSchedule
import json

router = APIRouter()

@router.post("/upload-prescription")
async def upload_prescription(
    file: UploadFile = File(...),
    user_schedule_json: str = Form(...),
    user_id: str = Header(None, alias="X-User-ID")
):
    """
    Upload and process a prescription file with user schedule
    """
    try:
        # Parse the user schedule from JSON string
        user_schedule = json.loads(user_schedule_json)
        
        # Add user_id to user_schedule if provided
        if user_id:
            user_schedule["user_id"] = user_id
        
        # Validate required fields
        required_fields = ["patient_name", "contact_number", "wake_up_time", "breakfast_time", 
                          "lunch_time", "dinner_time", "sleep_time"]
        
        for field in required_fields:
            if field not in user_schedule:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Set default values for optional fields
        user_schedule.setdefault("before_breakfast_offset_minutes", 20)
        user_schedule.setdefault("after_lunch_offset_minutes", 30)
        user_schedule.setdefault("before_lunch_offset_minutes", 10)
        user_schedule.setdefault("after_dinner_offset_minutes", 45)
        
        # Process the prescription with the full user schedule
        return await process_prescription(file, user_schedule)
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format for user_schedule")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/prescriptions/{patient_name}")
async def get_prescriptions(
    patient_name: str,
    user_id: str = Header(None, alias="X-User-ID")
):
    """
    Get all prescriptions for a patient
    """
    return await get_user_prescriptions(patient_name, user_id)

@router.get("/active-medications/{patient_name}")
async def get_medications(
    patient_name: str,
    user_id: str = Header(None, alias="X-User-ID")
):
    """
    Get all active medication reminders for a patient
    """
    return await get_active_medications(patient_name, user_id)

@router.delete("/prescription/{prescription_id}")
async def delete_prescription_endpoint(
    prescription_id: str,
    user_id: str = Header(None, alias="X-User-ID")
):
    """
    Delete a prescription and its associated medication reminders
    """
    return await delete_prescription(prescription_id, user_id)