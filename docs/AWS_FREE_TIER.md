# AWS Free Tier - Análisis para AI Assistants

## Free Tier Disponible (12 meses desde creación de cuenta)

### ✅ Servicios Gratuitos que Podemos Usar

#### 1. **ECS Fargate** - ✅ PARCIALMENTE GRATIS
- **750 horas/mes** de uso de Fargate
- **0.25 vCPU + 0.5 GB RAM** por hora
- **Cálculo para nuestra arquitectura:**
  - Backend: 512 CPU (0.5 vCPU) + 1024 MB (1 GB RAM) = **2 horas por hora de ejecución**
  - WhatsApp: 256 CPU (0.25 vCPU) + 512 MB (0.5 GB RAM) = **1 hora por hora de ejecución**
  - **Total: 3 horas por hora real = 72 horas/día**
  - **750 horas / 72 horas/día = ~10 días gratis**
  - **Conclusión: Solo 1 instancia de cada servicio gratis por ~10 días**

#### 2. **RDS PostgreSQL** - ✅ GRATIS (db.t2.micro o db.t3.micro)
- **750 horas/mes** de instancia
- **20 GB de almacenamiento**
- **20 GB de backup storage**
- **Perfecto para desarrollo/testing**

#### 3. **ElastiCache Redis** - ✅ GRATIS (cache.t2.micro)
- **750 horas/mes**
- **Perfecto para rate limiting**

#### 4. **Application Load Balancer** - ❌ NO GRATIS
- **$0.0225/hora = ~$16/mes** (mínimo)
- **No hay Free Tier**

#### 5. **EFS (Elastic File System)** - ✅ GRATIS
- **5 GB de almacenamiento**
- **Suficiente para auth_info de WhatsApp**

#### 6. **ECR (Elastic Container Registry)** - ✅ GRATIS
- **500 MB de almacenamiento/mes**
- **Suficiente para imágenes Docker**

#### 7. **CloudWatch** - ✅ PARCIALMENTE GRATIS
- **10 métricas personalizadas**
- **5 GB de logs**
- **1 millón de API requests**

#### 8. **Secrets Manager** - ❌ NO GRATIS
- **$0.40/secret/mes**
- **Alternativa: Usar Systems Manager Parameter Store (GRATIS)**

#### 9. **S3** - ✅ GRATIS
- **5 GB de almacenamiento**
- **20,000 GET requests**
- **2,000 PUT requests**

#### 10. **CloudFront** - ✅ PARCIALMENTE GRATIS
- **50 GB de transferencia de datos**
- **2,000,000 HTTP/HTTPS requests**

#### 11. **VPC** - ✅ GRATIS
- **Sin costo adicional**

#### 12. **Data Transfer** - ✅ PARCIALMENTE GRATIS
- **100 GB/mes saliente** (dentro de AWS)
- **1 GB/mes saliente** (a internet)

## Arquitectura Optimizada para Free Tier

### Opción 1: Máximo Free Tier (Recomendada para Testing)

```
┌─────────────────────────────────────────────────────────┐
│   EC2 t2.micro (Free Tier)                              │
│   - Backend Python (1 instancia)                        │
│   - WhatsApp Service (1 instancia)                       │
│   - MCP Servers (opcional, mismo servidor)              │
└─────────────────────────────────────────────────────────┘
                    │
    ┌───────────────▼────────────────┐
    │   RDS PostgreSQL (db.t2.micro) │
    │   - 750 horas/mes GRATIS        │
    └─────────────────────────────────┘
    
    ┌─────────────────────────────────┐
    │   ElastiCache Redis (cache.t2) │
    │   - 750 horas/mes GRATIS        │
    └─────────────────────────────────┘
    
    ┌─────────────────────────────────┐
    │   EFS (5 GB GRATIS)              │
    │   - WhatsApp auth_info          │
    └─────────────────────────────────┘
```

**Costo: $0/mes** (dentro de Free Tier)

**Limitaciones:**
- ❌ Sin Load Balancer (usar IP pública directa)
- ❌ Sin alta disponibilidad
- ❌ EC2 t2.micro puede ser lento (1 vCPU, 1 GB RAM)
- ✅ Perfecto para desarrollo/testing

### Opción 2: Híbrida (Free Tier + Mínimo Costo)

