# Guia Completo de Deploy no Render

## Pré-requisitos

- Conta no [Render](https://render.com)
- Repositório GitHub com o código
- Chave de API segura gerada

## Gerar Chave de API Segura

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Passo 1: Preparar o Repositório

```bash
git init
git add .
git commit -m "YOLO API v2.0 - Production Ready"
git remote add origin https://github.com/seu-usuario/seu-repo.git
git push -u origin main
```

## Passo 2: Acessar Render Dashboard

1. Vá para https://dashboard.render.com
2. Faça login com sua conta GitHub
3. Clique em "New +" no canto superior direito

## Passo 3: Criar Web Service

1. Selecione **"Web Service"**
2. Conecte seu repositório GitHub
3. Selecione o repositório com o código da API

## Passo 4: Configurar o Serviço

| Campo | Valor |
|-------|-------|
| **Name** | `yolo-damage-api` |
| **Runtime** | Docker |
| **Region** | Escolha a mais próxima |
| **Branch** | main |
| **Build Command** | (deixe em branco) |
| **Start Command** | (deixe em branco) |
| **Plan** | Standard (recomendado) |

## Passo 5: Configurar Variáveis de Ambiente

| Key | Value |
|-----|-------|
| `API_KEY_DEMO` | sua-chave-segura |
| `PORT` | 8000 |
| `MODEL_VERSION` | v2.0.0 |
| `MAX_UPLOAD_SIZE` | 10485760 |
| `MAX_IMAGE_DIMENSION` | 1280 |
| `CORS_ORIGINS` | https://seu-frontend.com |

## Passo 6: Deploy

1. Clique em **"Create Web Service"**
2. Aguarde o build (5-10 minutos)
3. Verifique os logs em **"Logs"**

## Após o Deploy

### Testar Health Check
```bash
curl https://seu-servico.onrender.com/health
```

### Testar Detecção de Danos
```bash
curl -X POST https://seu-servico.onrender.com/v1/damage:detect \
  -H "X-API-Key: sua-chave" \
  -F "image=@car_damage.jpg"
```

## Troubleshooting

### Timeout na Primeira Requisição
Use endpoint `/warmup` para pré-aquecer:
```bash
curl -X POST https://seu-servico.onrender.com/warmup \
  -H "X-API-Key: sua-chave"
```

### Memória Insuficiente
Aumente o plano para Standard ou superior

### CORS Bloqueado
Configure `CORS_ORIGINS` com seu domínio

## Segurança

⚠️ **IMPORTANTE:**
1. Altere a chave padrão
2. Use HTTPS em produção
3. Configure CORS corretamente
4. Monitore os logs

---

**Sua API está em produção no Render! 🚀**
