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

def summarize_multiple_documents(combined_text, file_names=None, max_words=500):
    """
    Generates a structured summary from multiple documents.
    
    Args:
        combined_text (str): The combined text from multiple documents
        file_names (list): List of document file names for reference
        max_words (int): Maximum length of the summary
        
    Returns:
        str: A structured summary of all documents
    """
    if not combined_text or combined_text.isspace():
        return "No text provided for summarization."
    
    # Create a more specific prompt for multiple document summarization
    try:
        files_info = ""
        if file_names:
            files_info = "Documents analyzed: " + ", ".join(file_names)
        
        prompt = f"""
        Create a professional and structured summary of the following travel documents.
        {files_info}

        Format the summary in this exact order with clear section breaks (---) and bold headers:

        **TRAVELER DETAILS**
        • Full Name
        • Number of Companions
        • Additional Personal Details

        ---
        **TRAVEL DETAILS**
        For each journey (Train/Flight/Bus), include:
        • PNR Number
        • Mode of Transport (Train/Flight/Bus Number and Name)
        • Date and Time (Departure - Arrival)
        • Route (From - To)
        • Seat/Berth Details
        • Fare

        ---
        **ACCOMMODATION DETAILS**
        • Property Name
        • Booking ID/PNR
        • Check-in/Check-out Dates
        • Room Type and Basis
        • Number of Guests
        • Total Cost
        • Key Amenities (bullet points)

        ---
        **COST BREAKDOWN**
        • Transportation Costs (itemized)
        • Accommodation Costs
        • Total Trip Cost

        ---
        **IMPORTANT NOTES**
        • Critical Information
        • Special Requirements
        • Document-specific Notes

        ---
        **OVERVIEW**
        Brief summary of the entire trip (2-3 sentences)

        ---
        **DOCUMENT INSIGHTS**
        Key information from each document

        ---
        **CONCLUSION**
        Final analysis with important highlights

        Note: Format all headings in bold, use bullet points for lists, and maintain clear section breaks.
        Maximum length: {max_words} words.

        Here are the document contents:

        {combined_text}
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
            return f"Error during multi-document summarization: {str(fallback_e)}"

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
