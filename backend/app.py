import os
import shutil
import boto3
import json
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

# Remove the undefined LimitUploadSizeMiddleware
# MAX_UPLOAD_SIZE = 500 * 1024 * 1024  # 500MB
# app.add_middleware(LimitUploadSizeMiddleware, max_upload_size=MAX_UPLOAD_SIZE)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow only this origin
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Get the current script directory and create uploads path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(CURRENT_DIR, "uploads")

# Create an 'uploads' directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# AWS Textract client setup with error handling
textract_client = None
try:
    aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    
    if aws_access_key and aws_secret_key:
        textract_client = boto3.client('textract', 
                                       aws_access_key_id=aws_access_key, 
                                       aws_secret_access_key=aws_secret_key,
                                       region_name="us-east-1")
        print("✅ AWS Textract client initialized successfully")
    else:
        print("⚠️  AWS credentials not found. Textract features will be disabled.")
        print("   Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables to enable PDF/image processing.")
except Exception as e:
    print(f"⚠️  Failed to initialize AWS Textract client: {str(e)}")
    print("   PDF and image processing will use fallback methods only.")

def extract_text_from_pdf(pdf_file_path: str) -> str:
    """
    Extracts text from PDF using AWS Textract, with fallback to PyPDF2.
    Handles multi-page PDFs by processing each page sequentially.
    """
    try:
        # Check if AWS Textract is available
        if textract_client is None:
            print("AWS Textract not available, using PyPDF2 fallback...")
            return extract_text_with_pypdf2(pdf_file_path)
        
        # Try AWS Textract first
        with open(pdf_file_path, 'rb') as document:
            try:
                response = textract_client.analyze_expense(
                    Document={'Bytes': document.read()}
                )
                
                # Extract structured data from the response
                extracted_data = {}
                for expense_doc in response["ExpenseDocuments"]:
                    for line_item in expense_doc["LineItemGroups"]:
                        for item in line_item["LineItems"]:
                            for value in item["LineItemExpenseFields"]:
                                field_name = value["Type"]["Text"] if "Type" in value else "Unknown"
                                field_value = value["ValueDetection"]["Text"] if "ValueDetection" in value else ""
                                extracted_data[field_name] = field_value

                if extracted_data:
                    return json.dumps(extracted_data)

            except textract_client.exceptions.UnsupportedDocumentException:
                # Fallback to AnalyzeDocument API
                document.seek(0)
                try:
                    response = textract_client.analyze_document(
                        Document={'Bytes': document.read()},
                        FeatureTypes=["FORMS"]
                    )
                    
                    # Extract text from AnalyzeDocument response
                    extracted_text = ""
                    for block in response["Blocks"]:
                        if block["BlockType"] == "LINE":
                            extracted_text += block["Text"] + "\n"
                    
                    return extracted_text.strip()

                except textract_client.exceptions.UnsupportedDocumentException:
                    # Final fallback to PyPDF2
                    return extract_text_with_pypdf2(pdf_file_path)

        return "No data was detected in the document."

    except Exception as e:
        # If any error occurs with Textract, fall back to PyPDF2
        print(f"Textract error: {str(e)}, falling back to PyPDF2...")
        return extract_text_with_pypdf2(pdf_file_path)

def extract_text_with_pypdf2(pdf_file_path: str) -> str:
    """
    Fallback method to extract text from PDF using PyPDF2.
    """
    try:
        import PyPDF2
        with open(pdf_file_path, 'rb') as document:
            reader = PyPDF2.PdfReader(document)
            text = ""
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text += f"\n--- PAGE {page_num + 1} ---\n"
                    text += page_text
            return text.strip() if text.strip() else "No text could be extracted from the PDF."
    except ImportError:
        return "Error: PyPDF2 library not installed. Please install it with: pip install PyPDF2"
    except Exception as e:
        return f"Error extracting text from PDF: {str(e)}"

