from utils.db import db
from datetime import datetime, timedelta
from fastapi import HTTPException
from bson import ObjectId
import re

medications_collection = db["medications"]
medication_logs_collection = db["medication_logs"]
medication_confirmations_collection = db["medication_confirmations"]

async def log_medication_reminder(medication_id: str, patient_name: str, contact_number: str, scheduled_time: str):
    """
    Log when a medication reminder is sent
    """
    try:
        log_entry = {
            "medication_id": medication_id,
            "patient_name": patient_name,
            "contact_number": contact_number,
            "scheduled_time": scheduled_time,
            "sent_time": datetime.now(),
            "status": "pending",
            "response_received": False
        }
        
        result = await medication_logs_collection.insert_one(log_entry)
        return str(result.inserted_id)
    except Exception as e:
        print(f"Error logging medication reminder: {e}")
        return None

def normalize_phone_number(phone_number: str) -> str:
    """
    Normalize phone number by removing prefixes and formatting consistently
    """
    # Remove whatsapp: prefix if present
    phone_number = phone_number.replace('whatsapp:', '')
    
    # Remove any spaces, dashes, or other formatting
    phone_number = re.sub(r'[^\d+]', '', phone_number)
    
    # Ensure it starts with + if it doesn't already
    if not phone_number.startswith('+'):
        phone_number = '+' + phone_number
    
    return phone_number

async def process_medication_response(contact_number: str, message: str):
    """
    Process incoming SMS/WhatsApp responses for medication confirmation
    """
    try:
        # Normalize the contact number
        normalized_contact = normalize_phone_number(contact_number)
        print(f"Processing response from {contact_number} -> normalized: {normalized_contact}")
        print(f"Message: {message}")
        
        # Clean and normalize the message
        message_lower = message.lower().strip()
        
        # Check for positive confirmation keywords
        positive_keywords = ['yes', 'y', 'taken', 'done', 'ok', 'okay', 'completed', 'finished']
        negative_keywords = ['no', 'n', 'not taken', 'missed', 'forgot', 'skip', 'skipped']
        
        is_positive = any(keyword in message_lower for keyword in positive_keywords)
        is_negative = any(keyword in message_lower for keyword in negative_keywords)
        
        if not (is_positive or is_negative):
            return {"status": "ignored", "message": "Message not recognized as medication response"}
        
        # Find the most recent pending medication log for this contact number
        current_time = datetime.now()
        # Look for logs from the last 4 hours (increased window)
        time_threshold = current_time - timedelta(hours=4)
        
        # Try multiple contact number formats
        possible_numbers = [
            normalized_contact,
            contact_number,
            contact_number.replace('whatsapp:', ''),
            '+' + contact_number.replace('whatsapp:', '').replace('+', ''),
        ]
        
        # Remove duplicates while preserving order
        possible_numbers = list(dict.fromkeys(possible_numbers))
        
        print(f"Searching for logs with contact numbers: {possible_numbers}")
        
        recent_log = await medication_logs_collection.find_one({
            "contact_number": {"$in": possible_numbers},
            "status": "pending",
            "sent_time": {"$gte": time_threshold}
        }, sort=[("sent_time", -1)])
        
        if not recent_log:
            print(f"No pending medication log found for any of these numbers: {possible_numbers}")
            print(f"Time threshold: {time_threshold}")
            
            # Debug: Show recent logs for this number
            debug_logs = []
            async for log in medication_logs_collection.find({
                "contact_number": {"$in": possible_numbers}
            }).sort("sent_time", -1).limit(5):
                debug_logs.append({
                    "contact_number": log.get("contact_number"),
                    "status": log.get("status"),
                    "sent_time": log.get("sent_time"),
                    "scheduled_time": log.get("scheduled_time")
                })
            
            print(f"Recent logs for debugging: {debug_logs}")
            return {"status": "no_pending", "message": "No pending medication reminder found", "debug_logs": debug_logs}
        
        print(f"Found matching log: {recent_log}")
        
        # Update the log status
        new_status = "taken" if is_positive else "missed"
        
        update_result = await medication_logs_collection.update_one(
            {"_id": recent_log["_id"]},
            {
                "$set": {
                    "status": new_status,
                    "response_received": True,
                    "response_time": current_time,
                    "response_message": message
                }
            }
        )
        
        print(f"Update result: {update_result.modified_count} documents modified")
        
        # Create confirmation record
        confirmation_record = {
            "medication_id": recent_log["medication_id"],
            "patient_name": recent_log["patient_name"],
            "contact_number": normalized_contact,
            "scheduled_time": recent_log["scheduled_time"],
            "confirmation_time": current_time,
            "is_taken": is_positive,
            "response_message": message,
            "log_id": str(recent_log["_id"])
        }
        
        await medication_confirmations_collection.insert_one(confirmation_record)
        
        return {
            "status": "success",
            "message": f"Medication marked as {new_status}",
            "is_taken": is_positive,
            "patient_name": recent_log["patient_name"],
            "log_updated": update_result.modified_count > 0
        }
        
    except Exception as e:
        print(f"Error processing medication response: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

async def get_medication_adherence(patient_name: str, days: int = 7):
    """
    Get medication adherence statistics for a patient
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get all medication logs for the patient in the specified period
        logs = []
        async for log in medication_logs_collection.find({
            "patient_name": patient_name,
            "sent_time": {"$gte": start_date, "$lte": end_date}
        }):
            log["_id"] = str(log["_id"])
            logs.append(log)
        
        total_reminders = len(logs)
        taken_count = len([log for log in logs if log["status"] == "taken"])
        missed_count = len([log for log in logs if log["status"] == "missed"])
        pending_count = len([log for log in logs if log["status"] == "pending"])
        
        adherence_rate = (taken_count / total_reminders * 100) if total_reminders > 0 else 0
        
        return {
            "status": "success",
            "patient_name": patient_name,
            "period_days": days,
            "total_reminders": total_reminders,
            "taken": taken_count,
            "missed": missed_count,
            "pending": pending_count,
            "adherence_rate": round(adherence_rate, 2),
            "logs": logs
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting adherence data: {str(e)}")

async def get_recent_confirmations(patient_name: str, limit: int = 10):
    """
    Get recent medication confirmations for a patient
    """
    try:
        confirmations = []
        async for confirmation in medication_confirmations_collection.find(
            {"patient_name": patient_name}
        ).sort("confirmation_time", -1).limit(limit):
            confirmation["_id"] = str(confirmation["_id"])
            confirmations.append(confirmation)
        
        return {
            "status": "success",
            "confirmations": confirmations
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting confirmations: {str(e)}")