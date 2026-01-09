# Arquitectura de Despliegue en AWS

## Análisis de Requisitos

### Componentes del Sistema
1. **Backend Python FastAPI** - API REST + WebSocket
2. **WhatsApp Baileys Service (Node.js)** - Conexión persistente con WhatsApp
3. **MCP Servers** - Múltiples servidores (Calendar, Professionals, Booking Log, LLM)
4. **Admin Frontend** - Interfaz de administración (React/Vite)
5. **Bases de Datos SQLite** - Persistencia local (necesita migración)

### Requisitos Críticos
- ✅ **Conexión persistente**: WhatsApp Baileys necesita mantener sesión activa
- ✅ **Tiempo real**: Procesamiento rápido de mensajes (< 5 segundos)
- ✅ **Alta disponibilidad**: WhatsApp debe estar siempre conectado
- ✅ **Escalabilidad**: Backend debe escalar según carga
- ✅ **Persistencia**: Datos de conversaciones, memoria, jobs
- ✅ **Seguridad**: Autenticación, rate limiting, webhooks

## Recomendación: Arquitectura Híbrida ECS + RDS

### Opción 1: ECS Fargate (Recomendada) ⭐

**Ventajas:**
- ✅ Sin gestión de servidores (serverless containers)
- ✅ Escalado automático fácil
- ✅ Alta disponibilidad nativa
- ✅ Costo eficiente (pago por uso)
- ✅ Integración fácil con otros servicios AWS

**Arquitectura:**

```
┌─────────────────────────────────────────────────────────┐
│                    Application Load Balancer             │
│                    (HTTPS + WebSocket)                  │
└──────────────┬──────────────────────────┬──────────────┘
               │                          │
               │                          │
    ┌──────────▼──────────┐   ┌──────────▼──────────┐
    │   ECS Fargate        │   │   ECS Fargate       │
    │   Backend Python     │   │   WhatsApp Service  │
    │   (FastAPI)          │   │   (Node.js)        │
    │   - Auto Scaling     │   │   - 1 Task Always  │
    │   - 2-10 Tasks       │   │   - Persistent     │
    └──────────┬───────────┘   └──────────┬──────────┘
               │                          │
               │                          │
    ┌──────────▼──────────────────────────▼──────────┐
    │              RDS PostgreSQL                      │
    │              (Multi-AZ para HA)                 │
    └─────────────────────────────────────────────────┘
    
    ┌─────────────────────────────────────────────────┐
    │   ECS Fargate - MCP Servers                     │
    │   - Calendar MCP                                 │
    │   - Professionals MCP                           │
    │   - Booking Log MCP                              │
    │   - LLM MCP (opcional)                           │
    └─────────────────────────────────────────────────┘
    
    ┌─────────────────────────────────────────────────┐
    │   S3 + CloudFront                                │
    │   - Admin Frontend (Static Hosting)              │
    └─────────────────────────────────────────────────┘
```

**Servicios AWS Necesarios:**
- **ECS Fargate**: Contenedores sin servidores
- **Application Load Balancer**: Balanceo de carga + WebSocket
- **RDS PostgreSQL**: Base de datos (migrar de SQLite)
- **ElastiCache Redis**: Cache y rate limiting
- **S3 + CloudFront**: Frontend estático
- **Secrets Manager**: Variables de entorno sensibles
- **CloudWatch**: Logs y métricas
- **VPC**: Red privada segura

**Costo Estimado (mensual):**
- ECS Fargate: ~$50-150 (depende de tráfico)
- RDS PostgreSQL (db.t3.micro): ~$15-30
- ALB: ~$20
- ElastiCache (cache.t3.micro): ~$15
- S3 + CloudFront: ~$5-10
- **Total: ~$105-225/mes** (para tráfico moderado)

### Opción 2: EC2 con Auto Scaling (Alternativa)

**Ventajas:**
- ✅ Control total sobre el entorno
- ✅ Más económico para cargas constantes
- ✅ Mejor para servicios que requieren estado persistente

**Desventajas:**
- ❌ Más mantenimiento (patches, updates)
- ❌ Configuración más compleja
- ❌ Menos automático

**Arquitectura:**

```
┌─────────────────────────────────────────────────────────┐
│                    Application Load Balancer             │
└──────────────┬──────────────────────────┬──────────────┘
               │                          │
    ┌──────────▼──────────┐   ┌──────────▼──────────┐
    │   Auto Scaling Group │   │   EC2 Instance      │
    │   Backend Python     │   │   WhatsApp Service  │
    │   (t3.medium)        │   │   (t3.small)        │
    │   - 2-5 instances    │   │   - Always On       │
    └──────────┬───────────┘   └──────────┬──────────┘
               │                          │
    ┌──────────▼──────────────────────────▼──────────┐
    │              RDS PostgreSQL                      │
    └─────────────────────────────────────────────────┘
```

