## Objetivo

Este repo está orientado a construir **chatbots/agents con LangGraph** para orquestar flujos de negocio (reservas, compras, seguimiento, reclamos) de forma **modular, tipada y mantenible**.

La idea central es separar:

- **Orquestación conversacional** (graphs, estado, routing)
- **Lógica de negocio** (servicios de dominio)
- **Integraciones** (adapters: DB, pagos, CRM, etc.)

## Estructura

- `src/ai_assistants/api/`: API (FastAPI) y contratos HTTP
- `src/ai_assistants/channels/`: adapters de canal (Web/WhatsApp) y normalización de mensajes
- `src/ai_assistants/orchestrator/`: runtime (ejecución de graphs, estado, checkpointing)
- `src/ai_assistants/graphs/`: router graph y sub-graphs por dominio
- `src/ai_assistants/tools/`: herramientas (contratos + validación)
- `src/ai_assistants/domain/`: reglas y servicios determinísticos
- `src/ai_assistants/persistence/`: stores (conversaciones/checkpoints)
- `src/ai_assistants/observability/`: logging/tracing

## Ejecutar (demo local, sin LLM)

1) Crear entorno e instalar dependencias (ejemplo con `pip`):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Recomendación de runtime: **Python 3.11–3.13** (Python 3.14+ puede emitir warnings por dependencias transitorias).

2) Levantar API:

```bash
uvicorn ai_assistants.api.app:app --reload
```

3) Probar:

```bash
curl -X POST "http://127.0.0.1:8000/v1/conversations/demo/messages" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <project-api-key>" \
  -d '{"text":"Quiero revisar una compra: ORDER-100"}'
```

## Configuración (env vars)

- `AI_ASSISTANTS_API_KEYS`: habilita auth por API key. Formato: `projectA:keyA,projectB:keyB`
  - Si no está seteada, auth queda **deshabilitada** (modo dev).
- `AI_ASSISTANTS_ENABLE_LEGACY_ROUTES`: habilita rutas no versionadas (legacy). Default: `1`
  - Setear a `0` para exponer únicamente `/v1/...` en producción.
- `AI_ASSISTANTS_RATE_LIMIT`: rate limit fijo por proyecto. Formato: `60/60` (60 requests cada 60s)
  - Si no está seteada, rate limit queda deshabilitado.
- `AI_ASSISTANTS_SQLITE_PATH`: path a SQLite para persistencia. Default: `.data/ai_assistants.sqlite3`
- `AI_ASSISTANTS_MAX_MESSAGES`: máximo de mensajes guardados por conversación. Default: `200`
- `AI_ASSISTANTS_MAX_PROCESSED_EVENTS`: máximo de `message_id` recordados para idempotencia. Default: `5000`
- Memoria (recuerdo) persistida:
  - Se guarda por `project_id + customer_id` en SQLite.
  - Actualmente persiste claves como `last_order_id` y `last_tracking_id` para follow-ups entre sesiones.
- TTL de memoria:
  - `AI_ASSISTANTS_MEMORY_TTL_SECONDS_LAST_IDS` (default 30 días) expira `last_order_id/last_tracking_id`.

## Administración de memoria (API)

- `GET /v1/memory` (requiere `X-API-Key` y `X-Customer-Id`)
- `DELETE /v1/memory` (requiere `X-API-Key` y `X-Customer-Id`)
- `WHATSAPP_WEBHOOK_SECRET`: habilita verificación HMAC para el inbound del gateway (recomendado)
- `WHATSAPP_WEBHOOK_MAX_DRIFT_SECONDS`: tolerancia de drift para timestamp (default 300)
- `AI_ASSISTANTS_LLM_ROUTER_ENABLED`: habilita router por LLM (default: 0)
- `AI_ASSISTANTS_LLM_BASE_URL`: base URL OpenAI-compatible (ej: `http://localhost:11434` o endpoint de proveedor)
- `AI_ASSISTANTS_LLM_API_KEY`: api key del proveedor
- `AI_ASSISTANTS_LLM_MODEL`: modelo (según proveedor)
- `AI_ASSISTANTS_LLM_TIMEOUT_SECONDS`: timeout del router LLM (default: 10)
- `AI_ASSISTANTS_LLM_NLG_ENABLED`: habilita “redacción” por LLM (default: 0). Si se activa, cambia los textos y puede requerir actualizar goldens.
- `AI_ASSISTANTS_LLM_NLG_STRICT`: guardrails del NLG (default: 1). Si está activo, rechaza reescrituras que cambien o inventen `ORDER-XXX`/`TRACK-XXX` o timestamps ISO.
- `AI_ASSISTANTS_PURCHASES_PLANNER_ENABLED`: habilita planner LLM para el dominio `purchases` (default: 0). El LLM propone tool-calls JSON (allowlist + validación), el código ejecuta.
- `AI_ASSISTANTS_BOOKINGS_PLANNER_ENABLED`: habilita planner LLM para el dominio `bookings` (default: 0). Similar a purchases, pero enfocado en reservas.
- `AI_ASSISTANTS_CLAIMS_PLANNER_ENABLED`: habilita planner LLM para el dominio `claims` (default: 0). Similar a purchases, pero enfocado en reclamos.

