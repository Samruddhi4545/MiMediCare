from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import math
import requests
import numpy as np
import cv2
import easyocr

# ---------------- EASYOCR (OFFLINE MODE) ----------------
reader = easyocr.Reader(
    ['en'],
    model_storage_directory=r"C:\Users\Samruddhi pai\.EasyOCR\model",
    download_enabled=False
)

# ---------------- AI MODEL PLACEHOLDER ----------------
try:
    from .logic import predict_medicine, predict_xray_part  # type: ignore
except:
    def predict_medicine(image_bytes):
        return "UNKNOWN"

    def predict_xray_part(image_bytes):
        return "Lung-Right"

# ---------------- FASTAPI ----------------
app = FastAPI()

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- MODELS ----------------
class SymptomInput(BaseModel):
    text: str

class LocationInput(BaseModel):
    lat: float
    lon: float

# ---------------- OCR FUNCTION ----------------
def extract_text_from_image(image_bytes):
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        result = reader.readtext(img)
        return " ".join([res[1] for res in result]).upper()
    except:
        return ""

# ---------------- MEDICINE DATABASE ----------------
MED_DB = {
    "DOLO 650": {
        "title": "Dolo 650",
        "manufacturer": "Micro Labs Ltd.",
        "composition": "Paracetamol 650 mg",
        "usage_intro": "Used for fever and pain relief",
        "uses_list": ["Fever", "Headache", "Body pain"]
    },
    "PARACETAMOL": {
        "title": "Paracetamol",
        "manufacturer": "Generic",
        "composition": "Paracetamol",
        "usage_intro": "Pain reliever",
        "uses_list": ["Fever", "Pain"]
    },
    "IBUPROFEN": {
        "title": "Ibuprofen",
        "manufacturer": "Generic",
        "composition": "Ibuprofen",
        "usage_intro": "Anti-inflammatory",
        "uses_list": ["Pain", "Inflammation"]
    }
}

# ---------------- OPENFDA API ----------------
def fetch_drug_info(name):
    try:
        url = f"https://api.fda.gov/drug/label.json?search={name}&limit=1"
        res = requests.get(url)
        if res.status_code == 200:
            data = res.json()["results"][0]
            return {
                "title": data.get("openfda", {}).get("brand_name", ["Unknown"])[0],
                "manufacturer": data.get("openfda", {}).get("manufacturer_name", ["Unknown"])[0],
                "composition": "See official label",
                "usage_intro": data.get("indications_and_usage", ["Not available"])[0],
                "uses_list": data.get("purpose", ["General use"])
            }
    except:
        pass
    return None

# ---------------- DOCTOR SEARCH ----------------
def get_nearby_doctors(lat, lon, specialty=None):
    try:
        conn = sqlite3.connect("Database/doctors.db")
        cursor = conn.cursor()

        if specialty:
            cursor.execute("SELECT name, specialty, lat, lon, address FROM doctors WHERE specialty=?", (specialty,))
        else:
            cursor.execute("SELECT name, specialty, lat, lon, address FROM doctors")

        docs = cursor.fetchall()
        conn.close()

        results = []
        for d in docs:
            dist = math.sqrt((lat - d[2])**2 + (lon - d[3])**2) * 111
            if dist < 15:
                results.append({
                    "name": d[0],
                    "specialty": d[1],
                    "address": d[4],
                    "distance": round(dist, 2)
                })

        return sorted(results, key=lambda x: x["distance"])
    except:
        return []

