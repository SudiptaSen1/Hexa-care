from pydantic import BaseModel

class FileUploadResponse(BaseModel):
    filename: str
    url: str
    public_id: str
    resource_type: str

