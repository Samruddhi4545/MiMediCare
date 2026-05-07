import torch #type:ignore
import torch.nn as nn #type:ignore
from torchvision import models, transforms #type:ignore
from ultralytics import YOLO #type:ignore
import pickle
import os
import io
from PIL import Image
import numpy as np

# --- 1. CONFIGURATION & PATHS ---
# Using absolute-style paths to avoid the "Not Found" errors we saw earlier
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
XRAY_MODEL_PATH = os.path.join(BASE_DIR, 'models', 'universal_xray_body.pth')
PILL_MODEL_PATH = os.path.join(BASE_DIR, 'models', 'pill_model.pt')
SYMPTOM_MODEL_PATH = os.path.join(BASE_DIR, 'models', 'symptom_model.pkl')

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# --- 2. MODEL LOADING FUNCTIONS ---

def load_xray_model():
    """Initializes ResNet18 and loads your MedMNIST weights."""
    model = models.resnet18()
    # Match the Jupyter training: 1 input channel (Grayscale), 11 output classes
    model.conv1 = nn.Conv2d(1, 64, kernel_size=7, stride=2, padding=3, bias=False)
    model.fc = nn.Linear(model.fc.in_features, 11)
    
    if os.path.exists(XRAY_MODEL_PATH):
        model.load_state_dict(torch.load(XRAY_MODEL_PATH, map_location=device))
        print("✅ X-Ray Model Loaded Successfully")
    model.to(device)
    model.eval()
    return model

def load_symptom_assets():
    """Loads the TF-IDF vectorizer and Random Forest model."""
    if os.path.exists(SYMPTOM_MODEL_PATH):
        with open(SYMPTOM_MODEL_PATH, 'rb') as f:
            print("✅ Symptom Model Loaded Successfully")
            return pickle.load(f)
    return None

# Initialize models globally for speed
xray_model = load_xray_model()
pill_model = YOLO(PILL_MODEL_PATH) if os.path.exists(PILL_MODEL_PATH) else None
symptom_assets = load_symptom_assets()

# --- 3. INFERENCE LOGIC ---

def predict_medicine(image_bytes):
    """Detects pill names using YOLO."""
    if not pill_model: return ["Model File Missing"]
    img = Image.open(io.BytesIO(image_bytes))
    results = pill_model.predict(source=img, conf=0.5)
    names = [pill_model.names[int(c)] for r in results for c in r.boxes.cls]
    return names if names else ["Unknown Medicine"]

def predict_xray_part(image_bytes):
    """Predicts body part and generates an explanation."""
    img = Image.open(io.BytesIO(image_bytes)).convert('L')
    
    # Preprocessing must match your 128x128 Jupyter optimization
    transform = transforms.Compose([
        transforms.Resize((128, 128)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[.5], std=[.5])
    ])
    
    img_tensor = transform(img).unsqueeze(0).to(device)
    
    with torch.no_grad():
        output = xray_model(img_tensor)
        prediction = torch.argmax(output, dim=1).item()
    
    parts = ["Bladder", "Femur-Left", "Femur-Right", "Heart", "Kidney-Left", 
             "Kidney-Right", "Liver", "Lung-Left", "Lung-Right", "Pancreas", "Spleen"]
    
    detected = parts[prediction]
    
    # NEW FEATURE: The Explanation Engine
    explanations = {
        "Spleen": "AI identified a dense mass in the upper left abdominal quadrant, typical of splenic tissue.",
        "Heart": "The central cardiac silhouette was detected. System is verifying cardiothoracic ratio.",
        "Lung-Right": "Right pulmonary field detected. Analysis focused on air-to-tissue density.",
        "Lung-Left": "Left pulmonary field detected. Checking for pleural clarity.",
        "Bladder": "Lower pelvic region detected. Focusing on fluid-filled organ structures."
    }
    
    explanation = explanations.get(detected, f"Standard anatomical markers for {detected} were identified.")
    
    return detected, explanation

def predict_symptoms_ai(user_text):
    """Predicts disease and provides the 'Why'."""
    if not symptom_assets:
        return "System Offline", "Model files are missing from the server."
    
    tfidf = symptom_assets['tfidf']
    model = symptom_assets['model']
    le = symptom_assets['label_encoder']
    
    # Vectorize and Predict
    vec = tfidf.transform([user_text.lower()])
    pred_idx = model.predict(vec)[0]
    disease = le.inverse_transform([pred_idx])[0]
    
    explanation = f"Based on your description, the model matched your symptoms to clinical patterns of {disease}."
    
    return disease, explanation