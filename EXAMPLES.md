# Exemplos de Uso da API YOLO Damage Detection

## 1. Health Check

### cURL
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{"status": "ok"}
```

---

## 2. Detecção de Danos

### cURL
```bash
curl -X POST http://localhost:8000/v1/damage:detect \
  -H "X-API-Key: demo-key-12345" \
  -F "image=@car_damage.jpg"
```

### Python
```python
import requests

api_url = "http://localhost:8000/v1/damage:detect"
api_key = "demo-key-12345"
image_path = "car_damage.jpg"

with open(image_path, "rb") as f:
    files = {"image": f}
    headers = {"X-API-Key": api_key}
    response = requests.post(api_url, files=files, headers=headers)
    
result = response.json()
print(f"Model: {result['model_version']}")
print(f"Image size: {result['image_width']}x{result['image_height']}")
print(f"Detections: {len(result['detections'])}")

for detection in result['detections']:
    print(f"\n- Class: {detection['class']}")
    print(f"  Confidence: {detection['confidence']:.2%}")
    print(f"  Severity: {detection['severity']}")
    print(f"  Area: {detection['area_affected']}")
    print(f"  Cost Range: R$ {detection['estimated_cost_range']['min']} - R$ {detection['estimated_cost_range']['max']}")
```

### JavaScript/Node.js
```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

async function detectDamage() {
  const formData = new FormData();
  formData.append('image', fs.createReadStream('car_damage.jpg'));

  try {
    const response = await axios.post(
      'http://localhost:8000/v1/damage:detect',
      formData,
      {
        headers: {
          ...formData.getHeaders(),
          'X-API-Key': 'demo-key-12345'
        }
      }
    );
    
    console.log('Model:', response.data.model_version);
    console.log('Detections:', response.data.detections);
  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
  }
}

detectDamage();
```

### Response Example
```json
{
  "model_version": "v2.0.0",
  "image_width": 1920,
  "image_height": 1080,
  "timestamp": "2024-01-28T10:30:45.123456Z",
  "detections": [
    {
      "class": "dent",
      "confidence": 0.92,
      "bbox": {
        "x1": 150.5,
        "y1": 200.3,
        "x2": 350.7,
        "y2": 400.2
      },
      "severity": "Moderado",
      "area_affected": "Carroceria",
      "estimated_cost_range": {
        "min": 500,
        "max": 2000,
        "currency": "BRL"
      }
    },
    {
      "class": "scratch",
      "confidence": 0.87,
      "bbox": {
        "x1": 400.0,
        "y1": 150.0,
        "x2": 600.0,
        "y2": 300.0
      },
      "severity": "Leve",
      "area_affected": "Pintura",
      "estimated_cost_range": {
        "min": 150,
        "max": 800,
        "currency": "BRL"
      }
    }
  ]
}
```

---

## 3. Listar Modelos

### cURL
```bash
curl http://localhost:8000/v1/models \
  -H "X-API-Key: demo-key-12345"
```

### Python
```python
import requests

headers = {"X-API-Key": "demo-key-12345"}
response = requests.get("http://localhost:8000/v1/models", headers=headers)
print(response.json())
```

### Response
```json
{
  "models": [
    {
      "name": "car_damage_best",
      "version": "v2.0.0",
      "classes": [
        "dent",
        "scratch",
        "crack",
        "shattered_glass",
        "broken_lamp",
        "flat_tire"
      ],
      "framework": "YOLOv8"
    }
  ]
}
```

---

## 4. Listar Classes de Danos

### cURL
```bash
curl http://localhost:8000/v1/damage-classes \
  -H "X-API-Key: demo-key-12345"
```

### Python
```python
import requests
import json

headers = {"X-API-Key": "demo-key-12345"}
response = requests.get("http://localhost:8000/v1/damage-classes", headers=headers)
classes = response.json()['damage_classes']

for class_name, config in classes.items():
    print(f"\n{class_name}:")
    print(f"  Severity: {config['severity']}")
    print(f"  Area: {config['area_affected']}")
    print(f"  Cost: R$ {config['estimated_cost_range']['min']} - R$ {config['estimated_cost_range']['max']}")
