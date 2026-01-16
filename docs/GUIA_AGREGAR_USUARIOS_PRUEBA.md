# Guía Rápida: Agregar Usuarios de Prueba

## Pasos Rápidos

### 1. Ir a Google Cloud Console
- URL: https://console.cloud.google.com/apis/credentials/consent
- Selecciona tu proyecto: **testing-trade**

### 2. Agregar Usuario de Prueba
1. Busca la sección **"Test users"** o **"Usuarios de prueba"**
2. Haz clic en **"+ ADD USERS"** o **"+ AGREGAR USUARIOS"**
3. Ingresa el email del cliente (ej: `carriagada@grupobanados.com`)
4. Haz clic en **"ADD"** o **"AGREGAR"**
5. El usuario aparecerá en la lista

### 3. Verificar
- El usuario ahora puede autorizar la aplicación
- No necesitas esperar verificación de Google
- Funciona inmediatamente

## Proceso para Cada Nuevo Cliente

Cuando tengas un nuevo cliente:

1. **Obtén el email del cliente** (ej: `nuevo-cliente@empresa.com`)
2. **Agrega en Google Cloud Console**:
   - Ve a OAuth consent screen
   - Agrega el email en "Test users"
3. **En tu Admin-Frontend**:
   - Agrega el cliente con su email
   - Haz clic en "Conectar Calendario"
   - El cliente puede autorizar inmediatamente

## Límites

- ✅ **Hasta 100 usuarios de prueba**
- ✅ **Sin límite de tiempo**
- ✅ **Funciona inmediatamente**
- ✅ **No requiere verificación de Google**

## Ventajas para tu Caso

- ✅ Perfecto para empezar con pocos clientes
- ✅ No necesitas crear política de privacidad ahora
- ✅ No necesitas términos de servicio ahora
- ✅ Puedes agregar clientes sobre la marcha
- ✅ Cuando tengas más de 100 clientes, puedes publicar la app

## Nota Importante

Cuando agregues un nuevo cliente:
1. **Primero** agrégalo en Google Cloud Console (Test users)
2. **Luego** agrégalo en tu Admin-Frontend
3. **Finalmente** el cliente puede autorizar

Si el cliente intenta autorizar antes de agregarlo en Google Cloud Console, verá el error 403.

## Checklist para Nuevo Cliente

- [ ] Cliente te proporciona su email de Google
- [ ] Agregas el email en Google Cloud Console > Test users
- [ ] Agregas el cliente en Admin-Frontend (`/clientes`)
- [ ] Generas el link de autorización
- [ ] Cliente autoriza su calendario
- [ ] Verificas que el estado sea "Conectado" en Admin-Frontend

## Ejemplo de Flujo Completo

**Cliente: "Carriagada - Grupo Bañados"**

1. Email: `carriagada@grupobanados.com`
2. Agregar en Google Cloud Console:
   - OAuth consent screen > Test users > + ADD USERS
   - Email: `carriagada@grupobanados.com`
3. Agregar en Admin-Frontend:
   - ID: `empresa-carriagada`
   - Email: `carriagada@grupobanados.com`
   - Nombre: `Carriagada - Grupo Bañados`
4. Conectar:
   - Click en "Conectar Calendario"
   - Modal aparece con opciones
   - Cliente autoriza con su cuenta Google
5. Verificar:
   - Estado: "Conectado" ✅
   - Calendar Email: `carriagada@grupobanados.com`

¡Listo! El asistente IA puede usar ese calendario.
