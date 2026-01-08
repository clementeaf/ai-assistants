# Solución de Problemas de WebSocket

## Error: WebSocket connection failed

Si ves el error `WebSocket connection to 'ws://localhost:8000/v1/ws/conversations/...' failed`, sigue estos pasos:

### 1. Verificar que el servidor backend esté corriendo

```bash
# Desde el directorio backend
cd backend
python run_server.py
```

O usando el script de inicio:
```bash
./start.sh
```

El servidor debe estar corriendo en `http://localhost:8000`

### 2. Verificar la configuración de la URL

Asegúrate de que la variable de entorno esté configurada correctamente:

```bash
# En el frontend (.env o .env.local)
VITE_API_BASE_URL=http://localhost:8000
```

### 3. Verificar que el endpoint WebSocket esté disponible

Puedes probar manualmente la conexión WebSocket usando herramientas como:

- **Browser DevTools**: Abre la consola y ejecuta:
```javascript
const ws = new WebSocket('ws://localhost:8000/v1/ws/conversations/test?api_key=dev');
ws.onopen = () => console.log('Connected');
ws.onerror = (e) => console.error('Error:', e);
```

- **wscat** (si está instalado):
```bash
wscat -c ws://localhost:8000/v1/ws/conversations/test?api_key=dev
```

### 4. Verificar autenticación

Si la autenticación está habilitada, necesitas:

1. Configurar `AI_ASSISTANTS_API_KEYS` en el backend
2. Obtener una API key válida
3. Configurarla en el frontend (localStorage o variable de entorno)

Para desarrollo, puedes deshabilitar la autenticación no configurando `AI_ASSISTANTS_API_KEYS`.

### 5. Verificar CORS

El backend debe tener CORS configurado para permitir conexiones desde el frontend. FastAPI maneja esto automáticamente, pero verifica que no haya restricciones adicionales.

### 6. Verificar firewall/proxy

Asegúrate de que no haya firewall o proxy bloqueando las conexiones WebSocket en el puerto 8000.

### 7. Verificar logs del servidor

Revisa los logs del servidor backend para ver si hay errores específicos cuando intentas conectarte.

### Solución rápida para desarrollo

Si estás en desarrollo y quieres deshabilitar la autenticación temporalmente:

1. No configures `AI_ASSISTANTS_API_KEYS` en el backend
2. El código automáticamente usará modo "dev" sin autenticación

### Códigos de error comunes

- **1006**: Conexión cerrada anormalmente (servidor no disponible)
- **1008**: Error de autenticación
- **1011**: Error interno del servidor
