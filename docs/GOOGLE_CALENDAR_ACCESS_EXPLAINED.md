# Cómo el Sistema Accede al Google Calendar de tus Clientes

Este documento explica cómo funciona técnicamente el acceso al Google Calendar de cada cliente y cómo hacerlo viable para vender el servicio.

## 🔐 Dos Opciones para Acceder al Calendario de Otra Persona

### Opción 1: OAuth2 con Consentimiento del Usuario (RECOMENDADA) ✅

**Cómo funciona:**
1. El cliente autoriza una vez el acceso a su Google Calendar
2. Google proporciona tokens (access_token + refresh_token)
3. El sistema guarda estos tokens encriptados
4. El sistema puede acceder al calendario del cliente usando estos tokens
5. Los tokens se renuevan automáticamente cuando expiran

**Ventajas:**
- ✅ Seguro: El cliente controla qué acceso otorga
- ✅ Escalable: Funciona para cualquier número de clientes
- ✅ Multi-tenant: Cada cliente tiene sus propios tokens
- ✅ No requiere que el cliente comparta su calendario manualmente

**Desventajas:**
- ⚠️ Requiere autorización inicial del cliente (una vez)
- ⚠️ Si el cliente revoca el acceso, hay que re-autorizar

**Flujo de Autorización:**
```
1. Cliente proporciona su email: cliente@ejemplo.com
2. Admin genera URL de autorización OAuth2
3. Cliente hace clic en el link
4. Google muestra pantalla: "¿Permitir que AI Assistants acceda a tu Google Calendar?"
5. Cliente hace clic en "Permitir"
6. Google redirige al callback con código de autorización
7. Sistema intercambia código por tokens
8. Tokens se guardan encriptados en base de datos
9. Sistema puede usar calendario del cliente automáticamente
```

### Opción 2: Service Account con Calendario Compartido

**Cómo funciona:**
1. Creas un Service Account en Google Cloud
2. Cada cliente comparte su calendario con el email del Service Account
3. El sistema usa las credenciales del Service Account para acceder

**Ventajas:**
- ✅ No requiere autorización OAuth2 por cliente
- ✅ Más simple de configurar (una vez)

**Desventajas:**
- ❌ Cada cliente debe compartir su calendario manualmente
- ❌ Menos seguro: El Service Account tiene acceso a todos los calendarios compartidos
- ❌ No escalable: Requiere acción manual de cada cliente

## 🎯 Implementación Actual: OAuth2 Multi-Usuario

El sistema actual usa **Opción 1 (OAuth2)** porque es:
- Más seguro
- Más escalable
- Mejor experiencia para el cliente

## 📋 Proceso Completo para Vender el Servicio

### Paso 1: Configuración Inicial (Una vez)

1. **Crear Proyecto en Google Cloud Console**
   ```
   https://console.cloud.google.com/
   ```

2. **Habilitar Google Calendar API**
   - Ir a "APIs & Services" > "Library"
   - Buscar "Google Calendar API"
   - Click en "Enable"

3. **Crear Credenciales OAuth2**
   - Ir a "APIs & Services" > "Credentials"
   - Click en "Create Credentials" > "OAuth client ID"
   - Tipo: "Web application"
   - Name: "AI Assistants Calendar Access"
   - Authorized redirect URIs: `http://localhost:60000/oauth/callback`
     (En producción: `https://tu-dominio.com/oauth/callback`)

4. **Configurar Variables de Entorno**
   ```bash
   # En el MCP Calendar Server
   GOOGLE_OAUTH_CLIENT_ID=tu-client-id.apps.googleusercontent.com
   GOOGLE_OAUTH_CLIENT_SECRET=tu-client-secret
   GOOGLE_OAUTH_REDIRECT_URI=http://localhost:60000/oauth/callback
   TOKEN_ENCRYPTION_KEY=tu-clave-de-encriptacion-segura
   ```

### Paso 2: Onboarding de Cliente Nuevo

**Escenario: Cliente quiere contratar el servicio**

1. **Cliente proporciona:**
   - Email de Google (ej: cliente@ejemplo.com)
   - Nombre
   - Teléfono (WhatsApp)

2. **Admin configura en sistema:**
   - Va a Admin-Frontend > Clientes
   - Agrega cliente con:
     - ID: número de WhatsApp o ID único
     - Email: cliente@ejemplo.com
     - Nombre: Nombre del cliente

3. **Admin genera link de autorización:**
   - Click en "Conectar"
   - Sistema genera URL de autorización OAuth2
   - Admin puede:
     - Abrir link ahora (si tiene acceso a la cuenta del cliente)
     - Copiar link y enviarlo al cliente por WhatsApp/email

4. **Cliente autoriza acceso:**
   - Cliente recibe link por WhatsApp/email
   - Cliente hace clic en el link
   - Google muestra: "¿Permitir que AI Assistants acceda a tu Google Calendar?"
   - Cliente hace clic en "Permitir"
   - Google redirige y los tokens se guardan automáticamente

