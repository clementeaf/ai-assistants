# Reglas de Arquitectura: HOC, Flex, Props y Componentes Reutilizables - APLICACIÓN AUTOMÁTICA

**IMPORTANTE**: Estas reglas deben aplicarse AUTOMÁTICAMENTE en cada desarrollo de arquitectura de componentes.

## Higher Order Components (HOC)

### 1. Definición y Propósito
- **HOC**: Función que toma un componente y retorna un nuevo componente con funcionalidad adicional
- **Uso**: Reutilizar lógica entre componentes sin duplicar código
- **Principio**: Composición sobre herencia

### 2. Estructura de HOC
- **Tipado correcto**: Usar tipos genéricos para preservar tipos del componente original
- **Preservar props**: Mantener todas las props del componente original
- **Nomenclatura**: Prefijo `with`: `withAuth`, `withLoading`, `withErrorBoundary`

```typescript
import React from 'react';

/**
 * HOC que agrega funcionalidad de autenticación
 * @param Component - Componente a envolver
 * @returns Componente con autenticación
 */
function withAuth<P extends object>(
  Component: React.ComponentType<P>
) {
  return function AuthenticatedComponent(props: P) {
    const [isAuthenticated, setIsAuthenticated] = React.useState(false);
    const [loading, setLoading] = React.useState(true);

    React.useEffect(() => {
      // Lógica de autenticación
      checkAuth().then(auth => {
        setIsAuthenticated(auth);
        setLoading(false);
      });
    }, []);

    if (loading) {
      return <div>Loading...</div>;
    }

    if (!isAuthenticated) {
      return <div>Please log in</div>;
    }

    return <Component {...props} />;
  };
}

// Uso:
interface UserProfileProps {
  userId: string;
  name: string;
}

function UserProfile({ userId, name }: UserProfileProps) {
  return <div>Profile: {name}</div>;
}

const AuthenticatedUserProfile = withAuth(UserProfile);
```

### 3. HOC con Props Adicionales
- **Tipar props adicionales**: Especificar qué props adicionales agrega el HOC
- **Merge de props**: Combinar props del componente original con props del HOC

```typescript
interface WithLoadingProps {
  loading: boolean;
  loadingText?: string;
}

function withLoading<P extends object>(
  Component: React.ComponentType<P>
) {
  return function ComponentWithLoading(
    props: P & WithLoadingProps
  ) {
    const { loading, loadingText = 'Loading...', ...componentProps } = props;

    if (loading) {
      return <div>{loadingText}</div>;
    }

    return <Component {...(componentProps as P)} />;
  };
}

// Uso:
interface DataDisplayProps {
  data: string[];
}

function DataDisplay({ data }: DataDisplayProps) {
  return <ul>{data.map(item => <li key={item}>{item}</li>)}</ul>;
}

const DataDisplayWithLoading = withLoading(DataDisplay);
```

### 4. HOC con Ref Forwarding
- **forwardRef**: Usar cuando el HOC necesita pasar refs al componente interno
- **Tipar refs correctamente**: Especificar el tipo del elemento ref

```typescript
function withClickOutside<P extends object>(
  Component: React.ComponentType<P>
) {
  return React.forwardRef<HTMLElement, P & { onOutsideClick: () => void }>(
    function ComponentWithClickOutside(props, ref) {
      const { onOutsideClick, ...componentProps } = props;
      const containerRef = React.useRef<HTMLElement>(null);

      React.useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
          if (
            containerRef.current &&
            !containerRef.current.contains(event.target as Node)
          ) {
            onOutsideClick();
          }
        }

        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
      }, [onOutsideClick]);

      return (
        <div ref={containerRef as React.RefObject<HTMLDivElement>}>
          <Component {...(componentProps as P)} ref={ref} />
        </div>
      );
    }
  );
}
```

## Arquitectura Flex (Flexible Components)

### 1. Principios de Diseño Flexible
- **Composición**: Componentes pequeños que se combinan
- **Configurabilidad**: Props que permiten múltiples variaciones
- **Extensibilidad**: Fácil de extender sin modificar el componente base

### 2. Patrón de Componentes Flexibles
- **Props polimórficos**: Permitir diferentes tipos de contenido
- **Variantes**: Sistema de variantes para diferentes estilos/comportamientos
- **Slots**: Usar children y render props para contenido flexible

