from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class Medicine(BaseModel):
    name: str
    dosage: str
    duration: str
    original_schedule_text: List[str]
    scheduled_times: List[str]
    notes: Optional[str] = ""

class DoctorAppointment(BaseModel):
    date: str
    time: str
    reason: str
    doctor_name: str

class PrescriptionData(BaseModel):
    age: str
    date: str
    medicines: List[Medicine]
    diagnosis: str
    doctor_appointments: List[DoctorAppointment]
    doctor_instructions: List[str]

class UserSchedule(BaseModel):
    patient_name: str
    contact_number: str
    wake_up_time: str
    breakfast_time: str
    lunch_time: str
    dinner_time: str
    sleep_time: str
    before_breakfast_offset_minutes: int = 20
    after_lunch_offset_minutes: int = 30
    before_lunch_offset_minutes: int = 10
    after_dinner_offset_minutes: int = 45

class PrescriptionUploadRequest(BaseModel):
    user_schedule: UserSchedule