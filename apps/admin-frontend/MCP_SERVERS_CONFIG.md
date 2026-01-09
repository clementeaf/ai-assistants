# Configuración de Servidores MCP

## Variables de Entorno Requeridas

Para que el frontend se comunique correctamente con los servidores MCP, configura las siguientes variables de entorno:

### Archivo `.env` o `.env.local` en `admin-frontend/`

```bash
# Servidor MCP de Flujos (Booking Flow)
VITE_FLOW_MCP_SERVER_URL=http://localhost:60006

# Servidor MCP de Calendario
VITE_CALENDAR_MCP_SERVER_URL=http://localhost:60000

# Servidor Backend API
VITE_API_BASE_URL=http://localhost:8000
```

## Puertos por Defecto de los Servidores MCP

| Servidor | Puerto | Variable de Entorno |
|----------|--------|---------------------|
| Calendar MCP Server | 60000 | `CALENDAR_SERVER_PORT` |
| Professionals MCP Server | 60002 | `PROFESSIONALS_SERVER_PORT` |
| Booking Log MCP Server | 60003 | `BOOKING_LOG_SERVER_PORT` |
| LLM MCP Server | 60004 | `LLM_MCP_SERVER_PORT` |
| Booking Flow MCP Server | 60006 | `BOOKING_FLOW_SERVER_PORT` |

## Verificar que los Servidores Estén Corriendo

### Calendar MCP Server
```bash
cd calendar-mcp-server
python main.py
# O
./start.sh
```

### Booking Flow MCP Server
```bash
cd booking-flow-mcp-server
python main.py
# O
./start.sh
```

### Verificar Salud de los Servidores

```bash
# Calendar
curl http://localhost:60000/health

# Booking Flow
curl http://localhost:60006/health
```

## Solución de Problemas

### Error: "Unknown tool: list_flows"

Este error indica que:
1. El servidor MCP de flujos no está corriendo
2. El servidor está en un puerto diferente al configurado
3. La URL de conexión es incorrecta

**Solución:**
1. Verifica que el servidor esté corriendo: `curl http://localhost:60006/health`
2. Verifica la variable de entorno: `VITE_FLOW_MCP_SERVER_URL=http://localhost:60006`
3. Reinicia el servidor de desarrollo del frontend después de cambiar variables de entorno

### Error: "ECONNREFUSED"

El servidor MCP no está disponible en la URL configurada.

**Solución:**
1. Inicia el servidor MCP correspondiente
2. Verifica que el puerto sea correcto
3. Verifica que no haya firewall bloqueando la conexión
