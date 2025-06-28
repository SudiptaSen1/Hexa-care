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
            message = f"👋 Hello {med['patient_name']}, {med['message']}"
        else:
            # Default message format for manually added medications
            message = f"👋 Hello {med['patient_name']}, it's {current_time_str}. Please take your 💊 {med['name']} ({med['dosage']})."

        # Send both SMS and WhatsApp
        print(f"Sending reminder to {med['contact_number']}: {message}")
        send_sms(med["contact_number"], message)
        send_whatsapp(med["contact_number"], message)

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_and_send_sms, 'interval', minutes=1)
    scheduler.start()
    print("Medication reminder scheduler started successfully!")