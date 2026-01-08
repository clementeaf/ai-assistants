# MCP Calendar Server

Servidor MCP (Model Context Protocol) básico para gestión de calendario y reservas.

## Características

- Implementa el protocolo MCP (JSON-RPC 2.0)
- Almacenamiento persistente en SQLite
- 7 herramientas disponibles:
  - `check_availability` - Verificar disponibilidad de un horario
  - `get_available_slots` - Obtener horarios disponibles para una fecha
  - `create_booking` - Crear una nueva reserva
  - `get_booking` - Obtener una reserva por ID
  - `list_bookings` - Listar reservas de un cliente
  - `update_booking` - Modificar una reserva
  - `delete_booking` - Eliminar una reserva

## Instalación

```bash
cd calendar-mcp-server

# Crear entorno virtual (recomendado)
python3 -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

## Configuración

Variables de entorno:

- `CALENDAR_SERVER_PORT` - Puerto del servidor (default: 3000)
- `CALENDAR_DB_PATH` - Ruta del archivo SQLite (default: calendar.db)

## Ejecución

### Opción 1: Script de inicio
```bash
./start.sh
```

### Opción 2: Python directo
```bash
python main.py
```

### Opción 3: Uvicorn directamente
```bash
uvicorn main:app --host 0.0.0.0 --port 3000
```

El servidor estará disponible en `http://localhost:3000`

## Uso

El servidor expone un endpoint `/mcp` que acepta requests JSON-RPC 2.0:

```bash
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "create_booking",
      "arguments": {
        "customer_id": "customer-123",
        "customer_name": "Juan Pérez",
        "date_iso": "2025-01-08",
        "start_time_iso": "2025-01-08T18:00:00Z",
        "end_time_iso": "2025-01-08T19:00:00Z"
      }
    }
  }'
```

## Health Check

```bash
curl http://localhost:3000/health
```

## Pruebas

Para probar el servidor, ejecuta:

```bash
# Primero, asegúrate de que el servidor esté corriendo
python main.py

# En otra terminal, ejecuta las pruebas
pip install requests  # Si no está instalado
python test_mcp.py
```

## Integración con AI Assistants

Para usar este servidor con el asistente, configura:

```bash
export AI_ASSISTANTS_MCP_CALENDAR_URL=http://localhost:3000
```

El asistente detectará automáticamente el servidor MCP y lo usará en lugar del adapter demo.

