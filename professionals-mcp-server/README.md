# MCP Professionals Server

Servidor MCP (Model Context Protocol) para gestión de profesionales, áreas y especialidades.

## Características

- **Áreas**: Categorías principales (ej: "Medicina", "Psicología", "Fisioterapia")
- **Especialidades**: Subcategorías dentro de áreas (ej: "Cardiología", "Neurología")
- **Profesionales**: Personas que pueden tener una o más especialidades
- **Relaciones**: Muchos a muchos entre profesionales y especialidades

## Estructura de Datos

```
Área
  └── Especialidad 1
      └── Profesional A
      └── Profesional B
  └── Especialidad 2
      └── Profesional C
```

## Instalación

```bash
cd professionals-mcp-server

# Crear entorno virtual (recomendado)
python3 -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

## Configuración

Variables de entorno:

- `PROFESSIONALS_SERVER_PORT` - Puerto del servidor (default: 3002)
- `PROFESSIONALS_DB_PATH` - Ruta del archivo SQLite (default: professionals.db)

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
uvicorn main:app --host 0.0.0.0 --port 3002
```

El servidor estará disponible en `http://localhost:3002`

## Herramientas MCP Disponibles

### Áreas
- `create_area` - Crear área
- `get_area` - Obtener área por ID
- `list_areas` - Listar todas las áreas

### Especialidades
- `create_specialty` - Crear especialidad
- `get_specialty` - Obtener especialidad por ID
- `list_specialties` - Listar especialidades (opcionalmente filtradas por área)

### Profesionales
- `create_professional` - Crear profesional
- `get_professional` - Obtener profesional por ID (incluye sus especialidades)
- `list_professionals` - Listar profesionales (opcionalmente filtrados por especialidad o área)
- `assign_specialty` - Asignar especialidad a profesional
- `remove_specialty` - Remover especialidad de profesional
- `update_professional` - Actualizar datos de profesional
- `delete_professional` - Desactivar profesional

## Ejemplo de Uso

```bash
# Crear un área
curl -X POST http://localhost:3002/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "create_area",
      "arguments": {
        "name": "Medicina",
        "description": "Área de medicina general y especialidades"
      }
    }
  }'

# Crear una especialidad
curl -X POST http://localhost:3002/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "create_specialty",
      "arguments": {
        "name": "Cardiología",
        "area_id": "AREA-XXXXX",
        "description": "Especialidad en enfermedades del corazón"
      }
    }
  }'

# Crear un profesional
curl -X POST http://localhost:3002/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "create_professional",
      "arguments": {
        "name": "Dr. Juan Pérez",
        "email": "juan.perez@example.com",
        "phone": "+5491112345678"
      }
    }
  }'

# Asignar especialidad a profesional
curl -X POST http://localhost:3002/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "assign_specialty",
      "arguments": {
        "professional_id": "PROF-XXXXX",
        "specialty_id": "SPEC-XXXXX"
      }
    }
  }'

# Listar profesionales de una especialidad
curl -X POST http://localhost:3002/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "list_professionals",
      "arguments": {
        "specialty_id": "SPEC-XXXXX"
      }
    }
  }'
```

## Health Check

```bash
curl http://localhost:3002/health
```

## Integración con Sistema de Calendario

Este servidor se integra con el sistema de calendario para:
- Consultar qué profesionales están disponibles para una especialidad
- Filtrar horarios disponibles por profesional
- Asociar reservas con profesionales específicos

