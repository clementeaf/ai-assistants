# MCP Booking Log Server

Servidor MCP (Model Context Protocol) para bitácora/agenda de reservas.

## Características

Registra y gestiona el historial completo de reservas con:
- **Cliente**: Nombre e ID del cliente
- **Día y hora**: Fecha y horario de la reserva
- **Área/Especialidad/Especialista**: Información del profesional y especialidad
- **Código de Reserva**: Identificador único de la reserva
- **Observaciones**: Notas adicionales sobre la reserva

## Instalación

```bash
cd booking-log-mcp-server

# Crear entorno virtual (recomendado)
python3 -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

## Configuración

Variables de entorno:

- `BOOKING_LOG_SERVER_PORT` - Puerto del servidor (default: 60003)
- `BOOKING_LOG_DB_PATH` - Ruta del archivo SQLite (default: booking_log.db)

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
uvicorn main:app --host 0.0.0.0 --port 60003
```

El servidor estará disponible en `http://localhost:60003`

## Herramientas MCP Disponibles

### 1. `create_booking_log`
Crear una nueva entrada en la bitácora.

**Input:**
```json
{
  "booking_code": "BOOKING-ABC123",
  "customer_name": "Juan Pérez",
  "customer_id": "customer-123",
  "date_iso": "2025-01-08",
  "time_iso": "2025-01-08T18:00:00Z",
  "area_id": "AREA-XXXXX",
  "area_name": "Medicina",
  "specialty_id": "SPEC-XXXXX",
  "specialty_name": "Cardiología",
  "professional_id": "PROF-XXXXX",
  "professional_name": "Dr. María González",
  "observations": "Primera consulta, traer estudios previos"
}
```

### 2. `get_booking_log`
Obtener una entrada por código de reserva o log ID.

**Input:**
```json
{
  "booking_code": "BOOKING-ABC123"
}
```
o
```json
{
  "log_id": "LOG-XXXXX"
}
```

### 3. `list_booking_logs`
Listar entradas con filtros opcionales.

**Input:**
```json
{
  "customer_id": "customer-123",
  "date_iso": "2025-01-08",
  "professional_id": "PROF-XXXXX",
  "specialty_id": "SPEC-XXXXX",
  "area_id": "AREA-XXXXX",
  "limit": 50
}
```

### 4. `update_booking_log`
Actualizar una entrada existente.

**Input:**
```json
{
  "booking_code": "BOOKING-ABC123",
  "observations": "Consulta completada, paciente derivado a especialista"
}
```

### 5. `delete_booking_log`
Eliminar una entrada de la bitácora.

**Input:**
```json
{
  "booking_code": "BOOKING-ABC123"
}
```

## Ejemplo de Uso

```bash
# Crear entrada en bitácora
curl -X POST http://localhost:60003/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "create_booking_log",
      "arguments": {
        "booking_code": "BOOKING-123",
        "customer_name": "Juan Pérez",
        "customer_id": "customer-123",
        "date_iso": "2025-01-08",
        "time_iso": "2025-01-08T18:00:00Z",
        "area_name": "Medicina",
        "specialty_name": "Cardiología",
        "professional_name": "Dr. María González",
        "observations": "Primera consulta"
      }
    }
  }'
```

## Health Check

```bash
curl http://localhost:60003/health
```

## Integración con Otros Servicios

Este servidor se integra con:
- **Calendar MCP Server**: Para obtener información de reservas
- **Professionals MCP Server**: Para obtener información de profesionales, áreas y especialidades

La bitácora actúa como un registro histórico y de auditoría de todas las reservas realizadas.

