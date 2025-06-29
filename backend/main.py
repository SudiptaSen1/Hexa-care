from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.auth_route import auth_router
from routes.upload_routes import upload_router
from routes.medication_routes import medication_router
from routes.prescription_routes import prescription_router
from routes.chat_routes import chat_router
from routes.twilio_webhook import twilio_router

app = FastAPI(title="MedTracker API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(upload_router, prefix="/api/upload", tags=["Upload"])
app.include_router(medication_router, prefix="/api/medications", tags=["Medications"])
app.include_router(prescription_router, prefix="/api/prescriptions", tags=["Prescriptions"])
app.include_router(chat_router, prefix="/api/chat", tags=["Chat"])
app.include_router(twilio_router, prefix="/api/twilio", tags=["Twilio"])

@app.get("/")
async def root():
    return {"message": "MedTracker API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}