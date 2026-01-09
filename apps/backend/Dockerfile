FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Variables de entorno por defecto
ENV PYTHONUNBUFFERED=1
ENV AI_ASSISTANTS_DATA_DIR=/data

# Crear directorio de datos
RUN mkdir -p /data

# Exponer puerto
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/docs', timeout=5)" || exit 1

# Comando de inicio
CMD ["python", "run_server.py"]
