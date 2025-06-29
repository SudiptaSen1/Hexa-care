from utils.db import db
from datetime import datetime, timedelta
from fastapi import HTTPException
from bson import ObjectId
import re

prescriptions_collection = db["prescriptions"]

async def get_user_prescriptions(patient_name: str, user_id: str = None):
    """
    Get all prescriptions for a specific patient, optionally filtered by user_id
    """
    try:
        # Build query with user_id filter if provided and use regex for patient name
        query = {"patient_name": {"$regex": f"^{re.escape(patient_name)}$", "$options": "i"}}
        if user_id:
            query["user_id"] = user_id
            
        prescriptions = []
        async for prescription in prescriptions_collection.find(query):
            # Convert ObjectId to string and datetime objects to strings for JSON serialization
            prescription_dict = {
                "_id": str(prescription["_id"]),
                "user_id": prescription.get("user_id", ""),
                "patient_name": prescription.get("patient_name", ""),
                "age": prescription.get("age", ""),
                "date": prescription.get("date", ""),
                "medicines": prescription.get("medicines", []),
                "diagnosis": prescription.get("diagnosis", ""),
                "doctor_instructions": prescription.get("doctor_instructions", []),
                "upload_date": prescription.get("upload_date").isoformat() if prescription.get("upload_date") else None,
                "created_at": prescription.get("created_at").isoformat() if prescription.get("created_at") else None
            }
            prescriptions.append(prescription_dict)
        
        return {
            "status": "success",
            "prescriptions": prescriptions
        }
    except Exception as e:
        print(f"Error in get_user_prescriptions: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching prescriptions: {str(e)}")

async def delete_prescription(prescription_id: str, user_id: str = None):
    """
    Delete a prescription
    """
    try:
        # Build query with user_id filter if provided
        query = {"_id": ObjectId(prescription_id)}
        if user_id:
            query["user_id"] = user_id
        
        # Delete prescription
        prescription_result = await prescriptions_collection.delete_one(query)
        
        if prescription_result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Prescription not found or access denied")
        
        return {
            "status": "success",
            "message": "Prescription deleted successfully"
        }
        
    except Exception as e:
        print(f"Error in delete_prescription: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error deleting prescription: {str(e)}")