# YOLO Vehicle Damage Detection API

API FastAPI para detecção de danos veiculares usando YOLOv8. Transformação do projeto Streamlit original em uma API REST pronta para produção.

## Características

- **Detecção de Danos**: Identifica 6 tipos de danos em veículos (dent, scratch, crack, shattered_glass, broken_lamp, flat_tire)
- **Classificação de Severidade**: Classifica danos como Leve, Moderado ou Severo
- **Estimativa de Custo**: Fornece estimativas de custo de reparo em BRL
- **Autenticação**: Validação via API Key (header X-API-Key)
- **Documentação Automática**: Swagger UI e ReDoc integrados
- **Pronto para Deploy**: Dockerfile e configuração Render inclusos

## Endpoints

### Health Check
```
GET /health
```
Retorna: `{"status": "ok"}`

### Detecção de Danos
```
POST /v1/damage:detect
```

**Headers:**
- `X-API-Key`: Chave de autenticação (obrigatória)

**Body (multipart/form-data):**
- `image`: Arquivo de imagem (jpg/png/jpeg)

**Response:**
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
    }
  ]
}
```

### Listar Modelos
```
GET /v1/models
```

**Headers:**
- `X-API-Key`: Chave de autenticação (obrigatória)

### Listar Classes de Danos
```
GET /v1/damage-classes
```

**Headers:**
- `X-API-Key`: Chave de autenticação (obrigatória)

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

## Documentação Interativa

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Deploy no Render

### Método 1: Deploy via Git (Recomendado)

1. **Prepare seu repositório Git:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: YOLO API"
   git remote add origin <seu-repositorio-github>
   git push -u origin main
   ```

2. **Acesse o Render:**
   - Vá para https://dashboard.render.com
   - Clique em "New +" → "Web Service"
   - Conecte seu repositório GitHub
   - Selecione o repositório do projeto

3. **Configure o Deploy:**
   - **Name**: `yolo-damage-api` (ou seu nome preferido)
   - **Runtime**: Docker
   - **Build Command**: (deixe em branco - usa Dockerfile)
   - **Start Command**: (deixe em branco - usa Dockerfile)
   - **Plan**: Standard ou superior (recomendado Standard)

4. **Configure Variáveis de Ambiente:**
   - Clique em "Environment"
   - Adicione a variável:
     - **Key**: `API_KEY_DEMO`
     - **Value**: Sua chave de API segura (altere de `demo-key-12345`)

5. **Deploy:**
   - Clique em "Create Web Service"
   - Aguarde o build e deploy (pode levar 5-10 minutos)

### Método 2: Deploy via Docker Image

Se preferir usar uma imagem Docker pré-construída:

1. **Build a imagem localmente:**
   ```bash
   docker build -t yolo-damage-api:latest .
   ```

2. **Teste localmente:**
   ```bash
   docker run -p 8000:8000 \
     -e API_KEY_DEMO=demo-key-12345 \
     yolo-damage-api:latest
   ```

3. **Push para Docker Hub:**
   ```bash
   docker tag yolo-damage-api:latest seu-usuario/yolo-damage-api:latest
   docker push seu-usuario/yolo-damage-api:latest
   ```

4. **No Render:**
   - Crie um Web Service
   - Selecione "Docker" como Runtime
   - Insira a URL da imagem: `seu-usuario/yolo-damage-api:latest`
   - Configure as variáveis de ambiente conforme acima

## Variáveis de Ambiente

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `API_KEY_DEMO` | `demo-key-12345` | Chave de autenticação da API |
| `PORT` | `8000` | Porta em que a API roda |
| `MODEL_VERSION` | `v2.0.0` | Versão do modelo YOLO |

## Testando a API

### Com cURL

```bash
# Health check
curl http://localhost:8000/health

# Detecção de danos
curl -X POST http://localhost:8000/v1/damage:detect \
  -H "X-API-Key: demo-key-12345" \
  -F "image=@caminho/para/imagem.jpg"

# Listar classes
curl http://localhost:8000/v1/damage-classes \
  -H "X-API-Key: demo-key-12345"
```

### Com Python

```python
import requests

api_url = "http://localhost:8000/v1/damage:detect"
api_key = "demo-key-12345"

with open("imagem.jpg", "rb") as f:
    files = {"image": f}
    headers = {"X-API-Key": api_key}
    response = requests.post(api_url, files=files, headers=headers)
    print(response.json())
```

### Com JavaScript/Node.js

```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

const formData = new FormData();
formData.append('image', fs.createReadStream('imagem.jpg'));

axios.post('http://localhost:8000/v1/damage:detect', formData, {
  headers: {
    ...formData.getHeaders(),
    'X-API-Key': 'demo-key-12345'
  }
}).then(response => {
  console.log(response.data);
}).catch(error => {
  console.error(error);
});
```

## Estrutura do Projeto

```
yolo-api/
├── main.py                 # Aplicação FastAPI principal
├── requirements.txt        # Dependências Python
├── Dockerfile             # Configuração Docker
├── .dockerignore          # Arquivos ignorados no build Docker
├── render.yaml            # Configuração Render
├── .env.example           # Exemplo de variáveis de ambiente
├── .gitignore             # Arquivos ignorados pelo Git
└── README.md              # Este arquivo
```

## Monitoramento no Render

Após o deploy:

1. **Logs**: Acesse "Logs" na dashboard do Render para monitorar a execução
2. **Métricas**: Visualize CPU, memória e requisições em "Metrics"
3. **Health Checks**: O Render verifica `/health` automaticamente

## Troubleshooting

### Erro: "Model download failed"
- Verifique a conexão com a internet
- Confirme que a URL do GitHub está acessível
- Verifique se a versão do modelo existe em releases

### Erro: "Invalid API key"
- Confirme que o header `X-API-Key` está sendo enviado
- Verifique se a chave corresponde à variável de ambiente `API_KEY_DEMO`

### Timeout no Render
- O download do modelo pode levar tempo na primeira execução
- Considere usar um plano com mais recursos
- Pré-baixe o modelo e adicione ao repositório (não recomendado por tamanho)

### Memória insuficiente
- Use pelo menos o plano Standard do Render
- Considere usar um plano com mais memória se processar muitas imagens simultaneamente

## Performance

- **Tempo de inferência**: ~500-1000ms por imagem (varia com tamanho)
- **Memória**: ~2GB para o modelo YOLO
- **Recomendação**: Mínimo 2GB RAM no Render

## Segurança

- A API requer autenticação via API Key
- Altere `API_KEY_DEMO` para uma chave segura em produção
- Use HTTPS (Render fornece automaticamente)
- Considere adicionar rate limiting em produção

## Próximos Passos

- [ ] Implementar rate limiting
- [ ] Adicionar logging estruturado
- [ ] Implementar cache de modelos
- [ ] Adicionar suporte a batch processing
- [ ] Implementar webhooks para processamento assíncrono
- [ ] Adicionar métricas Prometheus

## Licença

Este projeto mantém a mesma licença do projeto original YOLO.

## Suporte

Para problemas ou dúvidas:
1. Verifique a documentação em `/docs`
2. Consulte os logs no Render
3. Abra uma issue no repositório GitHub

## Changelog

### v1.0.0 (2024-01-28)
- Transformação de Streamlit para FastAPI
- Endpoints de detecção de danos
- Autenticação via API Key
- Documentação completa
- Pronto para deploy no Render
