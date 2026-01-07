# Reglas de Desarrollo de Componentes React - APLICACIÓN AUTOMÁTICA

**IMPORTANTE**: Estas reglas deben aplicarse AUTOMÁTICAMENTE en cada desarrollo de componente React.

## Estructura de Componentes

### 1. Organización de Archivos
- **Un componente por archivo**: Cada componente debe estar en su propio archivo
- **Nomenclatura**: Usar PascalCase para nombres de archivos: `Button.tsx`, `UserProfile.tsx`
- **Carpetas de componentes**: Agrupar componentes relacionados en carpetas:
  ```
  components/
    Button/
      Button.tsx
      Button.test.tsx
      Button.module.css (si aplica)
    UserProfile/
      UserProfile.tsx
      UserProfile.test.tsx
  ```

### 2. Estructura Interna del Componente
- **Orden de elementos**:
  1. Imports (React, librerías, tipos, utilidades, estilos)
  2. Tipos e interfaces
  3. Constantes del componente
  4. Componente principal
  5. Hooks personalizados (si aplica)
  6. Funciones auxiliares
  7. Exports

### 3. Ejemplo de Estructura
```typescript
// 1. Imports
import React, { useState, useEffect } from 'react';
import type { User } from '@/types/user';
import { formatDate } from '@/utils/date';
import './Button.css';

// 2. Tipos e interfaces
interface ButtonProps {
  label: string;
  onClick: () => void;
  variant?: 'primary' | 'secondary';
  disabled?: boolean;
}

// 3. Constantes
const BUTTON_VARIANTS = {
  primary: 'btn-primary',
  secondary: 'btn-secondary',
} as const;

// 4. Componente principal
/**
 * Botón reutilizable con múltiples variantes
 * @param props - Props del botón
 * @returns Botón renderizado
 */
function Button({ 
  label, 
  onClick, 
  variant = 'primary', 
  disabled = false 
}: ButtonProps) {
  const [isPressed, setIsPressed] = useState(false);

  const handleClick = () => {
    if (!disabled) {
      setIsPressed(true);
      onClick();
      setTimeout(() => setIsPressed(false), 150);
    }
  };

  return (
    <button
      className={`${BUTTON_VARIANTS[variant]} ${isPressed ? 'pressed' : ''}`}
      onClick={handleClick}
      disabled={disabled}
      aria-label={label}
    >
      {label}
    </button>
  );
}

// 5. Export
export default Button;
```

## Tipado de Componentes

### 1. Props
- **Siempre definir interface/type para props**: Nunca usar props sin tipar
- **Props opcionales**: Usar `?` para props opcionales
- **Props requeridos**: Sin `?` para props obligatorios
- **Valores por defecto**: Usar destructuring con valores por defecto

```typescript
interface CardProps {
  title: string;              // Requerido
  description?: string;       // Opcional
  onClick?: () => void;       // Opcional
  variant?: 'default' | 'compact'; // Opcional con valores específicos
}

function Card({ 
  title, 
  description = '', 
  onClick, 
  variant = 'default' 
}: CardProps) {
  // ...
}
```

### 2. Estado
- **Tipar explícitamente useState**: `useState<string>('')` en lugar de `useState('')`
- **Estado complejo**: Usar interfaces para objetos de estado
- **Estado derivado**: Preferir `useMemo` para cálculos costosos

```typescript
interface FormState {
  email: string;
  password: string;
  errors: Record<string, string>;
}

function LoginForm() {
  const [formState, setFormState] = useState<FormState>({
    email: '',
    password: '',
    errors: {},
  });
  
  // Estado derivado
  const isValid = useMemo(() => {
    return formState.email.length > 0 && formState.password.length > 0;
  }, [formState.email, formState.password]);
}
```

### 3. Event Handlers
- **Tipar eventos correctamente**: Usar tipos de React para eventos
- **Nombres descriptivos**: `handleSubmit`, `handleInputChange`, `handleClick`

```typescript
function Form() {
  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    // ...
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    // ...
  };

  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    // ...
  };
}
```

## Hooks y Lógica

### 1. Hooks Personalizados
- **Extraer lógica compleja**: Crear hooks personalizados para lógica reutilizable
- **Tipar hooks**: Especificar tipos de entrada y salida
- **Nomenclatura**: Prefijo `use`: `useAuth`, `useLocalStorage`, `useApi`

```typescript
interface UseCounterReturn {
  count: number;
  increment: () => void;
  decrement: () => void;
  reset: () => void;
}

function useCounter(initialValue = 0): UseCounterReturn {
  const [count, setCount] = useState<number>(initialValue);

  const increment = () => setCount(prev => prev + 1);
  const decrement = () => setCount(prev => prev - 1);
  const reset = () => setCount(initialValue);

  return { count, increment, decrement, reset };
}
```

### 2. useEffect
- **Tipar dependencias**: Asegurar que todas las dependencias estén tipadas
- **Cleanup**: Siempre limpiar recursos (timeouts, listeners, suscripciones)
- **Evitar dependencias faltantes**: Incluir todas las dependencias necesarias

```typescript
function UserProfile({ userId }: { userId: string }) {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchUser() {
      const userData = await getUserById(userId);
      if (!cancelled) {
        setUser(userData);
      }
    }

    fetchUser();

    return () => {
      cancelled = true;
    };
  }, [userId]);
}
```

### 3. useMemo y useCallback
- **Usar cuando sea necesario**: Solo para optimizaciones reales
- **Tipar correctamente**: Especificar tipos genéricos
- **Dependencias completas**: Incluir todas las dependencias

