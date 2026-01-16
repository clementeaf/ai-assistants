# Variables de Entorno para Despliegue en AWS

## Frontend (admin-frontend)

### Variables Requeridas

```bash
# API Backend
VITE_API_BASE_URL=https://api.tudominio.com

# Flow MCP Server
VITE_FLOW_MCP_SERVER_URL=https://flow-mcp.tudominio.com

# WhatsApp
VITE_WHATSAPP_NUMBER=56959263366

# Calendar MCP Server (opcional)
VITE_CALENDAR_MCP_SERVER_URL=https://calendar-mcp.tudominio.com

# WhatsApp Service (opcional)
VITE_WHATSAPP_SERVICE_URL=https://whatsapp-service.tudominio.com
```

### Configuración en AWS

1. **CloudFront / S3**: Configurar variables de entorno en el build
2. **Amplify**: Agregar en "Environment variables" del proyecto
3. **ECS/Fargate**: Configurar en task definition

### Build con Variables

```bash
# Build para producción
VITE_API_BASE_URL=https://api.tudominio.com \
VITE_FLOW_MCP_SERVER_URL=https://flow-mcp.tudominio.com \
VITE_WHATSAPP_NUMBER=56959263366 \
npm run build
```

## Backend (apps/backend)

### Variables Requeridas

```bash
# LLM Configuration
AI_ASSISTANTS_LLM_BASE_URL=https://api.openai.com/v1
AI_ASSISTANTS_LLM_API_KEY=sk-...
AI_ASSISTANTS_LLM_MODEL=gpt-4o-mini

# Autonomous Mode
AI_ASSISTANTS_AUTONOMOUS_ENABLED=1
AI_ASSISTANTS_AUTONOMOUS_MAX_HISTORY=10

# Router
AI_ASSISTANTS_LLM_ROUTER_ENABLED=1

# MCP Servers
AI_ASSISTANTS_MCP_BOOKING_FLOW_SERVER_URL=https://flow-mcp.tudominio.com
AI_ASSISTANTS_MCP_CALENDAR_SERVER_URL=https://calendar-mcp.tudominio.com
AI_ASSISTANTS_MCP_LLM_SERVER_URL=https://llm-mcp.tudominio.com

# Database (SQLite paths)
AI_ASSISTANTS_CONVERSATION_STORE_PATH=/data/conversations.db
AI_ASSISTANTS_JOB_STORE_PATH=/data/jobs.db
AI_ASSISTANTS_MEMORY_STORE_PATH=/data/memory.db

# Security
AI_ASSISTANTS_API_KEYS=project1:key1,project2:key2
AI_ASSISTANTS_ENABLE_AUTH=1

# CORS
AI_ASSISTANTS_CORS_ALLOWED_ORIGINS=https://admin.tudominio.com,https://app.tudominio.com
```

### Configuración en AWS

1. **ECS Task Definition**: Agregar en "Environment variables"
2. **Lambda**: Configurar en función Lambda
3. **EC2**: Usar `.env` o sistema de gestión de secretos (AWS Secrets Manager)

### Recomendaciones AWS

- **Secrets Manager**: Para API keys y credenciales sensibles
- **Parameter Store**: Para configuración no sensible
- **IAM Roles**: Para acceso a recursos AWS
- **VPC**: Para comunicación segura entre servicios

## MCP Servers

Cada MCP server tiene sus propias variables de entorno. Ver documentación específica en cada servidor.