```
┌─────────────────────────────────────────────────────────┐
│   ECS Fargate (Free Tier limitado)                      │
│   - Backend: 1 task (512 CPU, 1 GB)                     │
│   - WhatsApp: 1 task (256 CPU, 512 MB)                  │
│   - Usa ~3 horas por hora real                          │
│   - ~10 días gratis, luego ~$15-20/mes                 │
└─────────────────────────────────────────────────────────┘
                    │
    ┌───────────────▼────────────────┐
    │   RDS PostgreSQL (db.t2.micro) │
    │   - GRATIS (750 horas/mes)      │
    └─────────────────────────────────┘
    
    ┌─────────────────────────────────┐
    │   ElastiCache Redis (cache.t2)  │
    │   - GRATIS (750 horas/mes)      │
    └─────────────────────────────────┘
```

**Costo:**
- Primeros 10 días: **$0**
- Después: **~$15-20/mes** (sin ALB)

### Opción 3: EC2 Free Tier (Más Control)

```
┌─────────────────────────────────────────────────────────┐
│   EC2 t2.micro (Free Tier)                               │
│   - 750 horas/mes GRATIS                                 │
│   - 1 vCPU, 1 GB RAM                                    │
│   - Docker Compose con todos los servicios              │
└─────────────────────────────────────────────────────────┘
```

**Costo: $0/mes** (dentro de Free Tier)

**Ventajas:**
- ✅ Totalmente gratis
- ✅ Control total
- ✅ Fácil de configurar

**Desventajas:**
- ❌ Limitado en recursos (1 vCPU, 1 GB RAM)
- ❌ Puede ser lento con múltiples servicios
- ❌ Sin alta disponibilidad

## Recomendación para Free Tier

### Para Desarrollo/Testing (Primeros 6 meses):

**Usar EC2 t2.micro con Docker Compose**

```yaml
# docker-compose.yml
services:
  backend:
    image: backend:latest
    ports:
      - "8000:8000"
  
  whatsapp:
    image: whatsapp:latest
    ports:
      - "60007:60007"
    volumes:
      - ./auth_info:/app/auth_info
  
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ai_assistants
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

**Costo: $0/mes**

### Para Producción (Después de Free Tier):

**Migrar a ECS Fargate + RDS**

**Costo estimado: ~$30-50/mes** (sin ALB)

## Checklist de Verificación Free Tier

Para verificar tu cuenta actual:

```bash
# 1. Verificar edad de cuenta
aws account get-contact-information

# 2. Verificar uso actual de Free Tier
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-12-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=SERVICE

# 3. Verificar límites de servicio
aws service-quotas get-service-quota \
  --service-code ec2 \
  --quota-code L-0263D0A3  # Running On-Demand EC2 instances
```

## Servicios que NO tienen Free Tier (Costos Mínimos)

1. **Application Load Balancer**: ~$16/mes
   - **Alternativa**: Usar IP pública directa (gratis pero sin balanceo)

2. **Secrets Manager**: ~$0.40/secret/mes
   - **Alternativa**: Systems Manager Parameter Store (GRATIS)

3. **NAT Gateway**: ~$32/mes
   - **Alternativa**: Usar instancias públicas (gratis)

## Estimación de Costos

### Con Free Tier (Primeros 12 meses):
- **EC2 t2.micro**: $0 (750 horas/mes)
- **RDS db.t2.micro**: $0 (750 horas/mes)
- **ElastiCache cache.t2.micro**: $0 (750 horas/mes)
- **EFS**: $0 (5 GB)
- **ECR**: $0 (500 MB)
- **S3**: $0 (5 GB)
- **CloudWatch**: $0 (límites básicos)
- **Total: $0/mes** ✅

### Después de Free Tier (Mínimo):
- **EC2 t2.micro**: ~$8.50/mes
- **RDS db.t2.micro**: ~$15/mes
- **ElastiCache cache.t2.micro**: ~$12/mes
- **EFS**: ~$1.50/mes (5 GB)
- **Total: ~$37/mes**

### Con ECS Fargate (Después de Free Tier):
- **ECS Fargate**: ~$15-20/mes (2 tasks pequeños)
- **RDS db.t2.micro**: ~$15/mes
- **ElastiCache cache.t2.micro**: ~$12/mes
- **EFS**: ~$1.50/mes
- **Total: ~$43-48/mes**

## Conclusión

✅ **SÍ, puedes tener esto GRATIS por 12 meses** usando:

1. **EC2 t2.micro** (Free Tier) con Docker Compose
2. **RDS PostgreSQL db.t2.micro** (Free Tier)
3. **ElastiCache Redis cache.t2.micro** (Free Tier)
4. **EFS** (5 GB gratis)
5. **S3** (5 GB gratis)

**Limitación**: Sin Load Balancer (usar IP pública directa)

**Recomendación**: 
- **Meses 1-12**: EC2 t2.micro (gratis)
- **Después**: Migrar a ECS Fargate (~$40-50/mes)
