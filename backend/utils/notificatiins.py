import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

account_sid = os.getenv("Twilio_Sid")
auth_token = os.getenv("Twilio_auth_token")
from_number_sms = os.getenv("TWILIO_SMS_FROM")
from_number_whatsapp = os.getenv("TWILIO_WHATSAPP_FROM")  
client = Client(account_sid, auth_token)

def send_sms(to_number: str, message: str):
    try:
        msg = client.messages.create(
            body=message,
            from_=from_number_sms,
            to=to_number
        )
        print("✅ SMS sent:", msg.sid)
        return {"status": "sent"}
    except Exception as e:
        print("❌ SMS Error:", str(e))
        return {"status": "error", "detail": str(e)}
def send_whatsapp(to_number: str, message: str):
    try:
        from_number_whatsapp = os.getenv("TWILIO_WHATSAPP_FROM")  # 'whatsapp:+14155238886'
        to_whatsapp = f'whatsapp:{to_number}'

        msg = client.messages.create(
            body=message,
            from_=from_number_whatsapp,
            to=to_whatsapp
        )
        print(f"✅ WhatsApp sent to {to_number}: {msg.sid}")
    except Exception as e:
        print(f"❌ WhatsApp Error: {str(e)}")
