# Reglas de React TypeScript - APLICACIÓN AUTOMÁTICA

**IMPORTANTE**: Estas reglas deben aplicarse AUTOMÁTICAMENTE en cada solicitud de código React TypeScript.

## Configuración Estricta de TypeScript

### 1. Prohibición de `any`
- **Nunca usar `any`**: El tipo `any` desactiva completamente el sistema de tipos
- **Alternativas recomendadas**:
  - `unknown` para valores de tipo desconocido
  - Tipos específicos cuando sea posible
  - Uniones de tipos para múltiples posibilidades
  - `React.ReactNode` para contenido de React

### 2. Prohibición de `implicit any`
- **Todos los tipos deben ser explícitos**
- **Configuración de TypeScript**:
  ```json
  {
    "compilerOptions": {
      "noImplicitAny": true,
      "strict": true,
      "strictNullChecks": true,
      "strictFunctionTypes": true,
      "noImplicitReturns": true
    }
  }
  ```

### 3. Tipado de Componentes React
- **Props**: Todos los props deben tener tipos explícitos usando `interface` o `type`
- **Estado**: Tipar explícitamente el estado con `useState<T>()`
- **Refs**: Usar tipos genéricos para refs: `useRef<HTMLElement>(null)`
- **Event Handlers**: Tipar eventos: `(e: React.ChangeEvent<HTMLInputElement>) => void`

### 4. Componentes Funcionales
- **Siempre usar componentes funcionales** (no clases)
- **Tipar el valor de retorno**: `JSX.Element` o dejar que TypeScript infiera
- **Usar `React.FC` solo cuando sea necesario**, preferir funciones normales con tipos explícitos

## Principios de Desarrollo

### 1. SOLID, DRY y YAGNI
- **SOLID**: Aplicar principios de diseño
- **DRY**: Evitar duplicación de código
- **YAGNI**: No implementar funcionalidad innecesaria

### 2. Componentes
- **Componentes pequeños y enfocados**: Una responsabilidad por componente
- **Props tipados**: Siempre definir interfaces para props
- **Composición sobre herencia**: Preferir composición de componentes

### 3. Hooks
- **Tipar hooks personalizados**: Especificar tipos de entrada y salida
- **Dependencias explícitas**: Incluir todas las dependencias en arrays de dependencias
- **Reglas de Hooks**: Seguir las reglas de React Hooks

## Documentación

### 1. Comentarios de Funciones y Componentes
- **Solo JSDoc como encabezado**: Únicamente comentarios de documentación
- **Formato estándar**:
  ```typescript
  /**
   * Descripción breve del componente
   * @param props - Props del componente
   * @returns Elemento JSX
   */
  ```

### 2. Prohibición de Emojis
- **Sin emojis en código**: No usar emojis en:
  - Comentarios
  - Nombres de variables
  - Nombres de funciones
  - Strings de la aplicación
  - Mensajes de log

### 3. Código Autodocumentado
- **Nombres descriptivos**: Variables y funciones con nombres claros
- **Estructura clara**: Código organizado y legible
- **Evitar comentarios innecesarios**: El código debe ser autoexplicativo

## Desarrollo de Funciones y Componentes

### 1. Prohibición de TODOs
- **No generar funciones con contenido "TODO"**
- **Si no hay claridad**: Preguntar antes de implementar
- **Funciones completas**: Cada función debe estar totalmente implementada

### 2. Componentes Completos
- **Componentes funcionales**: Cada componente debe tener una implementación completa
- **Manejo de estados**: Tipar correctamente todos los estados
- **Props validation**: Usar TypeScript para validar props (no PropTypes)

## Ejemplos de Buenas Prácticas

### ✅ Correcto
```typescript
interface ButtonProps {
  label: string;
  onClick: () => void;
  disabled?: boolean;
}

/**
 * Botón reutilizable con estilos personalizados
 * @param props - Props del botón
 * @returns Botón renderizado
 */
function Button({ label, onClick, disabled = false }: ButtonProps) {
  return (
    <button onClick={onClick} disabled={disabled}>
      {label}
    </button>
  );
}
```

### ❌ Incorrecto
```typescript
// ❌ Uso de any
function Button(props: any) {
  return <button>{props.label}</button>;
}

// ❌ Sin tipos explícitos
function Button({ label, onClick }) {
  return <button onClick={onClick}>{label}</button>;
}

// ❌ Componente con TODO
function Button() {
  // TODO: implementar lógica
  return <button>Button</button>;
}
```

## INSTRUCCIONES AUTOMÁTICAS PARA EL ASISTENTE

**EN CADA RESPUESTA DE CÓDIGO REACT TYPESCRIPT**:

1. **NUNCA** usar `any` - usar tipos específicos o `unknown`
2. **SIEMPRE** tipar explícitamente todos los props con interfaces
3. **SIEMPRE** tipar el estado con `useState<T>()`
4. **SIEMPRE** tipar event handlers correctamente
5. **SIEMPRE** agregar comentarios JSDoc a componentes
6. **NUNCA** incluir emojis en código
7. **NUNCA** dejar componentes con contenido "TODO"
8. **SIEMPRE** implementar componentes completamente
9. **SIEMPRE** seguir principios SOLID, DRY y YAGNI
10. **SIEMPRE** usar componentes funcionales (no clases)

