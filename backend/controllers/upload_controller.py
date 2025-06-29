import uuid
import json
import logging
import os
import tempfile
from datetime import datetime
from io import BytesIO

import google.generativeai as genai
from fastapi import UploadFile, HTTPException
from pdf2image import convert_from_bytes
from PIL import Image
from utils.db import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuration ---
GENAI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GENAI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set.")
genai.configure(api_key=GENAI_API_KEY)

# Initialize the Generative Model
gemini_vision_model = genai.GenerativeModel("gemini-2.5-flash")

# MongoDB collections
prescriptions_collection = db["prescriptions"]
user_summaries_collection = db["user_summaries"]

async def process_file_with_vision(file_bytes: bytes, file_ext: str):
    """
    Processes file bytes (image or PDF) using Gemini Vision Pro.
    Returns the extracted JSON string.
    """
    images = []
    if file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
        try:
            image = Image.open(BytesIO(file_bytes))
            images.append(image)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error opening image: {e}")
    elif file_ext == '.pdf':
        try:
            images = convert_from_bytes(file_bytes)
        except Exception as e:
            error_message = f"Error converting PDF: {e}. Ensure Poppler is installed and in your system's PATH."
            raise HTTPException(status_code=500, detail=error_message)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_ext}. Please use JPG, PNG, or PDF.")

    if not images:
        raise HTTPException(status_code=500, detail="No images could be extracted from the file.")

    prompt_parts = [
        """Extract the following fields from this prescription and provide the output ONLY in JSON format. Do not include any other text, explanations, or formatting outside of the JSON. If a field is not found, use an empty string "" for string values, and an empty array [] for array values.

The desired JSON structure is:
{
  "patient_name": "",
  "age": "",
  "date": "",
  "medicines": [
    {
      "name": "",
      "dosage": "",
      "duration": "",
      "notes": ""
    }
  ],
  "diagnosis": "",
  "doctor_instructions": []
}
""",
        images[0]  # Process the first page
    ]

    try:
        response = gemini_vision_model.generate_content(prompt_parts)
        # Clean up potential markdown formatting from the model's response
        extracted_text = response.text.strip().lstrip('```json').rstrip('```')
        return extracted_text
    except Exception as e:
        logger.error(f"Gemini Vision Pro extraction failed: {e}")
        raise HTTPException(status_code=500, detail="AI model failed to extract information from the document.")

async def store_prescription_in_db(extracted_data: dict, user_id: str):
    """Store prescription data in MongoDB"""
    try:
        prescription_record = {
            "user_id": user_id,
            "patient_name": extracted_data.get("patient_name", ""),
            "age": extracted_data.get("age", ""),
            "date": extracted_data.get("date", ""),
            "medicines": extracted_data.get("medicines", []),
            "diagnosis": extracted_data.get("diagnosis", ""),
            "doctor_instructions": extracted_data.get("doctor_instructions", []),
            "upload_date": datetime.utcnow(),
            "created_at": datetime.utcnow()
        }
        
        result = await prescriptions_collection.insert_one(prescription_record)
        logger.info(f"Stored prescription with ID: {result.inserted_id}")
        return str(result.inserted_id)
    except Exception as e:
        logger.error(f"Error storing prescription: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to store prescription: {e}")

async def generate_summary(extracted_data: dict) -> str:
    """Generate a user-friendly summary of the prescription"""
    try:
        summary_parts = []
        
        if extracted_data.get("patient_name"):
            summary_parts.append(f"**Patient:** {extracted_data['patient_name']}")
        
        if extracted_data.get("age"):
            summary_parts.append(f"**Age:** {extracted_data['age']}")
            
        if extracted_data.get("date"):
            summary_parts.append(f"**Date:** {extracted_data['date']}")
            
        if extracted_data.get("diagnosis"):
            summary_parts.append(f"**Diagnosis:** {extracted_data['diagnosis']}")
        
        medicines = extracted_data.get("medicines", [])
        if medicines:
            summary_parts.append("**Medications:**")
            for med in medicines:
                med_line = f"- {med.get('name', 'Unknown medication')}"
                if med.get('dosage'):
                    med_line += f": {med['dosage']}"
                if med.get('duration'):
                    med_line += f" for {med['duration']}"
                if med.get('notes'):
                    med_line += f" ({med['notes']})"
                summary_parts.append(med_line)
        
        instructions = extracted_data.get("doctor_instructions", [])
        if instructions:
            summary_parts.append("**Doctor's Instructions:**")
            for instruction in instructions:
                summary_parts.append(f"- {instruction}")
        
        return "\n".join(summary_parts)
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        return "Summary could not be generated."

async def upload_prescription_and_process(file_bytes: bytes, file_ext: str, user_id: str):
    try:
        logger.info(f"Upload started for user_id: {user_id}. File extension: {file_ext}, Size: {len(file_bytes)} bytes.")

        # Step 1: Call Gemini Vision Pro for extraction
        extracted_json_str = await process_file_with_vision(file_bytes, file_ext)
        logger.info(f"Extraction complete for user_id: {user_id}. Extracted text length: {len(extracted_json_str)}")

        # Validate that the output is valid JSON before proceeding
        try:
            extracted_data = json.loads(extracted_json_str)
            logger.info(f"Successfully parsed JSON for user_id: {user_id}")
        except json.JSONDecodeError as e:
            logger.error(f"AI extraction failed to produce valid JSON for user_id: {user_id}. Output: {extracted_json_str}")
            raise HTTPException(status_code=500, detail="The AI model could not structure the extracted data correctly. Please try a clearer image.")

        # Step 2: Store in MongoDB
        prescription_id = await store_prescription_in_db(extracted_data, user_id)
        
        # Step 3: Generate summary
        summary = await generate_summary(extracted_data)
        
        logger.info(f"Processing completed successfully for user_id: {user_id}.")
        return {
            "filename": "prescription.jpg",
            "url": "N/A",
            "public_id": user_id,
            "resource_type": "image",
            "extracted_json": extracted_data,
            "summary": summary,
            "prescription_id": prescription_id,
            "error": None
        }

    except HTTPException as http_e:
        raise http_e
    except Exception as e:
        error_message = f"An unexpected server error occurred: {str(e)}"
        logger.exception(error_message)
        raise HTTPException(status_code=500, detail=error_message)