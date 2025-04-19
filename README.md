# Multi-PDF Extractor and Summarizer

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100.0-green)
![AWS Textract](https://img.shields.io/badge/AWS-Textract-orange)
![Gemini AI](https://img.shields.io/badge/Google-Gemini_AI-red)

A powerful tool that extracts text from multiple PDF documents using AWS Textract OCR and generates a comprehensive AI-powered summary using Google's Gemini model.

## ✨ Features

- **Multiple PDF Processing** - Upload and process multiple PDF documents in a single request
- **OCR Text Extraction** - Extract text from PDFs using AWS Textract
- **AI-Powered Summarization** - Generate concise, structured summaries using Google's Gemini AI
- **Cost-Effective Processing** - Uses Textract's `detect_document_text` API for lower costs
- **Structured Output** - Organized summaries with Overview, Key Findings, Document Insights, and Conclusion sections

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- AWS account with Textract access
- Google AI Platform account with Gemini API access

### Setup

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/multi-pdf-extractor.git
cd multi-pdf-extractor
```

2. **Create and activate a virtual environment**

```powershell
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

3. **Install dependencies**

```powershell
pip install -r requirements.txt
```

4. **Create `.env` file in the backend directory**

```
# AWS credentials
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key

# Google Gemini API
GEMINI_API_KEY=your_gemini_api_key
```

## 💻 Usage

### Starting the Backend Server

```powershell
# Navigate to backend directory
cd backend

# Start the FastAPI server
python app.py
```

The server will start at `http://127.0.0.1:8000`.

### Starting the Frontend (Optional)

```powershell
# From the project root directory
python -m http.server 9000
```

Access the frontend interface at `http://localhost:9000`.

### API Endpoints

#### Single PDF Upload
- **URL**: `/upload`
- **Method**: POST
- **Body**: form-data with key "file" containing a PDF file

#### Multiple PDF Upload
- **URL**: `/upload-multiple`
- **Method**: POST
- **Body**: form-data with multiple keys all named "files" (one for each PDF)

## 📝 Example Requests Using Postman

### For Single PDF
1. Create a POST request to `http://127.0.0.1:8000/upload`
2. In the Body tab, select "form-data"
3. Add key "file" and select a PDF file
4. Send request

### For Multiple PDFs
1. Create a POST request to `http://127.0.0.1:8000/upload-multiple`
2. In the Body tab, select "form-data"
3. Add multiple keys ALL named "files" (this is important)
4. For each key, select a different PDF file
5. Send request

## ⚠️ Limitations

1. **Single-Page PDF Only**: The current implementation only processes the first page of each PDF. Multi-page PDFs will have only their first page extracted.
2. **AWS Free Tier**: AWS Textract offers 1,000 pages per month free for the first 3 months. Beyond that, charges apply.
3. **Synchronous Processing**: Large files might cause timeout errors. Consider implementing asynchronous processing for production use.

## 🏗️ Project Structure

```
multi-pdf-extractor/
├── venv/                  # Virtual environment (not in repo)
├── backend/
│   ├── app.py             # FastAPI application
│   ├── Summarization.py   # Text summarization using Gemini AI
│   ├── .env               # Environment variables (not in repo)
│   └── uploads/           # Directory for uploaded files
├── index.html             # Frontend interface
├── script.js              # Frontend JavaScript
├── styles.css             # CSS styles
├── requirements.txt       # Project dependencies
└── README.md              # Project documentation
```

## 🔮 Future Improvements

- Add support for multi-page PDFs using Textract's asynchronous APIs
- Implement progress tracking for processing large documents
- Add user authentication for secure API access
- Create Docker containers for easy deployment
- Add support for more document formats (Word, Excel, etc.)

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgements

- [AWS Textract](https://aws.amazon.com/textract/) for OCR capabilities
- [Google Gemini AI](https://ai.google.dev/) for text summarization
- [FastAPI](https://fastapi.tiangolo.com/) for the backend API framework 