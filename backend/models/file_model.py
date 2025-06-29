from pydantic import BaseModel

class FileUploadResponse(BaseModel):
    filename: str
    url: str
    public_id: str
    resource_type: str
    extracted_json: dict | None = None
    summary: str | None = None
    error: str | None = None