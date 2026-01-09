# Integración de Google Calendar con MCP

## Viabilidad: ✅ SÍ ES VIABLE

Es totalmente viable integrar Google Calendar con el MCP de calendario existente. La arquitectura MCP permite mantener la misma interfaz mientras se cambia el backend de almacenamiento.

## Arquitectura Propuesta

```
┌─────────────────┐
│  Backend AI     │
│  Assistants     │
└────────┬────────┘
         │ MCP Protocol (JSON-RPC)
         │
┌────────▼────────────────────────┐
│   MCP Calendar Server           │
│   (main.py)                     │
│                                 │
│   ┌──────────────────────────┐ │
│   │  Backend Adapter         │ │
│   │  - SQLite (actual)       │ │
│   │  - Google Calendar (nuevo)│ │
│   └──────────────────────────┘ │
└─────────────────────────────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼──────────┐
│SQLite │ │Google       │
│(local)│ │Calendar API │
└───────┘ └─────────────┘
```

## Opciones de Autenticación

### Opción 1: Service Account (Recomendada para servidores)
- **Ventajas**: No requiere interacción del usuario, ideal para servicios backend
- **Desventajas**: Requiere compartir el calendario con la cuenta de servicio
- **Uso**: Ideal para calendarios corporativos o de negocio

### Opción 2: OAuth2 (Para usuarios individuales)
- **Ventajas**: Acceso directo al calendario del usuario
- **Desventajas**: Requiere flujo de autenticación inicial
- **Uso**: Ideal para integraciones personales

## Configuración Requerida

### Variables de Entorno

```bash
# Backend de almacenamiento: 'sqlite' o 'google_calendar'
CALENDAR_BACKEND=google_calendar

# Para Google Calendar - Service Account
GOOGLE_CALENDAR_SERVICE_ACCOUNT_FILE=/path/to/service-account.json
GOOGLE_CALENDAR_ID=primary  # o el ID del calendario específico

# Para Google Calendar - OAuth2
GOOGLE_CALENDAR_CLIENT_ID=your-client-id
GOOGLE_CALENDAR_CLIENT_SECRET=your-client-secret
GOOGLE_CALENDAR_REFRESH_TOKEN=your-refresh-token
```

### Pasos de Configuración

#### 1. Service Account (Recomendado)

1. Ir a [Google Cloud Console](https://console.cloud.google.com/)
2. Crear un proyecto o seleccionar uno existente
3. Habilitar Google Calendar API
4. Crear una Service Account
5. Descargar el archivo JSON de credenciales
6. Compartir el calendario con el email de la service account:
   - Abrir Google Calendar
   - Configuración → Compartir con personas específicas
   - Agregar el email de la service account con permisos de "Hacer cambios en eventos"

#### 2. OAuth2 (Alternativa)

1. Crear credenciales OAuth2 en Google Cloud Console
2. Configurar redirect URI
3. Obtener refresh token mediante flujo de autorización
4. Configurar variables de entorno

## Implementación

La implementación mantiene la misma interfaz MCP, por lo que **no requiere cambios en el backend** de AI Assistants.

### Estructura de Código

```
calendar-mcp-server/
├── main.py                    # Servidor MCP (sin cambios)
├── backends/
│   ├── __init__.py
│   ├── base.py                # Interfaz base para backends
│   ├── sqlite_backend.py      # Backend SQLite actual
│   └── google_calendar_backend.py  # Nuevo backend Google Calendar
└── requirements.txt           # Actualizado con google-api-python-client
```

### Compatibilidad

- ✅ Mismo protocolo MCP (JSON-RPC 2.0)
- ✅ Mismas herramientas (`check_availability`, `create_booking`, etc.)
- ✅ Mismo formato de datos
- ✅ Sin cambios en el backend de AI Assistants
- ✅ Cambio transparente mediante variable de entorno

## Ventajas de la Integración

1. **Sincronización Real**: Los eventos se crean directamente en Google Calendar
2. **Acceso Universal**: Accesible desde cualquier dispositivo con Google Calendar
3. **Notificaciones**: Google Calendar envía recordatorios automáticos
4. **Integración**: Compatible con otras herramientas de Google Workspace
5. **Backup Automático**: Los datos están en la nube de Google

## Limitaciones

1. **Rate Limits**: Google Calendar API tiene límites de requests (1,000,000 por día)
2. **Autenticación**: Requiere configuración inicial
3. **Dependencia Externa**: Requiere conexión a internet

## Próximos Pasos

1. Implementar `google_calendar_backend.py`
2. Actualizar `main.py` para usar el backend configurado
3. Agregar dependencias a `requirements.txt`
4. Crear script de configuración inicial
5. Documentar proceso de setup
