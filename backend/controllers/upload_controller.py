import uuid
from fastapi import UploadFile
from cloudinary.uploader import upload
from io import BytesIO

async def upload_file_logic(file: UploadFile):
    try:
        file_bytes = await file.read()
        file_stream = BytesIO(file_bytes)  # ✅ wrap in BytesIO
        file_ext = file.filename.split('.')[-1].lower()
        public_id = f"uploads/{uuid.uuid4()}"

        # Choose resource type
        resource_type = "auto" if file_ext == "pdf" else "image"

        result = upload(
            file_stream,  # ✅ file-like object
            resource_type=resource_type,
            public_id=public_id,
            overwrite=True,
            filename=file.filename
        )

        return {
            "filename": file.filename,
            "url": result.get("secure_url"),
            "public_id": result.get("public_id"),
            "resource_type": result.get("resource_type")
        }

    except Exception as e:
        raise Exception(f"Cloudinary upload failed: {str(e)}")