5. **Sistema listo para usar:**
   - Estado cambia a "Conectado"
   - Asistente IA puede crear/modificar reservas en el calendario del cliente
   - Todo automático desde ahora

### Paso 3: Uso Diario

Una vez configurado, el flujo es automático:

```
Cliente: "Quiero reservar para mañana a las 3 PM"

Asistente: [Consulta Google Calendar del cliente]
           "¡Perfecto! El horario está disponible. ¿Confirmas?"

Cliente: "Sí"

Asistente: [Crea evento en Google Calendar del cliente]
           "¡Reserva confirmada! Se creó en tu Google Calendar."
```

## 🔒 Seguridad

### Tokens Encriptados
- Los tokens OAuth2 se almacenan **encriptados** en la base de datos
- Cada cliente tiene sus **propios tokens** (aislamiento completo)
- Los tokens se **refrescan automáticamente** cuando expiran

### Permisos Mínimos
- El sistema solo solicita acceso a **Google Calendar** (scope mínimo)
- No accede a otros datos de Google (Gmail, Drive, etc.)
- El cliente puede **revocar el acceso** en cualquier momento desde su cuenta de Google

### Multi-Tenant
- Cada cliente tiene su propio `customer_id`
- Los tokens están asociados al `customer_id`
- No hay riesgo de que un cliente acceda al calendario de otro

## 🚀 Escalabilidad

### ¿Cuántos clientes puedo tener?
- **Ilimitado**: Cada cliente tiene sus propios tokens
- **Sin límites de Google**: Google Calendar API permite 1,000,000 requests/día
- **Rendimiento**: El sistema maneja múltiples clientes simultáneamente

### ¿Qué pasa si tengo 100 clientes?
- Cada cliente autoriza una vez
- Los tokens se guardan encriptados
- El sistema identifica qué calendario usar basado en `customer_id`
- Todo funciona automáticamente

## 💰 Modelo de Negocio

### Opción A: Servicio Mensual
- Cliente paga mensualidad
- Incluye configuración inicial (una vez)
- Asistente IA gestiona reservas en su calendario

### Opción B: Pago por Uso
- Cliente paga por cada reserva creada
- Configuración inicial incluida

### Opción C: Licencia Anual
- Cliente paga anualidad
- Incluye todas las reservas del año

## 📝 Checklist para Vender el Servicio

- [ ] Configurar Google Cloud Console
- [ ] Habilitar Google Calendar API
- [ ] Crear credenciales OAuth2
- [ ] Configurar variables de entorno
- [ ] Probar con un cliente de prueba
- [ ] Documentar proceso para clientes
- [ ] Crear materiales de marketing (ej: "Conecta tu Google Calendar en 2 minutos")

## 🎯 Ventajas Competitivas

1. **Automatización Total**: Una vez configurado, todo es automático
2. **Integración Nativa**: Las reservas aparecen directamente en Google Calendar
3. **Recordatorios Automáticos**: Google Calendar envía recordatorios
4. **Sincronización**: Disponible en todos los dispositivos del cliente
5. **Multi-Dispositivo**: Cliente ve reservas en móvil, tablet, desktop

## ❓ Preguntas Frecuentes

### ¿El cliente puede revocar el acceso?
Sí, en cualquier momento desde su cuenta de Google. Si lo hace, el sistema detectará que el token expiró y pedirá re-autorización.

### ¿Qué pasa si el cliente cambia su email de Google?
Necesita re-configurar con el nuevo email. El sistema detectará que el calendario anterior ya no es válido.

### ¿Puedo acceder a otros datos del cliente?
No. El sistema solo solicita acceso a Google Calendar. No puede acceder a Gmail, Drive, Fotos, etc.

### ¿Es seguro almacenar tokens?
Sí. Los tokens se almacenan encriptados usando Fernet (cifrado simétrico). Solo el sistema puede desencriptarlos.

### ¿Qué pasa si tengo muchos clientes?
El sistema escala automáticamente. Cada cliente tiene sus propios tokens y no hay límite de clientes.

## 🔧 Troubleshooting

### Error: "OAuth2 not configured"
- Verificar que las variables de entorno están configuradas
- Verificar que el MCP Calendar Server está corriendo

### Error: "Invalid redirect URI"
- Verificar que el redirect URI en Google Cloud Console coincide con `GOOGLE_OAUTH_REDIRECT_URI`
- En producción, usar HTTPS

### Error: "Token expired"
- Los tokens se renuevan automáticamente
- Si falla, el cliente necesita re-autorizar

### Cliente no puede autorizar
- Verificar que el link de autorización es correcto
- Verificar que el cliente está usando el email correcto de Google
- Verificar que el cliente tiene acceso a Google Calendar
