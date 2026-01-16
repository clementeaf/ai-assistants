# Pasos para Agregar Usuario de Prueba

## Paso 1: Ir a Pantalla de Consentimiento

En el menú lateral izquierdo, haz clic en:
**"Pantalla de consentimiento..."** o **"OAuth consent screen"**

(No estás en "Credenciales", necesitas ir a la pantalla de consentimiento)

## Paso 2: Buscar Sección "Test users"

Una vez en la pantalla de consentimiento:
1. Desplázate hacia abajo
2. Busca la sección **"Test users"** o **"Usuarios de prueba"**
3. Deberías ver un botón **"+ ADD USERS"** o **"+ AGREGAR USUARIOS"**

## Paso 3: Agregar Email

1. Haz clic en **"+ ADD USERS"** o **"+ AGREGAR USUARIOS"**
2. Se abrirá un campo de texto
3. Ingresa el email: `carriagada@grupobanados.com`
4. Haz clic en **"ADD"** o **"AGREGAR"**
5. El email aparecerá en la lista de usuarios de prueba

## Paso 4: Guardar

- Los cambios se guardan automáticamente
- No necesitas hacer nada más

## Paso 5: Probar

1. Vuelve a tu Admin-Frontend
2. Intenta conectar el calendario de nuevo
3. El error 403 debería desaparecer
4. El usuario `carriagada@grupobanados.com` podrá autorizar

## Ubicación Exacta

```
Google Cloud Console
  └─ APIs & Services (APIs y servicios)
      └─ OAuth consent screen (Pantalla de consentimiento) ← AQUÍ
          └─ Test users (Usuarios de prueba) ← AQUÍ agregas el email
```

## Nota

El ícono de advertencia amarillo en "Clemente" es normal - indica que la app está en modo de prueba. Eso es correcto para usuarios de prueba.