**Costo Estimado (mensual):**
- EC2 Backend (2x t3.medium): ~$60
- EC2 WhatsApp (1x t3.small): ~$15
- RDS PostgreSQL: ~$15-30
- ALB: ~$20
- **Total: ~$110-125/mes**

## Implementación Recomendada: ECS Fargate

### 1. Migración de SQLite a RDS PostgreSQL

**Razones:**
- SQLite no es adecuado para producción multi-instancia
- RDS ofrece backups automáticos, replicación, alta disponibilidad
- Mejor rendimiento para múltiples conexiones concurrentes

**Pasos:**
```bash
# 1. Crear base de datos en RDS
aws rds create-db-instance \
  --db-instance-identifier ai-assistants-db \
  --db-instance-class db.t3.micro \
  --engine postgresql \
  --master-username admin \
  --master-user-password <password> \
  --allocated-storage 20 \
  --multi-az

# 2. Migrar datos (usar pgloader o script Python)
pgloader sqlite:///path/to/db.sqlite3 postgresql://user:pass@rds-endpoint/dbname
```

### 2. Configuración de ECS

**Task Definitions:**

**Backend Python:**
```json
{
  "family": "ai-assistants-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [{
    "name": "backend",
    "image": "<account>.dkr.ecr.<region>.amazonaws.com/ai-assistants-backend:latest",
    "portMappings": [{
      "containerPort": 8000,
      "protocol": "tcp"
    }],
    "environment": [
      {"name": "AI_ASSISTANTS_DATA_DIR", "value": "/tmp"},
      {"name": "AI_ASSISTANTS_ENABLE_LEGACY_ROUTES", "value": "0"}
    ],
    "secrets": [
      {
        "name": "DATABASE_URL",
        "valueFrom": "arn:aws:secretsmanager:region:account:secret:db-credentials"
      },
      {
        "name": "AI_ASSISTANTS_API_KEYS",
        "valueFrom": "arn:aws:secretsmanager:region:account:secret:api-keys"
      }
    ],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "/ecs/ai-assistants-backend",
        "awslogs-region": "us-east-1",
        "awslogs-stream-prefix": "ecs"
      }
    }
  }]
}
```

**WhatsApp Service:**
```json
{
  "family": "whatsapp-baileys-service",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "containerDefinitions": [{
    "name": "whatsapp",
    "image": "<account>.dkr.ecr.<region>.amazonaws.com/whatsapp-service:latest",
    "portMappings": [{
      "containerPort": 60007,
      "protocol": "tcp"
    }],
    "environment": [
      {"name": "BACKEND_URL", "value": "http://backend-alb-<id>.us-east-1.elb.amazonaws.com"},
      {"name": "PORT", "value": "60007"}
    ],
    "mountPoints": [{
      "sourceVolume": "whatsapp-auth",
      "containerPath": "/app/auth_info",
      "readOnly": false
    }],
    "volumes": [{
      "name": "whatsapp-auth",
      "efsVolumeConfiguration": {
        "fileSystemId": "fs-xxxxx",
        "rootDirectory": "/auth_info"
      }
    }]
  }]
}
```

### 3. EFS para Persistencia de WhatsApp Auth

**Importante:** WhatsApp Baileys necesita persistir `auth_info/` entre reinicios.

**Solución:** Usar EFS (Elastic File System) montado en el contenedor.

```bash
# Crear EFS
aws efs create-file-system \
  --creation-token whatsapp-auth \
  --performance-mode generalPurpose \
  --throughput-mode provisioned \
  --provisioned-throughput-in-mibps 100

# Crear mount target en cada subnet
aws efs create-mount-target \
  --file-system-id fs-xxxxx \
  --subnet-id subnet-xxxxx \
  --security-groups sg-xxxxx
```

### 4. Auto Scaling Configuration

**Backend Service:**
```json
{
  "serviceName": "ai-assistants-backend",
  "desiredCount": 2,
  "autoScaling": {
    "minCapacity": 2,
    "maxCapacity": 10,
    "targetTrackingScalingPolicies": [{
      "targetValue": 70.0,
      "predefinedMetricSpecification": {
        "predefinedMetricType": "ECSServiceAverageCPUUtilization"
      }
    }]
  }
}
```

**WhatsApp Service:**
- **Siempre 1 task** (no escalar, necesita conexión persistente)
- Configurar health checks para reinicio automático

