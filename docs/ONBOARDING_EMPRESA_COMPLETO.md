# Flujo Completo: Onboarding de Empresa que Contrata el Servicio

Este documento explica paso a paso qué ocurre cuando una empresa contrata el servicio de asistente IA.

## 📋 Escenario: Empresa "XXXX" Contrata el Servicio

### Paso 1: Empresa Contacta para Contratar

**Empresa "XXXX" te dice:**
> "Queremos integrar tu asistente IA en nuestro sistema para gestionar reservas"

### Paso 2: Tú (Admin) Configuras la Empresa

**En Admin-Frontend (`/clientes`):**

1. Haces clic en "Agregar Cliente"
2. Ingresas datos de la empresa:
   - **ID del Cliente**: `empresa-xxxx` (identificador único de la empresa)
   - **Email del Cliente**: `contacto@empresa-xxxx.com` (email de Google de la empresa)
   - **Nombre del Cliente**: `Empresa XXXX S.A.`
3. Haces clic en "Conectar Calendario"

### Paso 3: Sistema Genera DOS Links

**Link 1: Link de WhatsApp para Clientes de la Empresa**

Este link permite que los **clientes finales** de la empresa hagan clic y se abra WhatsApp con el asistente IA.

**Cómo se genera:**
- En Admin-Frontend (`/flujos`), seleccionas el flujo de reservas
- El sistema genera automáticamente:
  ```
  https://wa.me/56959263366?text=FLOW_RESERVA_INIT
  ```
  (Donde `56959263366` es el número de WhatsApp del asistente IA)

**Este link lo das a la empresa** para que lo ponga en su sitio web, botones, etc.

**Link 2: Link de OAuth2 para Autorizar Google Calendar**

Este link permite que la **empresa** autorice el acceso a su Google Calendar.

**Cómo se genera:**
- Cuando haces clic en "Conectar Calendario" en `/clientes`
- El sistema genera automáticamente:
  ```
  https://accounts.google.com/o/oauth2/v2/auth?
    client_id=TU_CLIENT_ID
    &redirect_uri=http://localhost:60000/oauth/callback
    &scope=https://www.googleapis.com/auth/calendar
    &state=empresa-xxxx-xyz123random
  ```

**Este link también se lo das a la empresa** para que autorice.

### Paso 4: Empresa Autoriza Google Calendar

**Qué ocurre:**

1. **Empresa hace clic en el link de OAuth2**
2. **Google muestra pantalla de consentimiento:**
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

3. **Empresa hace clic en "Permitir"**

4. **Google redirige automáticamente** al callback del MCP Calendar Server

5. **MCP Calendar Server:**
   - Intercambia código por tokens
   - **Guarda tokens encriptados automáticamente** en `tokens.db`
   - **NO necesita que la empresa te dé los tokens manualmente**

6. **Estado cambia a "Conectado"** en Admin-Frontend

### Paso 5: ¡Listo! Todo Funciona Automáticamente

**Ahora:**

1. **Clientes de la empresa** hacen clic en el link de WhatsApp
2. Se abre WhatsApp con el asistente IA
3. **Asistente IA usa automáticamente** el Google Calendar de la empresa
4. Las reservas se crean directamente en el calendario de la empresa

## ❌ Lo que NO ocurre

**NO necesitas que la empresa te dé los tokens manualmente.**

Cuando la empresa autoriza en Google:
- Google redirige al callback
- Los tokens se guardan **automáticamente** en la base de datos
- Todo es transparente para la empresa

## ✅ Resumen del Flujo

```
1. Empresa "XXXX" contrata servicio
   ↓
2. Tú configuras en Admin-Frontend:
   - ID: empresa-xxxx
   - Email: contacto@empresa-xxxx.com
   ↓
3. Sistema genera DOS links:
   a) Link WhatsApp: https://wa.me/56959263366?text=FLOW_RESERVA_INIT
      → Para clientes de la empresa
   b) Link OAuth2: https://accounts.google.com/o/oauth2/v2/auth?...
      → Para que la empresa autorice su Google Calendar
   ↓
4. Tú le das AMBOS links a la empresa:
   - "Este link de WhatsApp ponlo en tu sitio web para tus clientes"
   - "Este link de Google autoriza el acceso a tu calendario"
   ↓
5. Empresa:
   - Pone link de WhatsApp en su sitio web
   - Hace clic en link de OAuth2 y autoriza
   ↓
6. Sistema guarda tokens automáticamente
   ↓
7. ¡Listo! Asistente IA usa calendario de la empresa automáticamente
```

## 🔑 Puntos Clave

1. **Dos links diferentes:**
   - Link de WhatsApp → Para clientes finales de la empresa
   - Link de OAuth2 → Para que la empresa autorice su calendario

2. **Autorización es automática:**
   - La empresa autoriza una vez
   - Los tokens se guardan automáticamente
   - No necesitas que te den tokens manualmente

3. **Uso automático:**
   - Una vez autorizado, el asistente usa el calendario automáticamente
   - No hay pasos adicionales

## 📝 Checklist para Onboarding

- [ ] Configurar empresa en Admin-Frontend (`/clientes`)
- [ ] Generar link de WhatsApp para clientes de la empresa
- [ ] Generar link de OAuth2 para autorizar Google Calendar
- [ ] Enviar ambos links a la empresa
- [ ] Empresa autoriza Google Calendar (una vez)
- [ ] Verificar que estado sea "Conectado"
- [ ] ¡Listo! Asistente funciona automáticamente
