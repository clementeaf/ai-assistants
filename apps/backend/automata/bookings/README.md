# Autómata de Reservas (Bookings)

Autómata especializado en gestión de reservas y citas con Google Calendar.

## Funcionalidad

- Consulta de horarios disponibles
- Creación de reservas
- Modificación y cancelación de reservas
- Listado de reservas del cliente

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
AI_ASSISTANTS_BOOKINGS_PLANNER_ENABLED=1
```

## Uso

```python
from ai_assistants.automata.bookings import get_bookings_planner

planner = get_bookings_planner()
if planner:
    plan = planner.plan(user_text="Quiero reservar", customer_id="123")
```
