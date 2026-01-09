#!/bin/bash
# Script para iniciar el servidor backend

# Ir al directorio raíz del proyecto
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT" || exit 1

# Activar entorno virtual si existe
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "Entorno virtual activado: .venv"
elif [ -d "venv" ]; then
    source venv/bin/activate
    echo "Entorno virtual activado: venv"
else
    echo "Error: No se encontró entorno virtual. Ejecuta: python3 -m venv .venv"
    exit 1
fi

# Instalar dependencias si es necesario
if ! python -c "import uvicorn" 2>/dev/null; then
    echo "Instalando dependencias..."
    pip install -r backend/requirements.txt
fi

# Agregar el directorio raíz al PYTHONPATH
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Iniciar servidor
cd backend || exit 1
echo "Iniciando servidor en http://localhost:8000"
python run_server.py