### Quick start (LLM + planner de compras)

1) Copiá el ejemplo de env:

```bash
cp examples/env.example .env
```

2) Editá `.env` y seteá `AI_ASSISTANTS_LLM_API_KEY` (y opcionalmente modelos).

3) Levantá la API y probá un mensaje ambiguo (ej: “creo que pedí algo el mes pasado…”).  
Con `AI_ASSISTANTS_PURCHASES_PLANNER_ENABLED=1`, el bot va a planificar tools (JSON) y ejecutar de forma tipada.

## Memoria vectorial (RAG-like)

Además de la memoria por “slots”, existe memoria **vectorial** para “recuerdos” semánticos.

- Store: SQLite (`vector_memory`) con búsqueda cosine (brute-force).
- Embeddings: OpenAI-compatible `/v1/embeddings` (configurable por env).

Env vars:
- `AI_ASSISTANTS_VECTOR_MEMORY_ENABLED`: habilita memoria vectorial (default 0)
- `AI_ASSISTANTS_FIXED_NOW_ISO`: fija “now” (solo tests/evals)
- `AI_ASSISTANTS_EMBEDDINGS_BASE_URL` (fallback: `AI_ASSISTANTS_LLM_BASE_URL`)
- `AI_ASSISTANTS_EMBEDDINGS_API_KEY` (fallback: `AI_ASSISTANTS_LLM_API_KEY`)
- `AI_ASSISTANTS_EMBEDDINGS_MODEL` (requerido para activar embeddings)
- `AI_ASSISTANTS_EMBEDDINGS_TIMEOUT_SECONDS` (default 10)

## Hook externo (compras + seguimiento)

Para consumir datos reales, `ai-assistants` puede delegar en un **hook API externo** configurando:

- `AI_ASSISTANTS_PURCHASES_HOOK_URL`: URL del hook (habilita modo real)
- `AI_ASSISTANTS_PURCHASES_HOOK_API_KEY`: (opcional) API key para el hook (se envía como `X-API-Key`)
- `AI_ASSISTANTS_PURCHASES_HOOK_TIMEOUT_SECONDS`: timeout (default: 5)
- `AI_ASSISTANTS_PURCHASES_HOOK_MAX_RETRIES`: reintentos ante errores transitorios (default: 2)
- `AI_ASSISTANTS_PURCHASES_HOOK_SIGNATURE_SECRET`: (opcional) habilita firma HMAC saliente hacia el hook

### Contrato del hook (request/response)

Request (POST JSON) hacia `AI_ASSISTANTS_PURCHASES_HOOK_URL`:

```json
{
  "action": "get_order",
  "payload": { "order_id": "ORDER-200" }
}
```

Acciones soportadas:
- `get_order` payload: `{ "order_id": "..." }`
- `list_orders` payload: `{ "customer_id": "..." }`
- `get_shipment_by_order_id` payload: `{ "order_id": "..." }`
- `get_shipment_by_tracking_id` payload: `{ "tracking_id": "..." }`

Response (POST JSON):

```json
{
  "ok": true,
  "order": {
    "order_id": "ORDER-200",
    "customer_id": "+5491112345678",
    "status": "shipped",
    "total_amount": 120.0,
    "currency": "USD",
    "created_at_iso": "2025-02-10T16:30:00+00:00"
  },
  "shipment": {
    "tracking_id": "TRACK-9002",
    "order_id": "ORDER-200",
    "carrier": "DemoCarrier",
    "status": "in_transit",
    "last_update_at_iso": "2025-02-12T09:00:00+00:00",
    "estimated_delivery_at_iso": "2025-02-14T18:00:00+00:00"
  }
}
```

### Seguridad del hook (firma saliente, recomendado)

Si seteás `AI_ASSISTANTS_PURCHASES_HOOK_SIGNATURE_SECRET`, `ai-assistants` envía:

