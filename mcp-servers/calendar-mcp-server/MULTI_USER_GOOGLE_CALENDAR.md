# Sistema Multi-Usuario para Google Calendar

## Objetivo

Permitir que cada usuario conecte su propia cuenta de Google Calendar a través de un flujo OAuth2, de manera que cada asistente IA pueda acceder al calendario personal del usuario.

## Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│  Usuario 1 (customer_id: user-123)                      │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Asistente IA                                     │  │
│  │  └─> MCP Calendar Server                          │  │
│  │      └─> Google Calendar Backend                  │  │
│  │          └─> Token: user-123-token (OAuth2)      │  │
│  │              └─> Calendar: user-123@gmail.com     │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  Usuario 2 (customer_id: user-456)                      │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Asistente IA                                     │  │
│  │  └─> MCP Calendar Server                          │  │
│  │      └─> Google Calendar Backend                  │  │
│  │          └─> Token: user-456-token (OAuth2)      │  │
│  │              └─> Calendar: user-456@gmail.com    │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Componentes Necesarios

### 1. Token Store
Almacenar tokens OAuth2 de forma segura por usuario:
- `customer_id` como clave
- Tokens encriptados
- Refresh tokens para renovación automática

### 2. OAuth2 Flow
- Endpoint para iniciar autorización: `/oauth/authorize`
- Callback para recibir código: `/oauth/callback`
- Endpoint para verificar estado: `/oauth/status/{customer_id}`

### 3. Backend Dinámico
- El backend debe obtener el token del usuario actual
- Usar el token para autenticar con Google Calendar API
- Refrescar tokens automáticamente cuando expiren

### 4. Integración con Backend AI
- El backend debe pasar el `customer_id` al MCP Calendar Server
- El MCP Server identifica al usuario y usa su token

## Flujo de Conexión

```
1. Usuario inicia conversación con asistente
   └─> customer_id: "user-123"

2. Usuario dice: "Conecta mi Google Calendar"
   └─> Backend AI detecta intención
   └─> Llama a MCP: /oauth/authorize?customer_id=user-123

3. MCP Server genera URL de autorización
   └─> Redirige a Google OAuth2
   └─> Usuario autoriza acceso

4. Google redirige a callback
   └─> /oauth/callback?code=xxx&state=user-123
   └─> MCP Server intercambia código por tokens
   └─> Almacena tokens encriptados

5. Usuario puede usar su calendario
   └─> Backend AI llama a MCP con customer_id
   └─> MCP Server usa token del usuario
   └─> Accede a su Google Calendar
```

## Seguridad

- Tokens encriptados en almacenamiento
- HTTPS obligatorio para OAuth2
- Tokens con scope mínimo necesario
- Refresh automático de tokens expirados
- Validación de customer_id en cada request

## Variables de Entorno

```bash
# OAuth2 Configuration
GOOGLE_OAUTH_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret
GOOGLE_OAUTH_REDIRECT_URI=https://your-domain.com/oauth/callback

# Token Storage
TOKEN_STORAGE_TYPE=sqlite  # o 'encrypted_file', 'database'
TOKEN_DB_PATH=tokens.db
TOKEN_ENCRYPTION_KEY=your-encryption-key  # Para encriptar tokens

# Server
CALENDAR_SERVER_PORT=60000
CALENDAR_SERVER_BASE_URL=https://your-domain.com
```

## Endpoints Adicionales

### POST /oauth/authorize
Inicia el flujo OAuth2 para un usuario.

**Request:**
```json
{
  "customer_id": "user-123"
}
```

**Response:**
```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?...",
  "state": "user-123-random-state"
}
```

### GET /oauth/callback
Recibe el código de autorización de Google.

**Query Params:**
- `code`: Código de autorización
- `state`: Estado (incluye customer_id)

**Response:**
```json
{
  "success": true,
  "customer_id": "user-123",
  "message": "Google Calendar conectado exitosamente"
}
```

### GET /oauth/status/{customer_id}
Verifica si un usuario tiene Google Calendar conectado.

**Response:**
```json
{
  "connected": true,
  "customer_id": "user-123",
  "calendar_email": "user-123@gmail.com",
  "expires_at": "2025-12-31T23:59:59Z"
}
```

### POST /oauth/disconnect
Desconecta Google Calendar de un usuario.

**Request:**
```json
{
  "customer_id": "user-123"
}
```

## Modificaciones al Backend AI

El backend AI debe pasar el `customer_id` en cada request al MCP:

```python
# En router_graph.py o donde se llame al MCP
customer_id = conversation.customer_id

# Al llamar al MCP, incluir customer_id
mcp_response = client.post(
    f"{mcp_url}/mcp",
    json={
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "create_booking",
            "arguments": {
                "customer_id": customer_id,  # Para identificar al usuario
                # ... otros argumentos
            }
        }
    }
)
```

## Implementación

1. **Token Store Module** (`token_store.py`)
   - Almacenar/recuperar tokens por customer_id
   - Encriptación de tokens sensibles
   - Refresh automático

2. **OAuth2 Module** (`oauth2_handler.py`)
   - Generar URLs de autorización
   - Manejar callback
   - Intercambiar código por tokens

3. **Google Calendar Backend Modificado**
   - Aceptar customer_id en cada operación
   - Obtener token del usuario
   - Usar token para autenticar

4. **Endpoints OAuth2** (en `main.py`)
   - `/oauth/authorize`
   - `/oauth/callback`
   - `/oauth/status/{customer_id}`
   - `/oauth/disconnect`