```typescript
type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'ghost';
type ButtonSize = 'sm' | 'md' | 'lg';

interface FlexibleButtonProps {
  variant?: ButtonVariant;
  size?: ButtonSize;
  children: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  fullWidth?: boolean;
  className?: string;
}

/**
 * Botón flexible con múltiples variantes y configuraciones
 * @param props - Props del botón flexible
 * @returns Botón renderizado
 */
function FlexibleButton({
  variant = 'primary',
  size = 'md',
  children,
  onClick,
  disabled = false,
  leftIcon,
  rightIcon,
  fullWidth = false,
  className = '',
}: FlexibleButtonProps) {
  const baseClasses = 'button';
  const variantClasses = `button--${variant}`;
  const sizeClasses = `button--${size}`;
  const widthClasses = fullWidth ? 'button--full-width' : '';

  return (
    <button
      className={`${baseClasses} ${variantClasses} ${sizeClasses} ${widthClasses} ${className}`}
      onClick={onClick}
      disabled={disabled}
    >
      {leftIcon && <span className="button__icon-left">{leftIcon}</span>}
      {children}
      {rightIcon && <span className="button__icon-right">{rightIcon}</span>}
    </button>
  );
}
```

### 3. Sistema de Variantes con Type Safety
- **Constantes tipadas**: Usar `as const` para inferencia de tipos
- **Uniones de tipos**: Definir variantes como uniones de tipos literales
- **Validación en tiempo de compilación**: TypeScript valida variantes

```typescript
const BUTTON_VARIANTS = {
  primary: 'primary',
  secondary: 'secondary',
  danger: 'danger',
} as const;

type ButtonVariant = typeof BUTTON_VARIANTS[keyof typeof BUTTON_VARIANTS];

interface ButtonProps {
  variant: ButtonVariant;
  // ...
}
```

### 4. Componentes Polimórficos
- **Component prop**: Permitir cambiar el elemento HTML base
- **Preservar tipos**: Mantener tipos correctos según el elemento

```typescript
type PolymorphicComponentProps<T extends React.ElementType> = {
  as?: T;
  children: React.ReactNode;
} & React.ComponentPropsWithoutRef<T>;

/**
 * Componente polimórfico que puede renderizarse como diferentes elementos
 */
function PolymorphicComponent<T extends React.ElementType = 'div'>({
  as,
  children,
  ...props
}: PolymorphicComponentProps<T>) {
  const Component = as || 'div';
  return <Component {...props}>{children}</Component>;
}

// Uso:
<PolymorphicComponent as="button" onClick={handleClick}>
  Click me
</PolymorphicComponent>
<PolymorphicComponent as="a" href="/link">
  Link
</PolymorphicComponent>
```

## Uso de Props

### 1. Diseño de Props
- **Props mínimas**: Solo props necesarias, evitar props excesivas
- **Props opcionales**: Usar `?` para props no requeridas
- **Valores por defecto**: Proporcionar valores por defecto sensatos
- **Props compuestas**: Agrupar props relacionadas en objetos

```typescript
// ❌ Mal: Demasiadas props individuales
interface BadComponentProps {
  paddingTop?: number;
  paddingRight?: number;
  paddingBottom?: number;
  paddingLeft?: number;
  marginTop?: number;
  marginRight?: number;
  marginBottom?: number;
  marginLeft?: number;
}

// ✅ Bien: Props agrupadas
interface Spacing {
  top?: number;
  right?: number;
  bottom?: number;
  left?: number;
}

interface GoodComponentProps {
  padding?: Spacing | number; // Permite objeto o número único
  margin?: Spacing | number;
}
```

### 2. Props con Valores por Defecto
- **Destructuring con defaults**: Usar valores por defecto en destructuring
- **Valores seguros**: Proporcionar valores que no rompan la funcionalidad

```typescript
interface CardProps {
  title: string;
  description?: string;
  elevation?: 0 | 1 | 2 | 3 | 4;
  rounded?: boolean;
  onClick?: () => void;
}

function Card({
  title,
  description = '',
  elevation = 1,
  rounded = true,
  onClick,
}: CardProps) {
  // ...
}
```

### 3. Props Condicionales
- **Tipos condicionales**: Usar tipos condicionales para props que dependen de otras
- **Discriminated unions**: Para variantes mutuamente excluyentes

```typescript
type ButtonProps =
  | {
      variant: 'link';
      href: string;
      onClick?: never;
    }
  | {
      variant: 'button';
      href?: never;
      onClick: () => void;
    };

function Button(props: ButtonProps) {
  if (props.variant === 'link') {
    return <a href={props.href}>Link</a>;
  }
  return <button onClick={props.onClick}>Button</button>;
}
```

