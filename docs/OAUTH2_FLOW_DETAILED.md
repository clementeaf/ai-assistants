# Flujo Detallado: OAuth2 para Conectar Google Calendar

Este documento explica paso a paso qué ocurre cuando el admin genera el link OAuth2 y la empresa autoriza.

## 🔄 Flujo Completo Paso a Paso

### Paso 1: Admin Ingresa Datos de la Empresa

**En Admin-Frontend (`/clientes`):**

1. Admin hace clic en "Agregar Cliente"
2. Completa formulario:
   - **ID del Cliente**: `empresa-abc-123` (identificador único de la empresa)
   - **Email del Cliente**: `contacto@empresa-abc.com` (email de Google de la empresa)
   - **Nombre del Cliente**: `Empresa ABC S.A.`
3. Admin hace clic en "Conectar Calendario"

### Paso 2: Sistema Genera URL de Autorización

**Qué ocurre técnicamente:**

1. **Frontend** → Llama a `POST /v1/customer-calendars/connect`
   ```json
   {
     "customer_id": "empresa-abc-123",
     "customer_email": "contacto@empresa-abc.com",
     "customer_name": "Empresa ABC S.A."
   }
   ```

2. **Backend** (`customer_calendars.py`):
   - Guarda email en `customer_memory` (base de datos)
   - Llama al **MCP Calendar Server**: `POST http://localhost:60000/oauth/authorize`
   - Pasa `customer_id`: `"empresa-abc-123"`

3. **MCP Calendar Server** (`oauth2_handler.py`):
   - Genera un `state` único: `"empresa-abc-123-xyz123random"`
   - Guarda en memoria: `state → customer_id`
   - Construye URL de Google OAuth2:
     ```
     https://accounts.google.com/o/oauth2/v2/auth?
       client_id=TU_CLIENT_ID.apps.googleusercontent.com
       &redirect_uri=http://localhost:60000/oauth/callback
       &scope=https://www.googleapis.com/auth/calendar
       &response_type=code
       &access_type=offline
       &prompt=consent
       &state=empresa-abc-123-xyz123random
     ```

4. **Backend** retorna al Frontend:
   ```json
   {
     "customer_id": "empresa-abc-123",
     "customer_email": "contacto@empresa-abc.com",
     "customer_name": "Empresa ABC S.A.",
     "calendar_connected": false,
     "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?...",
     "shareable_link": "https://accounts.google.com/o/oauth2/v2/auth?..."
   }
   ```

### Paso 3: Admin Obtiene el Link

**En Admin-Frontend:**

El sistema muestra dos opciones:

**Opción A: Abrir Ahora**
- Se abre popup con la URL de Google OAuth2
- Admin puede autorizar si tiene acceso a la cuenta de Google de la empresa

**Opción B: Copiar Link**
- Se copia la URL al portapapeles
- Admin puede enviar el link a la empresa por:
  - Email
  - WhatsApp
  - Slack
  - Cualquier medio de comunicación

### Paso 4: Empresa Hace Clic en el Link

**Qué ve la empresa:**

1. Se abre Google en el navegador
2. Google muestra pantalla de login (si no está logueado)
3. Empresa inicia sesión con su cuenta de Google: `contacto@empresa-abc.com`
4. Google muestra pantalla de consentimiento:
   ```
   ┌─────────────────────────────────────────┐
   │  AI Assistants quiere acceder a tu      │
   │  cuenta de Google                       │
   │                                         │
   │  Ver y gestionar tus eventos de        │
   │  Google Calendar                        │
   │                                         │
   │  [Cancelar]  [Permitir]                │
   └─────────────────────────────────────────┘
   ```

### Paso 5: Empresa Autoriza

**Qué ocurre técnicamente:**

1. Empresa hace clic en **"Permitir"**

2. **Google redirige** al callback:
   ```
   http://localhost:60000/oauth/callback?
     code=4/0AeanS...&
     state=empresa-abc-123-xyz123random
   ```

3. **MCP Calendar Server** (`oauth2_handler.py`):
   - Recibe `code` y `state`
   - Verifica `state` → obtiene `customer_id`: `"empresa-abc-123"`
   - Intercambia `code` por tokens:
     ```python
     # Llama a Google Token API
     POST https://oauth2.googleapis.com/token
     {
       "code": "4/0AeanS...",
       "client_id": "TU_CLIENT_ID",
       "client_secret": "TU_CLIENT_SECRET",
       "redirect_uri": "http://localhost:60000/oauth/callback",
       "grant_type": "authorization_code"
     }
     ```
   - Google responde con tokens:
     ```json
     {
       "access_token": "ya29.a0AfH6SMC...",
       "refresh_token": "1//0gabc123...",
       "expires_in": 3600,
       "token_type": "Bearer"
     }
     ```

4. **MCP Calendar Server** (`token_store.py`):
   - Encripta los tokens usando Fernet
   - Guarda en base de datos SQLite (`tokens.db`):
     ```sql
     INSERT INTO oauth_tokens (
       customer_id,
       access_token,      -- Encriptado
       refresh_token,     -- Encriptado
       token_expiry,
       calendar_email,
       created_at,
       updated_at
     ) VALUES (
       'empresa-abc-123',
       'gAAAAABh...',     -- Token encriptado
       'gAAAAABi...',     -- Refresh token encriptado
       '2025-01-20T12:00:00Z',
       'contacto@empresa-abc.com',
       '2025-01-15T10:00:00Z',
       '2025-01-15T10:00:00Z'
     )
     ```

5. **Google redirige** a página de éxito (configurable):
   ```
   https://calendar.google.com
   ```

### Paso 6: Sistema Listo para Usar

**Estado final:**

