# Solución de Problemas CORS

## Error: CORS policy blocked

Si ves el error `Access to XMLHttpRequest at 'http://localhost:60000/mcp' from origin 'http://localhost:38000' has been blocked by CORS policy`, sigue estos pasos:

### 1. Verificar que el servidor MCP esté corriendo

```bash
# Calendar MCP Server (puerto 60000)
cd calendar-mcp-server
python main.py

# O usando el script
./start.sh
```

Verifica que responda:
```bash
curl http://localhost:60000/health
```

### 2. Verificar configuración CORS

Todos los servidores MCP tienen CORS configurado con `allow_origins=["*"]`, pero si el error persiste:

1. **Reinicia el servidor MCP** después de cualquier cambio
2. **Verifica que el middleware esté antes de las rutas** (ya está correcto)
3. **Limpia la caché del navegador** o usa modo incógnito

### 3. Verificar que el servidor responda a OPTIONS

El navegador envía un request OPTIONS (preflight) antes del POST. FastAPI debería manejarlo automáticamente, pero puedes verificar:

```bash
curl -X OPTIONS http://localhost:60000/mcp \
  -H "Origin: http://localhost:38000" \
  -H "Access-Control-Request-Method: POST" \
  -v
```

Deberías ver headers como:
- `Access-Control-Allow-Origin: *`
- `Access-Control-Allow-Methods: *`
- `Access-Control-Allow-Headers: *`

### 4. Solución temporal: Proxy en Vite

Si el problema persiste, puedes configurar un proxy en `vite.config.ts`:

```typescript
export default defineConfig({
  plugins: [react()],
  server: {
    port: 38000,
    proxy: {
      '/api/calendar': {
        target: 'http://localhost:60000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/calendar/, ''),
      },
    },
  },
})
```

Y luego usar `/api/calendar/mcp` en lugar de `http://localhost:60000/mcp`.

### 5. Verificar variables de entorno

Asegúrate de que las variables de entorno estén configuradas correctamente:

```bash
# En admin-frontend/.env
VITE_CALENDAR_MCP_SERVER_URL=http://localhost:60000
VITE_FLOW_MCP_SERVER_URL=http://localhost:60006
```

### 6. Verificar en DevTools

1. Abre DevTools → Network
2. Busca la petición fallida
3. Verifica los headers de la respuesta
4. Si no hay respuesta, el servidor no está corriendo

### Solución rápida

Si nada funciona, reinicia todos los servidores:

```bash
# Terminal 1: Calendar MCP Server
cd calendar-mcp-server && python main.py

# Terminal 2: Booking Flow MCP Server  
cd booking-flow-mcp-server && python main.py

# Terminal 3: Frontend
cd admin-frontend && npm run dev
```