### 4. Props de Renderizado
- **Render props**: Funciones que retornan JSX
- **Children como función**: Permite máxima flexibilidad

```typescript
interface RenderPropsComponentProps<T> {
  data: T[];
  renderItem: (item: T, index: number) => React.ReactNode;
  renderEmpty?: () => React.ReactNode;
}

function RenderPropsComponent<T>({
  data,
  renderItem,
  renderEmpty,
}: RenderPropsComponentProps<T>) {
  if (data.length === 0) {
    return renderEmpty ? renderEmpty() : <div>No items</div>;
  }

  return (
    <ul>
      {data.map((item, index) => (
        <li key={index}>{renderItem(item, index)}</li>
      ))}
    </ul>
  );
}
```

## Componentes UI/UX Agnósticos Reutilizables

### 1. Principios de Componentes Agnósticos
- **Sin dependencias de estilo**: No asumir framework CSS específico
- **Props de estilo**: Permitir inyección de clases/estilos
- **Tema agnóstico**: No hardcodear colores, tamaños, etc.
- **Comportamiento puro**: Lógica de UI sin dependencias externas

### 2. Estructura de Componente Agnóstico
- **Props de estilo**: `className`, `style`, `css` según necesidad
- **Props de tema**: Permitir inyección de tokens de diseño
- **Sin estilos inline hardcodeados**: Usar props o CSS variables

```typescript
interface AgnosticButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  className?: string;
  style?: React.CSSProperties;
  variant?: string; // String genérico, no valores específicos
  'data-testid'?: string;
  ariaLabel?: string;
}

/**
 * Botón agnóstico sin dependencias de estilo
 * Los estilos deben ser proporcionados externamente
 */
function AgnosticButton({
  children,
  onClick,
  disabled = false,
  className = '',
  style,
  variant,
  'data-testid': testId,
  ariaLabel,
}: AgnosticButtonProps) {
  return (
    <button
      className={className}
      style={style}
      onClick={onClick}
      disabled={disabled}
      data-variant={variant}
      data-testid={testId}
      aria-label={ariaLabel}
    >
      {children}
    </button>
  );
}
```

### 3. Sistema de Tokens de Diseño
- **CSS Variables**: Usar variables CSS para temas
- **Props de tokens**: Permitir inyección de tokens de diseño
- **Valores por defecto**: Proporcionar tokens por defecto

```typescript
interface DesignTokens {
  colors: {
    primary: string;
    secondary: string;
    text: string;
    background: string;
  };
  spacing: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
  };
  typography: {
    fontFamily: string;
    fontSize: {
      sm: string;
      md: string;
      lg: string;
    };
  };
}

interface ThemedComponentProps {
  children: React.ReactNode;
  tokens?: Partial<DesignTokens>;
  className?: string;
}

function ThemedComponent({
  children,
  tokens,
  className = '',
}: ThemedComponentProps) {
  const defaultTokens: DesignTokens = {
    colors: {
      primary: 'var(--color-primary, #007bff)',
      secondary: 'var(--color-secondary, #6c757d)',
      text: 'var(--color-text, #212529)',
      background: 'var(--color-background, #ffffff)',
    },
    spacing: {
      xs: 'var(--spacing-xs, 0.25rem)',
      sm: 'var(--spacing-sm, 0.5rem)',
      md: 'var(--spacing-md, 1rem)',
      lg: 'var(--spacing-lg, 1.5rem)',
    },
    typography: {
      fontFamily: 'var(--font-family, sans-serif)',
      fontSize: {
        sm: 'var(--font-size-sm, 0.875rem)',
        md: 'var(--font-size-md, 1rem)',
        lg: 'var(--font-size-lg, 1.25rem)',
      },
    },
  };

  const mergedTokens = { ...defaultTokens, ...tokens };

  return (
    <div
      className={className}
      style={{
        '--color-primary': mergedTokens.colors.primary,
        '--color-secondary': mergedTokens.colors.secondary,
        '--color-text': mergedTokens.colors.text,
        '--color-background': mergedTokens.colors.background,
      } as React.CSSProperties}
    >
      {children}
    </div>
  );
}
```

### 4. Componentes Headless (Sin UI)
- **Solo lógica**: Componentes que proporcionan solo lógica y estado
- **Render prop**: El consumidor controla el renderizado
- **Hooks personalizados**: Alternativa a componentes headless

