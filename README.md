# YOLO Vehicle Damage Detection API v2.0

API FastAPI de produção para detecção de danos veiculares usando YOLOv8. Retorna imagens anotadas em base64 + JSON estruturado com resumo e detalhes.

## Características de Produção

- **Singleton Model**: Modelo carregado uma única vez no startup e reutilizado
- **Warmup Automático**: Aquecimento do modelo para evitar primeira requisição lenta
- **Imagens Anotadas**: Retorna PNG com bounding boxes e labels em base64
- **Redimensionamento Automático**: Imagens grandes redimensionadas mantendo proporções
- **Limite de Upload**: 10MB com validação e erro 413
- **Tratamento de Erro Completo**: 401/403/422/413/500 com mensagens claras
- **Logging Estruturado**: Rastreamento completo de requisições
- **CORS Configurável**: Sem allow_credentials com "*"
- **Documentação Automática**: Swagger UI e ReDoc

## Endpoints

### Health Check
```
GET /health
```

**Response:**
```json
{"status": "ok"}
```

---

### Warmup (Opcional)
```
POST /warmup
```

**Headers:**
- `X-API-Key`: Chave de autenticação

**Response:**
```json
{"status": "warmup_completed"}
```

---

### Detecção de Danos (Principal)
```
POST /v1/damage:detect
```

**Headers:**
- `X-API-Key`: Chave de autenticação (obrigatória)

**Body (multipart/form-data):**
- `image`: Arquivo de imagem (jpg/png/jpeg, máx 10MB)

**Response (HTTP 200):**
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "model_version": "v2.0.0",
  "image": {
    "width": 1920,
    "height": 1080
  },
  "summary": {
    "total_damages": 2,
    "by_type": {
      "dent": 1,
      "scratch": 1,
      "crack": 0,
      "shattered_glass": 0,
      "broken_lamp": 0,
      "flat_tire": 0
    },
    "by_severity": {
      "Leve": 1,
      "Moderado": 1,
      "Severo": 0
    },
    "by_area_affected": {
      "Carroceria": 1,
      "Pintura": 1,
      "Vidros": 0,
      "Iluminação": 0,
      "Rodas": 0
    },
    "estimated_total_cost_range": "R$ 650 - R$ 2800"
  },
  "detections": [
    {
      "id": "dmg_001",
      "class": "dent",
      "confidence": 0.92,
      "bbox": {
        "x1": 150,
        "y1": 200,
        "x2": 350,
        "y2": 400
      },
      "severity": "Moderado",
      "area_affected": "Carroceria",
      "estimated_cost_range": "R$ 500 - R$ 2000"
    },
    {
      "id": "dmg_002",
      "class": "scratch",
      "confidence": 0.87,
      "bbox": {
        "x1": 400,
        "y1": 150,
        "x2": 600,
        "y2": 300
      },
      "severity": "Leve",
      "area_affected": "Pintura",
      "estimated_cost_range": "R$ 150 - R$ 800"
    }
  ],
  "annotated_image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
  "timestamp": "2024-01-28T10:30:45.123456Z"
}
```

**Códigos de Erro:**
- `401`: API Key ausente
- `403`: API Key inválida
- `413`: Arquivo muito grande (>10MB)
- `422`: Formato de imagem inválido
- `500`: Erro ao processar imagem

---

### Listar Modelos
```
GET /v1/models
```

**Headers:**
- `X-API-Key`: Chave de autenticação

---

### Listar Classes de Danos
```
GET /v1/damage-classes
```

**Headers:**
- `X-API-Key`: Chave de autenticação

---

## Instalação Local

### Pré-requisitos
- Python 3.11+
- pip ou uv

### Setup

1. Clone o repositório:
```bash
git clone <seu-repo>
cd yolo-api
```

2. Crie um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:
```bash
cp .env.example .env
# Edite .env conforme necessário
```

5. Execute a API:
```bash
python main.py
```

A API estará disponível em `http://localhost:8000`

### Com Docker Compose
```bash
docker-compose up --build
```

## Documentação Interativa

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Variáveis de Ambiente

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `API_KEY_DEMO` | `demo-key-12345` | Chave de autenticação da API |
| `PORT` | `8000` | Porta em que a API roda |
| `MODEL_VERSION` | `v2.0.0` | Versão do modelo YOLO |
| `MAX_UPLOAD_SIZE` | `10485760` | Tamanho máximo de upload em bytes (10MB) |
| `MAX_IMAGE_DIMENSION` | `1280` | Dimensão máxima da imagem (lado maior) |
| `CORS_ORIGINS` | `http://localhost:3000,http://localhost:8000` | Origens CORS permitidas |

