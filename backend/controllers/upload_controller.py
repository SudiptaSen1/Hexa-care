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
from cloudinary.uploader import upload

# Import the RAG pipeline
from rag_pipeline.summary_graph import ingestion_graph, PrescriptionIngestionState

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

async def upload_file_logic(file: UploadFile):
    try:
        file_bytes = await file.read()
        file_stream = BytesIO(file_bytes)
        file_ext = file.filename.split('.')[-1].lower()
        public_id = f"uploads/{uuid.uuid4()}"

        # Choose resource type
        resource_type = "auto" if file_ext == "pdf" else "image"

        result = upload(
            file_stream,
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

async def upload_prescription_and_process(file_bytes: bytes, file_ext: str, user_id: str):
    try:
        logger.info(f"Upload started for user_id: {user_id}. File extension: {file_ext}, Size: {len(file_bytes)} bytes.")

        # Step 1: Call Gemini Vision Pro for extraction
        extracted_json_str = await process_file_with_vision(file_bytes, file_ext)
        logger.info(f"Extraction complete for user_id: {user_id}. Extracted text length: {len(extracted_json_str)}")

        # Validate that the output is valid JSON before proceeding
        try:
            json.loads(extracted_json_str)
        except json.JSONDecodeError:
            logger.error(f"AI extraction failed to produce valid JSON for user_id: {user_id}. Output: {extracted_json_str}")
            raise HTTPException(status_code=500, detail="The AI model could not structure the extracted data correctly. Please try a clearer image.")

        # Step 2: Pass data to LangGraph for parsing, storing, and summarizing
        initial_state: PrescriptionIngestionState = {
            "user_id": user_id,
            "session_id": None,
            "prescription_text": extracted_json_str,
            "chat_history": [],
            "question": "",
            "answer": "",
            "retrieved_info": [],
            "parsed_prescription": None,
            "user_summary": None,
            "ingestion_status": "started",
        }
        logger.info(f"Invoking ingestion graph for user_id: {user_id}.")

        final_ingestion_state = await ingestion_graph.ainvoke(initial_state)
        logger.info(f"Graph invocation complete for user_id: {user_id}. Final status: {final_ingestion_state.get('ingestion_status')}")

        ingestion_status = final_ingestion_state.get("ingestion_status", "unknown")
        user_summary = final_ingestion_state.get("user_summary")
        
        if "completed" in ingestion_status:
            logger.info(f"Processing completed successfully for user_id: {user_id}.")
            return {
                "filename": "prescription.jpg",
                "url": "N/A",
                "public_id": user_id,
                "resource_type": "image",
                "extracted_json": json.loads(extracted_json_str),
                "summary": user_summary,
                "error": None
            }
        else:
            error_detail = f"Processing failed after data extraction. Status: {ingestion_status}"
            logger.error(f"{error_detail} for user_id: {user_id}")
            raise HTTPException(status_code=500, detail=error_detail)

    except HTTPException as http_e:
        raise http_e
    except Exception as e:
        error_message = f"An unexpected server error occurred: {str(e)}"
        logger.exception(error_message)
        raise HTTPException(status_code=500, detail=error_message)