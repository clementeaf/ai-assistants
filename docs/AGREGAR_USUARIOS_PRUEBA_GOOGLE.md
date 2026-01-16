# Agregar Usuarios de Prueba en Google Cloud Console

## Problema
Error: "Access blocked: testing-trade has not completed the Google verification process"

Esto ocurre porque la aplicación OAuth2 está en modo de prueba y solo permite usuarios de prueba aprobados.

## Solución: Agregar Usuarios de Prueba

### Paso 1: Ir a OAuth Consent Screen

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Selecciona tu proyecto: **testing-trade** (o el nombre de tu proyecto)
3. En el menú lateral, ve a: **APIs & Services** > **OAuth consent screen**

### Paso 2: Agregar Usuarios de Prueba

1. En la sección **"Test users"** (Usuarios de prueba), haz clic en **"+ ADD USERS"** o **"+ AGREGAR USUARIOS"**
2. Ingresa el email: `carriagada@grupobanados.com`
3. Haz clic en **"ADD"** o **"AGREGAR"**
4. El usuario aparecerá en la lista de usuarios de prueba

### Paso 3: Verificar

1. El usuario `carriagada@grupobanados.com` ahora puede autorizar la aplicación
2. Intenta de nuevo el flujo de OAuth2
3. Debería funcionar correctamente

## Alternativa: Publicar la Aplicación (No Recomendado para Desarrollo)

Si quieres que cualquier usuario pueda autorizar (sin agregar manualmente):

1. Ve a **OAuth consent screen**
2. Haz clic en **"PUBLISH APP"** o **"PUBLICAR APLICACIÓN"**
3. **⚠️ ADVERTENCIA**: Esto requiere completar el proceso de verificación de Google, que puede tomar varios días y requiere información adicional (política de privacidad, términos de servicio, etc.)

**Recomendación**: Para desarrollo y pruebas, es mejor usar usuarios de prueba.

## Límites de Usuarios de Prueba

- Puedes agregar hasta **100 usuarios de prueba**
- Los usuarios de prueba pueden autorizar la aplicación sin restricciones
- No necesitas verificación de Google para usuarios de prueba

## Verificar Usuarios Agregados

1. Ve a **OAuth consent screen**
2. Busca la sección **"Test users"**
3. Verifica que `carriagada@grupobanados.com` esté en la lista

## Si el Error Persiste

1. Verifica que el email esté correctamente escrito en la lista de usuarios de prueba
2. Asegúrate de que estás iniciando sesión con el email correcto en el popup de Google
3. Espera unos minutos después de agregar el usuario (a veces hay un pequeño delay)
4. Intenta cerrar y volver a abrir el popup de autorización
