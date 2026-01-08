#!/bin/bash
# Script para iniciar el servidor MCP de calendario

cd "$(dirname "$0")"

# Activar venv si existe
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Ejecutar servidor
python main.py

