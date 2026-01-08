# Integración de Calendario vía MCP

## Arquitectura

El sistema de calendario puede funcionar de dos formas:

1. **Modo Local (Demo)**: Usa `DemoBookingsAdapter` con almacenamiento en memoria
2. **Modo MCP**: Conecta a un servidor de calendario externo vía Model Context Protocol

## Configuración MCP

Para usar un servidor de calendario MCP, configura estas variables de entorno:

```bash
# URL del servidor MCP de calendario
AI_ASSISTANTS_MCP_CALENDAR_URL=http://localhost:60000

# API Key (opcional, si el servidor requiere autenticación)
AI_ASSISTANTS_MCP_CALENDAR_API_KEY=your-api-key

# Timeout en segundos (opcional, default: 10)
AI_ASSISTANTS_MCP_CALENDAR_TIMEOUT_SECONDS=10
```

## Protocolo MCP

El servidor MCP debe exponer las siguientes herramientas:

### 1. `check_availability`
Verifica si un horario está disponible.

**Input:**
```json
{
  "date_iso": "2025-01-08",
  "start_time_iso": "2025-01-08T18:00:00Z",
  "end_time_iso": "2025-01-08T19:00:00Z"
}
```

**Output:**
```json
{
  "available": true
}
```

### 2. `get_available_slots`
Obtiene los horarios disponibles para una fecha.

**Input:**
```json
{
  "date_iso": "2025-01-08"
}
```

**Output:**
```json
{
  "slots": [
    {
      "date_iso": "2025-01-08",
      "start_time_iso": "2025-01-08T09:00:00Z",
      "end_time_iso": "2025-01-08T10:00:00Z",
      "available": true
    }
  ]
}
```

### 3. `create_booking`
Crea una nueva reserva.

**Input:**
```json
{
  "customer_id": "customer-123",
  "customer_name": "Juan Pérez",
  "date_iso": "2025-01-08",
  "start_time_iso": "2025-01-08T18:00:00Z",
  "end_time_iso": "2025-01-08T19:00:00Z"
}
```

**Output:**
```json
{
  "booking": {
    "booking_id": "BOOKING-ABC123",
    "customer_id": "customer-123",
    "customer_name": "Juan Pérez",
    "date_iso": "2025-01-08",
    "start_time_iso": "2025-01-08T18:00:00Z",
    "end_time_iso": "2025-01-08T19:00:00Z",
    "status": "confirmed",
    "created_at": "2025-01-07T10:00:00Z",
    "confirmation_email_sent": false,
    "reminder_sent": false
  }
}
```

### 4. `get_booking`
Obtiene una reserva por ID.

**Input:**
```json
{
  "booking_id": "BOOKING-ABC123"
}
```

**Output:**
```json
{
  "booking": {
    "booking_id": "BOOKING-ABC123",
    "customer_id": "customer-123",
    "customer_name": "Juan Pérez",
    "date_iso": "2025-01-08",
    "start_time_iso": "2025-01-08T18:00:00Z",
    "end_time_iso": "2025-01-08T19:00:00Z",
    "status": "confirmed",
    "created_at": "2025-01-07T10:00:00Z",
    "confirmation_email_sent": false,
    "reminder_sent": false
  }
}
```

### 5. `list_bookings`
Lista las reservas de un cliente.

**Input:**
```json
{
  "customer_id": "customer-123"
}
```

**Output:**
```json
{
  "bookings": [
    {
      "booking_id": "BOOKING-ABC123",
      "customer_id": "customer-123",
      "customer_name": "Juan Pérez",
      "date_iso": "2025-01-08",
      "start_time_iso": "2025-01-08T18:00:00Z",
      "end_time_iso": "2025-01-08T19:00:00Z",
      "status": "confirmed",
      "created_at": "2025-01-07T10:00:00Z",
      "confirmation_email_sent": false,
      "reminder_sent": false
    }
  ]
}
```

### 6. `update_booking`
Actualiza una reserva existente.

**Input:**
```json
{
  "booking_id": "BOOKING-ABC123",
  "date_iso": "2025-01-09",
  "start_time_iso": "2025-01-09T18:00:00Z",
  "end_time_iso": "2025-01-09T19:00:00Z",
  "status": "confirmed"
}
```

**Output:**
```json
{
  "booking": {
    "booking_id": "BOOKING-ABC123",
    "customer_id": "customer-123",
    "customer_name": "Juan Pérez",
    "date_iso": "2025-01-09",
    "start_time_iso": "2025-01-09T18:00:00Z",
    "end_time_iso": "2025-01-09T19:00:00Z",
    "status": "confirmed",
    "created_at": "2025-01-07T10:00:00Z",
    "confirmation_email_sent": false,
    "reminder_sent": false
  }
}
```

### 7. `delete_booking`
Elimina una reserva.

**Input:**
```json
{
  "booking_id": "BOOKING-ABC123"
}
```

**Output:**
```json
{
  "success": true
}
```

## Formato de Request MCP

El adapter envía requests en formato JSON-RPC 2.0:

```json
{
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
}
```

## Ventajas de MCP

1. **Desacoplamiento**: El calendario es un servicio independiente
2. **Escalabilidad**: Puede escalar independientemente del asistente
3. **Reutilización**: Otros sistemas pueden usar el mismo servidor MCP
4. **Estándar**: MCP es un protocolo estándar para herramientas de IA
5. **Flexibilidad**: Fácil cambiar entre demo y producción

## Ejemplo de Servidor MCP

Un servidor MCP de calendario podría ser:

- Un servicio FastAPI/Express que expone endpoints MCP
- Un servidor dedicado con base de datos PostgreSQL/MySQL
- Un servicio cloud (AWS, GCP, Azure) con API REST
- Un servidor que integra con Google Calendar, Outlook, etc.

