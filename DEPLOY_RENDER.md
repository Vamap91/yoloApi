# Guia Rápido de Deploy no Render

## Pré-requisitos
- Conta no [Render](https://render.com)
- Repositório GitHub com o código

## Passos para Deploy

### 1. Prepare o Repositório
```bash
git init
git add .
git commit -m "Initial YOLO API commit"
git remote add origin https://github.com/seu-usuario/seu-repo.git
git push -u origin main
```

### 2. Acesse o Render Dashboard
- Vá para https://dashboard.render.com
- Faça login com sua conta GitHub

### 3. Crie um Novo Web Service
1. Clique em **"New +"** no canto superior direito
2. Selecione **"Web Service"**
3. Conecte seu repositório GitHub
4. Selecione o repositório com o código da API

### 4. Configure o Serviço
- **Name**: `yolo-damage-api`
- **Runtime**: Docker
- **Build Command**: (deixe em branco)
- **Start Command**: (deixe em branco)
- **Plan**: Standard (recomendado)

### 5. Configure Variáveis de Ambiente
Clique em **"Environment"** e adicione:

| Key | Value |
|-----|-------|
| `API_KEY_DEMO` | sua-chave-segura-aqui |
| `PORT` | 8000 |

### 6. Deploy
Clique em **"Create Web Service"**

O deploy levará 5-10 minutos. Você pode acompanhar o progresso na aba "Logs".

## Após o Deploy

### Acessar a API
- URL: `https://seu-servico.onrender.com`
- Swagger UI: `https://seu-servico.onrender.com/docs`
- ReDoc: `https://seu-servico.onrender.com/redoc`

### Testar a API
```bash
# Health check
curl https://seu-servico.onrender.com/health

# Detecção de danos
curl -X POST https://seu-servico.onrender.com/v1/damage:detect \
  -H "X-API-Key: sua-chave-segura-aqui" \
  -F "image=@imagem.jpg"
```

## Troubleshooting

### Build falha
- Verifique os logs em "Logs"
- Confirme que o Dockerfile está correto
- Verifique se todas as dependências estão em requirements.txt

### Timeout no primeiro acesso
- O modelo YOLO é baixado na primeira execução
- Isso pode levar alguns minutos
- Aguarde pacientemente

### Memória insuficiente
- Aumente o plano para Standard ou superior
- Considere usar um plano com mais recursos

## Monitoramento

- **Logs**: Acesse a aba "Logs" para ver a saída da aplicação
- **Métricas**: Visualize CPU, memória e requisições em "Metrics"
- **Health Checks**: O Render verifica `/health` automaticamente

## Atualizar o Código

Após fazer alterações no código:
```bash
git add .
git commit -m "Sua mensagem de commit"
git push origin main
```

O Render fará o deploy automaticamente (se autoDeploy estiver ativado).

## Segurança

⚠️ **Importante**: Altere a chave `API_KEY_DEMO` para uma chave segura em produção!

Gere uma chave segura:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Custos

- Plano **Free**: Limitado, pode não ser suficiente
- Plano **Standard**: ~$7/mês, recomendado
- Plano **Pro**: ~$25/mês, para alta demanda

## Próximas Etapas

1. Implemente rate limiting
2. Configure logging estruturado
3. Adicione monitoramento
4. Configure CI/CD avançado
5. Implemente cache de modelos

## Suporte

- Documentação Render: https://render.com/docs
- Comunidade: https://render.com/community
- Issues: Abra uma issue no seu repositório GitHub
