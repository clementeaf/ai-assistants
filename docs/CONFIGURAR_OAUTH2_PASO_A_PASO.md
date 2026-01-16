# Configurar OAuth2 - Paso a Paso

## ✅ Ya Tienes:
- ✅ Google Calendar API habilitada
- ✅ Credencial OAuth2 creada ("Clemente")

## 📋 Pasos Siguientes:

### Paso 1: Obtener Client ID y Client Secret

1. En Google Cloud Console, en la sección "IDs de clientes de OAuth 2.0"
2. Haz clic en el nombre "Clemente" (el link azul)
3. Se abrirá la página de detalles de la credencial
4. Copia:
   - **ID de cliente**: `420852401159-iv8t...` (copia el completo)
   - **Secreto de cliente**: Haz clic en el ojo para mostrarlo y copiarlo

### Paso 2: Configurar Redirect URI

En la misma página de detalles de la credencial:

1. Busca la sección "URI de redirección autorizados"
2. Haz clic en "+ Agregar URI"
3. Agrega: `http://localhost:60000/oauth/callback`
4. Haz clic en "Guardar"

### Paso 3: Configurar Variables de Entorno

Crea el archivo `.env` en `mcp-servers/calendar-mcp-server/`:

```bash
CALENDAR_BACKEND=google_calendar
GOOGLE_OAUTH_CLIENT_ID=420852401159-iv8t...TU_CLIENT_ID_COMPLETO
GOOGLE_OAUTH_CLIENT_SECRET=TU_CLIENT_SECRET_COMPLETO
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:60000/oauth/callback
TOKEN_DB_PATH=tokens.db
TOKEN_ENCRYPTION_KEY=GENERA_UNA_CLAVE_DE_32_CARACTERES
CALENDAR_SERVER_PORT=60000
```

**Para generar la clave de encriptación:**
```bash
cd mcp-servers/calendar-mcp-server
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Copia el resultado y úsalo como `TOKEN_ENCRYPTION_KEY`.

### Paso 4: Reiniciar MCP Calendar Server

```bash
cd mcp-servers/calendar-mcp-server
# Detener el servidor actual si está corriendo (Ctrl+C)
python3 main_multi_user.py
```

### Paso 5: Verificar que Funciona

```bash
# Probar endpoint de autorización
curl -X POST http://localhost:60000/oauth/authorize \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "test-123"}'
```

Deberías recibir una respuesta con `authorization_url`.

### Paso 6: Agregar Empresa en Admin-Frontend

1. Abre: `http://localhost:5173/clientes`
2. Click en "Agregar Cliente"
3. Ingresa:
   - **ID del Cliente**: `empresa-carriagada`
   - **Email del Cliente**: `carriagada@grupobanados.com`
   - **Nombre del Cliente**: `Carriagada - Grupo Bañados`
4. Click en "Conectar Calendario"
5. Copia el link de OAuth2 que se genera

### Paso 7: Autorizar Google Calendar

1. Abre el link de OAuth2 en el navegador
2. Inicia sesión con `carriagada@grupobanados.com`
3. Google mostrará: "¿Permitir que AI Assistants acceda a tu Google Calendar?"
4. Click en "Permitir"
5. Google redirigirá automáticamente
6. Los tokens se guardarán automáticamente

### Paso 8: Verificar Estado

En Admin-Frontend (`/clientes`), verifica:
- Estado: "Conectado" ✅
- Calendar Email: `carriagada@grupobanados.com`

¡Listo! El asistente IA puede usar el calendario automáticamente.
