#!/usr/bin/env python3
"""Script to run the FastAPI server with uvicorn."""

import sys
from pathlib import Path
from dotenv import load_dotenv


def find_project_root(start_path: Path) -> Path:
    """
    Busca la raíz del proyecto subiendo desde start_path.
    
    Busca marcadores de raíz del proyecto (.git, pyproject.toml, .env) y
    devuelve el directorio que los contiene. Funciona tanto en localhost
    como en producción (Docker, servidores, etc.).
    
    Args:
        start_path: Ruta desde donde empezar a buscar (típicamente el directorio del script)
    
    Returns:
        Path a la raíz del proyecto
    """
    current = start_path.resolve()
    
    # Marcadores de raíz del proyecto (en orden de prioridad)
    markers = [".git", "pyproject.toml", ".env"]
    
    # Subir hasta encontrar un marcador o llegar a la raíz del sistema
    while current != current.parent:  # No subir más allá de /
        for marker in markers:
            if (current / marker).exists():
                return current
        current = current.parent
    
    # Fallback: si no se encuentra marcador, subir dos niveles desde el script
    # (estructura esperada: proyecto/apps/backend/run_server.py)
    return start_path.parent.parent


# Encontrar raíz del proyecto de forma robusta
current_file = Path(__file__).resolve()
backend_dir = current_file.parent  # .../ai_assistants/apps/backend/
# Empezar a buscar desde un nivel arriba para evitar encontrar .env en backend/
project_root = find_project_root(backend_dir.parent)  # .../ai-assistants/

# Cargar .env desde la raíz del proyecto (prioridad) y luego desde backend/
env_path_root = project_root / ".env"
env_path_backend = backend_dir / ".env"

# Cargar primero el .env de la raíz (prioridad máxima) y luego el del backend
if env_path_root.exists():
    load_dotenv(env_path_root, override=True)
    print(f"✅ Cargado .env desde: {env_path_root} (prioridad)")
    
if env_path_backend.exists():
    load_dotenv(env_path_backend, override=False)  # override=False para no sobrescribir la raíz
    print(f"✅ Cargado .env desde: {env_path_backend}")

if not env_path_root.exists() and not env_path_backend.exists():
    print("⚠️  No se encontró archivo .env")

# Agregar el directorio apps al path (donde está el módulo backend)
apps_dir = project_root / "apps"
sys.path.insert(0, str(apps_dir))

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
        port=9000,
        log_level="info",
    )

