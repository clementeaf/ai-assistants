# 🚀 Quick Start: Despliegue en AWS Free Tier

## Inicio Rápido (5 minutos)

### 1. Prerequisitos
```bash
# Verificar AWS CLI
aws --version

# Verificar Terraform
terraform --version

# Crear key pair (si no existe)
aws ec2 create-key-pair \
  --key-name ai-assistants-key \
  --query 'KeyMaterial' \
  --output text > ~/.ssh/ai-assistants-key.pem
chmod 400 ~/.ssh/ai-assistants-key.pem
```

### 2. Desplegar Automáticamente
```bash
# Ejecutar script de despliegue
./scripts/deploy-aws-free-tier.sh
```

**El script hará todo automáticamente:**
- ✅ Crear infraestructura (VPC, EC2, RDS, Redis, EFS)
- ✅ Configurar instancia EC2
- ✅ Desplegar servicios con Docker Compose
- ✅ Configurar variables de entorno

**Tiempo: 15-20 minutos**

### 3. Acceder a los Servicios

Una vez desplegado:

```bash
# Obtener IP de EC2
cd terraform
EC2_IP=$(terraform output -raw ec2_public_ip)
echo "Backend: http://$EC2_IP:8000/docs"
echo "WhatsApp: http://$EC2_IP:60007"
```

## Estructura de Archivos Creados

```
.
├── terraform/                    # Infraestructura como código
│   ├── main.tf                  # Recursos AWS
│   ├── variables.tf             # Variables
│   └── terraform.tfvars.example # Ejemplo de configuración
│
├── docker-compose.aws.yml        # Docker Compose para AWS
│
├── scripts/
│   ├── deploy-aws-free-tier.sh  # Script de despliegue completo
│   ├── check-aws-free-tier.sh   # Verificar Free Tier
│   └── aws-deploy.sh            # Deploy a ECS (futuro)
│
├── DEPLOYMENT_GUIDE.md          # Guía detallada paso a paso
├── AWS_FREE_TIER.md             # Análisis de Free Tier
└── DEPLOYMENT_RECOMMENDATION.md # Recomendaciones
```

## Recursos Creados (Free Tier)

- ✅ **EC2 t2.micro**: Servidor principal
- ✅ **RDS PostgreSQL db.t2.micro**: Base de datos
- ✅ **ElastiCache Redis cache.t2.micro**: Cache
- ✅ **EFS**: Almacenamiento para WhatsApp auth
- ✅ **VPC + Security Groups**: Red segura

**Costo: $0/mes (primeros 12 meses)**

## Comandos Útiles

### Verificar Estado
```bash
cd terraform
terraform output
```

### Conectar a EC2
```bash
EC2_IP=$(cd terraform && terraform output -raw ec2_public_ip)
ssh -i ~/.ssh/ai-assistants-key.pem ec2-user@$EC2_IP
```

### Ver Logs
```bash
# En EC2
docker-compose -f docker-compose.aws.yml logs -f
```

### Actualizar Código
```bash
# En EC2
cd /home/ec2-user/ai-assistants
git pull
docker-compose -f docker-compose.aws.yml build
docker-compose -f docker-compose.aws.yml up -d
```

### Destruir Todo
```bash
cd terraform
terraform destroy
```

## Próximos Pasos

1. ✅ **Desplegar**: Ejecutar `./scripts/deploy-aws-free-tier.sh`
2. ✅ **Configurar WhatsApp**: Escanear QR en `http://$EC2_IP:60007`
3. ✅ **Probar Backend**: Acceder a `http://$EC2_IP:8000/docs`
4. ✅ **Monitorear**: Revisar CloudWatch y logs

## Documentación Completa

- 📖 **Guía Detallada**: `DEPLOYMENT_GUIDE.md`
- 💰 **Free Tier**: `AWS_FREE_TIER.md`
- 🎯 **Recomendaciones**: `DEPLOYMENT_RECOMMENDATION.md`
- ☁️ **Arquitectura AWS**: `AWS_DEPLOYMENT.md`

## Soporte

Si encuentras problemas:
1. Revisa `DEPLOYMENT_GUIDE.md` sección Troubleshooting
2. Verifica logs: `docker-compose logs`
3. Verifica recursos: `terraform output`

¡Listo para desplegar! 🚀
