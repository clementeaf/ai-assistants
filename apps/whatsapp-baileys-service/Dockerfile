FROM node:18-slim

WORKDIR /app

# Instalar dependencias del sistema para QR
RUN apt-get update && apt-get install -y \
    python3 \
    make \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copiar package files
COPY package*.json ./

# Instalar dependencias
RUN npm ci --only=production

# Copiar código
COPY . .

# Variables de entorno por defecto
ENV NODE_ENV=production
ENV PORT=60007
ENV WHATSAPP_AUTH_DIR=/app/auth_info

# Crear directorio de autenticación
RUN mkdir -p /app/auth_info

# Exponer puerto
EXPOSE 60007

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD node -e "require('http').get('http://localhost:60007/status', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})" || exit 1

# Comando de inicio
CMD ["node", "index.js"]