# =====================================================
# ✅ FEATURE 1: SMART MEDICINE IDENTIFICATION
# =====================================================
@app.post("/identify-pill")
async def identify_pill(file: UploadFile = File(...)):

    image_bytes = await file.read()

    extracted_text = extract_text_from_image(image_bytes)
    ai_prediction = predict_medicine(image_bytes)

    combined = (extracted_text + " " + str(ai_prediction)).upper()

    for key in MED_DB:
        if key in combined:
            return {
                "source": "local_db",
                "detected_text": extracted_text,
                "ai_prediction": ai_prediction,
                "details": MED_DB[key]
            }

    api_data = fetch_drug_info(combined)
    if api_data:
        return {
            "source": "openfda",
            "detected_text": extracted_text,
            "ai_prediction": ai_prediction,
            "details": api_data
        }

    return {
        "source": "unknown",
        "detected_text": extracted_text,
        "ai_prediction": ai_prediction,
        "details": {
            "title": combined,
            "manufacturer": "Unknown",
            "composition": "Unknown",
            "usage_intro": "Consult pharmacist",
            "uses_list": ["Verification required"]
        }
    }

# =====================================================
# ✅ FEATURE 2: XRAY ANALYSIS (WITH CONDITION)
# =====================================================
@app.post("/analyze-xray")
async def analyze_xray(
    user_lat: float = Form(...),
    user_lon: float = Form(...),
    file: UploadFile = File(...)
):

    image_bytes = await file.read()
    result = predict_xray_part(image_bytes)

    diagnostic_models = {

        "Lung-Right": {
            "condition": "Right Lung Abnormality Detected",
            "explanation": "Possible infection or inflammation in right lung region.",
            "specialist": "Pulmonologist"
        },

        "Lung-Left": {
            "condition": "Left Lung Abnormality Detected",
            "explanation": "Density variation observed in left lung.",
            "specialist": "Pulmonologist"
        },

        "Chest-Clear": {
            "condition": "Normal Chest X-ray",
            "explanation": "No visible abnormality detected.",
            "specialist": "General Physician"
        },

        "Bone-Fracture": {
            "condition": "Bone Fracture Detected",
            "explanation": "Discontinuity in bone structure.",
            "specialist": "Orthopedic Surgeon"
        }
    }

    report = diagnostic_models.get(
        result,
        {
            "condition": f"Analysis of {result}",
            "explanation": "No mapping available.",
            "specialist": "General Physician"
        }
    )

    doctors = get_nearby_doctors(user_lat, user_lon, report["specialist"])

    return {
        "detected_part": result,
        **report,
        "nearby_doctors": doctors
    }

# =====================================================
# ✅ FEATURE 3: SYMPTOM CHECKER
# =====================================================
@app.post("/predict-symptoms")
async def predict_symptoms(data: SymptomInput):

    text = data.text.lower()

    disease_db = {
        "Common Cold": ["cough", "sneezing", "runny nose", "mild fever"],
        "Flu": ["fever", "body pain", "chills", "fatigue"],
        "COVID-19": ["fever", "cough", "loss of taste", "breath"],
        "Allergy": ["rash", "itching", "sneezing"],
        "Malaria": ["fever", "chills", "sweating"],
        "Typhoid": ["fever", "weakness", "abdominal pain"],
        "Pneumonia": ["cough", "fever", "breathing", "chest pain"]
    }

    scores = {}

    # Count matching symptoms
    for disease, symptoms in disease_db.items():
        match_count = sum(1 for s in symptoms if s in text)
        if match_count > 0:
            scores[disease] = match_count

    if not scores:
        return {
            "prediction": "No symptoms detected. Please describe symptoms like fever, cough, pain, etc."
        }

    # Sort diseases by highest match
    sorted_diseases = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    # Top predictions
    result = []
    for disease, score in sorted_diseases[:3]:
        result.append({
            "disease": disease,
            "confidence": f"{round((score/5)*100, 1)}%"
        })

    return {
        "prediction": result
    }

# =====================================================
# ✅ FEATURE 4: DOCTOR LOCATOR
# =====================================================
@app.post("/find-nearby-doctors")
async def find_nearby_doctors(loc: LocationInput):

    doctors = get_nearby_doctors(loc.lat, loc.lon)

    if not doctors:
        raise HTTPException(status_code=404, detail="No doctors found")

    return {"nearby_facilities": doctors}

# ---------------- ROOT ----------------
@app.get("/")
async def root():
    return {"message": "MiMediCare API Running"}