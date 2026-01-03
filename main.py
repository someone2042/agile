from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from transformers import pipeline
from PIL import Image
import io

app = FastAPI()

# Enable CORS so your frontend can talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with your frontend URL
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the model once when the server starts
print("Loading AI model... please wait.")
classifier = pipeline("image-classification", model="VRJBro/skin-cancer-detection")

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    # 1. Read the uploaded image bytes
    request_object_content = await file.read()
    image = Image.open(io.BytesIO(request_object_content))

    # 2. Run the model
    results = classifier(image)

    # 3. Return the results as JSON
    # result is a list like: [{"label": "cancerous", "score": 0.98}, ...]
    return {"predictions": results}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)