- `X-Hook-Timestamp`: epoch seconds (string)
- `X-Hook-Signature`: `base64(HMAC_SHA256(secret, timestamp + "." + raw_body))`

### Especificación formal (JSON Schema)

Podés generar el schema v1 del hook con:

```bash
./.venv/bin/python scripts/generate_purchases_hook_schema.py
```

Esto genera: `schemas/purchases_hook_v1.json`

## Canales (Web / WhatsApp)

- **Web**: usa el endpoint de conversación (o su alias por canal).
- **WhatsApp**: expone un endpoint `provider-agnostic` que normaliza la entrada a un contrato interno estable.

Ejemplo WhatsApp inbound:

```bash
curl -X POST "http://127.0.0.1:8000/v1/channels/whatsapp/inbound" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <project-api-key>" \
  -d '{"from_number":"+5491112345678","text":"Revisar compra ORDER-100"}'
```

### Identidad de cliente (Web)

Para que “mis compras” funcione en Web, el cliente puede enviar:

- Header `X-Customer-Id: <customer_id>`

Esto se persiste en el estado de la conversación y se usa por defecto para tools de compras.

## Modo async (202 + polling)

Para evitar bloquear cuando el hook externo esté lento, podés usar endpoints async:

- `POST /v1/async/conversations/{conversation_id}/messages` → `202 { "job_id": "..." }`
- `POST /v1/async/channels/whatsapp/gateway/inbound` → `202 { "job_id": "..." }`
- `GET /v1/jobs/{job_id}` → estado y resultado (cuando termine)

Ejemplo:

```bash
curl -X POST "http://127.0.0.1:8000/v1/async/conversations/demo/messages" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <project-api-key>" \
  -d '{"text":"TRACK-9001"}'
```

### Callback opcional al completar el job (push)

Si no querés hacer polling, podés configurar un callback:

- `AI_ASSISTANTS_JOB_CALLBACK_URL`: URL a la que se enviará `POST` al finalizar (succeeded/failed)
- `AI_ASSISTANTS_JOB_CALLBACK_API_KEY`: (opcional) se envía como `X-API-Key`
- `AI_ASSISTANTS_JOB_CALLBACK_SIGNATURE_SECRET`: (opcional) firma HMAC saliente
- `AI_ASSISTANTS_JOB_CALLBACK_TIMEOUT_SECONDS`: timeout (default 5)
- `AI_ASSISTANTS_JOB_CALLBACK_MAX_RETRIES`: reintentos (default 2)

Headers emitidos (si aplica):
- `X-Request-Id`, `X-Project-Id`
- `X-Callback-Timestamp`, `X-Callback-Signature` (si hay secret)

### WhatsApp via gateway (otro servidor)

Si tenés un servicio gateway (Baileys u otro), la forma recomendada es que ese servicio haga `POST` a:

- `POST /v1/channels/whatsapp/gateway/inbound`

El gateway debe **tomar el `response_text` de la respuesta HTTP** y usarlo para **enviar el mensaje por WhatsApp** (modo pull). `ai-assistants` no necesita llamar a ningún servicio externo.

Body esperado:

```json
{
  "message_id": "wamid-or-bailedys-internal-id",
  "from_number": "+5491112345678",
  "text": "Revisar compra ORDER-100",
  "timestamp_iso": "2025-12-18T12:00:00Z",
  "customer_id": "+5491112345678"
}
```

Respuesta esperada (para que el gateway envíe WhatsApp):

```json
{
  "conversation_id": "whatsapp:+5491112345678",
  "message_id": "wamid-or-bailedys-internal-id",
  "response_text": "Orden ORDER-100: estado=delivered, total=39.99 USD, creada=2025-01-05T12:00:00+00:00."
}
```

#### Seguridad (opcional, recomendado)

Si seteás `WHATSAPP_WEBHOOK_SECRET`, el endpoint requiere:

- `X-Webhook-Timestamp`: epoch seconds (string)
- `X-Webhook-Signature`: `base64(HMAC_SHA256(secret, timestamp + "." + raw_body))`

Opcionalmente podés ajustar la tolerancia de drift con `WHATSAPP_WEBHOOK_MAX_DRIFT_SECONDS` (default: 300).

> Compatibilidad: `POST /channels/whatsapp/baileys/inbound` queda como alias.
> También quedan como endpoints legacy los no versionados bajo `/channels/...` y `/conversations/...`.

## Convenciones

- Los graphs **no** implementan reglas críticas; solo orquestan.
- Toda acción “externa” se hace vía **tools** (con inputs/outputs validados).
- El estado de conversación se versiona en `ConversationState`.

