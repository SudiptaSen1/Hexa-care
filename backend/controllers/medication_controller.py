from utils.db import db
from datetime import datetime, timedelta
from fastapi import HTTPException
from bson import ObjectId
import re

medications_collection = db["medications"]
medication_logs_collection = db["medication_logs"]
medication_confirmations_collection = db["medication_confirmations"]

def log_medication_reminder_sync(medication_id: str, patient_name: str, contact_number: str, scheduled_time: str, user_id: str = None):
    """
    Synchronous version of log_medication_reminder for use in scheduler
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
        
        # Add user_id if provided
        if user_id:
            log_entry["user_id"] = user_id
        
        # Use synchronous MongoDB client for scheduler
        from pymongo import MongoClient
        import os
        client = MongoClient(os.getenv("MONGODB_URI"))
        db_sync = client[os.getenv("DB_NAME", "hexacare")]
        result = db_sync["medication_logs"].insert_one(log_entry)
        print(f"✅ Logged medication reminder: {result.inserted_id}")
        return str(result.inserted_id)
    except Exception as e:
        print(f"❌ Error logging medication reminder: {e}")
        return None

async def log_medication_reminder(medication_id: str, patient_name: str, contact_number: str, scheduled_time: str, user_id: str = None):
    """
    Async version for use in API endpoints
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
        
        # Add user_id if provided
        if user_id:
            log_entry["user_id"] = user_id
        
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
                    "sent_time": log.get("sent_time").isoformat() if log.get("sent_time") else None,
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
        
        # Add user_id if present in the log
        if "user_id" in recent_log:
            confirmation_record["user_id"] = recent_log["user_id"]
        
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

