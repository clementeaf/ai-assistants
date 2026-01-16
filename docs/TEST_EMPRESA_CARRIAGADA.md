# Prueba con Empresa: carriagada@grupobanados.com

## 📋 Checklist de Configuración

### Paso 1: Verificar que los Servicios Estén Corriendo

```bash
# 1. Verificar MCP Calendar Server
curl http://localhost:60000/health

# 2. Verificar Backend
curl http://localhost:9000/health

# 3. Verificar Admin-Frontend (debe estar en http://localhost:5173)
```

### Paso 2: Configurar Variables de Entorno OAuth2

**En el MCP Calendar Server** (`mcp-servers/calendar-mcp-server/`):

Crea o edita un archivo `.env` con:

```bash
# Backend a usar
CALENDAR_BACKEND=google_calendar

# OAuth2 Configuration (debes obtener estos de Google Cloud Console)
GOOGLE_OAUTH_CLIENT_ID=tu-client-id.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=tu-client-secret
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:60000/oauth/callback

# Token Storage
TOKEN_DB_PATH=tokens.db
TOKEN_ENCRYPTION_KEY=tu-clave-de-encriptacion-segura-32-caracteres

# Server
CALENDAR_SERVER_PORT=60000
```

**⚠️ IMPORTANTE**: Si no tienes las credenciales OAuth2 de Google, primero debes:
1. Ir a Google Cloud Console
2. Crear proyecto
3. Habilitar Google Calendar API
4. Crear credenciales OAuth2
5. Configurar redirect URI: `http://localhost:60000/oauth/callback`

### Paso 3: Agregar Empresa en Admin-Frontend

1. Abre Admin-Frontend: `http://localhost:5173/clientes`
2. Haz clic en "Agregar Cliente"
3. Completa:
   - **ID del Cliente**: `empresa-carriagada` (o el que prefieras)
   - **Email del Cliente**: `carriagada@grupobanados.com`
   - **Nombre del Cliente**: `Carriagada - Grupo Bañados`
4. Haz clic en "Conectar Calendario"

### Paso 4: Obtener Link de OAuth2

Después de hacer clic en "Conectar Calendario":
- El sistema te preguntará si quieres abrir ahora o copiar link
- Si eliges "Copiar link", se copiará al portapapeles
- **Este link se lo das a la empresa** para que autorice

### Paso 5: Empresa Autoriza

1. La empresa (o tú con acceso a esa cuenta) hace clic en el link
2. Google muestra pantalla de consentimiento
3. Empresa hace clic en "Permitir"
4. Google redirige automáticamente
5. Los tokens se guardan automáticamente

### Paso 6: Verificar Estado

1. En Admin-Frontend (`/clientes`), verifica que el estado sea "Conectado"
2. Debe mostrar el email del calendario: `carriagada@grupobanados.com`

### Paso 7: Probar que Funciona

1. Usa el asistente IA (por WhatsApp o Chat del frontend)
2. Pide una reserva
3. El asistente debe consultar el Google Calendar de `carriagada@grupobanados.com`
4. Las reservas se crearán en ese calendario

## 🔧 Si Algo Falla

### Error: "OAuth2 not configured"
- Verifica que las variables de entorno estén configuradas en el MCP Calendar Server
- Verifica que el MCP Calendar Server esté usando `main_multi_user.py` o tenga los endpoints OAuth2

### Error: "Invalid redirect URI"
- Verifica que en Google Cloud Console, el redirect URI sea exactamente: `http://localhost:60000/oauth/callback`
- En producción, debe ser HTTPS

### Error: "MCP Calendar Server no está corriendo"
- Inicia el servidor:
  ```bash
  cd mcp-servers/calendar-mcp-server
  python main_multi_user.py
  # O
  ./start.sh
  ```

### El link de OAuth2 no se genera
- Verifica que el MCP Calendar Server esté corriendo
- Verifica que `AI_ASSISTANTS_MCP_CALENDAR_URL=http://localhost:60000` esté en el `.env` del backend
