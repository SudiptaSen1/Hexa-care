# upload_routes.py (UPDATED CONTENT)

from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from controllers.upload_controller import upload_prescription_and_process
from models.file_model import FileUploadResponse

router = APIRouter()

@router.post("/upload-prescription", response_model=FileUploadResponse)
async def upload_prescription(file: UploadFile = File(...), user_id: str = Form(...)):
    try:
        file_bytes = await file.read()
        file_ext = "." + file.filename.split('.')[-1].lower()
        # Pass user_id to the controller
        result = await upload_prescription_and_process(file_bytes, file_ext, user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))