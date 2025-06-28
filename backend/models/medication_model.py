from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class MedicationConfirmation(BaseModel):
    medication_id: str
    patient_name: str
    contact_number: str
    scheduled_time: str
    confirmation_time: Optional[datetime] = None
    is_taken: bool = False
    response_message: Optional[str] = None

class MedicationLog(BaseModel):
    medication_id: str
    patient_name: str
    contact_number: str
    scheduled_time: str
    actual_time: datetime
    status: str  # "taken", "missed", "pending"
    response_received: bool = False