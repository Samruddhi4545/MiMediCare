import torch #type:ignore
from ultralytics import YOLO #type:ignore
import tensorflow as tf #type:ignore
import numpy as np #type:ignore
from PIL import Image #type:ignore
import io

# 1. Load Symptom Model (Notebook #01)
# Assuming you saved your symptom model as a .h5 or pickle
# symptom_model = tf.keras.models.load_model('models/symptom_model.h5')

# 2. Load Pill Detection Model (Notebook #02)
pill_model = YOLO('Backend/models/pill_model.pt')

# 3. Load X-ray Model (Notebook #03)
# We load the architecture then the saved weights
from torchvision import models #type:ignore
import torch.nn as nn #type:ignore

def load_xray_model():
    # 1. Initialize standard ResNet18
    model = models.resnet18()
    
    # 2. FIX: Change the first convolutional layer to accept 1 channel (Grayscale)
    # instead of the default 3 channels (RGB)
    model.conv1 = nn.Conv2d(1, 64, kernel_size=7, stride=2, padding=3, bias=False)
    
    # 3. Change the final layer to match your 11 classes
    model.fc = nn.Linear(model.fc.in_features, 11) 
    
    # 4. Now load the weights—the shapes will match!
    model.load_state_dict(torch.load('Backend/models/universal_xray_body.pth', map_location=torch.device('cpu')))
    
    model.eval()
    return model

xray_model = load_xray_model()

# --- Inference Functions ---

def predict_medicine(image_bytes):
    img = Image.open(io.BytesIO(image_bytes))
    results = pill_model.predict(source=img, conf=0.5)
    # Extracts labels found in the image
    names = [pill_model.names[int(c)] for r in results for c in r.boxes.cls]
    return names if names else ["Unknown Medicine"]

def predict_xray_part(image_bytes):
    # Preprocessing to match 128x128 from your optimized code
    img = Image.open(io.BytesIO(image_bytes)).convert('L') # Grayscale
    img = img.resize((128, 128))
    img_tensor = torch.tensor(np.array(img)).unsqueeze(0).unsqueeze(0).float() / 255.0
    
    with torch.no_grad():
        output = xray_model(img_tensor)
        prediction = torch.argmax(output, dim=1).item()
    
    # Map back to body parts
    parts = ["Bladder", "Femur-Left", "Femur-Right", "Heart", "Kidney-Left", 
            "Kidney-Right", "Liver", "Lung-Left", "Lung-Right", "Pancreas", "Spleen"]
    return parts[prediction]