### 5. Application Load Balancer

**Configuración:**
- **HTTP/HTTPS Listener**: Para API REST
- **WebSocket Support**: Para `/v1/ws/conversations/{id}`
- **Health Checks**: `/health` endpoint
- **SSL Certificate**: ACM (Let's Encrypt gratis)

### 6. Secrets Management

**Usar AWS Secrets Manager:**
```bash
# Crear secret para base de datos
aws secretsmanager create-secret \
  --name ai-assistants/database \
  --secret-string '{"username":"admin","password":"xxx","host":"rds-endpoint","port":5432}'

# Crear secret para API keys
aws secretsmanager create-secret \
  --name ai-assistants/api-keys \
  --secret-string '{"keys":"project1:key1,project2:key2"}'
```

### 7. Monitoring y Logs

**CloudWatch:**
- Logs de todos los servicios
- Métricas de CPU, memoria, requests
- Alarmas para errores y latencia

**X-Ray (Opcional):**
- Tracing distribuido
- Análisis de performance

## Scripts de Despliegue

### build-and-push.sh
```bash
#!/bin/bash
# Build y push de imágenes Docker a ECR

AWS_REGION=us-east-1
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPO_BACKEND=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/ai-assistants-backend
ECR_REPO_WHATSAPP=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/whatsapp-service

# Login a ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Backend
cd backend
docker build -t $ECR_REPO_BACKEND:latest .
docker push $ECR_REPO_BACKEND:latest

# WhatsApp Service
cd ../whatsapp-baileys-service
docker build -t $ECR_REPO_WHATSAPP:latest .
docker push $ECR_REPO_WHATSAPP:latest
```

### deploy.sh
```bash
#!/bin/bash
# Desplegar servicios en ECS

# Actualizar servicio backend
aws ecs update-service \
  --cluster ai-assistants-cluster \
  --service ai-assistants-backend \
  --force-new-deployment

# Actualizar servicio WhatsApp
aws ecs update-service \
  --cluster ai-assistants-cluster \
  --service whatsapp-baileys-service \
  --force-new-deployment
```

## Consideraciones Importantes

### 1. WhatsApp Connection Persistence
- **Problema**: Si el contenedor se reinicia, se pierde la conexión
- **Solución**: 
  - Usar EFS para `auth_info/`
  - Health checks agresivos
  - Auto-restart en ECS
  - Considerar usar EC2 dedicado si es crítico

### 2. Database Connection Pooling
- Usar PgBouncer o connection pooling nativo
- Configurar `max_connections` en RDS según instancias

### 3. Rate Limiting
- Migrar de in-memory a Redis (ElastiCache)
- Compartir rate limits entre instancias

### 4. WebSocket Connections
- ALB soporta WebSocket nativamente
- Configurar timeout apropiado (5-10 minutos)

### 5. Costos
- **Desarrollo/Testing**: Usar t3.micro/t3.small
- **Producción**: Escalar según necesidad real
- **Reserved Instances**: Si carga es predecible, ahorra 30-40%

## Alternativa: Serverless (No Recomendada para WhatsApp)

**Lambda + API Gateway:**
- ✅ Excelente para backend API
- ❌ **NO funciona para WhatsApp Baileys** (necesita conexión persistente)
- ❌ WebSocket en Lambda tiene limitaciones

**Recomendación**: Usar Lambda solo para endpoints específicos, mantener ECS para WhatsApp.

## Checklist de Migración

- [ ] Crear VPC con subnets públicas/privadas
- [ ] Crear RDS PostgreSQL (Multi-AZ)
- [ ] Migrar datos de SQLite a PostgreSQL
- [ ] Crear EFS para WhatsApp auth
- [ ] Crear ECR repositories
- [ ] Build y push imágenes Docker
- [ ] Crear ECS cluster
- [ ] Crear task definitions
- [ ] Crear servicios ECS
- [ ] Configurar ALB
- [ ] Configurar Secrets Manager
- [ ] Configurar CloudWatch logs
- [ ] Configurar auto scaling
- [ ] Configurar health checks
- [ ] Testing de conexión WhatsApp
- [ ] Testing de escalado
- [ ] Configurar backups RDS
- [ ] Configurar alarmas CloudWatch

## Conclusión

**Recomendación Final: ECS Fargate**

- ✅ Mejor balance costo/beneficio
- ✅ Escalado automático
- ✅ Menos mantenimiento
- ✅ Alta disponibilidad
- ✅ Integración nativa con AWS

**Costo estimado inicial: $100-200/mes** (puede escalar según uso)

**Tiempo de implementación: 1-2 semanas** (depende de experiencia con AWS)