async def get_medication_adherence(patient_name: str, days: int = 7, user_id: str = None):
    """
    Get medication adherence statistics for a patient
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Build query with user_id filter if provided and use regex for patient name
        query = {
            "patient_name": {"$regex": f"^{re.escape(patient_name)}$", "$options": "i"},
            "sent_time": {"$gte": start_date, "$lte": end_date}
        }
        if user_id:
            query["user_id"] = user_id
        
        # Get all medication logs for the patient in the specified period
        logs = []
        async for log in medication_logs_collection.find(query):
            # Convert datetime objects to strings for JSON serialization
            log_dict = {
                "_id": str(log["_id"]),
                "medication_id": log.get("medication_id", ""),
                "patient_name": log.get("patient_name", ""),
                "contact_number": log.get("contact_number", ""),
                "scheduled_time": log.get("scheduled_time", ""),
                "sent_time": log.get("sent_time").isoformat() if log.get("sent_time") else None,
                "status": log.get("status", "pending"),
                "response_received": log.get("response_received", False),
                "response_time": log.get("response_time").isoformat() if log.get("response_time") else None,
                "response_message": log.get("response_message", "")
            }
            if "user_id" in log:
                log_dict["user_id"] = log["user_id"]
            logs.append(log_dict)
        
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
        print(f"Error in get_medication_adherence: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error getting adherence data: {str(e)}")

async def get_recent_confirmations(patient_name: str, limit: int = 10, user_id: str = None):
    """
    Get recent medication confirmations for a patient
    """
    try:
        # Build query with user_id filter if provided and use regex for patient name
        query = {"patient_name": {"$regex": f"^{re.escape(patient_name)}$", "$options": "i"}}
        if user_id:
            query["user_id"] = user_id
            
        confirmations = []
        async for confirmation in medication_confirmations_collection.find(
            query
        ).sort("confirmation_time", -1).limit(limit):
            # Convert datetime objects to strings for JSON serialization
            confirmation_dict = {
                "_id": str(confirmation["_id"]),
                "medication_id": confirmation.get("medication_id", ""),
                "patient_name": confirmation.get("patient_name", ""),
                "contact_number": confirmation.get("contact_number", ""),
                "scheduled_time": confirmation.get("scheduled_time", ""),
                "confirmation_time": confirmation.get("confirmation_time").isoformat() if confirmation.get("confirmation_time") else None,
                "is_taken": confirmation.get("is_taken", False),
                "response_message": confirmation.get("response_message", ""),
                "log_id": confirmation.get("log_id", "")
            }
            if "user_id" in confirmation:
                confirmation_dict["user_id"] = confirmation["user_id"]
            confirmations.append(confirmation_dict)
        
        return {
            "status": "success",
            "confirmations": confirmations
        }
        
    except Exception as e:
        print(f"Error in get_recent_confirmations: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error getting confirmations: {str(e)}")

async def get_medication_status(patient_name: str, user_id: str = None):
    """
    Get current medication status overview for a patient including pending medications
    """
    try:
        # Get today's medication logs
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        
        # Build query with user_id filter if provided and use regex for patient name
        query = {
            "patient_name": {"$regex": f"^{re.escape(patient_name)}$", "$options": "i"},
            "sent_time": {"$gte": today, "$lt": tomorrow}
        }
        if user_id:
            query["user_id"] = user_id
        
        today_logs = []
        async for log in medication_logs_collection.find(query).sort("sent_time", 1):
            # Convert datetime objects to strings for JSON serialization
            log_dict = {
                "_id": str(log["_id"]),
                "medication_id": log.get("medication_id", ""),
                "patient_name": log.get("patient_name", ""),
                "contact_number": log.get("contact_number", ""),
                "scheduled_time": log.get("scheduled_time", ""),
                "sent_time": log.get("sent_time").isoformat() if log.get("sent_time") else None,
                "status": log.get("status", "pending"),
                "response_received": log.get("response_received", False),
                "response_time": log.get("response_time").isoformat() if log.get("response_time") else None,
                "response_message": log.get("response_message", "")
            }
            if "user_id" in log:
                log_dict["user_id"] = log["user_id"]
            today_logs.append(log_dict)
        
        # Also get upcoming medications for today that haven't been sent yet
        current_time = datetime.now()
        
        # Find active medications that have times scheduled for today but haven't been logged yet
        active_meds_query = {
            "patient_name": {"$regex": f"^{re.escape(patient_name)}$", "$options": "i"},
            "start_date": {"$lte": current_time}
        }
        if user_id:
            active_meds_query["user_id"] = user_id
        
        # Get active medications and check for pending times
        pending_medications = []
        async for medication in medications_collection.find(active_meds_query):
            # Check if medication is still active
            start_date = medication["start_date"]
            duration_days = medication["duration_days"]
            end_date = start_date + timedelta(days=duration_days)
            
            if current_time <= end_date:
                # Check each scheduled time for today
                for scheduled_time in medication.get("times", []):
                    # Check if this time hasn't been logged today
                    existing_log = await medication_logs_collection.find_one({
                        "medication_id": str(medication["_id"]),
                        "scheduled_time": scheduled_time,
                        "sent_time": {"$gte": today, "$lt": tomorrow}
                    })
                    
                    if not existing_log:
                        # This is a pending medication for today
                        pending_medications.append({
                            "medication_id": str(medication["_id"]),
                            "medication_name": medication.get("name", ""),
                            "scheduled_time": scheduled_time,
                            "status": "pending"
                        })
        
        # Add pending medications to today's logs
        for pending in pending_medications:
            today_logs.append({
                "_id": f"pending_{pending['medication_id']}_{pending['scheduled_time']}",
                "medication_id": pending["medication_id"],
                "patient_name": patient_name,
                "contact_number": "",
                "scheduled_time": pending["scheduled_time"],
                "sent_time": None,
                "status": "pending",
                "response_received": False,
                "response_time": None,
                "response_message": ""
            })
        
        # Sort by scheduled time
        today_logs.sort(key=lambda x: x["scheduled_time"])
        
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
        print(f"Error in get_medication_status: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error getting medication status: {str(e)}")

async def create_test_medication_logs(patient_name: str, user_id: str = None):
    """
    Create test medication logs for demonstration purposes
    """
    try:
        current_time = datetime.now()
        today = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Create some test logs for today
        test_logs = [
            {
                "medication_id": "test_med_1",
                "patient_name": patient_name,
                "contact_number": "+1234567890",
                "scheduled_time": "08:00",
                "sent_time": today + timedelta(hours=8),
                "status": "taken",
                "response_received": True,
                "response_time": today + timedelta(hours=8, minutes=15),
                "response_message": "yes"
            },
            {
                "medication_id": "test_med_2",
                "patient_name": patient_name,
                "contact_number": "+1234567890",
                "scheduled_time": "12:00",
                "sent_time": today + timedelta(hours=12),
                "status": "missed",
                "response_received": True,
                "response_time": today + timedelta(hours=12, minutes=30),
                "response_message": "no"
            },
            {
                "medication_id": "test_med_3",
                "patient_name": patient_name,
                "contact_number": "+1234567890",
                "scheduled_time": "18:00",
                "sent_time": today + timedelta(hours=18),
                "status": "pending",
                "response_received": False
            },
            {
                "medication_id": "test_med_4",
                "patient_name": patient_name,
                "contact_number": "+1234567890",
                "scheduled_time": "22:00",
                "sent_time": None,
                "status": "pending",
                "response_received": False
            }
        ]
        
        # Add user_id if provided
        if user_id:
            for log in test_logs:
                log["user_id"] = user_id
        
        # Insert test logs
        await medication_logs_collection.insert_many(test_logs)
        
        return {
            "status": "success",
            "message": f"Created {len(test_logs)} test medication logs for {patient_name}"
        }
        
    except Exception as e:
        print(f"Error creating test logs: {e}")
        return {"status": "error", "message": str(e)}