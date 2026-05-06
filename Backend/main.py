from fastapi import FastAPI, File, UploadFile, Form #type:ignore
from .logic import predict_medicine, predict_xray_part #type:ignore
import sqlite3
import math

app = FastAPI()

# Helper for GPS Distance (as we discussed)
def get_nearest_doctors(lat, lon, specialty):
    conn = sqlite3.connect('Database/doctors.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name, specialty, lat, lon, address FROM doctors WHERE specialty=?", (specialty,))
    docs = cursor.fetchall()
    conn.close()
    
    results = []
    for d in docs:
        # Simple distance math
        dist = math.sqrt((lat - d[2])**2 + (lon - d[3])**2) 
        results.append({"name": d[0], "address": d[4], "distance": round(dist*111, 2)}) # ~111km per degree
    
    return sorted(results, key=lambda x: x['distance'])[:3]

@app.post("/analyze-xray")
async def analyze_xray(user_lat: float = Form(...), user_lon: float = Form(...), file: UploadFile = File(...)):
    image_bytes = await file.read()
    body_part = predict_xray_part(image_bytes)
    
    # Map body part to a specialist
    specialist_map = {"Lung-Left": "Pulmonologist", "Lung-Right": "Pulmonologist", "Femur-Left": "Orthopedic"}
    needed = specialist_map.get(body_part, "General Physician")
    
    doctors = get_nearest_doctors(user_lat, user_lon, needed)
    
    return {
        "detected_part": body_part,
        "recommended_specialist": needed,
        "nearby_doctors": doctors
    }

@app.post("/identify-pill")
async def identify_pill(file: UploadFile = File(...)):
    image_bytes = await file.read()
    pills = predict_medicine(image_bytes)
    return {"detected_pills": pills}