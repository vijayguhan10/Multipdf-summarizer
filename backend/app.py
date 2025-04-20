import os
import shutil
import boto3
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi import Request
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import sys
from typing import List
sys.path.append('..')  # Add parent directory to path
from backend.Summarization import get_summary_from_extracted_text
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables from .env file
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins in development
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Create an 'uploads' directory if it doesn't exist
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# AWS Textract client setup (make sure to set your AWS keys in the environment or manually)
textract_client = boto3.client('textract', 
                               aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"), 
                               aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                               region_name="us-east-1")

# Route to handle single file upload
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)

    # Save the uploaded file to the 'uploads' directory
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Check file extension to determine processing method
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    # For text files, directly read the content instead of using Textract
    if file_extension == '.txt':
        try:
            with open(file_path, 'r', encoding='utf-8') as text_file:
                extracted_text = text_file.read()
        except Exception as e:
            extracted_text = f"Error reading text file: {str(e)}"
    else:
        # For other formats (PDF, images), use Textract
        extracted_text = extract_text_from_pdf(file_path)
    
    # Get summary of the extracted text
    result = get_summary_from_extracted_text(extracted_text)
    
    # Return the extracted text and summary in JSON format
    return JSONResponse(content={
        "message": f"File '{file.filename}' uploaded, processed, and summarized successfully!",
        "extracted_text": result["original_text"],
        "summary": result["summary"]
    })

# New route to handle multiple file uploads
@app.post("/upload-multiple")
async def upload_multiple_files(files: List[UploadFile] = File(...)):
    combined_text = ""
    file_names = []
    individual_extractions = {}
    
    for file in files:
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file_names.append(file.filename)
        
        # Save the uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process based on file type
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension == '.txt':
            try:
                with open(file_path, 'r', encoding='utf-8') as text_file:
                    file_text = text_file.read()
            except Exception as e:
                file_text = f"Error reading text file {file.filename}: {str(e)}"
        else:
            # For PDFs and images, use Textract
            file_text = extract_text_from_pdf(file_path)
        
        # Store individual extraction
        individual_extractions[file.filename] = file_text
        
        # Add document separator and file name before content
        combined_text += f"\n\n--- DOCUMENT: {file.filename} ---\n\n"
        combined_text += file_text
    
    # Get summary of the combined text from all documents
    result = get_summary_from_extracted_text(
        extracted_text=combined_text,
        file_names=file_names,
        is_multiple=True
    )
    
    return JSONResponse(content={
        "message": f"{len(files)} files uploaded, processed, and summarized successfully!",
        "individual_extractions": individual_extractions,
       
        "summary": result["summary"]
    })

def extract_text_from_pdf(pdf_file_path: str) -> str:
    """
    Uses AWS Textract's DetectDocumentText API for more cost-effective text extraction.
    """
    try:
        # Open the PDF file and send it to AWS Textract
        with open(pdf_file_path, 'rb') as document:
            response = textract_client.detect_document_text(
                Document={'Bytes': document.read()}
            )
        
        # Extract the detected text from the response
        extracted_text = ""
        for item in response["Blocks"]:
            if item["BlockType"] == "LINE":
                extracted_text += item["Text"] + "\n"

        if not extracted_text:
            return "No text was detected in the document."
            
        return extracted_text

    except ClientError as e:
        return f"Error occurred: {str(e)}"

# Main function to run the app (for testing purposes or custom server startup)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, port=8000)
