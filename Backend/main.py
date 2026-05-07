from fastapi import FastAPI, File, UploadFile, Form, HTTPException #type:ignore
from fastapi.middleware.cors import CORSMiddleware #type:ignore
from pydantic import BaseModel
import sqlite3
import math
import requests
import numpy as np
import cv2 #type:ignore
import easyocr #type:ignore
import os

# Import your trained logic from logic.py
try:
    from .logic import predict_medicine, predict_xray_part, predict_symptoms_ai
except ImportError:
    # Fallback if running as a standalone script for testing
    from logic import predict_medicine, predict_xray_part, predict_symptoms_ai

# ---------------- EASYOCR (OFFLINE MODE) ----------------
# Using your specific path for local models
reader = easyocr.Reader(
    ['en'],
    model_storage_directory=r"C:\Users\Samruddhi pai\.EasyOCR\model",
    download_enabled=False
)

app = FastAPI(title="MiMediCare AI Backend")

# ---------------- CORS CONFIGURATION ----------------
# Allows your React App (localhost:3000) to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- DATA MODELS ----------------
class SymptomInput(BaseModel):
    text: str

class LocationInput(BaseModel):
    lat: float
    lon: float

# ---------------- HELPER FUNCTIONS ----------------

def extract_text_from_image(image_bytes):
    """Uses EasyOCR to detect medicine names on packaging."""
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        result = reader.readtext(img)
        return " ".join([res[1] for res in result]).upper()
    except Exception:
        return ""

def get_nearby_doctors(lat, lon, specialty=None):
    """Queries your local SQLite database for doctors within 15km."""
    try:
        db_path = os.path.join("Database", "doctors.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        if specialty:
            cursor.execute("SELECT name, specialty, lat, lon, address FROM doctors WHERE specialty=?", (specialty,))
        else:
            cursor.execute("SELECT name, specialty, lat, lon, address FROM doctors")

        docs = cursor.fetchall()
        conn.close()

        results = []
        for d in docs:
            # Haversine-lite distance calculation
            dist = math.sqrt((lat - d[2])**2 + (lon - d[3])**2) * 111
            if dist < 15:
                results.append({
                    "name": d[0],
                    "specialty": d[1],
                    "address": d[4],
                    "distance": round(dist, 2)
                })

        return sorted(results, key=lambda x: x["distance"])
    except Exception:
        return []

# =====================================================
# ✅ FEATURE 1: MEDICINE SCANNER (AI + OCR)
# =====================================================
@app.post("/identify-pill")
async def identify_pill(file: UploadFile = File(...)):
    image_bytes = await file.read()
    
    # 1. OCR Detection
    extracted_text = extract_text_from_image(image_bytes)
    # 2. AI Model Detection (Notebook #02)
    ai_prediction = predict_medicine(image_bytes)

    return {
        "status": "success",
        "detected_text": extracted_text,
        "ai_prediction": ai_prediction,
        "instructions": "Verify with the physical label before consumption."
    }

# =====================================================
# ✅ FEATURE 2: X-RAY ANALYSIS & EXPLANATION
# =====================================================
@app.post("/analyze-xray")
async def analyze_xray(
    user_lat: float = Form(...),
    user_lon: float = Form(...),
    file: UploadFile = File(...)
):
    image_bytes = await file.read()
    
    # Calls your ResNet-18 model from logic.py
    detected_part, explanation = predict_xray_part(image_bytes)

    # Map organ to specialty for doctor search
    specialty_map = {
        "Heart": "Cardiologist",
        "Lung-Left": "Pulmonologist",
        "Lung-Right": "Pulmonologist",
        "Spleen": "General Surgeon",
        "Pancreas": "Gastroenterologist"
    }
    
    target_specialty = specialty_map.get(detected_part, "General Physician")
    doctors = get_nearby_doctors(user_lat, user_lon, target_specialty)

    return {
        "detected_part": detected_part,
        "explanation": explanation,
        "recommended_specialist": target_specialty,
        "nearby_doctors": doctors
    }

# =====================================================
# ✅ FEATURE 3: SYMPTOM CHECKER (AI-DRIVEN)
# =====================================================
@app.post("/predict-symptoms")
async def predict_symptoms(data: SymptomInput):
    # Calls your TF-IDF + Random Forest model from logic.py
    disease, explanation = predict_symptoms_ai(data.text)
    
    return {
        "prediction": disease,
        "explanation": explanation,
        "disclaimer": "AI prediction only. Please seek professional medical advice."
    }

# =====================================================
# ✅ FEATURE 4: DOCTOR LOCATOR
# =====================================================

import os
import sqlite3
import math

def get_nearby_doctors(lat, lon, specialty=None):
    try:
        # Get the path of main.py
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        
        # JUMP: Go out of 'Backend' and into 'Database'
        # The '..' tells Python to go up one level
        db_path = os.path.join(BASE_DIR, "..", "Database", "doctors.db")
        
        if not os.path.exists(db_path):
            print(f"CRITICAL ERROR: Database not found at {db_path}")
            return []

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        if specialty:
            cursor.execute("SELECT name, specialty, lat, lon, address FROM doctors WHERE specialty=?", (specialty,))
        else:
            cursor.execute("SELECT name, specialty, lat, lon, address FROM doctors")

        docs = cursor.fetchall()
        conn.close()

        results = []
        for d in docs:
            # Haversine distance calculation (simplified for local use)
            dist = math.sqrt((lat - d[2])**2 + (lon - d[3])**2) * 111
            
            # Increase this to 500 if you are testing Mangaluru doctors from Bengaluru!
            if dist < 50: 
                results.append({
                    "name": d[0],
                    "specialty": d[1],
                    "address": d[4],
                    "distance": round(dist, 2)
                })

        return sorted(results, key=lambda x: x["distance"])
    except Exception as e:
        print(f"Database Error: {e}")
        return []
@app.post("/find-nearby-doctors")
async def find_nearby_doctors(loc: LocationInput):
    doctors = get_nearby_doctors(loc.lat, loc.lon)
    if not doctors:
        raise HTTPException(status_code=404, detail="No doctors found in your area.")
    return {"nearby_facilities": doctors}

@app.get("/")
async def root():
    return {"message": "MiMediCare API is Online"}