## Deploy no Render

### Pré-requisitos
- Conta no [Render](https://render.com)
- Repositório GitHub com o código

### Passos

1. **Prepare o repositório:**
```bash
git init
git add .
git commit -m "YOLO API v2.0 - Production Ready"
git remote add origin https://github.com/seu-usuario/seu-repo.git
git push -u origin main
```

2. **Acesse o Render Dashboard:**
- Vá para https://dashboard.render.com
- Clique em "New +" → "Web Service"
- Conecte seu repositório GitHub

3. **Configure o serviço:**
- **Name**: `yolo-damage-api`
- **Runtime**: Docker
- **Plan**: Standard (recomendado) ou superior
- **Auto-deploy**: Ativado

4. **Configure variáveis de ambiente:**

| Key | Value |
|-----|-------|
| `API_KEY_DEMO` | sua-chave-segura-aqui |
| `PORT` | 8000 |
| `MODEL_VERSION` | v2.0.0 |
| `MAX_UPLOAD_SIZE` | 10485760 |
| `MAX_IMAGE_DIMENSION` | 1280 |
| `CORS_ORIGINS` | https://seu-frontend.com |

5. **Deploy:**
- Clique em "Create Web Service"
- Aguarde 5-10 minutos para build e deploy

### Comandos Render

**Build Command:** (deixe em branco - usa Dockerfile)

**Start Command:** (deixe em branco - usa Dockerfile)

O Dockerfile já está configurado com:
```dockerfile
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:$PORT", "main:app"]
```

## Testando a API

### Com cURL

```bash
# Health check
curl http://localhost:8000/health

# Warmup (opcional)
curl -X POST http://localhost:8000/warmup \
  -H "X-API-Key: demo-key-12345"

# Detecção de danos
curl -X POST http://localhost:8000/v1/damage:detect \
  -H "X-API-Key: demo-key-12345" \
  -F "image=@car_damage.jpg"

# Listar classes
curl http://localhost:8000/v1/damage-classes \
  -H "X-API-Key: demo-key-12345"
```

### Com Python

```python
import requests
import json
import base64

api_url = "http://localhost:8000/v1/damage:detect"
api_key = "demo-key-12345"

with open("car_damage.jpg", "rb") as f:
    files = {"image": f}
    headers = {"X-API-Key": api_key}
    response = requests.post(api_url, files=files, headers=headers)

result = response.json()

# Imprimir resumo
print(f"Total de danos: {result['summary']['total_damages']}")
print(f"Custo estimado: {result['summary']['estimated_total_cost_range']}")

# Salvar imagem anotada
annotated_b64 = result['annotated_image_base64']
image_data = base64.b64decode(annotated_b64)
with open("annotated.png", "wb") as f:
    f.write(image_data)

print("Imagem anotada salva como annotated.png")
```

### Com Node.js

```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

const formData = new FormData();
formData.append('image', fs.createReadStream('car_damage.jpg'));

axios.post('http://localhost:8000/v1/damage:detect', formData, {
  headers: {
    ...formData.getHeaders(),
    'X-API-Key': 'demo-key-12345'
  }
}).then(response => {
  const result = response.data;
  console.log(`Total de danos: ${result.summary.total_damages}`);
  console.log(`Custo estimado: ${result.summary.estimated_total_cost_range}`);
  
  // Salvar imagem anotada
  const imageBuffer = Buffer.from(result.annotated_image_base64, 'base64');
  fs.writeFileSync('annotated.png', imageBuffer);
  console.log('Imagem anotada salva como annotated.png');
}).catch(error => {
  console.error('Error:', error.response?.data || error.message);
});
```

## Performance

- **Tempo de inferência**: ~500-1000ms por imagem (varia com tamanho)
- **Memória**: ~2GB para o modelo YOLO
- **Throughput**: ~3-5 imagens/segundo (com 4 workers)
- **Recomendação Render**: Mínimo Standard (2GB RAM)

## Monitoramento

### Logs no Render
- Acesse a aba "Logs" na dashboard do Render
- Cada requisição é rastreada com `request_id`

### Métricas
- CPU, memória e requisições em "Metrics"
- Health checks automáticos em `/health`

### Exemplo de Log
```
2024-01-28 10:30:45 - root - INFO - [550e8400-e29b-41d4-a716-446655440000] Processando imagem (245.3KB)
2024-01-28 10:30:46 - root - INFO - [550e8400-e29b-41d4-a716-446655440000] Detecções encontradas: 2
2024-01-28 10:30:46 - root - INFO - [550e8400-e29b-41d4-a716-446655440000] ✓ Requisição concluída com sucesso
```

## Tratamento de Erros

### Erro 401 - API Key Ausente
```bash
curl -X POST http://localhost:8000/v1/damage:detect \
  -F "image=@car.jpg"
```

**Response:**
```json
{
  "error": "Missing X-API-Key header",
  "status_code": 401,
  "timestamp": "2024-01-28T10:30:45.123456Z"
}
```

### Erro 403 - API Key Inválida
```bash
curl -X POST http://localhost:8000/v1/damage:detect \
  -H "X-API-Key: invalid-key" \
  -F "image=@car.jpg"
```

**Response:**
```json
{
  "error": "Invalid API key",
  "status_code": 403,
  "timestamp": "2024-01-28T10:30:45.123456Z"
}
```

### Erro 413 - Arquivo Muito Grande
```bash
# Arquivo > 10MB
curl -X POST http://localhost:8000/v1/damage:detect \
  -H "X-API-Key: demo-key-12345" \
  -F "image=@huge_image.jpg"
```

**Response:**
```json
{
  "error": "File too large. Maximum size: 10MB",
  "status_code": 413,
  "timestamp": "2024-01-28T10:30:45.123456Z"
}
```

### Erro 422 - Formato Inválido
```bash
curl -X POST http://localhost:8000/v1/damage:detect \
  -H "X-API-Key: demo-key-12345" \
  -F "image=@document.pdf"
```

**Response:**
```json
{
  "error": "Invalid image format. Only jpg, png, and jpeg are supported.",
  "status_code": 422,
  "timestamp": "2024-01-28T10:30:45.123456Z"
}
```

## Segurança

- ⚠️ **Altere `API_KEY_DEMO` para uma chave segura em produção**
- Use HTTPS em produção (Render fornece automaticamente)
- Gere uma chave segura:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```
- Configure `CORS_ORIGINS` com domínio específico do frontend
- Nunca commite `.env` com chaves reais no Git

## Troubleshooting

### Erro: "Model download failed"
- Verifique conexão com internet
- Confirme que a URL do GitHub está acessível
- Verifique se a versão do modelo existe em releases

### Erro: Timeout na primeira requisição
- O modelo é baixado e aquecido no startup
- Pode levar 2-3 minutos em conexão lenta
- Use endpoint `/warmup` para pré-aquecer manualmente

### Erro: Memória insuficiente
- Use plano Standard ou superior no Render
- Considere usar plano Pro para alta demanda
- Reduza `MAX_IMAGE_DIMENSION` se necessário

### Erro: CORS bloqueado
- Configure `CORS_ORIGINS` corretamente
- Exemplo: `CORS_ORIGINS=https://seu-frontend.com,https://outro-dominio.com`

## Próximos Passos

- [ ] Implementar rate limiting (ex: 100 req/min por API key)
- [ ] Adicionar cache de resultados
- [ ] Implementar webhooks para processamento assíncrono
- [ ] Adicionar suporte a batch processing
- [ ] Implementar métricas Prometheus
- [ ] Adicionar autenticação JWT avançada

## Estrutura do Projeto

```
yolo-api/
├── main.py                 # Aplicação FastAPI (277 linhas)
├── requirements.txt        # Dependências Python
├── Dockerfile             # Configuração Docker
├── docker-compose.yml     # Compose para desenvolvimento
├── render.yaml            # Configuração Render
├── .env.example           # Variáveis de ambiente
├── .gitignore             # Arquivos ignorados
├── README.md              # Este arquivo
├── DEPLOY_RENDER.md       # Guia rápido de deploy
├── EXAMPLES.md            # Exemplos de uso
└── test_api.py            # Script de testes
```

## Changelog

### v2.0.0 (2024-01-28)
- ✓ Singleton model manager
- ✓ Warmup automático no startup
- ✓ Imagens anotadas em base64
- ✓ Redimensionamento automático
- ✓ Limite de upload 10MB
- ✓ Tratamento de erro completo (401/403/413/422/500)
- ✓ Logging estruturado com request_id
- ✓ CORS configurável
- ✓ Gunicorn + Uvicorn workers
- ✓ Contrato JSON obrigatório

### v1.0.0 (2024-01-27)
- Transformação de Streamlit para FastAPI
- Endpoints básicos de detecção

## Licença

Este projeto mantém a mesma licença do projeto original YOLO.

## Suporte

- Documentação: http://localhost:8000/docs
- Issues: Abra uma issue no repositório GitHub
- Render Docs: https://render.com/docs
