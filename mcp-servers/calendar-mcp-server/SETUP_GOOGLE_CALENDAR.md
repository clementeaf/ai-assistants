# Setup de Google Calendar para MCP

## Resumen

Este documento explica cómo configurar el MCP de calendario para usar Google Calendar como backend en lugar de SQLite.

## Prerrequisitos

1. Cuenta de Google (Gmail o Google Workspace)
2. Acceso a [Google Cloud Console](https://console.cloud.google.com/)
3. Python 3.8+

## Opción 1: Service Account (Recomendado para producción)

### Paso 1: Crear Proyecto en Google Cloud

1. Ir a [Google Cloud Console](https://console.cloud.google.com/)
2. Crear un nuevo proyecto o seleccionar uno existente
3. Anotar el ID del proyecto

### Paso 2: Habilitar Google Calendar API

1. En Google Cloud Console, ir a **APIs & Services** > **Library**
2. Buscar "Google Calendar API"
3. Hacer clic en **Enable**

### Paso 3: Crear Service Account

1. Ir a **APIs & Services** > **Credentials**
2. Clic en **Create Credentials** > **Service Account**
3. Completar:
   - **Service account name**: `calendar-mcp-service`
   - **Service account ID**: Se genera automáticamente
   - **Description**: `Service account for MCP Calendar integration`
4. Clic en **Create and Continue**
5. En **Grant this service account access to project**, seleccionar rol **Editor** (o más específico)
6. Clic en **Continue** y luego **Done**

### Paso 4: Crear y Descargar Credenciales

1. En la lista de Service Accounts, hacer clic en la cuenta creada
2. Ir a la pestaña **Keys**
3. Clic en **Add Key** > **Create new key**
4. Seleccionar **JSON**
5. Descargar el archivo JSON
6. Guardar el archivo en un lugar seguro (ej: `~/credentials/google-calendar-service-account.json`)

### Paso 5: Compartir Calendario con Service Account

1. Abrir [Google Calendar](https://calendar.google.com/)
2. Ir a **Settings** (⚙️) > **Settings for my calendars**
3. Seleccionar el calendario que quieres usar (o crear uno nuevo)
4. Ir a **Share with specific people**
5. Clic en **Add people**
6. Agregar el email de la service account (formato: `nombre@proyecto.iam.gserviceaccount.com`)
7. Dar permisos: **Make changes to events**
8. Clic en **Send**

### Paso 6: Configurar Variables de Entorno

```bash
# Backend a usar
export CALENDAR_BACKEND=google_calendar

# Ruta al archivo JSON de service account
export GOOGLE_CALENDAR_SERVICE_ACCOUNT_FILE=/path/to/google-calendar-service-account.json

# ID del calendario (default: 'primary' para calendario principal)
export GOOGLE_CALENDAR_ID=primary

# Puerto del servidor (opcional)
export CALENDAR_SERVER_PORT=60000
```

### Paso 7: Instalar Dependencias

```bash
cd calendar-mcp-server
pip install -r requirements.txt
```

### Paso 8: Probar la Configuración

```bash
# Iniciar el servidor
./start.sh

# En otra terminal, probar
curl http://localhost:60000/health
```

## Opción 2: OAuth2 (Para uso personal)

### Paso 1-2: Igual que Service Account

### Paso 3: Crear Credenciales OAuth2

1. En Google Cloud Console, ir a **APIs & Services** > **Credentials**
2. Clic en **Create Credentials** > **OAuth client ID**
3. Si es la primera vez, configurar **OAuth consent screen**:
   - **User Type**: External (o Internal si es Google Workspace)
   - **App name**: `MCP Calendar`
   - **User support email**: Tu email
   - **Developer contact**: Tu email
   - **Scopes**: Agregar `https://www.googleapis.com/auth/calendar`
   - **Test users**: Agregar tu email
4. Crear **OAuth client ID**:
   - **Application type**: Desktop app
   - **Name**: `MCP Calendar Desktop`
5. Descargar el archivo JSON de credenciales

### Paso 4: Obtener Refresh Token

Ejecutar este script Python para obtener el refresh token:

```python
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import os

SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_refresh_token():
    creds = None
    token_file = 'token.pickle'
    
    if os.path.exists(token_file):
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)
    
    print(f"Refresh Token: {creds.refresh_token}")
    return creds.refresh_token

if __name__ == '__main__':
    get_refresh_token()
```

### Paso 5: Configurar Variables de Entorno

```bash
export CALENDAR_BACKEND=google_calendar
export GOOGLE_CALENDAR_CLIENT_ID=tu-client-id.apps.googleusercontent.com
export GOOGLE_CALENDAR_CLIENT_SECRET=tu-client-secret
export GOOGLE_CALENDAR_REFRESH_TOKEN=tu-refresh-token
export GOOGLE_CALENDAR_ID=primary
```

## Verificación

### Probar Crear una Reserva

```bash
curl -X POST http://localhost:60000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "create_booking",
      "arguments": {
        "customer_id": "test-123",
        "customer_name": "Test User",
        "date_iso": "2025-02-10",
        "start_time_iso": "2025-02-10T14:00:00Z",
        "end_time_iso": "2025-02-10T15:00:00Z"
      }
    }
  }'
```

### Verificar en Google Calendar

1. Abrir [Google Calendar](https://calendar.google.com/)
2. Buscar el evento "Reserva: Test User"
3. Verificar que se creó correctamente

## Troubleshooting

### Error: "Calendar not found"
- Verificar que el calendario esté compartido con la service account
- Verificar que `GOOGLE_CALENDAR_ID` sea correcto

### Error: "Insufficient permissions"
- Verificar que la service account tenga permisos de "Make changes to events"
- Verificar que Google Calendar API esté habilitada

### Error: "Invalid credentials"
- Verificar que el archivo JSON de service account sea válido
- Verificar que las variables de entorno estén configuradas correctamente

## Seguridad

⚠️ **IMPORTANTE**: 
- Nunca subas el archivo JSON de service account a repositorios públicos
- Agrega `*.json` a `.gitignore`
- Usa variables de entorno o un gestor de secretos en producción
- Limita los permisos de la service account al mínimo necesario
