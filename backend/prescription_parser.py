import google.generativeai as genai
from PIL import Image
import os
from pdf2image import convert_from_path
import json
from datetime import datetime, timedelta

# IMPORTANT: Replace with your actual API key.
# For production, consider using environment variables or a more secure method
# to store and access your API key.
API_KEY = "AIzaSyA9Wb32KCz3KfWPEMH8yIJm4sKvH5kXTGs" # <--- REPLACE THIS WITH YOUR ACTUAL API KEY
genai.configure(api_key=API_KEY)

def process_file(file_path):
    """
    Processes a given file (image or PDF) and returns a list of PIL Image objects.
    Each page of a PDF will be converted into a separate Image object.
    """
    file_extension = os.path.splitext(file_path)[1].lower()
    images = []

    if file_extension in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
        try:
            image = Image.open(file_path)
            images.append(image)
            print(f"Successfully loaded image file: '{file_path}'")
        except FileNotFoundError:
            print(f"Error: Image file '{file_path}' not found. Please ensure it's uploaded or the path is correct.")
            return []
        except Exception as e:
            print(f"Error opening image file '{file_path}': {e}")
            return []
    elif file_extension == '.pdf':
        try:
            images = convert_from_path(file_path)
            print(f"Successfully converted {len(images)} page(s) from PDF: '{file_path}'")
        except FileNotFoundError:
            print(f"Error: PDF file '{file_path}' not found. Please ensure it's uploaded or the path is correct.")
            print("Also, confirm Poppler is installed and accessible in your system's PATH (for Windows/Mac).")
            return []
        except Exception as e:
            print(f"Error converting PDF file '{file_path}': {e}")
            print("Please ensure you have Poppler installed and configured correctly for pdf2image.")
            return []
    else:
        print(f"Unsupported file type: {file_extension}. Please provide a JPG, PNG, or PDF file.")
        return []

    return images

def create_personalized_messages_by_exact_time(parsed_data):
    """
    Generates personalized messages for medicine schedules and doctor appointments,
    categorized by the exact HH:MM scheduled time. Consolidates medicine reminders.
    Returns a dictionary where keys are HH:MM and values are lists of messages.
    """
    messages_by_exact_time = {}

    # Store individual medicine names+dosages for consolidation later
    medicine_details_by_time = {}

    # Populate medicine_details_by_time
    if 'medicines' in parsed_data:
        for medicine in parsed_data['medicines']:
            name = medicine.get('name', 'Your medicine')
            dosage = medicine.get('dosage', '')
            scheduled_times = medicine.get('scheduled_times', [])

            for time_str in scheduled_times:
                if time_str not in medicine_details_by_time:
                    medicine_details_by_time[time_str] = []
                medicine_details_by_time[time_str].append(f"{name}{' (' + dosage + ')' if dosage else ''}")

    # Consolidate medicine messages
    for time_str, medicine_list in medicine_details_by_time.items():
        if medicine_list:
            # Join all medicine names with commas, and 'and' for the last one
            if len(medicine_list) > 1:
                medicines_str = ", ".join(medicine_list[:-1]) + f" and {medicine_list[-1]}"
            else:
                medicines_str = medicine_list[0]
            
            message = f"It's time to take {medicines_str} now ({time_str})."
            if time_str not in messages_by_exact_time:
                messages_by_exact_time[time_str] = []
            messages_by_exact_time[time_str].append(message)

    # Doctor appointment reminders (these remain individual messages)
    if 'doctor_appointments' in parsed_data:
        for appointment in parsed_data['doctor_appointments']:
            date = appointment.get('date', '')
            time_str = appointment.get('time', '')
            reason = appointment.get('reason', 'your appointment')
            doctor_name = appointment.get('doctor_name', 'your doctor')

            if time_str:
                time_key = time_str
                message = f"Reminder: You have {reason} with {doctor_name} on {date} at {time_str}."
                if time_key not in messages_by_exact_time:
                    messages_by_exact_time[time_key] = []
                messages_by_exact_time[time_key].append(message)

    return messages_by_exact_time

