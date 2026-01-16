# Publicar Aplicación OAuth2 en Google Cloud Console

## ¿Por qué Publicar?

Cuando publicas tu aplicación OAuth2, **cualquier usuario de Google puede autorizarla** sin necesidad de agregarlos manualmente como usuarios de prueba. Esto es esencial para un servicio comercial.

## Requisitos para Publicar

### 1. Información de la Aplicación
- ✅ Nombre de la aplicación (ya tienes: "testing-trade")
- ✅ Email de soporte
- ✅ Logo de la aplicación (opcional pero recomendado)
- ✅ Dominio autorizado (si aplica)

### 2. Política de Privacidad (OBLIGATORIO)
- Debe ser una URL pública accesible
- Debe explicar qué datos recopilas y cómo los usas
- Debe cumplir con GDPR si tienes usuarios en Europa

**Ejemplo de contenido mínimo:**
```
- Qué datos recopilamos (email, acceso a calendario)
- Cómo usamos los datos (para gestionar reservas)
- Cómo protegemos los datos
- Cómo contactar para eliminar datos
```

### 3. Términos de Servicio (OBLIGATORIO)
- URL pública accesible
- Condiciones de uso del servicio

### 4. Ámbitos (Scopes) Solicitados
- Actualmente solicitas: `https://www.googleapis.com/auth/calendar`
- Debes justificar por qué necesitas este acceso

## Pasos para Publicar

### Paso 1: Preparar Política de Privacidad y Términos

**Opción A: Crear páginas web simples**
1. Crea un sitio web simple (puede ser GitHub Pages, Netlify, etc.)
2. Crea `/privacy-policy.html` y `/terms-of-service.html`
3. Publica las URLs

**Opción B: Usar generadores**
- [Privacy Policy Generator](https://www.privacypolicygenerator.info/)
- [Terms of Service Generator](https://www.termsofservicegenerator.net/)

**Opción C: Usar servicios gratuitos**
- GitHub Pages
- Netlify
- Vercel

### Paso 2: Completar OAuth Consent Screen

1. Ve a: https://console.cloud.google.com/apis/credentials/consent
2. Completa todas las secciones:
   - **App information**: Nombre, logo, email de soporte
   - **App domain**: Tu dominio (si tienes)
   - **Authorized domains**: Dominios autorizados
   - **Developer contact information**: Tu email

### Paso 3: Agregar URLs Requeridas

1. En **OAuth consent screen**, busca:
   - **Privacy Policy URL**: `https://tudominio.com/privacy-policy`
   - **Terms of Service URL**: `https://tudominio.com/terms-of-service`
   - **Authorized domains**: Agrega tu dominio (ej: `tudominio.com`)

### Paso 4: Justificar Ámbitos

1. En la sección de **Scopes**, haz clic en cada scope
2. Justifica por qué necesitas ese acceso:
   - Para `calendar`: "Necesitamos acceso al calendario para gestionar reservas y citas de los clientes"

### Paso 5: Enviar para Verificación

1. Haz clic en **"PUBLISH APP"** o **"PUBLICAR APLICACIÓN"**
2. Google revisará tu solicitud (puede tomar varios días)
3. Mientras tanto, puedes seguir usando usuarios de prueba

## Alternativa Temporal: Agregar Múltiples Usuarios de Prueba

Mientras completas la verificación, puedes agregar hasta 100 usuarios de prueba:

### Método Manual
1. Ve a **OAuth consent screen** > **Test users**
2. Haz clic en **"+ ADD USERS"**
3. Agrega emails uno por uno (hasta 100)

### Método con CSV (si Google lo permite)
Algunas veces Google permite importar usuarios desde un CSV, pero esto no siempre está disponible.

## Recomendación

**Para un servicio comercial:**
1. **Corto plazo**: Agrega usuarios de prueba manualmente (hasta 100)
2. **Mediano plazo**: Prepara política de privacidad y términos de servicio
3. **Largo plazo**: Publica la aplicación para que cualquier usuario pueda autorizar

## Checklist de Publicación

- [ ] Política de privacidad publicada (URL pública)
- [ ] Términos de servicio publicados (URL pública)
- [ ] Logo de la aplicación (opcional)
- [ ] Email de soporte configurado
- [ ] Dominio autorizado configurado
- [ ] Ámbitos justificados
- [ ] Información de la aplicación completa
- [ ] Solicitud de publicación enviada

## Tiempo de Verificación

- **Típicamente**: 1-7 días hábiles
- **Puede ser más rápido**: Si la aplicación es simple y los scopes son estándar
- **Puede ser más lento**: Si Google necesita más información

## Mientras Esperas la Verificación

- Puedes seguir usando usuarios de prueba (hasta 100)
- La aplicación funcionará normalmente para usuarios de prueba
- Una vez verificada, funcionará para cualquier usuario
