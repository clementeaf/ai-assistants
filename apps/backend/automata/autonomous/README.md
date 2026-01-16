# Autómata Autónomo (Autonomous)

Autómata con conversación natural para gestión de reservas con Google Calendar.

## Funcionalidad

- Conversación natural en español
- Gestión completa de reservas
- Integración con Google Calendar
- Recolección inteligente de datos (nombre → fecha → hora)
- Personalización con memoria del cliente

## Herramientas

- `get_available_slots` - Obtener horarios disponibles
- `check_availability` - Verificar disponibilidad
- `create_booking` - Crear reserva
- `get_booking` - Obtener detalles
- `list_bookings` - Listar reservas
- `update_booking` - Actualizar reserva
- `delete_booking` - Cancelar reserva
- `vector_recall` - Memoria vectorial

## Configuración

```bash
AI_ASSISTANTS_AUTONOMOUS_ENABLED=1
AI_ASSISTANTS_AUTONOMOUS_MAX_HISTORY=10
```

## Uso

```python
from ai_assistants.automata.autonomous import get_autonomous_planner

planner = get_autonomous_planner()
if planner:
    plan = planner.plan(
        user_text="Quiero reservar",
        customer_id="123",
        customer_name="Juan Pérez"
    )
```