# Route to handle single file upload
@app.post("/upload")
async def upload_file(file: List[UploadFile] = File(description="The file(s) to upload")):
    file_path = None
    try:
        if not file or len(file) == 0:
            return JSONResponse(
                status_code=400,
                content={"error": "No file provided"}
            )
        
        # If multiple files were uploaded, redirect to multiple file handler
        if len(file) > 1:
            return await upload_multiple_files(file)
            
        # Single file processing
        file = file[0]
        print(f"Received file: {file.filename} (Type: {os.path.splitext(file.filename)[1].lower()})")

        # Validate file extension
        allowed_extensions = [".txt", ".pdf", ".png", ".jpg", ".jpeg"]
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in allowed_extensions:
            return JSONResponse(
                status_code=400,
                content={"error": f"Unsupported file type. Allowed types: {', '.join(allowed_extensions)}"}
            )

        # Create secure file path
        safe_filename = os.path.basename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, safe_filename)
        
        # Ensure the file path is within the upload directory (security check)
        if not file_path.startswith(UPLOAD_FOLDER):
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid file path"}
            )

        # Save the uploaded file to the 'uploads' directory
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Set file permissions
            
            print(f"✅ File saved to: {file_path}")
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"error": f"Failed to save file: {str(e)}"}
            )
        
        # Process based on file type
        if file_extension == '.txt':
            try:
                with open(file_path, 'r', encoding='utf-8') as text_file:
                    extracted_text = text_file.read()
            except Exception as e:
                return JSONResponse(
                    status_code=500,
                    content={"error": f"Error reading text file: {str(e)}"}
                )
        else:
            # For PDFs and images, use Textract
            extracted_text = extract_text_from_pdf(file_path)
            if extracted_text.startswith("Error occurred:"):
                return JSONResponse(
                    status_code=500,
                    content={"error": extracted_text}
                )
        
        # Get summary of the extracted text
        result = get_summary_from_extracted_text(extracted_text)
        
        print(f"Extracted text: {extracted_text[:200]}...")  # Only show first 200 chars in log
        
        # Clean up: remove the uploaded file after processing
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                print(f"✅ Cleaned up file: {file_path}")
        except Exception as e:
            print(f"⚠️  Warning: Could not clean up file {file_path}: {str(e)}")
        
        return JSONResponse(
            status_code=200,
            content={
                "message": f"File '{file.filename}' uploaded, processed, and summarized successfully!",
                "summary": result["summary"]
            }
        )

    except Exception as e:
        print(f"Error: {str(e)}")
        
        # Clean up file in case of error
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                print(f"✅ Cleaned up file after error: {file_path}")
        except Exception as cleanup_e:
            print(f"⚠️  Warning: Could not clean up file after error: {str(cleanup_e)}")
        
        return JSONResponse(
            status_code=500,
            content={"error": f"An unexpected error occurred: {str(e)}"}
        )

# Route to handle multiple file uploads
@app.post("/upload-multiple")
async def upload_multiple_files(files: List[UploadFile] = File(description="The files to upload")):
    try:
        if not files or len(files) == 0:
            return JSONResponse(
                status_code=400,
                content={"error": "No files provided"}
            )

        combined_text = ""
        file_names = []
        successful_files = []

        for file in files:
            print(f"Processing file: {file.filename}")
            
            # Validate file extension
            allowed_extensions = [".txt", ".pdf", ".png", ".jpg", ".jpeg"]
            file_extension = os.path.splitext(file.filename)[1].lower()
            if file_extension not in allowed_extensions:
                continue  # Skip unsupported files

            file_path = os.path.join(UPLOAD_FOLDER, file.filename)

            # Save the uploaded file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Extract text based on file type
            if file_extension == '.txt':
                try:
                    with open(file_path, 'r', encoding='utf-8') as text_file:
                        extracted_text = text_file.read()
                except Exception as e:
                    print(f"Error reading {file.filename}: {str(e)}")
                    continue
            else:
                # For PDFs and images, use Textract
                extracted_text = extract_text_from_pdf(file_path)
                if extracted_text.startswith("Error occurred:"):
                    print(f"Error extracting text from {file.filename}: {extracted_text}")
                    continue

            combined_text += f"\n\n--- Content from {file.filename} ---\n\n{extracted_text}"
            file_names.append(file.filename)
            successful_files.append(file.filename)

        if not combined_text:
            return JSONResponse(
                status_code=400,
                content={"error": "No valid text could be extracted from any file"}
            )

        # Get summary of the combined extracted text
        result = get_summary_from_extracted_text(combined_text, file_names, is_multiple=True)
        
        return JSONResponse(
            status_code=200,
            content={
                "message": f"Successfully processed {len(successful_files)} files: {', '.join(successful_files)}",
                "summary": result["summary"],
                "processed_files": successful_files
            }
        )

    except Exception as e:
        print(f"Error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"An unexpected error occurred: {str(e)}"}
        )

# Main function to run the app (for testing purposes or custom server startup)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
