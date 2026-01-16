# Autómatas

Cada autómata es un módulo independiente con su propia lógica, herramientas y configuración.

## Estructura de un Autómata

```
automata/
  {nombre}/
    __init__.py          # Exports principales
    planner.py           # Lógica de planificación (LLM)
    runtime.py           # Ejecución del plan
    prompt.txt           # Prompt del sistema
    tools.py             # Herramientas específicas del autómata
    config.py            # Configuración (env vars)
    contracts.py         # Contratos/Modelos Pydantic (opcional)
    README.md            # Documentación del autómata
```

## Autómatas Disponibles

### bookings
Autómata para gestión de reservas y citas con Google Calendar.

### purchases
Autómata para consulta de compras, órdenes y seguimiento de envíos.

### claims
Autómata para gestión de reclamos y quejas.

### autonomous
Autómata autónomo con conversación natural para reservas.

## Agregar un Nuevo Autómata

1. Crear carpeta `apps/automata/{nombre}/`
2. Implementar `planner.py` y `runtime.py`
3. Agregar `prompt.txt` con el prompt del sistema
4. Definir herramientas en `tools.py` si son específicas
5. Registrar en `apps/backend/routing/domain_router.py`
6. Agregar al router graph en `apps/backend/graphs/router_graph.py`
