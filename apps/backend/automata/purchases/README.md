# Autómata de Compras (Purchases)

Autómata especializado en consulta de órdenes, seguimiento de envíos y gestión de compras.

## Funcionalidad

- Consulta de órdenes por ID (ORDER-XXX)
- Seguimiento de envíos por ID (TRACK-XXX)
- Listado de compras del cliente
- Búsqueda en memoria vectorial

## Herramientas

- `get_order` - Obtener detalles de orden
- `get_tracking_status` - Estado de seguimiento
- `list_orders` - Listar órdenes del cliente
- `vector_recall` - Búsqueda en memoria vectorial

## Configuración

```bash
AI_ASSISTANTS_PURCHASES_PLANNER_ENABLED=1
```

## Uso

```python
from ai_assistants.automata.purchases import get_purchases_planner

planner = get_purchases_planner()
if planner:
    plan = planner.plan(user_text="Quiero ver mi orden ORDER-123", customer_id="123")
```