```typescript
interface UseToggleReturn {
  isOn: boolean;
  toggle: () => void;
  turnOn: () => void;
  turnOff: () => void;
}

/**
 * Hook headless para funcionalidad de toggle
 * No incluye UI, solo lógica
 */
function useToggle(initialState = false): UseToggleReturn {
  const [isOn, setIsOn] = React.useState(initialState);

  const toggle = React.useCallback(() => setIsOn(prev => !prev), []);
  const turnOn = React.useCallback(() => setIsOn(true), []);
  const turnOff = React.useCallback(() => setIsOn(false), []);

  return { isOn, toggle, turnOn, turnOff };
}

// Componente headless con render prop
interface ToggleProps {
  initialState?: boolean;
  children: (state: UseToggleReturn) => React.ReactNode;
}

function Toggle({ initialState = false, children }: ToggleProps) {
  const toggleState = useToggle(initialState);
  return <>{children(toggleState)}</>;
}

// Uso:
<Toggle>
  {({ isOn, toggle }) => (
    <button onClick={toggle}>
      {isOn ? 'ON' : 'OFF'}
    </button>
  )}
</Toggle>
```

### 5. Componentes Compuestos Agnósticos
- **Composición flexible**: Componentes que se combinan sin acoplamiento
- **Context opcional**: Usar Context para compartir estado sin hardcodear

```typescript
interface AccordionContextValue {
  openItems: Set<string>;
  toggleItem: (id: string) => void;
}

const AccordionContext = React.createContext<AccordionContextValue | null>(null);

function useAccordionContext() {
  const context = React.useContext(AccordionContext);
  if (!context) {
    throw new Error('Accordion components must be used within Accordion');
  }
  return context;
}

interface AccordionProps {
  children: React.ReactNode;
  allowMultiple?: boolean;
  defaultOpen?: string[];
}

function Accordion({
  children,
  allowMultiple = false,
  defaultOpen = [],
}: AccordionProps) {
  const [openItems, setOpenItems] = React.useState<Set<string>>(
    new Set(defaultOpen)
  );

  const toggleItem = React.useCallback((id: string) => {
    setOpenItems(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        if (!allowMultiple) {
          next.clear();
        }
        next.add(id);
      }
      return next;
    });
  }, [allowMultiple]);

  return (
    <AccordionContext.Provider value={{ openItems, toggleItem }}>
      <div className="accordion">{children}</div>
    </AccordionContext.Provider>
  );
}

interface AccordionItemProps {
  id: string;
  children: React.ReactNode;
}

function AccordionItem({ id, children }: AccordionItemProps) {
  const { openItems, toggleItem } = useAccordionContext();
  const isOpen = openItems.has(id);

  return (
    <div className="accordion-item">
      <button onClick={() => toggleItem(id)}>
        {isOpen ? '▼' : '▶'}
      </button>
      {isOpen && <div className="accordion-content">{children}</div>}
    </div>
  );
}

Accordion.Item = AccordionItem;

// Uso:
<Accordion allowMultiple>
  <Accordion.Item id="1">Content 1</Accordion.Item>
  <Accordion.Item id="2">Content 2</Accordion.Item>
</Accordion>
```

## INSTRUCCIONES AUTOMÁTICAS PARA EL ASISTENTE

**EN CADA DESARROLLO DE ARQUITECTURA DE COMPONENTES**:

### HOC:
1. **SIEMPRE** tipar HOC con tipos genéricos
2. **SIEMPRE** preservar props del componente original
3. **SIEMPRE** usar prefijo `with` en nombres
4. **SIEMPRE** usar `forwardRef` cuando sea necesario

### Arquitectura Flex:
1. **SIEMPRE** diseñar componentes con composición en mente
2. **SIEMPRE** usar variantes tipadas con `as const`
3. **SIEMPRE** permitir props polimórficas cuando sea apropiado
4. **SIEMPRE** usar render props para máxima flexibilidad

### Props:
1. **SIEMPRE** minimizar número de props
2. **SIEMPRE** agrupar props relacionadas
3. **SIEMPRE** usar valores por defecto apropiados
4. **SIEMPRE** usar tipos condicionales para props dependientes

### Componentes Agnósticos:
1. **SIEMPRE** permitir inyección de estilos (className, style)
2. **NUNCA** hardcodear estilos específicos
3. **SIEMPRE** usar CSS variables para temas
4. **SIEMPRE** proporcionar componentes headless cuando sea apropiado
5. **SIEMPRE** usar Context para estado compartido sin acoplamiento
6. **SIEMPRE** hacer componentes reutilizables sin dependencias de UI específica

