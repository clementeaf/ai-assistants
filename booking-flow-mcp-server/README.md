# MCP Booking Flow Server

Servidor MCP (Model Context Protocol) para gestionar flujos de conversación configurables del bot de reservas.

## Características

- **Configuración dinámica**: El frontend puede definir y modificar los pasos del flujo de conversación
- **Etapas configurables**: Cada etapa tiene nombre, orden, tipo, prompt y validaciones
- **Múltiples flujos**: Soporte para diferentes flujos por dominio (bookings, purchases, claims)
- **Flexibilidad**: Agregar, modificar o eliminar etapas sin modificar código
- **Validación**: Reglas de validación por campo

## Conceptos

### Flow (Flujo)
Un flujo define una secuencia de etapas que el bot debe seguir para completar una tarea (ej: crear una reserva).

### Stage (Etapa/Paso)
Cada etapa representa un paso en la conversación:
- **Tipo `greeting`**: Saludo inicial
- **Tipo `input`**: Solicita información al usuario (nombre, fecha, hora, etc.)
- **Tipo `confirmation`**: Confirma información antes de proceder
- **Tipo `action`**: Ejecuta una acción (crear reserva, enviar email, etc.)

Cada etapa puede tener:
- `prompt_text`: Texto que el bot debe decir
- `field_name`: Nombre del campo que se está capturando
- `field_type`: Tipo de dato (text, date, time, email, etc.)
- `validation_rules`: Reglas de validación (JSON)
- `is_required`: Si el campo es obligatorio

## Instalación

```bash
cd booking-flow-mcp-server

# Crear entorno virtual (recomendado)
python3 -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

## Configuración

Variables de entorno:

- `BOOKING_FLOW_SERVER_PORT` - Puerto del servidor (default: 3005)
- `BOOKING_FLOW_DB_PATH` - Ruta del archivo SQLite (default: booking_flow.db)

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
uvicorn main:app --host 0.0.0.0 --port 3005
```

El servidor estará disponible en `http://localhost:3005`

## Herramientas MCP Disponibles

### 1. `create_flow`
Crear un nuevo flujo de conversación.

**Input:**
```json
{
  "name": "Flujo de Reservas Personalizado",
  "description": "Flujo adaptado para nuestro negocio",
  "domain": "bookings"
}
```

### 2. `get_flow`
Obtener un flujo por ID o el flujo activo de un dominio.

**Input:**
```json
{
  "domain": "bookings"
}
```
o
```json
{
  "flow_id": "FLOW-XXXXX"
}
```

### 3. `list_flows`
Listar todos los flujos, opcionalmente filtrados por dominio.

**Input:**
```json
{
  "domain": "bookings",
  "include_inactive": false
}
```

### 4. `add_stage`
Agregar una etapa a un flujo.

**Input:**
```json
{
  "flow_id": "FLOW-XXXXX",
  "stage_order": 1,
  "stage_name": "get_name",
  "stage_type": "input",
  "prompt_text": "Por favor, dime tu nombre completo.",
  "field_name": "customer_name",
  "field_type": "text",
  "is_required": true
}
```

### 5. `get_flow_stages`
Obtener todas las etapas de un flujo, ordenadas por `stage_order`.

**Input:**
```json
{
  "flow_id": "FLOW-XXXXX"
}
```

### 6. `update_stage`
Actualizar una etapa existente.

**Input:**
```json
{
  "stage_id": "STAGE-XXXXX",
  "prompt_text": "Nuevo texto del prompt",
  "is_required": false
}
```

### 7. `delete_stage`
Eliminar una etapa de un flujo.

**Input:**
```json
{
  "stage_id": "STAGE-XXXXX"
}
```

## Ejemplo de Uso

### Crear un flujo personalizado

```bash
curl -X POST http://localhost:3005/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "create_flow",
      "arguments": {
        "name": "Reservas Express",
        "description": "Flujo rápido para reservas",
        "domain": "bookings"
      }
    }
  }'
```

### Agregar etapas al flujo

```bash
# Etapa 1: Saludo
curl -X POST http://localhost:3005/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "add_stage",
      "arguments": {
        "flow_id": "FLOW-XXXXX",
        "stage_order": 1,
        "stage_name": "greeting",
        "stage_type": "greeting",
        "prompt_text": "¡Hola! Soy tu asistente de reservas. ¿Cómo te llamas?"
      }
    }
  }'

# Etapa 2: Obtener nombre
curl -X POST http://localhost:3005/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "add_stage",
      "arguments": {
        "flow_id": "FLOW-XXXXX",
        "stage_order": 2,
        "stage_name": "get_name",
        "stage_type": "input",
        "prompt_text": "Por favor, dime tu nombre completo.",
        "field_name": "customer_name",
        "field_type": "text",
        "is_required": true
      }
    }
  }'
```

### Obtener el flujo completo

```bash
curl -X POST http://localhost:3005/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 4,
    "method": "tools/call",
    "params": {
      "name": "get_flow_stages",
      "arguments": {
        "flow_id": "FLOW-XXXXX"
      }
    }
  }'
```

## Flujo Predeterminado

Al iniciar por primera vez, el servidor crea automáticamente un flujo predeterminado con estas etapas:

1. **greeting** - Saludo inicial
2. **get_name** - Solicitar nombre del cliente
3. **get_date** - Solicitar fecha de reserva
4. **get_time** - Solicitar hora de reserva
5. **get_service** - Solicitar tipo de servicio (opcional)
6. **confirm** - Confirmar reserva

Este flujo puede ser modificado o reemplazado desde el frontend.

## Integración con el Backend

El backend puede consultar el flujo activo para un dominio y seguir las etapas definidas. Esto permite:

1. **Configuración sin código**: Cambiar el flujo desde el frontend
2. **A/B Testing**: Probar diferentes flujos
3. **Personalización**: Diferentes flujos para diferentes clientes o situaciones
4. **Mantenimiento**: Actualizar prompts sin deployar código

## Health Check

```bash
curl http://localhost:3005/health
```

## Próximas Mejoras

- [ ] Condiciones entre etapas (if/else)
- [ ] Etapas opcionales condicionales
- [ ] Validación avanzada con regex
- [ ] Templates de prompts con variables
- [ ] Historial de cambios en flujos
- [ ] Versionado de flujos
- [ ] Exportar/importar flujos como JSON

