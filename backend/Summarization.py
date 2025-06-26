import os
import re
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# Initialize Gemini model with a free alternative
# Using gemini-1.5-flash instead of gemini-pro
model = genai.GenerativeModel('gemini-1.5-flash-latest')

def summarize_text(text, max_words=1000):
    """
    Summarizes the provided text using Google's Gemini AI model.
    
    Args:
        text (str): The extracted text to summarize
        max_words (int): Maximum number of words for the summary
        
    Returns:
        str: Summarized text
    """
    if not text or text.isspace():
        return "No text provided for summarization."
    
    try:
        prompt = f"""
        Summarize the following text in a concise way, not exceeding {max_words} words. 
        Focus on the main points and key information:
        
        {text}
        """
        
        response = model.generate_content(prompt)
        return response.text.strip()
    
    except Exception as e:
        # If the first model fails, try with a fallback model
        try:
            print(f"First model attempt failed: {str(e)}. Trying fallback model...")
            fallback_model = genai.GenerativeModel('gemini-1.0-pro-latest')
            fallback_response = fallback_model.generate_content(prompt)
            return fallback_response.text.strip()
        except Exception as fallback_e:
            return f"Error during summarization: {str(fallback_e)}"

import json
import re

def clean_model_json_output(text):
    """
    Cleans up model output to extract valid JSON.
    - Removes Markdown code block markers (```json ... ```)
    - Strips any text before/after the JSON object
    - Attempts to extract the first valid JSON object found
    """
    # Remove Markdown code block markers
    text = re.sub(r"^```(?:json)?", "", text.strip(), flags=re.IGNORECASE)
    text = re.sub(r"```$", "", text.strip())
    # Find the first JSON object in the text
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        json_str = match.group(0)
        return json_str
    return text.strip()

def summarize_multiple_documents(combined_text, file_names=None, max_words=500):
    """
    Generates a structured summary from multiple documents.
    
    Args:
        combined_text (str): The combined text from multiple documents
        file_names (list): List of document file names for reference
        max_words (int): Maximum length of the summary
    
    Returns:
        dict: A structured summary of all documents as a JSON object
    """
    if not combined_text or combined_text.isspace():
        return {"error": "No text provided for summarization."}

    try:
        files_info = ""
        if file_names:
            files_info = "Documents analyzed: " + ", ".join(file_names)

        prompt = f"""
You are an expert travel document summarizer. Given the following travel documents, extract and return a JSON object with this structure:

{{
  "traveler_info": [
    {{
      "full_name": "",
      "number_of_companions": 0,
      "companions": []
    }}
  ],
  "travel_details": [
    {{
      "journey": 1,
      "pnr_number": "",
      "mode_of_transport": "",
      "train_or_flight_number": "",
      "date": "",
      "time": "",
      "route": "",
      "seat": "",
      "fare": ""
    }}
  ],
  "accommodation_details": [
    {{
      "hotel": "",
      "booking_id": "",
      "stay": "",
      "room_type": "",
      "guests": "",
      "total_cost": "",
      "key_amenities": []
    }}
  ],
  "cost_summary": {{
    "transportation": "",
    "accommodation": "",
    "total_trip_cost": ""
  }},
  "notes": {{
    "critical_info": "",
    "special_requirements": "",
    "extra_docs": ""
  }},
  "overview": ""
}}

Instructions:
- Extract every traveler's name from the documents and include each as an entry in "traveler_info".
- If travelers are part of the same booking (e.g., a family), use the same "travel_details", "accommodation_details", "cost_summary", and "notes" for all travelers.
- For the "notes" section:
    - "critical_info" should be concise (no more than 1-2 lines, only the most important info).
    - "special_requirements" and "extra_docs" should be brief and relevant.
- For "accommodation_details", include at most 5 or 6 of the most important hotel amenities in "key_amenities".
- For "overview", write a short, 3-4 line summary of the trip based on the invoices, mentioning the main highlights (e.g., destination, duration, travel/accommodation type, and any special notes).
- Do NOT omit any traveler or important field. If a field is missing, leave it as an empty string, 0, or empty list.
- For lists (like journeys, accommodations, companions, amenities), include all relevant items, but limit amenities as above.
- Do NOT include any explanation or text outside the JSON object.
- Maximum length: {max_words} words.

{files_info}

Here are the document contents:

{combined_text}
"""

        response = model.generate_content(prompt)
        try:
            cleaned = clean_model_json_output(response.text)
            summary_json = json.loads(cleaned)
        except Exception:
            # If the model returns invalid JSON, return as string for debugging
            summary_json = {"raw_summary": response.text.strip()}
        return summary_json

    except Exception as e:
        try:
            print(f"First model attempt failed: {str(e)}. Trying fallback model...")
            fallback_model = genai.GenerativeModel('gemini-1.0-pro-latest')
            fallback_response = fallback_model.generate_content(prompt)
            try:
                cleaned = clean_model_json_output(fallback_response.text)
                summary_json = json.loads(cleaned)
            except Exception:
                summary_json = {"raw_summary": fallback_response.text.strip()}
            return summary_json
        except Exception as fallback_e:
            return {"error": f"Error during multi-document summarization: {str(fallback_e)}"}

