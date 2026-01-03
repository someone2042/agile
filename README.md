# Skin Cancer AI Analyzer

## Overview
This project is an AI-powered web application for skin cancer detection and medical report generation. Users can upload dermoscopic images, receive instant analysis (Cancerous/Non-Cancerous), and download a comprehensive medical report in PDF or Word format. The backend uses a deep learning model and Google Gemini for report generation.

## Features
- Upload skin lesion images for analysis
- AI model classifies as "Cancerous" or "Non-Cancerous"
- Generates detailed medical reports in English, French, or Arabic
- Download reports as PDF or Word documents
- Modern, responsive frontend

## Technologies Used
- **Frontend:** HTML, CSS, JavaScript
- **Backend:** FastAPI, TensorFlow, HuggingFace Hub, Google Gemini API
- **Report Generation:** fpdf, python-docx, markdown, BeautifulSoup

## Setup Instructions

### 1. Clone the Repository
```powershell
git clone <your-repo-url>
cd agile
```

### 2. Install Python Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Set Up Google Gemini API Key
- Replace `GEMINI_API_KEY` in `skin-cancer-api/main.py` with your actual API key.

### 4. Run the Backend Server
```powershell
cd skin-cancer-api
uvicorn main:app --reload
```

### 5. Open the Frontend
- Open `index.html` in your browser.

## Usage
1. Select your preferred language.
2. Upload a dermoscopic image.
3. Click "Analyze Image" to get instant results.
4. Download the medical report in PDF or Word format.

## File Structure
```
index.html                # Frontend UI
main.py                   # Backend API (root)
skin-cancer-api/main.py   # FastAPI backend logic
requirements.txt          # Python dependencies
README.md                 # Project documentation
```

## Model Details
- The skin cancer detection model is downloaded from HuggingFace (`VRJBro/skin-cancer-detection`).
- Images are preprocessed using VGG16 standards.
- Model outputs a binary classification (Cancerous/Non-Cancerous).

## API Endpoints
- `POST /analyze` : Upload image and get prediction + report
- `POST /generate_report` : Download report as PDF or Word
- `GET /` : Health check

## License
This project is for educational and research purposes only. Not for clinical use.

## Disclaimer
This tool provides AI-generated analysis for educational purposes and is **not** a substitute for professional medical diagnosis. Always consult a qualified healthcare provider for medical concerns.
