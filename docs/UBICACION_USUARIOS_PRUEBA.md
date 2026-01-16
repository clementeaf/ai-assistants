# Ubicación de Usuarios de Prueba en Google Cloud Console

## Ubicación Exacta

Cuando estás en "Pantalla de consentimiento" (OAuth consent screen), la sección de usuarios de prueba puede estar en diferentes lugares según la versión de Google Cloud Console:

### Opción 1: Menú Lateral "Clientes"

1. En el menú lateral izquierdo, haz clic en **"Clientes"** o **"Clients"**
2. Busca la sección **"Test users"** o **"Usuarios de prueba"**
3. Haz clic en **"+ ADD USERS"** o **"+ AGREGAR USUARIOS"**

### Opción 2: Directamente en la Página Principal

1. En la página de "Descripción general de OAuth"
2. Desplázate hacia abajo
3. Busca una sección llamada **"Test users"** o **"Usuarios de prueba"**
4. Haz clic en **"+ ADD USERS"** o **"+ AGREGAR USUARIOS"**

### Opción 3: Pestaña "Público"

1. En el menú lateral, haz clic en **"Público"** o **"Public"**
2. Busca la sección **"Test users"** o **"Usuarios de prueba"**

## Pasos Detallados

### Desde "Descripción general de OAuth":

1. **Haz clic en "Clientes"** en el menú lateral izquierdo
2. Busca la sección **"Test users"** o **"Usuarios de prueba"**
3. Si no la ves, desplázate hacia abajo en la página
4. Haz clic en **"+ ADD USERS"** o **"+ AGREGAR USUARIOS"**
5. Ingresa el email: `carriagada@grupobanados.com`
6. Haz clic en **"ADD"** o **"AGREGAR"**

## Si No Encuentras la Sección

La sección "Test users" solo aparece si:
- Tu aplicación está en modo de prueba (no publicada)
- Estás en la pantalla de consentimiento OAuth

**Alternativa**: Si no encuentras "Test users", verifica que:
1. Estás en el proyecto correcto: **trade-462111**
2. Estás en "APIs & Services" > "OAuth consent screen"
3. Tu aplicación está en modo "Testing" (no "Published")

## URL Directa

Si tienes problemas encontrándola, puedes intentar ir directamente a:
```
https://console.cloud.google.com/apis/credentials/consent?project=trade-462111
```

Y luego buscar "Test users" o "Usuarios de prueba" en esa página.
