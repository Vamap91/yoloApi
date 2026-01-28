import os
import io
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

import numpy as np
from fastapi import FastAPI, File, UploadFile, Header, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from ultralytics import YOLO
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="YOLO Vehicle Damage Detection API",
    description="API for detecting vehicle damage using YOLOv8",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
DAMAGE_CONFIG = {
    'severity_map': {
        'shattered_glass': 'Severo',
        'broken_lamp': 'Severo',
        'flat_tire': 'Severo',
        'dent': 'Moderado',
        'scratch': 'Leve',
        'crack': 'Leve'
    },
    'location_map': {
        'shattered_glass': 'Vidros',
        'flat_tire': 'Rodas',
        'broken_lamp': 'Iluminação',
        'dent': 'Carroceria',
        'scratch': 'Pintura',
        'crack': 'Para-choque/Plásticos'
    },
    'cost_estimate': {
        'shattered_glass': (800, 2500),
        'broken_lamp': (300, 1500),
        'flat_tire': (200, 800),
        'dent': (500, 2000),
        'scratch': (150, 800),
        'crack': (200, 1000)
    }
}

MODEL_VERSION = "v2.0.0"
MODEL_PATH = f"car_damage_best_{MODEL_VERSION}.pt"
API_KEY_DEMO = os.getenv("API_KEY_DEMO", "demo-key-12345")

# Global model instance
_model = None


def get_model() -> YOLO:
    """Load or retrieve cached YOLO model"""
    global _model
    
    if _model is not None:
        return _model
    
    # Download model if not exists
    if not os.path.exists(MODEL_PATH):
        logger.info(f"Downloading model from GitHub release...")
        model_url = f"https://github.com/Vamap91/YOLOProject/releases/download/{MODEL_VERSION}/car_damage_best.pt"
        
        try:
            response = requests.get(model_url, stream=True, timeout=300)
            response.raise_for_status()
            
            with open(MODEL_PATH, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"Model downloaded successfully to {MODEL_PATH}")
        except Exception as e:
            logger.error(f"Failed to download model: {e}")
            raise RuntimeError(f"Failed to download model: {e}")
    
    # Load model
    try:
        _model = YOLO(MODEL_PATH)
        logger.info(f"Model loaded successfully from {MODEL_PATH}")
        return _model
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise RuntimeError(f"Failed to load model: {e}")


def validate_api_key(x_api_key: Optional[str] = Header(None)) -> None:
    """Validate API key from header"""
    if x_api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header"
        )
    
    if x_api_key != API_KEY_DEMO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )


def process_image(image: Image.Image, model: YOLO) -> tuple[List[Dict[str, Any]], int, int]:
    """Process image with YOLO model and return detections"""
    img_array = np.array(image)
    height, width = img_array.shape[:2]
    
    results = model(img_array, conf=0.25)
    
    detections = []
    if len(results[0].boxes) > 0:
        for box in results[0].boxes:
            class_id = int(box.cls)
            class_name = model.names[class_id]
            
            # Get bbox coordinates
            bbox_coords = box.xyxy[0].cpu().numpy().tolist()
            x1, y1, x2, y2 = bbox_coords
            
            # Get severity and area affected
            severity = DAMAGE_CONFIG['severity_map'].get(class_name, 'Moderado')
            area_affected = DAMAGE_CONFIG['location_map'].get(class_name, 'N/A')
            
            # Get cost range
            cost_range = DAMAGE_CONFIG['cost_estimate'].get(class_name, (0, 0))
            cost_min, cost_max = cost_range
            
            detection = {
                'class': class_name,
                'confidence': float(box.conf),
                'bbox': {
                    'x1': round(x1, 2),
                    'y1': round(y1, 2),
                    'x2': round(x2, 2),
                    'y2': round(y2, 2)
                },
                'severity': severity,
                'area_affected': area_affected,
                'estimated_cost_range': {
                    'min': cost_min,
                    'max': cost_max,
                    'currency': 'BRL'
                }
            }
            detections.append(detection)
    
    return detections, width, height


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


@app.post("/v1/damage:detect", tags=["Detection"])
async def detect_damage(
    image: UploadFile = File(...),
    x_api_key: Optional[str] = Header(None)
):
    """
    Detect vehicle damage in uploaded image
    
    - **image**: Image file (jpg/png/jpeg)
    - **X-API-Key**: API key header (required)
    
    Returns:
    - model_version: Version of the YOLO model
    - image_width: Width of the input image
    - image_height: Height of the input image
    - detections: List of detected damages with details
    """
    
    # Validate API key
    validate_api_key(x_api_key)
    
    # Validate file type
    if image.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image format. Only jpg, png, and jpeg are supported."
        )
    
    try:
        # Read image
        contents = await image.read()
        img = Image.open(io.BytesIO(contents)).convert("RGB")
        
        # Get model
        model = get_model()
        
        # Process image
        detections, width, height = process_image(img, model)
        
        # Prepare response
        response = {
            "model_version": MODEL_VERSION,
            "image_width": width,
            "image_height": height,
            "detections": detections,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        return JSONResponse(content=response, status_code=200)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing image: {str(e)}"
        )


@app.get("/v1/models", tags=["Models"])
async def list_models(x_api_key: Optional[str] = Header(None)):
    """List available models"""
    validate_api_key(x_api_key)
    
    return {
        "models": [
            {
                "name": "car_damage_best",
                "version": MODEL_VERSION,
                "classes": list(DAMAGE_CONFIG['severity_map'].keys()),
                "framework": "YOLOv8"
            }
        ]
    }


@app.get("/v1/damage-classes", tags=["Info"])
async def get_damage_classes(x_api_key: Optional[str] = Header(None)):
    """Get available damage classes and their configurations"""
    validate_api_key(x_api_key)
    
    classes = {}
    for class_name in DAMAGE_CONFIG['severity_map'].keys():
        cost_range = DAMAGE_CONFIG['cost_estimate'].get(class_name, (0, 0))
        classes[class_name] = {
            'severity': DAMAGE_CONFIG['severity_map'].get(class_name),
            'area_affected': DAMAGE_CONFIG['location_map'].get(class_name),
            'estimated_cost_range': {
                'min': cost_range[0],
                'max': cost_range[1],
                'currency': 'BRL'
            }
        }
    
    return {"damage_classes": classes}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
