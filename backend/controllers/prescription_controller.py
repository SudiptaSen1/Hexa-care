import os
import tempfile
from fastapi import UploadFile, HTTPException
from prescription_parser import get_prescription_data, create_personalized_messages_by_exact_time
from utils.db import db
from datetime import datetime, timedelta
import json

prescriptions_collection = db["prescriptions"]
medications_collection = db["medications"]

async def process_prescription(file: UploadFile, user_schedule: dict):
    """
    Process uploaded prescription file and store medication reminders in database
    """
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            # Parse prescription using AI
            parsed_data = get_prescription_data(temp_file_path, user_schedule)
            
            if not parsed_data:
                raise HTTPException(status_code=400, detail="Failed to parse prescription")

            # Generate personalized messages
            messages_by_time = create_personalized_messages_by_exact_time(parsed_data)

            # Store prescription data with user_id
            prescription_record = {
                "user_id": user_schedule.get("user_id"),
                "patient_name": user_schedule["patient_name"],
                "contact_number": user_schedule["contact_number"],
                "upload_date": datetime.now(),
                "parsed_data": parsed_data,
                "messages_by_time": messages_by_time,
                "user_schedule": user_schedule
            }
            
            prescription_result = await prescriptions_collection.insert_one(prescription_record)
            prescription_id = str(prescription_result.inserted_id)

            # Store individual medication reminders for the scheduler
            medication_records = []
            
            for time_str, messages in messages_by_time.items():
                for message in messages:
                    # Calculate duration in days (use the longest duration from medicines)
                    max_duration_days = 0
                    if 'medicines' in parsed_data:
                        for medicine in parsed_data['medicines']:
                            duration_str = medicine.get('duration', '0 days')
                            # Extract number from duration string (e.g., "20 days" -> 20)
                            try:
                                duration_days = int(''.join(filter(str.isdigit, duration_str)))
                                max_duration_days = max(max_duration_days, duration_days)
                            except:
                                duration_days = 30  # Default to 30 days if parsing fails
                                max_duration_days = max(max_duration_days, duration_days)
                    
                    if max_duration_days == 0:
                        max_duration_days = 30  # Default duration

                    medication_record = {
                        "user_id": user_schedule.get("user_id"),
                        "prescription_id": prescription_id,
                        "patient_name": user_schedule["patient_name"],
                        "contact_number": user_schedule["contact_number"],
                        "name": f"Prescription Medicines - {time_str}",
                        "dosage": "As prescribed",
                        "times": [time_str],
                        "duration_days": max_duration_days,
                        "start_date": datetime.now(),
                        "message": message,
                        "created_at": datetime.now()
                    }
                    medication_records.append(medication_record)

            if medication_records:
                await medications_collection.insert_many(medication_records)

            return {
                "status": "success",
                "message": "Prescription processed successfully",
                "prescription_id": prescription_id,
                "parsed_data": parsed_data,
                "messages_by_time": messages_by_time,
                "total_reminders": len(medication_records)
            }

        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing prescription: {str(e)}")

async def get_user_prescriptions(patient_name: str, user_id: str = None):
    """
    Get all prescriptions for a specific patient, optionally filtered by user_id
    """
    try:
        # Build query with user_id filter if provided and use regex for patient name
        query = {"patient_name": {"$regex": f"^{patient_name.replace(' ', '.*')}.*$", "$options": "i"}}
        if user_id:
            query["user_id"] = user_id
            
        prescriptions = []
        async for prescription in prescriptions_collection.find(query):
            # Convert ObjectId to string and datetime objects to strings for JSON serialization
            prescription_dict = {
                "_id": str(prescription["_id"]),
                "user_id": prescription.get("user_id", ""),
                "patient_name": prescription.get("patient_name", ""),
                "contact_number": prescription.get("contact_number", ""),
                "upload_date": prescription.get("upload_date").isoformat() if prescription.get("upload_date") else None,
                "parsed_data": prescription.get("parsed_data", {}),
                "messages_by_time": prescription.get("messages_by_time", {}),
                "user_schedule": prescription.get("user_schedule", {})
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

async def get_active_medications(patient_name: str, user_id: str = None):
    """
    Get all active medication reminders for a specific patient, optionally filtered by user_id
    """
    try:
        current_date = datetime.now()
        
        # Build query with user_id filter if provided and use regex for patient name
        query = {
            "patient_name": {"$regex": f"^{patient_name.replace(' ', '.*')}.*$", "$options": "i"},
            "start_date": {"$lte": current_date}
        }
        if user_id:
            query["user_id"] = user_id
        
        active_medications = []
        async for medication in medications_collection.find(query):
            # Check if medication is still active
            start_date = medication["start_date"]
            duration_days = medication["duration_days"]
            end_date = start_date + timedelta(days=duration_days)
            
            if current_date <= end_date:
                medication_dict = {
                    "_id": str(medication["_id"]),
                    "user_id": medication.get("user_id", ""),
                    "prescription_id": medication.get("prescription_id", ""),
                    "patient_name": medication.get("patient_name", ""),
                    "contact_number": medication.get("contact_number", ""),
                    "name": medication.get("name", ""),
                    "dosage": medication.get("dosage", ""),
                    "times": medication.get("times", []),
                    "duration_days": medication.get("duration_days", 0),
                    "start_date": medication.get("start_date").isoformat() if medication.get("start_date") else None,
                    "end_date": end_date.isoformat(),
                    "message": medication.get("message", ""),
                    "created_at": medication.get("created_at").isoformat() if medication.get("created_at") else None
                }
                active_medications.append(medication_dict)
        
        return {
            "status": "success",
            "active_medications": active_medications
        }
    except Exception as e:
        print(f"Error in get_active_medications: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching active medications: {str(e)}")

async def delete_prescription(prescription_id: str, user_id: str = None):
    """
    Delete a prescription and its associated medication reminders
    """
    try:
        from bson import ObjectId
        
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
        print(f"Error in delete_prescription: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error deleting prescription: {str(e)}")