def get_summary_from_extracted_text(extracted_text, file_names=None, is_multiple=False):
    """
    Takes extracted text from OCR and returns a summary.

    Args:
        extracted_text (str): Text extracted from document using OCR
        file_names (list): List of document file names (for multiple documents)
        is_multiple (bool): Flag to indicate if this is a multi-document summary

    Returns:
        dict: Contains the structured summary
    """
    filtered_text = filter_terms_and_conditions(extracted_text)

    if is_multiple or (file_names and len(file_names) > 1):
        summary = summarize_multiple_documents(filtered_text, file_names)
    else:
        summary = summarize_multiple_documents(filtered_text)  # Use the same JSON structure for single doc

    return summary

# Function to integrate with the main app
def filter_terms_and_conditions(text):
    """
    Filters out terms and conditions sections from the text.
    
    Args:
        text (str): The text to filter
    
    Returns:
        str: Filtered text without terms and conditions
    """
    # Common patterns for terms and conditions sections
    patterns = [
        r'Rules and policies.*?(?=\n\n)',
        r'Terms and conditions.*?(?=\n\n)',
        r'Policies.*?(?=\n\n)',
        r'Guest Profile.*?(?=\n\n)',
        r'Id Proof Related.*?(?=\n\n)',
        r'Food Arrangement.*?(?=\n\n)',
        r'Smoking/alcohol Consumption Rules.*?(?=\n\n)',
        r'Pet(s) Related.*?(?=\n\n)',
        r'Property Accessibility.*?(?=\n\n)',
        r'Other Rules.*?(?=\\n\\n)',
        r'Child / Extra Bed Policy.*?(?=\\n\\n)',
        r'Adult / Extra Bed Policy.*?(?=\\n\\n)',
        r'PNRs having fully waitlisted status.*?(?=\\n\\n)',
        r'clerkage charge.*?(?=\\n\\n)',
        r'Passengers travelling on a fully waitlisted.*?(?=\\n\\n)',
        r'Obtain certificate from the TTE.*?(?=\\n\\n)',
        r'In case, on a party e-ticket.*?(?=\\n\\n)',
        r'In case train is late more than 3 hours.*?(?=\\n\\n)',
        r'In case of train cancellation.*?(?=\\n\\n)',
        r'Never purchase e-ticket from unauthorized agents.*?(?=\\n\\n)',
        r'For detail, Rules, Refund rules.*?(?=\\n\\n)',
        r'While booking this ticket.*?(?=\\n\\n)',
        r'The FIR forms are available.*?(?=\\n\\n)',
        r'Variety of meals available.*?(?=\\n\\n)',
        r'National Consumer Helpline.*?(?=\\n\\n)',
        r'You can book unreserved ticket.*?(?=\\n\\n)',
        r'As per RBI guidelines.*?(?=\\n\\n)',
        r'Customer Care.*?(?=\\n\\n)'
    ]
    
    for pattern in patterns:
        text = re.sub(pattern, '', text, flags=re.DOTALL)
    
    # Filter out irrelevant images or non-text elements
    text = re.sub(r'\[image\].*?(?=\n\n)', '', text, flags=re.DOTALL)
    return text.strip()


def get_summary_from_extracted_text(extracted_text, file_names=None, is_multiple=False):
    """
    Takes extracted text from OCR and returns a summary.
    
    Args:
        extracted_text (str): Text extracted from document using OCR
        file_names (list): List of document file names (for multiple documents)
        is_multiple (bool): Flag to indicate if this is a multi-document summary
    
    Returns:
        dict: Contains both original text and summary
    """
    filtered_text = filter_terms_and_conditions(extracted_text)
    
    if is_multiple or (file_names and len(file_names) > 1):
        summary = summarize_multiple_documents(filtered_text, file_names)
    else:
        summary = summarize_text(filtered_text)
        
    return {"summary": summary}
