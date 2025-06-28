from apscheduler.schedulers.background import BackgroundScheduler
from pymongo import MongoClient
from datetime import datetime
from utils.notificatiins import send_sms, send_whatsapp
import pytz
import os
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.getenv("MONGODB_URI"))
db = client[os.getenv("DB_NAME", "hexacare")]
meds = db["medications"]
medication_logs = db["medication_logs"]

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
        
        result = medication_logs.insert_one(log_entry)
        return str(result.inserted_id)
    except Exception as e:
        print(f"Error logging medication reminder: {e}")
        return None

def check_and_send_sms():
    now = datetime.now(pytz.timezone("Asia/Kolkata"))
    current_time_str = now.strftime("%H:%M")

    # Find all medications scheduled for current time
    results = meds.find({"times": current_time_str})
    
    for med in results:
        start = med["start_date"]

        # Convert datetime to date if needed
        if isinstance(start, datetime):
            start = start.date()

        days_elapsed = (now.date() - start).days

        if days_elapsed >= med["duration_days"] or days_elapsed < 0:
            continue  # skip if expired or not started yet

        # Use custom message if available (from prescription parsing), otherwise use default format
        if "message" in med and med["message"]:
            # Add confirmation request to prescription messages
            base_message = f"👋 Hello {med['patient_name']}, {med['message']}"
            message = f"{base_message}\n\nPlease reply 'YES' if you've taken your medicine or 'NO' if you missed it."
        else:
            # Default message format for manually added medications
            base_message = f"👋 Hello {med['patient_name']}, it's {current_time_str}. Please take your 💊 {med['name']} ({med['dosage']})."
            message = f"{base_message}\n\nPlease reply 'YES' if you've taken your medicine or 'NO' if you missed it."

        # Log the reminder being sent
        medication_id = str(med.get("_id", ""))
        log_id = None
        try:
            log_entry = {
                "medication_id": medication_id,
                "patient_name": med['patient_name'],
                "contact_number": med["contact_number"],
                "scheduled_time": current_time_str,
                "sent_time": now,
                "status": "pending",
                "response_received": False
            }
            log_result = medication_logs.insert_one(log_entry)
            log_id = str(log_result.inserted_id)
        except Exception as e:
            print(f"Error logging medication reminder: {e}")

        # Send both SMS and WhatsApp
        print(f"Sending reminder to {med['contact_number']}: {message}")
        send_sms(med["contact_number"], message)
        send_whatsapp(med["contact_number"], message)

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_and_send_sms, 'interval', minutes=1)
    scheduler.start()
    print("Medication reminder scheduler started successfully!")