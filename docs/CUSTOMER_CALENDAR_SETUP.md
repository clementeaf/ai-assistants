# Flujo de Configuración de Calendario para Clientes

Este documento describe el flujo completo para que un cliente nuevo pueda conectar su Google Calendar al sistema.

## 📋 Flujo Completo

### Escenario: Cliente Nuevo Contrata el Servicio

```
1. Cliente contrata el servicio
   └─> Cliente proporciona: nombre, email, teléfono (WhatsApp)

2. Admin ingresa datos del cliente en Admin-Frontend
   └─> Admin va a /clientes
   └─> Click en "Agregar Cliente"
   └─> Ingresa:
       - ID del Cliente (ej: cliente-123 o número de WhatsApp)
       - Email del Cliente (ej: cliente@ejemplo.com)
       - Nombre del Cliente (ej: Juan Pérez)

3. Admin conecta Google Calendar del cliente
   └─> Click en "Conectar" junto al cliente
   └─> Se genera URL de autorización OAuth2
   └─> Se abre ventana popup con Google OAuth2

4. Autorización OAuth2
   └─> Cliente (o admin con permisos) autoriza acceso
   └─> Google redirige al callback
   └─> Se guardan tokens encriptados en base de datos
   └─> Estado cambia a "Conectado"

5. Asistente IA puede usar el calendario
   └─> Cuando el cliente habla con el asistente
   └─> El sistema identifica el customer_id
   └─> El MCP Calendar Server usa los tokens del cliente
   └─> Las reservas se crean en el Google Calendar del cliente
```

## 🔧 Pasos Detallados

### Paso 1: Admin Agrega Cliente

1. Acceder a Admin-Frontend: `http://localhost:5173/clientes`
2. Click en "Agregar Cliente"
3. Completar formulario:
   - **ID del Cliente**: Identificador único (puede ser número de WhatsApp, email, o ID personalizado)
   - **Email del Cliente**: Email de Google del cliente (debe ser el mismo que usa para Google Calendar)
   - **Nombre del Cliente**: Nombre completo (opcional pero recomendado)
4. Click en "Conectar Calendario"

### Paso 2: Generar URL de Autorización

El sistema:
1. Guarda el email en `customer_memory`
2. Llama al MCP Calendar Server: `POST /oauth/authorize`
3. Obtiene URL de autorización OAuth2
4. Abre la URL en una ventana popup

### Paso 3: Autorización OAuth2

**Opción A: Cliente autoriza directamente**
- El cliente hace clic en la URL que se abre
- Inicia sesión con su cuenta de Google
- Autoriza el acceso a Google Calendar
- Google redirige al callback
- Los tokens se guardan automáticamente

**Opción B: Admin autoriza en nombre del cliente**
- El admin puede hacer clic en la URL
- Inicia sesión con la cuenta de Google del cliente
- Autoriza el acceso
- Los tokens se guardan

### Paso 4: Verificación

1. El estado cambia a "Conectado" en Admin-Frontend
2. Se muestra el email del calendario conectado
3. El asistente IA puede usar el calendario automáticamente

## 🎯 Uso por el Asistente IA

Una vez configurado, el asistente:

1. **Detecta el customer_id** del cliente que está hablando
2. **Pasa el customer_id** al MCP Calendar Server como header `X-Customer-Id`
3. **MCP Server identifica** qué calendario usar basado en el customer_id
4. **Usa los tokens OAuth2** del cliente para acceder a su Google Calendar
5. **Crea/modifica/elimina reservas** directamente en el calendario del cliente

## 📝 Ejemplo de Conversación

```
Cliente: "Hola, quiero reservar para mañana a las 3 PM"

Asistente: "¡Hola Juan! Perfecto, déjame verificar disponibilidad 
           en tu calendario para mañana a las 3 PM..."

[Asistente consulta Google Calendar del cliente usando customer_id]

Asistente: "¡Perfecto! El horario está disponible. 
           ¿Confirmas la reserva para mañana 15/01 a las 15:00?"

Cliente: "Sí, confirmo"

Asistente: "¡Reserva confirmada! Se ha creado en tu Google Calendar. 
           Recibirás un recordatorio automático."
```

## 🔐 Seguridad

- Los tokens OAuth2 se almacenan **encriptados** en la base de datos
- Cada cliente tiene sus **propios tokens** (multi-tenant)
- Los tokens se **refrescan automáticamente** cuando expiran
- El acceso es **solo lectura/escritura de calendario** (scope mínimo)

## 🚨 Troubleshooting

### El cliente no aparece en la lista
- Verificar que el cliente fue agregado correctamente
- Revisar que el `customer_id` es único

### No se puede conectar el calendario
- Verificar que el MCP Calendar Server está corriendo
- Verificar variables de entorno OAuth2:
  - `GOOGLE_OAUTH_CLIENT_ID`
  - `GOOGLE_OAUTH_CLIENT_SECRET`
  - `GOOGLE_OAUTH_REDIRECT_URI`

### El asistente no puede crear reservas
- Verificar que el calendario está "Conectado"
- Verificar que el `customer_id` coincide entre la conversación y el cliente configurado
- Revisar logs del MCP Calendar Server

## 📚 Configuración Requerida

### Variables de Entorno (MCP Calendar Server)

```bash
# OAuth2 Configuration
GOOGLE_OAUTH_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:60000/oauth/callback

# Token Storage
TOKEN_DB_PATH=tokens.db
TOKEN_ENCRYPTION_KEY=your-encryption-key

# Backend Type
CALENDAR_BACKEND=google_calendar
```

### Configuración en Google Cloud Console

1. Crear proyecto en Google Cloud Console
2. Habilitar Google Calendar API
3. Crear credenciales OAuth2 (tipo: Web application)
4. Configurar redirect URI: `http://localhost:60000/oauth/callback`
5. Copiar Client ID y Client Secret