def get_prescription_data(file_path, user_schedule_input):
    """
    Processes a prescription file, generates a prompt based on user schedule,
    and uses the Gemini model to extract structured data.
    
    Args:
        file_path (str): The path to the prescription image or PDF.
        user_schedule_input (dict): A dictionary containing the user's daily schedule.
        
    Returns:
        dict: The parsed prescription data in JSON format, or None if an error occurs.
    """
    print(f"Attempting to process: {file_path}")

    # Get images from the file (handles both image and PDF)
    prescription_images = process_file(file_path)

    if not prescription_images:
        print("No valid images to process. Exiting.")
        return None

    # Initialize the Generative Model
    model = genai.GenerativeModel("gemini-2.5-flash")

    prompt_parts = [
        f"""
You are an expert medical assistant. Your task is to extract prescription details and generate a precise medicine schedule based on the provided prescription and the patient's daily routine.

**Patient's Daily Routine:**
- Wake Up Time: {user_schedule_input['wake_up_time']}
- Breakfast Time: {user_schedule_input['breakfast_time']}
- Lunch Time: {user_schedule_input['lunch_time']}
- Dinner Time: {user_schedule_input['dinner_time']}
- Sleep Time: {user_schedule_input['sleep_time']}
- Preferred offset for "before breakfast": {user_schedule_input['before_breakfast_offset_minutes']} minutes before.
- Preferred offset for "after lunch": {user_schedule_input['after_lunch_offset_minutes']} minutes after.
- Preferred offset for "before lunch": {user_schedule_input['before_lunch_offset_minutes']} minutes before.
- Preferred offset for "after dinner": {user_schedule_input['after_dinner_offset_minutes']} minutes after.

**Instructions:**
1.  Analyze the prescription for medicine names, dosages, durations, and original schedule instructions (e.g., "Twice Daily", "After Food", "At Bedtime").
2.  For each medicine, use the patient's daily routine and preferred offsets to convert the original schedule into **exact HH:MM times (24-hour format)**.
    * If a schedule is "Morning", use the patient's "Wake Up Time".
    * If a schedule is "Night" or "At Bedtime", use the patient's "Sleep Time".
    * If "Before Breakfast", calculate {user_schedule_input['before_breakfast_offset_minutes']} minutes before "Breakfast Time".
    * If "After Lunch", calculate {user_schedule_input['after_lunch_offset_minutes']} minutes after "Lunch Time".
    * If "Before Lunch", calculate {user_schedule_input['before_lunch_offset_minutes']} minutes before "Lunch Time".
    * If "After Dinner", calculate {user_schedule_input['after_dinner_offset_minutes']} minutes after "Dinner Time".
    * For "Twice Daily", provide two times: one based on "Wake Up Time" (or "Morning") and one based on "Sleep Time" (or "Night").
    * For "Thrice Daily", provide three times: one based on "Wake Up Time", one based on "Lunch Time", and one based on "Sleep Time".
    * For specific HH:MM times given in the prescription (e.g., "14:30"), use those directly.
    * For schedules like "Every X hours", you **must** pick a sensible starting time based on the patient's wake-up/meal times (e.g., first dose after wake up/breakfast) and then calculate subsequent doses. If you cannot derive an exact time, leave the array empty [] for scheduled_times.
    * If a medicine has multiple original schedule instructions (e.g., ["Once Daily", "14:30"]), interpret all of them and provide all calculated times.
3.  If a field is not found or is empty, use an empty string "" for string values, and an empty array [] for array values.
4.  Provide the output ONLY in JSON format. Do not include any other text, explanations, or formatting outside of the JSON.

Here is the desired JSON structure:
{{
  "age": "string",
  "date": "YYYY-MM-DD",
  "medicines": [
    {{
      "name": "string",
      "dosage": "string",
      "duration": "string",
      "original_schedule_text": ["string"],
      "scheduled_times": ["HH:MM"],
      "notes": "string"
    }}
  ],
  "diagnosis": "string",
  "doctor_appointments": [
    {{
      "date": "YYYY-MM-DD",
      "time": "HH:MM",
      "reason": "string",
      "doctor_name": "string"
    }}
  ],
  "doctor_instructions": ["string"]
}}
""",
        prescription_images[0]
    ]

    try:
        response = model.generate_content(prompt_parts)
        extracted_text = response.text
        # Clean the response text
        cleaned_text = extracted_text.strip()
        if cleaned_text.startswith('```json'):
            cleaned_text = cleaned_text[7:]
        if cleaned_text.endswith('```'):
            cleaned_text = cleaned_text[:-3]
        cleaned_text = cleaned_text.strip()
        
        parsed_data = json.loads(cleaned_text)
        return parsed_data
    except Exception as e:
        print(f"Error generating content or parsing JSON: {e}")
        print(f"Model response (raw): {response.text}")
        return None