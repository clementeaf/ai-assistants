# Guía Paso a Paso: Despliegue en AWS Free Tier

Esta guía te llevará paso a paso para desplegar AI Assistants en AWS usando recursos del Free Tier.

## 📋 Prerequisitos

### 1. Cuenta AWS
- ✅ Cuenta AWS activa
- ✅ AWS CLI configurado (`aws configure`)
- ✅ Permisos para crear recursos (EC2, RDS, VPC, etc.)

### 2. Herramientas Locales
```bash
# Instalar AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Instalar Terraform
brew install terraform  # macOS
# o descargar desde: https://www.terraform.io/downloads

# Instalar Docker (opcional, para testing local)
# https://docs.docker.com/get-docker/
```

### 3. Key Pair para EC2
```bash
# Crear key pair en AWS
aws ec2 create-key-pair \
  --key-name ai-assistants-key \
  --query 'KeyMaterial' \
  --output text > ~/.ssh/ai-assistants-key.pem

chmod 400 ~/.ssh/ai-assistants-key.pem
```

## 🚀 Despliegue Automatizado (Recomendado)

### Opción 1: Script Automático

```bash
# Ejecutar script de despliegue
./scripts/deploy-aws-free-tier.sh
```

El script:
1. ✅ Verifica prerequisitos
2. ✅ Crea infraestructura con Terraform
3. ✅ Configura instancia EC2
4. ✅ Despliega servicios con Docker Compose

**Tiempo estimado: 15-20 minutos**

## 🛠️ Despliegue Manual (Paso a Paso)

### Paso 1: Crear Infraestructura con Terraform

```bash
cd terraform

# 1. Configurar variables
cp terraform.tfvars.example terraform.tfvars
# Editar terraform.tfvars con tus valores:
# - aws_region
# - key_pair_name
# - db_password (generar con: openssl rand -base64 32)

# 2. Inicializar Terraform
terraform init

# 3. Ver plan
terraform plan

# 4. Aplicar
terraform apply
```

**Recursos creados:**
- ✅ VPC con subnet pública
- ✅ Security Groups
- ✅ EC2 t2.micro (Free Tier)
- ✅ RDS PostgreSQL db.t2.micro (Free Tier)
- ✅ ElastiCache Redis cache.t2.micro (Free Tier)
- ✅ EFS para WhatsApp auth

**Tiempo: 10-15 minutos**

### Paso 2: Obtener Información de Recursos

```bash
# Obtener IP de EC2
EC2_IP=$(terraform output -raw ec2_public_ip)
echo $EC2_IP

# Obtener endpoint de RDS
RDS_ENDPOINT=$(terraform output -raw rds_endpoint)
echo $RDS_ENDPOINT

# Obtener endpoint de Redis
REDIS_ENDPOINT=$(terraform output -raw redis_endpoint)
echo $REDIS_ENDPOINT

# Obtener EFS ID
EFS_ID=$(terraform output -raw efs_id)
echo $EFS_ID
```

### Paso 3: Configurar Instancia EC2

```bash
# Conectar a la instancia
ssh -i ~/.ssh/ai-assistants-key.pem ec2-user@$EC2_IP

# En la instancia EC2:
# 1. Instalar Docker Compose (si no está)
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 2. Instalar EFS utils
sudo yum install -y amazon-efs-utils

# 3. Montar EFS para WhatsApp auth
sudo mkdir -p /mnt/efs/whatsapp-auth
sudo mount -t efs -o tls $EFS_ID:/ /mnt/efs/whatsapp-auth
echo "$EFS_ID:/ /mnt/efs/whatsapp-auth efs _netdev,tls" | sudo tee -a /etc/fstab
```

### Paso 4: Clonar y Configurar Código

```bash
# En la instancia EC2
cd /home/ec2-user

# Clonar repositorio (o copiar código)
git clone <tu-repo> ai-assistants
cd ai-assistants

# O copiar desde local:
# scp -r -i ~/.ssh/ai-assistants-key.pem ./ ec2-user@$EC2_IP:/home/ec2-user/ai-assistants/
```

### Paso 5: Configurar Variables de Entorno

```bash
# Crear archivo .env
cat > .env <<EOF
# Database
DATABASE_URL=postgresql://postgres:TU_PASSWORD@$RDS_ENDPOINT/ai_assistants

# Redis
REDIS_URL=redis://$REDIS_ENDPOINT:6379/0

# Backend
AI_ASSISTANTS_DATA_DIR=/data
AI_ASSISTANTS_ENABLE_LEGACY_ROUTES=0

# WhatsApp
BACKEND_URL=http://localhost:8000
API_KEY=dev
ALLOWED_NUMBERS=
WHATSAPP_AUTH_DIR=/mnt/efs/whatsapp-auth
EOF
```

### Paso 6: Migrar Base de Datos