```

### Response
```json
{
  "damage_classes": {
    "dent": {
      "severity": "Moderado",
      "area_affected": "Carroceria",
      "estimated_cost_range": {
        "min": 500,
        "max": 2000,
        "currency": "BRL"
      }
    },
    "scratch": {
      "severity": "Leve",
      "area_affected": "Pintura",
      "estimated_cost_range": {
        "min": 150,
        "max": 800,
        "currency": "BRL"
      }
    },
    "crack": {
      "severity": "Leve",
      "area_affected": "Para-choque/Plásticos",
      "estimated_cost_range": {
        "min": 200,
        "max": 1000,
        "currency": "BRL"
      }
    },
    "shattered_glass": {
      "severity": "Severo",
      "area_affected": "Vidros",
      "estimated_cost_range": {
        "min": 800,
        "max": 2500,
        "currency": "BRL"
      }
    },
    "broken_lamp": {
      "severity": "Severo",
      "area_affected": "Iluminação",
      "estimated_cost_range": {
        "min": 300,
        "max": 1500,
        "currency": "BRL"
      }
    },
    "flat_tire": {
      "severity": "Severo",
      "area_affected": "Rodas",
      "estimated_cost_range": {
        "min": 200,
        "max": 800,
        "currency": "BRL"
      }
    }
  }
}
```

---

## 5. Processamento em Lote

### Python
```python
import requests
from pathlib import Path

api_url = "http://localhost:8000/v1/damage:detect"
api_key = "demo-key-12345"
image_dir = "images/"

results = []

for image_path in Path(image_dir).glob("*.jpg"):
    print(f"Processing {image_path.name}...")
    
    with open(image_path, "rb") as f:
        files = {"image": f}
        headers = {"X-API-Key": api_key}
        response = requests.post(api_url, files=files, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        results.append({
            "image": image_path.name,
            "detections": result['detections'],
            "timestamp": result['timestamp']
        })
        print(f"  Found {len(result['detections'])} damages")
    else:
        print(f"  Error: {response.status_code}")

# Save results
import json
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
```

---

## 6. Integração com Aplicação Web

### Flask
```python
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

API_URL = "http://localhost:8000"
API_KEY = "demo-key-12345"

@app.route('/analyze', methods=['POST'])
def analyze_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image provided"}), 400
    
    image = request.files['image']
    
    files = {"image": image}
    headers = {"X-API-Key": API_KEY}
    response = requests.post(
        f"{API_URL}/v1/damage:detect",
        files=files,
        headers=headers
    )
    
    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({"error": "Failed to analyze image"}), response.status_code

if __name__ == '__main__':
    app.run(debug=True)
```

### FastAPI (Proxy)
```python
from fastapi import FastAPI, UploadFile, File
import httpx

app = FastAPI()

YOLO_API_URL = "http://localhost:8000"
API_KEY = "demo-key-12345"

@app.post("/analyze")
async def analyze_image(image: UploadFile = File(...)):
    async with httpx.AsyncClient() as client:
        files = {"image": (image.filename, await image.read())}
        headers = {"X-API-Key": API_KEY}
        response = await client.post(
            f"{YOLO_API_URL}/v1/damage:detect",
            files=files,
            headers=headers
        )
    
    return response.json()
```

---

## 7. Tratamento de Erros

### Erro: API Key Inválida
```bash
curl -X POST http://localhost:8000/v1/damage:detect \
  -F "image=@car.jpg"
```

**Response:**
```json
{
  "detail": "Missing X-API-Key header"
}
```

### Erro: Formato de Imagem Inválido
```bash
curl -X POST http://localhost:8000/v1/damage:detect \
  -H "X-API-Key: demo-key-12345" \
  -F "image=@document.pdf"
```

**Response:**
```json
{
  "detail": "Invalid image format. Only jpg, png, and jpeg are supported."
}
```

### Erro: Arquivo Não Encontrado
```bash
curl -X POST http://localhost:8000/v1/damage:detect \
  -H "X-API-Key: demo-key-12345" \
  -F "image=@nonexistent.jpg"
```

**Response:**
```json
{
  "detail": "Error processing image: [Errno 2] No such file or directory"
}
```

---

## 8. Documentação Interativa

Acesse a documentação interativa em:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Você pode testar os endpoints diretamente na interface!

---

## 9. Performance e Otimizações

### Timeout para Requisições Longas
```python
import requests

response = requests.post(
    "http://localhost:8000/v1/damage:detect",
    files={"image": open("car.jpg", "rb")},
    headers={"X-API-Key": "demo-key-12345"},
    timeout=30  # 30 segundos
)
```

### Retry com Backoff
```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)

response = session.post(
    "http://localhost:8000/v1/damage:detect",
    files={"image": open("car.jpg", "rb")},
    headers={"X-API-Key": "demo-key-12345"}
)
```

---

## 10. Monitoramento e Logging

### Verificar Saúde da API
```python
import requests

response = requests.get("http://localhost:8000/health")
if response.status_code == 200:
    print("API is healthy")
else:
    print("API is down")
```

### Logs em Tempo Real (Docker)
```bash
docker-compose logs -f api
```

---

Mais exemplos e documentação em: http://localhost:8000/docs
