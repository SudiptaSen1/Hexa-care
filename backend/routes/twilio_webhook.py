from fastapi import APIRouter, Form, Request
from controllers.medication_controller import process_medication_response
import logging

router = APIRouter()

@router.post("/twilio-webhook")
async def twilio_webhook(
    request: Request,
    From: str = Form(...),
    Body: str = Form(...),
    MessageSid: str = Form(None),
    AccountSid: str = Form(None)
):
    """
    Webhook endpoint for Twilio to handle incoming SMS responses
    """
    try:
        # Log the incoming message
        print(f"=== TWILIO SMS WEBHOOK ===")
        print(f"From: {From}")
        print(f"Body: {Body}")
        print(f"MessageSid: {MessageSid}")
        
        # Process the medication response
        result = await process_medication_response(From, Body)
        
        print(f"Processing result: {result}")
        
        # Prepare response message based on the result
        if result["status"] == "success":
            if result["is_taken"]:
                response_message = f"Great job {result['patient_name']}! ✅ Your medication has been marked as taken. Keep up the good work!"
            else:
                response_message = f"Thanks for letting us know {result['patient_name']}. ⚠️ Your medication has been marked as missed. Please try to take it when possible and consult your doctor if you have concerns."
        elif result["status"] == "no_pending":
            response_message = "We couldn't find a recent medication reminder for your number. If you need help, please contact your healthcare provider."
        else:
            response_message = "Thank you for your message. If you need assistance, please contact your healthcare provider."
        
        # Return TwiML response
        twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{response_message}</Message>
</Response>"""
        
        return twiml_response
        
    except Exception as e:
        print(f"Error processing Twilio webhook: {e}")
        import traceback
        traceback.print_exc()
        # Return a generic response in case of error
        error_response = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>Thank you for your message. We're experiencing technical difficulties. Please contact your healthcare provider if you need immediate assistance.</Message>
</Response>"""
        return error_response

@router.post("/whatsapp-webhook")
async def whatsapp_webhook(
    request: Request,
    From: str = Form(...),
    Body: str = Form(...),
    MessageSid: str = Form(None),
    AccountSid: str = Form(None)
):
    """
    Webhook endpoint for Twilio WhatsApp to handle incoming responses
    """
    try:
        print(f"=== WHATSAPP WEBHOOK ===")
        print(f"From: {From}")
        print(f"Body: {Body}")
        print(f"MessageSid: {MessageSid}")
        
        # Process the medication response (From already includes whatsapp: prefix)
        result = await process_medication_response(From, Body)
        
        print(f"Processing result: {result}")
        
        # Prepare response message
        if result["status"] == "success":
            if result["is_taken"]:
                response_message = f"Excellent {result['patient_name']}! ✅ Your medication has been marked as taken. Stay healthy!"
            else:
                response_message = f"Thank you for the update {result['patient_name']}. ⚠️ Your medication has been marked as missed. Please consult your doctor if needed."
        elif result["status"] == "no_pending":
            response_message = "We couldn't find a recent medication reminder. If you need help, please contact your healthcare provider."
        else:
            response_message = "Thank you for your message. For assistance, please contact your healthcare provider."
        
        # Return TwiML response for WhatsApp
        twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{response_message}</Message>
</Response>"""
        
        return twiml_response
        
    except Exception as e:
        print(f"Error processing WhatsApp webhook: {e}")
        import traceback
        traceback.print_exc()
        error_response = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>Thank you for your message. We're experiencing technical difficulties. Please contact your healthcare provider if needed.</Message>
</Response>"""
        return error_response

# Add a test endpoint to manually test the response processing
@router.post("/test-medication-response")
async def test_medication_response(
    contact_number: str = Form(...),
    message: str = Form(...)
):
    """
    Test endpoint to manually process medication responses
    """
    try:
        result = await process_medication_response(contact_number, message)
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}