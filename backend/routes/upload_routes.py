from fastapi import APIRouter, UploadFile, File, HTTPException
from controllers.upload_controller import upload_file_logic
from models.file_model import FileUploadResponse

router = APIRouter()

@router.post("/upload", response_model=FileUploadResponse)
async def upload(file: UploadFile = File(...)):
    try:
        return await upload_file_logic(file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
