# Integración con Backend Python

Este servicio se integra con el backend Python FastAPI para procesar mensajes de WhatsApp usando el asistente de IA.

## Flujo de Integración

```
WhatsApp → Baileys Service → Backend Python → LLM → Backend Python → Baileys Service → WhatsApp
```

## Endpoint del Backend

El servicio envía mensajes al endpoint:

```
POST /v1/channels/whatsapp/gateway/inbound
```

### Headers Requeridos

- `Content-Type: application/json`
- `X-API-Key: <api_key>` (si la autenticación está habilitada)

### Payload

```json
{
  "message_id": "msg-1234567890",
  "from_number": "5491112345678",
  "text": "Hola, quiero hacer una reserva",
  "timestamp_iso": "2025-01-08T10:00:00.000Z"
}
```

### Respuesta Esperada

```json
{
  "conversation_id": "whatsapp:5491112345678",
  "message_id": "msg-1234567890",
  "response_text": "¡Hola! Claro, te ayudo con tu reserva..."
}
```

## Autenticación

### Modo Desarrollo (sin autenticación)

Si `AI_ASSISTANTS_API_KEYS` no está configurado en el backend, el servicio puede usar `API_KEY=dev`.

### Modo Producción (con autenticación)

1. Configura `AI_ASSISTANTS_API_KEYS` en el backend:
   ```bash
   export AI_ASSISTANTS_API_KEYS="project1:key1,project2:key2"
   ```

2. Configura la misma API key en el servicio:
   ```bash
   export API_KEY=key1
   ```

## Configuración del Backend

El backend debe estar configurado para:

1. **Recibir mensajes de WhatsApp**: El endpoint `/v1/channels/whatsapp/gateway/inbound` ya existe
2. **Procesar con el asistente de IA**: El backend usa el `Orchestrator` para procesar mensajes
3. **Devolver respuestas**: El backend devuelve `response_text` en la respuesta

## Variables de Entorno

### Backend Python

```bash
# Opcional: Autenticación
AI_ASSISTANTS_API_KEYS=project1:key1

# Opcional: Webhook security (para producción)
WHATSAPP_WEBHOOK_SECRET=your-secret-key
```

### Baileys Service

```bash
# URL del backend
BACKEND_URL=http://localhost:8000

# API Key (debe coincidir con una de las keys del backend)
API_KEY=key1

# Directorio de autenticación
WHATSAPP_AUTH_DIR=./auth_info
```

## Pruebas

### 1. Verificar que el backend esté corriendo

```bash
curl http://localhost:8000/docs
```

### 2. Iniciar el servicio de WhatsApp

```bash
cd whatsapp-baileys-service
npm start
```

### 3. Escanear el código QR

- Abre WhatsApp en tu teléfono
- Ve a Configuración → Dispositivos vinculados
- Escanea el código QR que aparece en la terminal

### 4. Enviar un mensaje de prueba

Envía un mensaje desde WhatsApp al número conectado. El servicio debería:
1. Recibir el mensaje
2. Enviarlo al backend
3. Recibir la respuesta del backend
4. Enviar la respuesta a WhatsApp

## Solución de Problemas

### El backend no recibe mensajes

1. Verifica que el backend esté corriendo: `curl http://localhost:8000/health`
2. Verifica la URL en `BACKEND_URL`
3. Verifica la autenticación (API_KEY)
4. Revisa los logs del servicio

### El backend no responde

1. Verifica los logs del backend
2. Verifica que el endpoint `/v1/channels/whatsapp/gateway/inbound` esté disponible
3. Verifica que el LLM esté configurado correctamente

### Los mensajes no se envían a WhatsApp

1. Verifica que la conexión de WhatsApp esté activa
2. Revisa los logs del servicio
3. Verifica que el número de destino sea correcto
