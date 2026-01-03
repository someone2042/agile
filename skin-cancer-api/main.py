import io
import os
import numpy as np
import tensorflow as tf
from PIL import Image
from tensorflow.keras.applications.vgg16 import preprocess_input # Add this import
from fastapi.middleware.cors import CORSMiddleware
from huggingface_hub import hf_hub_download
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import StreamingResponse
from google import genai
from google.genai import types
from fpdf import FPDF
from markdown import markdown
from docx import Document
from bs4 import BeautifulSoup

def add_markdown_to_word(document, md_text):
    """
    Converts Markdown to HTML and then injects it into a 
    python-docx document with basic formatting.
    """
    html = markdown(md_text)
    soup = BeautifulSoup(html, 'html.parser')

    for element in soup.find_all(['h1', 'h2', 'h3', 'p', 'ul', 'ol', 'li']):
        if element.name == 'h1':
            document.add_heading(element.get_text(), level=1)
        elif element.name == 'h2':
            document.add_heading(element.get_text(), level=2)
        elif element.name == 'h3':
            document.add_heading(element.get_text(), level=3)
        elif element.name == 'p':
            p = document.add_paragraph()
            # Handle bold/italic inside paragraphs
            for child in element.children:
                if child.name == 'strong' or child.name == 'b':
                    p.add_run(child.get_text()).bold = True
                elif child.name == 'em' or child.name == 'i':
                    p.add_run(child.get_text()).italic = True
                else:
                    p.add_run(str(child))
        elif element.name == 'ul':
            for li in element.find_all('li'):
                document.add_paragraph(li.get_text(), style='List Bullet')
        elif element.name == 'ol':
            for li in element.find_all('li'):
                document.add_paragraph(li.get_text(), style='List Number')

GEMINI_API_KEY = "dir api key dyallek"
client = genai.Client(api_key=GEMINI_API_KEY)

app = FastAPI()

# Enable CORS for your HTML frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = None
# This model specifically classifies into these two categories
labels = ["Non-Cancerous", "Cancerous"]

print("--- Downloading Specific Keras Model File ---")
try:
    # 1. Download ONLY the .keras file from the repository
    model_path = hf_hub_download(
        repo_id="VRJBro/skin-cancer-detection", 
        filename="skin_cancer_model.keras"
    )
    
    # 2. Load it using the native Keras 3 loader
    model = tf.keras.models.load_model(model_path)
    print(f"✅ SUCCESS: Model loaded from {model_path}")
    
except Exception as e:
    print(f"❌ LOADING ERROR: {e}")




@app.get("/")
async def health():
    return {"status": "online", "model_loaded": model is not None}


@app.post("/analyze")
async def analyze(file: UploadFile = File(...), language: str = Form(...)):
    """First Step: Get Prediction + Gemini Text"""

    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded.")

    try:
        contents = await file.read()
        img = Image.open(io.BytesIO(contents)).convert('RGB')
        img = img.resize((224, 224))
        
        # 1. Convert to array
        img_array = np.array(img).astype(np.float32)
        
        # 2. Add batch dimension
        img_array = np.expand_dims(img_array, axis=0)

        # 3. USE OFFICIAL VGG16 PREPROCESSING
        # This is more reliable than just / 255.0
        img_array = preprocess_input(img_array)

        # 4. Get Prediction
        predictions = model.predict(img_array)
        score = float(predictions[0][0])
        
        # DEBUG: Print this to your terminal to see the actual math
        print(f"DEBUG: Raw model score is {score}")

        # 5. LABELS (Adjust based on your test results)
        # If a known cancerous image gives a score NEAR 0: Swap these.
        # Current Logic: 0 = Non-Cancerous, 1 = Cancerous
        if score > 0.5:
            label = "Cancerous"
            confidence = score
        else:
            label = "Non-Cancerous"
            confidence = 1 - score
        prompt = f"""
ACT AS: An expert Dermatologist and Medical Consultant.
CONTEXT: A patient has uploaded a dermoscopic image for skin lesion analysis. 
AI MODEL RESULT: The local analysis model has classified the lesion as '{label}' with a confidence of {confidence*100:.2f}%.

TASK: Generate a comprehensive medical analysis report in {language}. 

REPORT STRUCTURE (Use Markdown):
1. ## Patient Report Summary
   - State the classification result clearly.
   - Explain what '{label}' generally means in simple terms.
2. ## Clinical Observations
   - Based on the image analysis, describe what clinical features a specialist would look for (e.g., symmetry, borders, color variations).
3. ## Recommendations & Next Steps
   - Provide clear actionable advice (e.g., "Monitor for changes using the ABCDE rule", "Consult a specialist for a biopsy", "Annual skin checks").
4. ## Important Disclaimer
   - Include a standard medical disclaimer: This is an AI-generated report for educational purposes and NOT a final diagnosis.

TONE: Professional, supportive, and clinical.
FORMATTING: Use clear headings, bullet points, and bold text for emphasis.
"""
    
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[types.Part.from_bytes(data=contents, mime_type="image/jpeg"), prompt]
        )
        
        return {
            "prediction": label,
            "confidence": confidence,
            "report_text": response.text
        }
    except Exception as e:
        print(f"Prediction Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
class PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "AI Medical Analysis Report", border=False, ln=True, align="C")
        self.ln(5)

@app.post("/generate_report")
async def generate_report(
    report_text: str = Form(...), 
    report_type: str = Form(...),
    label: str = Form(...),
    confidence: float = Form(...)
):
    if report_type == "pdf":
        pdf = PDF()
        pdf.add_page()
        
        # 1. Add the Result Summary
        pdf.set_font("Arial", 'B', 14)
        color = (220, 38, 38) if label.lower() == "cancerous" else (22, 163, 74)
        pdf.set_text_color(*color)
        pdf.cell(0, 10, f"Analysis Result: {label.upper()}", ln=True)
        
        pdf.set_font("Arial", size=11)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, f"Confidence Score: {float(confidence)*100:.2f}%", ln=True)
        pdf.ln(5)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y()) # Horizontal line
        pdf.ln(5)

        # 2. Convert Markdown to HTML for Rendering
        # Gemini's markdown is converted to basic HTML tags (<b>, <h1>, <ul>)
        html_content = markdown(report_text)
        
        # Clean up some common markdown-to-html issues for FPDF
        pdf.set_font("Arial", size=10)
        pdf.write_html(html_content)

        # 3. Finalize and Return Bytes
        # In fpdf2, output() returns bytes directly
        pdf_bytes = pdf.output()
            
        return StreamingResponse(
            io.BytesIO(pdf_bytes), 
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=Report.pdf",
                "Cache-Control": "no-cache"
            }
        )    
    # Word logic remains standard
    if report_type == "word":
        doc = Document()
        
        # Add Header/Title
        title = doc.add_heading('Medical Analysis Report', 0)
        title.alignment = 1 # Center
        
        # Add Summary Box
        p = doc.add_paragraph()
        run = p.add_run(f"FINAL RESULT: {label.upper()}")
        run.bold = True
        run.font.size = 140000 # Approx 14pt
        
        doc.add_paragraph(f"Confidence Score: {float(confidence)*100:.2f}%")
        doc.add_section() # Divider

        # Render Markdown Content
        add_markdown_to_word(doc, report_text)

        # Save to BytesIO
        out = io.BytesIO()
        doc.save(out)
        out.seek(0)

        return StreamingResponse(
            out, 
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": "attachment; filename=Analysis_Report.docx"}
        )