# Autómata de Reclamos (Claims)

Autómata especializado en gestión de reclamos, quejas y devoluciones.

## Funcionalidad

- Consulta de reclamos anteriores
- Creación de nuevos reclamos
- Búsqueda de información relacionada

## Herramientas

- `get_order` - Obtener orden relacionada
- `vector_recall` - Búsqueda de reclamos anteriores en memoria

## Configuración

```bash
AI_ASSISTANTS_CLAIMS_PLANNER_ENABLED=1
```

## Uso

```python
from ai_assistants.automata.claims import get_claims_planner

planner = get_claims_planner()
if planner:
    plan = planner.plan(user_text="Quiero hacer un reclamo", customer_id="123")
```
