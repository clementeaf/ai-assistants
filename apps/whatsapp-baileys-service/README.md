# WhatsApp Baileys Service

Servicio Node.js que usa Baileys para conectarse a WhatsApp Web y se integra con el backend Python FastAPI.

## Características

- ✅ Conexión a WhatsApp Web usando Baileys
- ✅ Autenticación mediante código QR
- ✅ Recepción de mensajes en tiempo real
- ✅ Integración con backend Python FastAPI
- ✅ Envío automático de respuestas
- ✅ Reconexión automática
- ✅ Persistencia de sesión

## Instalación

```bash
cd whatsapp-baileys-service
npm install
```

## Configuración

Variables de entorno:

- `BACKEND_URL` - URL del backend Python (default: `http://localhost:8000`)
- `API_KEY` - API Key para autenticación con el backend (default: `dev`)
- `WHATSAPP_AUTH_DIR` - Directorio para guardar información de autenticación (default: `./auth_info`)
- `PORT` - Puerto del servicio (default: `60007`)

### Archivo `.env` (opcional)

```bash
BACKEND_URL=http://localhost:8000
API_KEY=dev
WHATSAPP_AUTH_DIR=./auth_info
```

## Uso

### Iniciar el servicio

```bash
npm start
```

O directamente:

```bash
node index.js
```

### Primera conexión

1. Ejecuta el servicio
2. Escanea el código QR que aparece en la terminal con WhatsApp
3. La sesión se guardará automáticamente en `auth_info/`
4. En futuras ejecuciones, se conectará automáticamente sin necesidad de escanear el QR

## Flujo de Mensajes

1. **Mensaje entrante en WhatsApp** → Baileys lo detecta
2. **Baileys** → Envía al backend Python vía `POST /v1/channels/whatsapp/gateway/inbound`
3. **Backend Python** → Procesa el mensaje con el asistente de IA
4. **Backend Python** → Devuelve la respuesta
5. **Baileys** → Envía la respuesta de vuelta a WhatsApp

## Integración con Backend

El servicio envía mensajes al endpoint:

```
POST /v1/channels/whatsapp/gateway/inbound
```

Con el siguiente payload:

```json
{
  "message_id": "msg-123456",
  "from_number": "5491112345678",
  "text": "Hola, quiero hacer una reserva",
  "timestamp_iso": "2025-01-08T10:00:00Z"
}
```

El backend responde con:

```json
{
  "conversation_id": "whatsapp:5491112345678",
  "message_id": "msg-123456",
  "response_text": "¡Hola! Claro, te ayudo con tu reserva..."
}
```

## Estructura de Archivos

```
whatsapp-baileys-service/
├── index.js              # Servicio principal
├── package.json          # Dependencias
├── README.md            # Documentación
├── .gitignore           # Archivos a ignorar
└── auth_info/           # Información de autenticación (generado)
```

## Solución de Problemas

### El código QR no aparece

- Verifica que no haya una sesión guardada en `auth_info/`
- Elimina el directorio `auth_info/` y reinicia el servicio

### No se conecta al backend

- Verifica que el backend esté corriendo en `BACKEND_URL`
- Verifica que la `API_KEY` sea correcta
- Revisa los logs del servicio

### Mensajes no se envían

- Verifica que el backend esté respondiendo correctamente
- Revisa los logs del servicio y del backend
- Verifica que el número de WhatsApp esté en formato correcto

## Notas

- La primera vez que ejecutes el servicio, necesitarás escanear el código QR
- La sesión se guarda automáticamente, no necesitarás escanear el QR en futuras ejecuciones
- Si cierras sesión desde WhatsApp, necesitarás escanear el QR nuevamente
- El servicio se reconecta automáticamente si se pierde la conexión
