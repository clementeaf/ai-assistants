# MCP LLM Server

Servidor MCP (Model Context Protocol) para servicios de LLM (Large Language Models).

## Características

- **Desacoplamiento**: El backend no necesita conocer directamente la API del LLM
- **Estandarización**: Usa el mismo protocolo MCP que los otros servidores
- **Flexibilidad**: Cambiar de proveedor LLM sin modificar el backend
- **Escalabilidad**: Centraliza rate limiting, caching y retry logic
- **Observabilidad**: Logs y métricas en un solo lugar

## Proveedores Compatibles

Este servidor es compatible con cualquier API que siga el formato de OpenAI:
- **OpenAI** (GPT-4, GPT-3.5, etc.)
- **Anthropic** (Claude) - con adaptador
- **Ollama** (modelos locales)
- **Groq** (inferencia rápida)
- **Otros proveedores** compatibles con OpenAI API

## Instalación

```bash
cd llm-mcp-server

# Crear entorno virtual (recomendado)
python3 -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

## Configuración

Variables de entorno:

- `LLM_MCP_SERVER_PORT` - Puerto del servidor (default: 60004)
- `LLM_MCP_BASE_URL` - URL base de la API del LLM (default: https://api.openai.com/v1)
- `LLM_MCP_API_KEY` - API key del proveedor LLM
- `LLM_MCP_MODEL` - Modelo a usar (default: gpt-4o-mini)
- `LLM_MCP_TIMEOUT_SECONDS` - Timeout en segundos (default: 30)
- `LLM_MCP_TEMPERATURE` - Temperatura para generación (default: 0)

### Ejemplos de Configuración

**OpenAI:**
```bash
export LLM_MCP_BASE_URL="https://api.openai.com/v1"
export LLM_MCP_API_KEY="sk-..."
export LLM_MCP_MODEL="gpt-4o-mini"
```

**Ollama (local):**
```bash
export LLM_MCP_BASE_URL="http://localhost:11434/v1"
export LLM_MCP_API_KEY=""  # Ollama no requiere API key
export LLM_MCP_MODEL="llama3.2"
```

**Groq:**
```bash
export LLM_MCP_BASE_URL="https://api.groq.com/openai/v1"
export LLM_MCP_API_KEY="gsk_..."
export LLM_MCP_MODEL="llama-3.1-70b-versatile"
```

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
uvicorn main:app --host 0.0.0.0 --port 60004
```

El servidor estará disponible en `http://localhost:60004` (o el puerto configurado en `LLM_MCP_SERVER_PORT`)

## Herramientas MCP Disponibles

### 1. `chat_completion`
Realizar una completación de chat con el LLM.

**Input:**
```json
{
  "system": "Eres un asistente útil.",
  "user": "¿Cuál es la capital de Francia?",
  "temperature": 0.7,
  "model": "gpt-4o-mini"
}
```

**Output:**
```json
{
  "content": "La capital de Francia es París.",
  "model": "gpt-4o-mini",
  "usage": {
    "prompt_tokens": 20,
    "completion_tokens": 10,
    "total_tokens": 30
  },
  "elapsed_seconds": 0.523
}
```

**Parámetros:**
- `system` (requerido): Mensaje del sistema
- `user` (requerido): Mensaje del usuario
- `temperature` (opcional): Temperatura para generación (0-2)
- `model` (opcional): Modelo específico a usar (sobrescribe el default)

## Ejemplo de Uso

```bash
# Realizar una completación
curl -X POST http://localhost:60004/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "chat_completion",
      "arguments": {
        "system": "Eres un asistente de reservas.",
        "user": "¿Qué horarios están disponibles para mañana?",
        "temperature": 0
      }
    }
  }'
```

## Health Check

```bash
curl http://localhost:60004/health
```

Respuesta:
```json
{
  "status": "ok",
  "service": "mcp-llm-server",
  "model": "gpt-4o-mini",
  "base_url": "https://api.openai.com/v1"
}
```

## Integración con el Backend

El backend se conecta a este servidor MCP mediante el `MCPLLMAdapter`, que implementa el protocolo `ChatClient`. Esto permite:

1. **Desacoplamiento**: El backend no conoce el proveedor LLM específico
2. **Flexibilidad**: Cambiar de OpenAI a Ollama sin modificar código
3. **Estandarización**: Mismo protocolo MCP para todos los servicios
4. **Escalabilidad**: El servidor MCP puede manejar rate limiting y caching

## Ventajas sobre Integración Directa

1. **Centralización**: Un solo punto de configuración para el LLM
2. **Observabilidad**: Logs y métricas centralizados
3. **Rate Limiting**: Control centralizado de límites de API
4. **Caching**: Cache de respuestas comunes (futuro)
5. **Retry Logic**: Reintentos automáticos en caso de fallos
6. **Multi-tenancy**: Soporte para múltiples clientes con diferentes configuraciones

## Próximas Mejoras

- [ ] Rate limiting por cliente
- [ ] Caching de respuestas
- [ ] Retry logic con backoff exponencial
- [ ] Métricas y observabilidad (Prometheus)
- [ ] Soporte para function calling
- [ ] Streaming de respuestas
- [ ] Soporte para múltiples modelos simultáneos

