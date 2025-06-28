from fastapi import FastAPI
from routes.upload_routes import router as upload_router
from routes.auth_route import router as auth_router
import utils.cloudinary_config  # auto-loads config
from utils.schedular import start_scheduler
from pydantic import BaseModel
from typing import List
from pymongo import MongoClient
from datetime import date
from datetime import datetime
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to frontend URL in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "X-User-ID"],
)
@app.on_event("startup")
def startup_event():
    start_scheduler()

class Medicine(BaseModel):
    patient_name: str
    name: str
    dosage: str
    times: List[str]
    duration_days: int
    start_date: date
    contact_number: str
load_dotenv()
client = MongoClient(os.getenv("MONGODB_URI"))
db = client[os.getenv("DB_NAME")]
medications = db["medications"]
@app.post("/add-medication")
async def add_medication(med: Medicine):
    try:
        data = med.dict()
        data["start_date"] = datetime.combine(data["start_date"], datetime.min.time())  # 👈 convert date to datetime
        medications.insert_one(data)
        return {"status": "success", "message": "Medication reminder added"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
print(os.getenv("TWILIO_SMS_FROM"))

include_router = [upload_router, auth_router]
for router in include_router:
    app.include_router(router)  