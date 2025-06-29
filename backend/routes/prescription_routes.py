from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Header
from controllers.prescription_controller import process_prescription, get_user_prescriptions, get_active_medications
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
    Upload and process a prescription file
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
async def delete_prescription(
    prescription_id: str,
    user_id: str = Header(None, alias="X-User-ID")
):
    """
    Delete a prescription and its associated medication reminders
    """
    try:
        from utils.db import db
        from bson import ObjectId
        
        prescriptions_collection = db["prescriptions"]
        medications_collection = db["medications"]
        
        # Build query with user_id filter if provided
        query = {"_id": ObjectId(prescription_id)}
        if user_id:
            query["user_id"] = user_id
        
        # Delete prescription
        prescription_result = await prescriptions_collection.delete_one(query)
        
        if prescription_result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Prescription not found or access denied")
        
        # Delete associated medication reminders
        med_query = {"prescription_id": prescription_id}
        if user_id:
            med_query["user_id"] = user_id
            
        medication_result = await medications_collection.delete_many(med_query)
        
        return {
            "status": "success",
            "message": "Prescription and associated reminders deleted successfully",
            "deleted_reminders": medication_result.deleted_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting prescription: {str(e)}")