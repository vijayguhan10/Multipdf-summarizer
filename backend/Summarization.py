import os
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

def summarize_text(text, max_words=150):
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
        Analyze and create a comprehensive summary of the following multiple documents.
        {files_info}
        
        Task:
        1. Identify the main topics across all documents
        2. Extract key insights and important information from each document
        3. Identify any relationships or patterns between the documents
        4. Create a structured summary with clear sections
        
        Format the summary with these sections:
        - OVERVIEW: Brief high-level summary of all documents (2-3 sentences)
        - KEY FINDINGS: Bullet points of the most important information
        - DOCUMENT INSIGHTS: Brief summary of each document's unique contribution
        - CONCLUSION: Final analysis integrating all documents
        
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
    if is_multiple or (file_names and len(file_names) > 1):
        summary = summarize_multiple_documents(extracted_text, file_names)
    else:
        summary = summarize_text(extracted_text)
        
    return {
        "original_text": extracted_text,
        "summary": summary
    }