```bash
# Conectar a RDS y crear base de datos
psql -h $RDS_ENDPOINT -U postgres -d postgres <<EOF
CREATE DATABASE ai_assistants;
\q
EOF

# Si tienes datos en SQLite local, migrar:
# pgloader sqlite:///path/to/db.sqlite3 postgresql://postgres:password@$RDS_ENDPOINT/ai_assistants
```

### Paso 7: Desplegar con Docker Compose

```bash
# Construir imágenes
docker-compose -f docker-compose.aws.yml build

# Levantar servicios
docker-compose -f docker-compose.aws.yml up -d

# Ver logs
docker-compose -f docker-compose.aws.yml logs -f
```

### Paso 8: Verificar Despliegue

```bash
# Verificar servicios
docker-compose -f docker-compose.aws.yml ps

# Verificar backend
curl http://localhost:8000/docs

# Verificar WhatsApp service
curl http://localhost:60007/status
```

## 🔧 Configuración Post-Despliegue

### 1. Configurar WhatsApp

1. Acceder a: `http://$EC2_IP:60007`
2. Escanear código QR con WhatsApp
3. La sesión se guardará en EFS automáticamente

### 2. Configurar Dominio (Opcional)

```bash
# En Route 53 o tu proveedor DNS:
# A Record: tu-dominio.com -> $EC2_IP

# Actualizar security group para permitir tráfico HTTP/HTTPS
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxx \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxx \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0
```

### 3. Configurar SSL (Opcional)

```bash
# Usar Let's Encrypt con Certbot
sudo yum install -y certbot
sudo certbot certonly --standalone -d tu-dominio.com

# Configurar nginx como reverse proxy (opcional)
```

## 📊 Monitoreo

### CloudWatch

```bash
# Ver métricas de EC2
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=i-xxxxx \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Average
```

### Logs Locales

```bash
# En la instancia EC2
docker-compose -f docker-compose.aws.yml logs backend
docker-compose -f docker-compose.aws.yml logs whatsapp
```

## 🔄 Actualizaciones

### Actualizar Código

```bash
# En la instancia EC2
cd /home/ec2-user/ai-assistants
git pull  # o copiar nuevo código

# Reconstruir y reiniciar
docker-compose -f docker-compose.aws.yml build
docker-compose -f docker-compose.aws.yml up -d
```

### Backup de Base de Datos

```bash
# Backup manual
pg_dump -h $RDS_ENDPOINT -U postgres ai_assistants > backup.sql

# RDS tiene backups automáticos configurados (7 días)
```

## 🗑️ Limpieza (Destruir Recursos)

```bash
cd terraform
terraform destroy
```

**⚠️ Esto eliminará todos los recursos y datos!**

## 🐛 Troubleshooting

### Problema: No puedo conectar por SSH

```bash
# Verificar security group
aws ec2 describe-security-groups --group-ids sg-xxxxx

# Verificar que la instancia esté corriendo
aws ec2 describe-instances --instance-ids i-xxxxx
```

### Problema: Servicios no inician

```bash
# Ver logs
docker-compose -f docker-compose.aws.yml logs

# Verificar recursos
docker-compose -f docker-compose.aws.yml ps
df -h  # Verificar espacio en disco
free -h  # Verificar memoria
```

### Problema: WhatsApp no se conecta

```bash
# Verificar que EFS esté montado
df -h | grep efs

# Verificar permisos
ls -la /mnt/efs/whatsapp-auth

# Ver logs de WhatsApp
docker-compose -f docker-compose.aws.yml logs whatsapp
```

## 📝 Checklist Final

- [ ] Infraestructura creada con Terraform
- [ ] EC2 accesible por SSH
- [ ] RDS accesible desde EC2
- [ ] Redis accesible desde EC2
- [ ] EFS montado correctamente
- [ ] Servicios Docker corriendo
- [ ] Backend respondiendo en :8000
- [ ] WhatsApp service respondiendo en :60007
- [ ] WhatsApp conectado (QR escaneado)
- [ ] Base de datos migrada
- [ ] Monitoreo configurado
- [ ] Backups configurados

## 💰 Costo Estimado

**Con Free Tier (primeros 12 meses):**
- EC2 t2.micro: $0
- RDS db.t2.micro: $0
- ElastiCache cache.t2.micro: $0
- EFS (5 GB): $0
- **Total: $0/mes** ✅

**Después de Free Tier:**
- EC2 t2.micro: ~$8.50/mes
- RDS db.t2.micro: ~$15/mes
- ElastiCache cache.t2.micro: ~$12/mes
- EFS: ~$1.50/mes
- **Total: ~$37/mes**

## 🎉 ¡Listo!

Tu sistema está desplegado y funcionando. Ahora puedes:

1. ✅ Probar el backend en `http://$EC2_IP:8000/docs`
2. ✅ Conectar WhatsApp en `http://$EC2_IP:60007`
3. ✅ Monitorear en CloudWatch
4. ✅ Iterar y mejorar

**¿Necesitas ayuda?** Revisa la sección de Troubleshooting o los logs.
