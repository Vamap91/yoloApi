import os
import io
import logging
import base64
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

import numpy as np
import cv2
from fastapi import FastAPI, File, UploadFile, Header, HTTPException, status, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from ultralytics import YOLO
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

MODEL_VERSION = os.getenv("MODEL_VERSION", "v2.0.0")
API_KEY_DEMO = os.getenv("API_KEY_DEMO", "demo-key-12345")
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", 10 * 1024 * 1024))  # 10MB
MAX_IMAGE_DIMENSION = int(os.getenv("MAX_IMAGE_DIMENSION", 1280))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")

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
        'crack': 'Pintura'
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

MODEL_PATH = f"car_damage_best_{MODEL_VERSION}.pt"

# ============================================================================
# SINGLETON MODEL MANAGER
# ============================================================================

class ModelManager:
    """Singleton para gerenciar o modelo YOLO"""
    _instance = None
    _model = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
        return cls._instance

    def initialize(self):
        """Inicializar o modelo na primeira vez"""
        if self._initialized:
            return
        
        logger.info("Iniciando carregamento do modelo YOLO...")
        
        # Download model if not exists
        if not os.path.exists(MODEL_PATH):
            logger.info(f"Modelo não encontrado. Baixando de GitHub...")
            self._download_model()
        
        # Load model
        try:
            self._model = YOLO(MODEL_PATH)
            logger.info(f"✓ Modelo carregado com sucesso: {MODEL_PATH}")
            self._initialized = True
        except Exception as e:
            logger.error(f"✗ Erro ao carregar modelo: {e}")
            raise RuntimeError(f"Failed to load model: {e}")

    def _download_model(self):
        """Baixar modelo do GitHub release"""
        model_url = f"https://github.com/Vamap91/YOLOProject/releases/download/{MODEL_VERSION}/car_damage_best.pt"
        
        try:
            logger.info(f"Baixando de: {model_url}")
            response = requests.get(model_url, stream=True, timeout=300)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(MODEL_PATH, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            logger.info(f"Download: {downloaded / 1024 / 1024:.1f}MB / {total_size / 1024 / 1024:.1f}MB ({percent:.1f}%)")
            
            logger.info(f"✓ Modelo baixado com sucesso")
        except Exception as e:
            logger.error(f"✗ Erro ao baixar modelo: {e}")
            raise RuntimeError(f"Failed to download model: {e}")

    def get_model(self) -> YOLO:
        """Obter instância do modelo"""
        if not self._initialized:
            self.initialize()
        return self._model

    def warmup(self):
        """Aquecimento do modelo com imagem dummy"""
        if not self._initialized:
            self.initialize()
        
        try:
            logger.info("Executando warmup do modelo...")
            dummy_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
            _ = self._model(dummy_image, verbose=False)
            logger.info("✓ Warmup concluído com sucesso")
        except Exception as e:
            logger.warning(f"Warmup falhou (não crítico): {e}")


# ============================================================================
# INITIALIZE FASTAPI APP
# ============================================================================

app = FastAPI(
    title="YOLO Vehicle Damage Detection API",
    description="API para detecção de danos em veículos usando YOLOv8",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key"],
)

# Initialize model manager
model_manager = ModelManager()


# ============================================================================
# STARTUP/SHUTDOWN EVENTS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Inicializar modelo e executar warmup no startup"""
    logger.info("=" * 60)
    logger.info("INICIANDO APLICAÇÃO")
    logger.info("=" * 60)
    
    try:
        model_manager.initialize()
        model_manager.warmup()
        logger.info("✓ Aplicação pronta para receber requisições")
    except Exception as e:
        logger.error(f"✗ Erro fatal no startup: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup no shutdown"""
    logger.info("Encerrando aplicação...")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def validate_api_key(x_api_key: Optional[str] = Header(None)) -> None:
    """Validar API key do header"""
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


def resize_image_if_needed(image: Image.Image, max_dimension: int = MAX_IMAGE_DIMENSION) -> Image.Image:
    """Redimensionar imagem se necessário, mantendo proporções"""
    width, height = image.size
    
    if max(width, height) > max_dimension:
        scale = max_dimension / max(width, height)
        new_width = int(width * scale)
        new_height = int(height * scale)
        
        logger.info(f"Redimensionando imagem de {width}x{height} para {new_width}x{new_height}")
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    return image


def draw_annotations(
    image_array: np.ndarray,
    detections: List[Dict[str, Any]]
) -> np.ndarray:
    """Desenhar bounding boxes e labels na imagem"""
    annotated = image_array.copy()
    
    for i, detection in enumerate(detections, 1):
        bbox = detection['bbox']
        x1, y1, x2, y2 = int(bbox['x1']), int(bbox['y1']), int(bbox['x2']), int(bbox['y2'])
        confidence = detection['confidence']
        class_name = detection['class']
        severity = detection['severity']
        
        # Cores por severidade
        color_map = {
            'Leve': (0, 255, 0),      # Verde
            'Moderado': (0, 165, 255),  # Laranja
            'Severo': (0, 0, 255)       # Vermelho
        }
        color = color_map.get(severity, (0, 255, 0))
        
        # Desenhar bounding box
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 3)
        
        # Preparar label
        label = f"{class_name} ({confidence:.0%}) [{severity}]"
        
        # Desenhar background do label
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        thickness = 2
        
        (text_width, text_height), baseline = cv2.getTextSize(label, font, font_scale, thickness)
        
        cv2.rectangle(
            annotated,
            (x1, y1 - text_height - 10),
            (x1 + text_width + 10, y1),
            color,
            -1
        )
        
        # Desenhar texto
        cv2.putText(
            annotated,
            label,
            (x1 + 5, y1 - 5),
            font,
            font_scale,
            (255, 255, 255),
            thickness
        )
    
    return annotated


def process_image(image: Image.Image, model: YOLO) -> tuple[List[Dict[str, Any]], np.ndarray]:
    """Processar imagem com modelo YOLO e retornar detecções + imagem anotada"""
    img_array = np.array(image)
    height, width = img_array.shape[:2]
    
    # Executar inferência
    results = model(img_array, conf=0.25, verbose=False)
    
    detections = []
    if len(results[0].boxes) > 0:
        for idx, box in enumerate(results[0].boxes, 1):
            class_id = int(box.cls)
            class_name = model.names[class_id]
            
            # Coordenadas do bbox
            bbox_coords = box.xyxy[0].cpu().numpy().tolist()
            x1, y1, x2, y2 = bbox_coords
            
            # Informações de severidade e localização
            severity = DAMAGE_CONFIG['severity_map'].get(class_name, 'Moderado')
            area_affected = DAMAGE_CONFIG['location_map'].get(class_name, 'N/A')
            
            # Estimativa de custo
            cost_range = DAMAGE_CONFIG['cost_estimate'].get(class_name, (0, 0))
            cost_min, cost_max = cost_range
            
            detection = {
                'id': f"dmg_{idx:03d}",
                'class': class_name,
                'confidence': float(box.conf),
                'bbox': {
                    'x1': int(x1),
                    'y1': int(y1),
                    'x2': int(x2),
                    'y2': int(y2)
                },
                'severity': severity,
                'area_affected': area_affected,
                'estimated_cost_range': f"R$ {cost_min} - R$ {cost_max}"
            }
            detections.append(detection)
    
    # Desenhar anotações
    annotated_image = draw_annotations(img_array, detections)
    
    return detections, annotated_image


def build_summary(detections: List[Dict[str, Any]], image_width: int, image_height: int) -> Dict[str, Any]:
    """Construir resumo das detecções"""
    summary = {
        'total_damages': len(detections),
        'by_type': {
            'dent': 0,
            'scratch': 0,
            'crack': 0,
            'shattered_glass': 0,
            'broken_lamp': 0,
            'flat_tire': 0
        },
        'by_severity': {
            'Leve': 0,
            'Moderado': 0,
            'Severo': 0
        },
        'by_area_affected': {
            'Carroceria': 0,
            'Pintura': 0,
            'Vidros': 0,
            'Iluminação': 0,
            'Rodas': 0
        },
        'estimated_total_cost_range': 'R$ 0 - R$ 0'
    }
    
    total_min = 0
    total_max = 0
    
    for detection in detections:
        # By type
        class_name = detection['class']
        if class_name in summary['by_type']:
            summary['by_type'][class_name] += 1
        
        # By severity
        severity = detection['severity']
        if severity in summary['by_severity']:
            summary['by_severity'][severity] += 1
        
        # By area affected
        area = detection['area_affected']
        if area in summary['by_area_affected']:
            summary['by_area_affected'][area] += 1
        
        # Total cost
        cost_range_str = detection['estimated_cost_range']
        # Parse "R$ min - R$ max"
        try:
            parts = cost_range_str.replace('R$', '').split('-')
            min_cost = int(parts[0].strip())
            max_cost = int(parts[1].strip())
            total_min += min_cost
            total_max += max_cost
        except:
            pass
    
    summary['estimated_total_cost_range'] = f"R$ {total_min} - R$ {total_max}"
    
    return summary


def image_to_base64(image_array: np.ndarray) -> str:
    """Converter imagem numpy para base64 PNG"""
    # Converter BGR para RGB se necessário
    if len(image_array.shape) == 3 and image_array.shape[2] == 3:
        image_rgb = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
    else:
        image_rgb = image_array
    
    # Codificar para PNG
    success, buffer = cv2.imencode('.png', image_rgb)
    if not success:
        raise ValueError("Falha ao codificar imagem para PNG")
    
    # Converter para base64
    base64_str = base64.b64encode(buffer).decode('utf-8')
    return base64_str


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


@app.post("/warmup", tags=["Utility"])
async def warmup(x_api_key: Optional[str] = Header(None)):
    """Endpoint de warmup do modelo"""
    validate_api_key(x_api_key)
    
    try:
        model_manager.warmup()
        return {"status": "warmup_completed"}
    except Exception as e:
        logger.error(f"Erro no warmup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Warmup failed: {str(e)}"
        )


@app.post("/v1/damage:detect", tags=["Detection"])
async def detect_damage(
    request: Request,
    image: UploadFile = File(...),
    x_api_key: Optional[str] = Header(None)
):
    """
    Detectar danos em imagem de veículo
    
    - **image**: Arquivo de imagem (jpg/png/jpeg)
    - **X-API-Key**: Chave de autenticação (obrigatória)
    
    Retorna JSON com detecções, resumo e imagem anotada em base64
    """
    
    request_id = str(uuid.uuid4())
    
    try:
        # Validar API key
        validate_api_key(x_api_key)
        
        # Validar tipo de arquivo
        if image.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
            logger.warning(f"[{request_id}] Tipo de arquivo inválido: {image.content_type}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid image format. Only jpg, png, and jpeg are supported."
            )
        
        # Validar tamanho do arquivo
        contents = await image.read()
        file_size = len(contents)
        
        if file_size > MAX_UPLOAD_SIZE:
            logger.warning(f"[{request_id}] Arquivo muito grande: {file_size} bytes")
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {MAX_UPLOAD_SIZE / 1024 / 1024:.0f}MB"
            )
        
        logger.info(f"[{request_id}] Processando imagem ({file_size / 1024:.1f}KB)")
        
        # Abrir imagem
        img = Image.open(io.BytesIO(contents)).convert("RGB")
        original_width, original_height = img.size
        
        # Redimensionar se necessário
        img = resize_image_if_needed(img, MAX_IMAGE_DIMENSION)
        
        # Obter modelo
        model = model_manager.get_model()
        
        # Processar imagem
        detections, annotated_image = process_image(img, model)
        
        logger.info(f"[{request_id}] Detecções encontradas: {len(detections)}")
        
        # Construir resumo
        summary = build_summary(detections, original_width, original_height)
        
        # Converter imagem anotada para base64
        annotated_base64 = image_to_base64(annotated_image)
        
        # Preparar resposta
        response = {
            "request_id": request_id,
            "model_version": MODEL_VERSION,
            "image": {
                "width": original_width,
                "height": original_height
            },
            "summary": summary,
            "detections": detections,
            "annotated_image_base64": annotated_base64,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        logger.info(f"[{request_id}] ✓ Requisição concluída com sucesso")
        
        return JSONResponse(content=response, status_code=200)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] ✗ Erro ao processar imagem: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing image: {str(e)}"
        )


@app.get("/v1/models", tags=["Models"])
async def list_models(x_api_key: Optional[str] = Header(None)):
    """Listar modelos disponíveis"""
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
    """Obter configuração de classes de danos"""
    validate_api_key(x_api_key)
    
    classes = {}
    for class_name in DAMAGE_CONFIG['severity_map'].keys():
        cost_range = DAMAGE_CONFIG['cost_estimate'].get(class_name, (0, 0))
        classes[class_name] = {
            'severity': DAMAGE_CONFIG['severity_map'].get(class_name),
            'area_affected': DAMAGE_CONFIG['location_map'].get(class_name),
            'estimated_cost_range': f"R$ {cost_range[0]} - R$ {cost_range[1]}"
        }
    
    return {"damage_classes": classes}


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handler customizado para HTTPException"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handler para exceções genéricas"""
    logger.error(f"Erro não tratado: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    )


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
