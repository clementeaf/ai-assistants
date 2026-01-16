# Iniciar Servidores para Probar con carriagada@grupobanados.com

## ✅ Configuración Completada:
- ✅ Google Calendar API habilitada
- ✅ Credenciales OAuth2 configuradas en `.env`
- ✅ Redirect URI agregado en Google Cloud Console: `http://localhost:60000/oauth/callback`
- ✅ `email-validator` instalado
- ✅ `AI_ASSISTANTS_MCP_CALENDAR_URL` configurado en `.env` del backend

## 🚀 Pasos para Iniciar:

### Paso 1: Iniciar MCP Calendar Server

Abre una terminal y ejecuta:

```bash
cd mcp-servers/calendar-mcp-server
python3 main_multi_user.py
```

Deberías ver algo como:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:60000
```

**⚠️ Deja esta terminal abierta.**

### Paso 2: Iniciar Backend Server

Abre **otra terminal** y ejecuta:

```bash
cd apps/backend
python3 run_server.py
```

Deberías ver algo como:
```
✅ Cargado .env desde: ...
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:9000
```

**⚠️ Deja esta terminal abierta también.**

### Paso 3: Verificar que Ambos Servidores Están Corriendo

En una tercera terminal, ejecuta:

```bash
# Verificar MCP Calendar Server
curl http://localhost:60000/health

# Verificar Backend
curl http://localhost:9000/health
```

Ambos deberían responder con `{"status": "ok"}` o similar.

### Paso 4: Agregar Empresa en Admin-Frontend

1. Abre: `http://localhost:5173/clientes`
2. Haz clic en "Agregar Cliente"
3. Completa:
   - **ID del Cliente**: `empresa-carriagada`
   - **Email del Cliente**: `carriagada@grupobanados.com`
   - **Nombre del Cliente**: `Carriagada - Grupo Bañados`
4. Haz clic en "Conectar Calendario"

### Paso 5: Obtener Link de OAuth2

Después de hacer clic en "Conectar Calendario":
- El sistema te mostrará un link de autorización
- Puedes abrirlo directamente o copiarlo
- **Este link se lo das a la empresa** (o lo abres tú si tienes acceso)

### Paso 6: Autorizar Google Calendar

1. Abre el link de OAuth2 en el navegador
2. Inicia sesión con `carriagada@grupobanados.com`
3. Google mostrará: "¿Permitir que AI Assistants acceda a tu Google Calendar?"
4. Haz clic en "Permitir"
5. Google redirigirá automáticamente
6. Los tokens se guardarán automáticamente en `tokens.db`

### Paso 7: Verificar Estado

1. En Admin-Frontend (`/clientes`), verifica:
   - Estado: "Conectado" ✅
   - Calendar Email: `carriagada@grupobanados.com`

### Paso 8: Probar que Funciona

1. Usa el asistente IA (Chat del frontend o WhatsApp)
2. Pide una reserva: "Quiero reservar para mañana a las 3 PM"
3. El asistente debe consultar el Google Calendar de `carriagada@grupobanados.com`
4. Las reservas se crearán en ese calendario

## 🔍 Troubleshooting

### Error: "Connection refused" al iniciar MCP Calendar Server
- Verifica que el puerto 60000 no esté en uso: `lsof -i :60000`
- Si está en uso, cambia `CALENDAR_SERVER_PORT` en `.env`

### Error: "redirect_uri_mismatch"
- Verifica que el redirect URI en Google Cloud Console sea exactamente: `http://localhost:60000/oauth/callback`
- Sin espacios, sin trailing slash

### El backend no inicia
- Verifica que `email-validator` esté instalado: `pip install email-validator`
- Verifica que todas las variables de entorno estén en `.env`
