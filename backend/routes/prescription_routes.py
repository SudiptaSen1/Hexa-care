from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Header
from controllers.prescription_controller import get_user_prescriptions, delete_prescription
from controllers.upload_controller import upload_prescription_and_process
import json

router = APIRouter()

@router.post("/upload-prescription")
async def upload_prescription(
    file: UploadFile = File(...),
    user_id: str = Header(None, alias="X-User-ID")
):
    """
    Upload and process a prescription file
    """
    try:
        file_bytes = await file.read()
        file_ext = "." + file.filename.split('.')[-1].lower()
        
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID is required")
        
        # Process the prescription
        result = await upload_prescription_and_process(file_bytes, file_ext, user_id)
        return result
        
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

@router.delete("/prescription/{prescription_id}")
async def delete_prescription_endpoint(
    prescription_id: str,
    user_id: str = Header(None, alias="X-User-ID")
):
    """
    Delete a prescription
    """
    return await delete_prescription(prescription_id, user_id)