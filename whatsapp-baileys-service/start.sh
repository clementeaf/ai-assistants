#!/bin/bash
# Script para iniciar el servicio de WhatsApp Baileys

cd "$(dirname "$0")"

# Cargar variables de entorno si existe .env
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Verificar que Node.js esté instalado
if ! command -v node &> /dev/null; then
    echo "Error: Node.js no está instalado"
    echo "Instala Node.js desde https://nodejs.org/"
    exit 1
fi

# Verificar que las dependencias estén instaladas
if [ ! -d "node_modules" ]; then
    echo "Instalando dependencias..."
    npm install
fi

# Iniciar servicio
echo "Iniciando WhatsApp Baileys Service..."
echo "Backend URL: ${BACKEND_URL:-http://localhost:8000}"
echo "API Key: ${API_KEY:-dev}"
echo ""

node index.js