```typescript
function ProductList({ products, filter }: ProductListProps) {
  const filteredProducts = useMemo<Product[]>(() => {
    return products.filter(p => p.category === filter);
  }, [products, filter]);

  const handleProductClick = useCallback((productId: string) => {
    navigate(`/products/${productId}`);
  }, [navigate]);
}
```

## Renderizado y JSX

### 1. Renderizado Condicional
- **Usar operadores ternarios o lógicos**: `{condition && <Component />}`
- **Evitar renderizado innecesario**: Usar `useMemo` para cálculos en render
- **Keys en listas**: Siempre proporcionar keys únicas y estables

```typescript
function UserList({ users }: { users: User[] }) {
  return (
    <ul>
      {users.map(user => (
        <li key={user.id}>
          {user.name}
        </li>
      ))}
    </ul>
  );
}
```

### 2. Accesibilidad
- **Atributos ARIA**: Incluir cuando sea necesario
- **Semántica HTML**: Usar elementos semánticos correctos
- **Navegación por teclado**: Asegurar que todos los elementos interactivos sean accesibles

```typescript
function Modal({ isOpen, onClose, children }: ModalProps) {
  useEffect(() => {
    if (isOpen) {
      const handleEscape = (e: KeyboardEvent) => {
        if (e.key === 'Escape') onClose();
      };
      document.addEventListener('keydown', handleEscape);
      return () => document.removeEventListener('keydown', handleEscape);
    }
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div 
      className="modal-overlay" 
      onClick={onClose}
      role="dialog"
      aria-modal="true"
    >
      <div 
        className="modal-content" 
        onClick={(e) => e.stopPropagation()}
      >
        {children}
      </div>
    </div>
  );
}
```

## Composición de Componentes

### 1. Componentes Compuestos
- **Usar children cuando sea apropiado**: Permitir composición flexible
- **Render props**: Usar cuando se necesite lógica compartida
- **Compound components**: Agrupar componentes relacionados

```typescript
interface CardProps {
  children: React.ReactNode;
  className?: string;
}

function Card({ children, className }: CardProps) {
  return <div className={`card ${className || ''}`}>{children}</div>;
}

Card.Header = function CardHeader({ children }: { children: React.ReactNode }) {
  return <div className="card-header">{children}</div>;
};

Card.Body = function CardBody({ children }: { children: React.ReactNode }) {
  return <div className="card-body">{children}</div>;
};

// Uso:
<Card>
  <Card.Header>Title</Card.Header>
  <Card.Body>Content</Card.Body>
</Card>
```

### 2. Props de Renderizado
- **Tipar render props correctamente**: Especificar la firma de la función
- **Flexibilidad**: Permitir tanto children como render props

```typescript
interface DataFetcherProps<T> {
  url: string;
  children: (data: T | null, loading: boolean, error: Error | null) => React.ReactNode;
}

function DataFetcher<T>({ url, children }: DataFetcherProps<T>) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    fetch(url)
      .then(res => res.json())
      .then(setData)
      .catch(setError)
      .finally(() => setLoading(false));
  }, [url]);

  return <>{children(data, loading, error)}</>;
}
```

## Manejo de Errores

### 1. Error Boundaries
- **Implementar Error Boundaries**: Para capturar errores en componentes
- **Tipar correctamente**: Usar tipos de React para error boundaries

```typescript
interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  ErrorBoundaryState
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return <div>Something went wrong: {this.state.error?.message}</div>;
    }
    return this.props.children;
  }
}
```

### 2. Validación de Props
- **Validación en runtime**: Usar TypeScript para validación en desarrollo
- **Valores por defecto seguros**: Proporcionar valores por defecto apropiados

## Performance

### 1. Optimizaciones
- **React.memo**: Usar para componentes que se re-renderizan frecuentemente
- **useMemo/useCallback**: Solo cuando sea necesario
- **Code splitting**: Lazy loading de componentes pesados

```typescript
interface ExpensiveComponentProps {
  data: ComplexData[];
}

const ExpensiveComponent = React.memo(function ExpensiveComponent({ 
  data 
}: ExpensiveComponentProps) {
  const processedData = useMemo(() => {
    return data.map(/* procesamiento costoso */);
  }, [data]);

  return <div>{/* renderizado */}</div>;
});
```

### 2. Lazy Loading
```typescript
const HeavyComponent = React.lazy(() => import('./HeavyComponent'));

function App() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <HeavyComponent />
    </Suspense>
  );
}
```

## INSTRUCCIONES AUTOMÁTICAS PARA EL ASISTENTE

**EN CADA DESARROLLO DE COMPONENTE**:

1. **SIEMPRE** crear interface/type para props
2. **SIEMPRE** tipar explícitamente el estado con `useState<T>()`
3. **SIEMPRE** tipar event handlers correctamente
4. **SIEMPRE** seguir la estructura de organización de archivos
5. **SIEMPRE** agregar comentarios JSDoc al componente
6. **SIEMPRE** incluir valores por defecto para props opcionales
7. **SIEMPRE** usar nombres descriptivos para funciones y variables
8. **SIEMPRE** incluir cleanup en useEffect cuando sea necesario
9. **SIEMPRE** proporcionar keys únicas en listas
10. **SIEMPRE** considerar accesibilidad (ARIA, semántica)
11. **NUNCA** usar `any` en ningún lugar
12. **NUNCA** dejar TODOs en componentes
13. **NUNCA** incluir emojis en código
14. **SIEMPRE** implementar componentes completamente funcionales

