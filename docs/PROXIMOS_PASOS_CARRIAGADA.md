# Próximos Pasos para Probar con carriagada@grupobanados.com

## ✅ Ya Configurado:
- ✅ Google Calendar API habilitada
- ✅ Credenciales OAuth2 extraídas del JSON
- ✅ Archivo `.env` del MCP Calendar Server actualizado con credenciales
- ✅ Clave de encriptación generada

## 📋 Pasos Siguientes:

### Paso 1: Agregar Redirect URI en Google Cloud Console

**IMPORTANTE**: Debes agregar el redirect URI en Google Cloud Console:

1. Ve a Google Cloud Console > APIs & Services > Credentials
2. Haz clic en "Clemente" (tu credencial OAuth2)
3. Busca la sección "URI de redirección autorizados"
4. Haz clic en "+ Agregar URI"
5. Agrega: `http://localhost:60000/oauth/callback`
6. Haz clic en "Guardar"

**⚠️ Sin este paso, la autorización fallará.**

### Paso 2: Reiniciar MCP Calendar Server

El servidor debe usar `main_multi_user.py` (tiene soporte OAuth2):

```bash
cd mcp-servers/calendar-mcp-server
# Detener el servidor actual si está corriendo (Ctrl+C)
python3 main_multi_user.py
```

Deberías ver que el servidor inicia correctamente.

### Paso 3: Verificar que el Backend Puede Conectarse

**En el `.env` del backend (raíz del proyecto):**
```bash
AI_ASSISTANTS_MCP_CALENDAR_URL=http://localhost:60000
```

Ya está configurado ✅

### Paso 4: Iniciar Backend (si no está corriendo)

```bash
cd apps/backend
python3 run_server.py
```

### Paso 5: Agregar Empresa en Admin-Frontend

1. Abre: `http://localhost:5173/clientes`
2. Haz clic en "Agregar Cliente"
3. Completa:
   - **ID del Cliente**: `empresa-carriagada`
   - **Email del Cliente**: `carriagada@grupobanados.com`
   - **Nombre del Cliente**: `Carriagada - Grupo Bañados`
4. Haz clic en "Conectar Calendario"

### Paso 6: Obtener Link de OAuth2

Después de hacer clic en "Conectar Calendario":
- El sistema te preguntará: "¿Quieres abrir la URL de autorización ahora?"
- Si eliges "No", se copiará el link al portapapeles
- **Este link se lo das a la empresa** (o lo abres tú si tienes acceso a la cuenta)

### Paso 7: Autorizar Google Calendar

1. Abre el link de OAuth2 en el navegador
2. Inicia sesión con `carriagada@grupobanados.com`
3. Google mostrará: "¿Permitir que AI Assistants acceda a tu Google Calendar?"
4. Haz clic en "Permitir"
5. Google redirigirá automáticamente a `http://localhost:60000/oauth/callback`
6. Los tokens se guardarán automáticamente en `tokens.db`

### Paso 8: Verificar Estado

1. En Admin-Frontend (`/clientes`), verifica:
   - Estado: "Conectado" ✅
   - Calendar Email: `carriagada@grupobanados.com`

### Paso 9: Probar que Funciona

1. Usa el asistente IA (Chat del frontend o WhatsApp)
2. Pide una reserva: "Quiero reservar para mañana a las 3 PM"
3. El asistente debe consultar el Google Calendar de `carriagada@grupobanados.com`
4. Las reservas se crearán en ese calendario

## 🔍 Verificación Rápida

```bash
# 1. Verificar MCP Calendar Server
curl http://localhost:60000/health

# 2. Probar endpoint de autorización
curl -X POST http://localhost:60000/oauth/authorize \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "test-123"}'
```

Deberías recibir una respuesta con `authorization_url`.

## ⚠️ Si Algo Falla

### Error: "redirect_uri_mismatch"
- Verifica que agregaste `http://localhost:60000/oauth/callback` en Google Cloud Console
- El URI debe ser exactamente igual (sin espacios, sin trailing slash)

### Error: "OAuth2 not configured"
- Verifica que el MCP Calendar Server esté usando `main_multi_user.py`
- Verifica que el archivo `.env` tenga todas las variables configuradas
- Reinicia el servidor

### El link no se genera
- Verifica que el backend esté corriendo
- Verifica que `AI_ASSISTANTS_MCP_CALENDAR_URL=http://localhost:60000` esté en `.env`
- Revisa los logs del backend
