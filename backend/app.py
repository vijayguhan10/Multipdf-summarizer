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
    allow_origins=["*"],  # Allow only this origin
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
async def upload_file(file: List[UploadFile] = File(description="The file(s) to upload")):
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

        file_path = os.path.join(UPLOAD_FOLDER, file.filename)

        # Save the uploaded file to the 'uploads' directory
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
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
        
        print(f"Extracted text: {extracted_text}")
        return JSONResponse(
            status_code=200,
            content={
                "message": f"File '{file.filename}' uploaded, processed, and summarized successfully!",
                "summary": result["summary"]
            }
        )

    except Exception as e:
        print(f"Error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"An unexpected error occurred: {str(e)}"}
        )

# New route to handle multiple file uploads
@app.post("/upload-multiple")
async def upload_multiple_files(file: List[UploadFile] = File(..., description="The file(s) to upload")):
    try:
        # Validate file input
        if not file:
            return JSONResponse(
                status_code=400,
                content={"error": "No files provided"}
            )

        # Validate file types
        allowed_extensions = [".txt", ".pdf", ".png", ".jpg", ".jpeg"]
        for upload_file in file:
            file_extension = os.path.splitext(upload_file.filename)[1].lower()
            if file_extension not in allowed_extensions:
                return JSONResponse(
                    status_code=400,
                    content={"error": f"Unsupported file type for {upload_file.filename}. Allowed types: {', '.join(allowed_extensions)}"}
                )

        print(f"Processing {len(file)} files:")
        individual_extractions = {}
        file_names = []
        combined_text = ""

        for upload_file in file:
            print(f"- Processing: {upload_file.filename}")
            file_path = os.path.join(UPLOAD_FOLDER, upload_file.filename)
            file_names.append(upload_file.filename)

            # Save uploaded file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(upload_file.file, buffer)

            # Extract text based on file type
            file_extension = os.path.splitext(upload_file.filename)[1].lower()
            try:
                if file_extension == '.txt':
                    with open(file_path, 'r', encoding='utf-8') as text_file:
                        file_text = text_file.read()
                else:
                    file_text = extract_text_from_pdf(file_path)

                if file_text.startswith("Error occurred:"):
                    raise Exception(file_text)

                individual_extractions[upload_file.filename] = file_text
                combined_text += f"\n\n--- DOCUMENT: {upload_file.filename} ---\n\n{file_text}"

            except Exception as e:
                return JSONResponse(
                    status_code=500,
                    content={"error": f"Error processing {upload_file.filename}: {str(e)}"}
                )

        # Generate summary for all documents
        result = get_summary_from_extracted_text(
            extracted_text=combined_text.strip(),
            file_names=file_names,
            is_multiple=True
        )

        return JSONResponse(
            status_code=200,
            content={
                "summary": result["summary"]
            }
        )

    except Exception as e:
        print(f"Error in upload_multiple_files: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"An unexpected error occurred: {str(e)}"}
        )

def extract_text_from_pdf(pdf_file_path: str) -> str:
    """
    Extracts text from PDF using AWS Textract, with fallback to AnalyzeDocument API.
    Handles multi-page PDFs by processing each page sequentially.
    """
    try:
        # First try AnalyzeExpense API
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
                    # Fallback to basic text extraction
                    try:
                        import PyPDF2
                        reader = PyPDF2.PdfReader(document)
                        text = ""
                        for page in reader.pages:
                            page_text = page.extract_text()
                            if page_text:
                                text += f"\n--- PAGE {reader.get_page_number(page) + 1} ---\n"
                                text += page_text
                        return text.strip()
                    except Exception as e:
                        return f"Error occurred: {str(e)}"

        return "No data was detected in the document."

    except ClientError as e:
        return f"Error occurred: {str(e)}"

# Main function to run the app (for testing purposes or custom server startup)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