- ✅ `customer_id`: `"empresa-abc-123"`
- ✅ `customer_email`: `"contacto@empresa-abc.com"`
- ✅ Tokens guardados encriptados en `tokens.db`
- ✅ Estado: `calendar_connected: true`

### Paso 7: Asistente IA Usa el Calendario Automáticamente

**Cuando la empresa usa el asistente:**

1. Cliente de la empresa escribe: `"Quiero reservar para mañana a las 3 PM"`

2. **Sistema identifica** `customer_id` de la conversación:
   - Puede ser el número de WhatsApp
   - O un ID único asociado a la empresa

3. **Asistente IA** llama a `get_available_slots`:
   ```python
   # En router_graph.py
   slots_out = get_available_slots(GetAvailableSlotsInput(date_iso="2025-01-16"))
   ```

4. **Booking Tool** → **MCP Calendar Adapter**:
   ```python
   # En mcp_calendar_adapter.py
   adapter.get_available_slots(
       date_iso="2025-01-16",
       customer_id="empresa-abc-123"  # ← Se pasa automáticamente
   )
   ```

5. **MCP Calendar Adapter** → **MCP Calendar Server**:
   ```http
   POST http://localhost:60000/mcp
   Headers:
     X-Customer-Id: empresa-abc-123  ← Identifica qué calendario usar
   Body:
     {
       "jsonrpc": "2.0",
       "method": "tools/call",
       "params": {
         "name": "get_available_slots",
         "arguments": {"date_iso": "2025-01-16"}
       }
     }
   ```

6. **MCP Calendar Server**:
   - Lee header `X-Customer-Id`: `"empresa-abc-123"`
   - Busca tokens en `tokens.db` para ese `customer_id`
   - Desencripta tokens
   - Usa tokens para autenticar con Google Calendar API:
     ```python
     credentials = Credentials(
         token=decrypted_access_token,
         refresh_token=decrypted_refresh_token,
         ...
     )
     service = build("calendar", "v3", credentials=credentials)
     events = service.events().list(
         calendarId="primary",
         timeMin="2025-01-16T00:00:00Z",
         timeMax="2025-01-16T23:59:59Z"
     ).execute()
     ```
   - Retorna horarios disponibles

7. **Asistente IA** responde:
   ```
   "¡Perfecto! El horario está disponible. ¿Confirmas la reserva?"
   ```

## 🔐 Seguridad

### Tokens Encriptados
- Los tokens se almacenan **encriptados** usando Fernet (cifrado simétrico)
- Solo el MCP Calendar Server puede desencriptarlos
- La clave de encriptación se configura en `TOKEN_ENCRYPTION_KEY`

### Aislamiento por Cliente
- Cada empresa tiene sus **propios tokens**
- No hay riesgo de que una empresa acceda al calendario de otra
- El `customer_id` identifica únicamente a cada empresa

### Renovación Automática
- Los `access_token` expiran después de 1 hora
- El sistema usa `refresh_token` para obtener nuevos tokens automáticamente
- El cliente no necesita re-autorizar (a menos que revoque el acceso)

## 📋 Resumen Visual

```
┌─────────────┐
│   Admin     │
│ Frontend    │
└──────┬──────┘
       │ 1. Ingresa datos empresa
       │    customer_id: "empresa-abc-123"
       │    email: "contacto@empresa-abc.com"
       ▼
┌─────────────────────┐
│   Backend API       │
│ /customer-calendars │
└──────┬──────────────┘
       │ 2. Llama MCP Calendar Server
       ▼
┌─────────────────────┐
│ MCP Calendar Server │
│ /oauth/authorize    │
└──────┬──────────────┘
       │ 3. Genera URL OAuth2
       │    con state único
       ▼
┌─────────────────────┐
│   Admin Frontend    │
│   (muestra link)    │
└──────┬──────────────┘
       │ 4. Admin envía link a empresa
       ▼
┌─────────────────────┐
│     Empresa         │
│  (hace clic link)   │
└──────┬──────────────┘
       │ 5. Google muestra consentimiento
       ▼
┌─────────────────────┐
│      Google         │
│  (empresa autoriza) │
└──────┬──────────────┘
       │ 6. Redirige con code
       ▼
┌─────────────────────┐
│ MCP Calendar Server │
│ /oauth/callback     │
└──────┬──────────────┘
       │ 7. Intercambia code por tokens
       │ 8. Guarda tokens encriptados
       ▼
┌─────────────────────┐
│   tokens.db         │
│ (tokens encriptados)│
└─────────────────────┘

[ASISTENTE IA USA CALENDARIO AUTOMÁTICAMENTE]
       │
       │ Cuando empresa usa asistente:
       │ customer_id → tokens → Google Calendar API
       ▼
┌─────────────────────┐
│  Google Calendar     │
│  de la Empresa       │
└─────────────────────┘
```

## ❓ Preguntas Frecuentes

### ¿El admin necesita acceso a la cuenta de Google de la empresa?
No necesariamente. El admin puede:
- Abrir el link él mismo (si tiene acceso)
- O enviar el link a la empresa para que autorice

### ¿Qué pasa si la empresa no autoriza?
El calendario queda como "No conectado". El asistente no puede usar el calendario hasta que se autorice.

### ¿La empresa puede revocar el acceso?
Sí, en cualquier momento desde su cuenta de Google. Si lo hace, el sistema detectará que los tokens expiraron y pedirá re-autorización.

### ¿Cuánto tiempo duran los tokens?
- `access_token`: 1 hora (se renueva automáticamente)
- `refresh_token`: Indefinido (hasta que se revoque)

### ¿Qué pasa si tengo 100 empresas?
Cada empresa autoriza una vez. Los tokens se guardan encriptados en `tokens.db`. El sistema identifica qué calendario usar basado en `customer_id`. Todo funciona automáticamente.
