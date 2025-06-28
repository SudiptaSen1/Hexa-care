import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

account_sid = os.getenv("Twilio_Sid")
auth_token = os.getenv("Twilio_auth_token")
from_number = os.getenv("TWILIO_SMS_FROM")

client = Client(account_sid, auth_token)

def send_sms(to_number: str, message: str):
    try:
        msg = client.messages.create(
            body=message,
            from_=from_number,
            to=to_number
        )
        print("✅ SMS sent:", msg.sid)
        return {"status": "sent"}
    except Exception as e:
        print("❌ SMS Error:", str(e))
        return {"status": "error", "detail": str(e)}
