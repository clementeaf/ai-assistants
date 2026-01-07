#!/usr/bin/env python3
"""Script to run the FastAPI server with uvicorn."""

import sys
from pathlib import Path

# Agregar el directorio que contiene 'backend' al PYTHONPATH
current_file = Path(__file__).resolve()
backend_dir = current_file.parent  # .../ai_assistants/backend/
project_root = backend_dir.parent  # .../ai_assistants/

# Agregar el directorio raíz al path
sys.path.insert(0, str(project_root))

# IMPORTANTE: Crear alias ANTES de importar cualquier módulo que use 'ai_assistants'
# El código usa 'ai_assistants' pero el directorio es 'backend'
import backend
sys.modules["ai_assistants"] = backend

# Ahora podemos importar el app que usará los imports de ai_assistants
import uvicorn
from backend.api.app import app

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )

