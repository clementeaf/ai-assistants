# Pasos para Probar con carriagada@grupobanados.com

## ✅ Estado Actual
- ✅ MCP Calendar Server corriendo (puerto 60000)
- ❌ Backend no está corriendo
- ❌ OAuth2 no está configurado

## 📋 Pasos a Seguir

### Paso 1: Configurar OAuth2 en Google Cloud Console

**Si aún no tienes credenciales OAuth2:**

1. Ir a [Google Cloud Console](https://console.cloud.google.com/)
2. Crear proyecto o seleccionar uno existente
3. Habilitar Google Calendar API:
   - APIs & Services > Library
   - Buscar "Google Calendar API"
   - Click en "Enable"
4. Configurar OAuth Consent Screen:
   - APIs & Services > OAuth consent screen
   - User Type: External
   - App name: `AI Assistants Calendar`
   - User support email: Tu email
   - Scopes: Agregar `https://www.googleapis.com/auth/calendar`
   - Test users: Agregar `carriagada@grupobanados.com`
5. Crear Credenciales OAuth2:
   - APIs & Services > Credentials
   - Create Credentials > OAuth client ID
   - Application type: **Web application**
   - Name: `AI Assistants Calendar Web`
   - Authorized redirect URIs: `http://localhost:60000/oauth/callback`
   - Click en "Create"
6. Copiar:
   - Client ID
   - Client Secret

### Paso 2: Configurar Variables de Entorno

**En `mcp-servers/calendar-mcp-server/.env`:**

```bash
# Backend a usar
CALENDAR_BACKEND=google_calendar

# OAuth2 Configuration (reemplaza con tus valores)
GOOGLE_OAUTH_CLIENT_ID=TU_CLIENT_ID.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=TU_CLIENT_SECRET
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:60000/oauth/callback

# Token Storage
TOKEN_DB_PATH=tokens.db
TOKEN_ENCRYPTION_KEY=tu-clave-segura-de-32-caracteres-minimo

# Server
CALENDAR_SERVER_PORT=60000
```

**Generar clave de encriptación:**
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Paso 3: Reiniciar MCP Calendar Server

```bash
cd mcp-servers/calendar-mcp-server
# Detener el servidor actual (Ctrl+C)
# Iniciar con main_multi_user.py (que tiene soporte OAuth2)
python main_multi_user.py
```

### Paso 4: Iniciar Backend

```bash
cd apps/backend
python run_server.py
```

### Paso 5: Verificar que Backend Puede Conectarse al MCP Calendar Server

**En `.env` del backend (raíz del proyecto):**
```bash
AI_ASSISTANTS_MCP_CALENDAR_URL=http://localhost:60000
```

### Paso 6: Agregar Empresa en Admin-Frontend

1. Abre: `http://localhost:5173/clientes`
2. Click en "Agregar Cliente"
3. Completa:
   - **ID del Cliente**: `empresa-carriagada`
   - **Email del Cliente**: `carriagada@grupobanados.com`
   - **Nombre del Cliente**: `Carriagada - Grupo Bañados`
4. Click en "Conectar Calendario"

### Paso 7: Obtener Link de OAuth2

Después de hacer clic en "Conectar Calendario":
- El sistema te preguntará: "¿Quieres abrir la URL de autorización ahora?"
- Si eliges "No", se copiará el link al portapapeles
- **Este link se lo das a la empresa** (o lo abres tú si tienes acceso a la cuenta)

### Paso 8: Autorizar Google Calendar

1. Abre el link de OAuth2
2. Inicia sesión con `carriagada@grupobanados.com`
3. Google muestra: "¿Permitir que AI Assistants acceda a tu Google Calendar?"
4. Click en "Permitir"
5. Google redirige automáticamente
6. Los tokens se guardan automáticamente

### Paso 9: Verificar Estado

1. En Admin-Frontend (`/clientes`), verifica:
   - Estado: "Conectado" ✅
   - Calendar Email: `carriagada@grupobanados.com`

### Paso 10: Probar que Funciona

1. Usa el asistente IA (Chat del frontend o WhatsApp)
2. Pide una reserva: "Quiero reservar para mañana a las 3 PM"
3. El asistente debe consultar el Google Calendar de `carriagada@grupobanados.com`
4. Las reservas se crearán en ese calendario

## 🔍 Verificación Rápida

```bash
# 1. Verificar MCP Calendar Server
curl http://localhost:60000/health

# 2. Verificar Backend
curl http://localhost:9000/health

# 3. Verificar OAuth2 endpoint
curl -X POST http://localhost:60000/oauth/authorize \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "test-123"}'
```

## ⚠️ Si Algo Falla

### "OAuth2 not configured"
- Verifica que `CALENDAR_BACKEND=google_calendar` esté en `.env`
- Verifica que `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`, `GOOGLE_OAUTH_REDIRECT_URI` estén configurados
- Reinicia el MCP Calendar Server

### "Invalid redirect URI"
- En Google Cloud Console, el redirect URI debe ser exactamente: `http://localhost:60000/oauth/callback`
- Verifica que no tenga espacios o caracteres extra

### El link no se genera
- Verifica que el backend esté corriendo
- Verifica que `AI_ASSISTANTS_MCP_CALENDAR_URL=http://localhost:60000` esté en `.env`
- Revisa los logs del backend
