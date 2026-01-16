import { useEffect, useRef, useState, useCallback } from 'react';

interface WebSocketMessage {
  type: 'user_message' | 'assistant_message' | 'error' | 'ping' | 'pong';
  text?: string;
  conversation_id?: string;
  error?: string;
  timestamp?: string;
}

interface UseWebSocketOptions {
  conversationId: string;
  apiKey?: string;
  customerId?: string;
  onMessage?: (message: WebSocketMessage) => void;
  onError?: (error: Event) => void;
  onClose?: () => void;
  onOpen?: () => void;
  autoReconnect?: boolean;
  reconnectInterval?: number;
}

interface UseWebSocketReturn {
  sendMessage: (text: string) => void;
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  disconnect: () => void;
  reconnect: () => void;
}

/**
 * Hook personalizado para manejar conexiones WebSocket
 * @param options - Opciones de configuración del WebSocket
 * @returns Funciones y estado del WebSocket
 */
export function useWebSocket(options: UseWebSocketOptions): UseWebSocketReturn {
  const {
    conversationId,
    apiKey,
    customerId,
    onMessage,
    onError,
    onClose,
    onOpen,
    autoReconnect = true,
    reconnectInterval = 3000,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const shouldReconnectRef = useRef(true);
  const isMountedRef = useRef(true);
  const hasConnectedRef = useRef(false);

  // Usar refs para callbacks para evitar loops infinitos
  const onMessageRef = useRef(onMessage);
  const onErrorRef = useRef(onError);
  const onCloseRef = useRef(onClose);
  const onOpenRef = useRef(onOpen);

  useEffect(() => {
    onMessageRef.current = onMessage;
    onErrorRef.current = onError;
    onCloseRef.current = onClose;
    onOpenRef.current = onOpen;
  }, [onMessage, onError, onClose, onOpen]);

  const getWebSocketUrl = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:9000';
    const baseUrl = apiBaseUrl.replace(/^https?:\/\//, '').replace(/^wss?:\/\//, '');
    const url = new URL(`${protocol}//${baseUrl}/v1/ws/conversations/${conversationId}`);

    const resolvedApiKey = apiKey || localStorage.getItem('api_key');
    if (resolvedApiKey) {
      url.searchParams.set('api_key', resolvedApiKey);
    }
    if (customerId) {
      url.searchParams.set('customer_id', customerId);
    }

    return url.toString();
  }, [conversationId, apiKey, customerId]);

  const connect = useCallback(() => {
    // Evitar múltiples conexiones simultáneas
    if (wsRef.current?.readyState === WebSocket.OPEN || wsRef.current?.readyState === WebSocket.CONNECTING) {
      return;
    }

    // Limpiar conexión anterior si existe
    if (wsRef.current) {
      try {
        wsRef.current.close();
      } catch {
        // Ignorar errores al cerrar
      }
      wsRef.current = null;
    }

    setIsConnecting(true);
    setError(null);

    try {
      const url = getWebSocketUrl();
      console.log('[WebSocket] Intentando conectar a:', url);
      const ws = new WebSocket(url);

      ws.onopen = () => {
        console.log('[WebSocket] Conexión establecida exitosamente');
        hasConnectedRef.current = true;
        setIsConnected(true);
        setIsConnecting(false);
        setError(null);
        onOpenRef.current?.();
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);

          if (message.type === 'pong') {
            return;
          }

          onMessageRef.current?.(message);
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };

      ws.onerror = (event) => {
        console.error('[WebSocket] Error en conexión:', event);
        setIsConnecting(false);
        const currentApiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:9000';
        const errorMessage = `WebSocket connection error. Verifica que el servidor esté corriendo en ${currentApiBaseUrl}`;
        setError(errorMessage);
        console.error('[WebSocket] URL intentada:', url);
        console.error('[WebSocket] Estado del WebSocket:', ws.readyState);
        onErrorRef.current?.(event);
      };

      ws.onclose = (event) => {
        console.log('[WebSocket] Conexión cerrada. Código:', event.code, 'Razón:', event.reason);
        setIsConnected(false);
        setIsConnecting(false);

        // Limpiar referencia
        if (wsRef.current === ws) {
          wsRef.current = null;
        }

        // Solo mostrar error si no fue un cierre normal y el componente sigue montado
        if (isMountedRef.current && event.code !== 1000 && event.code !== 1001) {
          const errorMessage = event.reason || `Connection closed (code: ${event.code})`;
          console.error('[WebSocket] Error al cerrar:', errorMessage);
          setError(errorMessage);
        }

        onCloseRef.current?.();

        // Solo reconectar si el componente sigue montado y no fue error de autenticación
        if (isMountedRef.current && shouldReconnectRef.current && autoReconnect && event.code !== 1008) {
          reconnectTimeoutRef.current = setTimeout(() => {
            if (isMountedRef.current && shouldReconnectRef.current) {
              connect();
            }
          }, reconnectInterval);
        }
      };

      wsRef.current = ws;
    } catch (err) {
      setIsConnecting(false);
      setError(err instanceof Error ? err.message : 'Failed to connect');
      wsRef.current = null;
    }
  }, [getWebSocketUrl, autoReconnect, reconnectInterval]);

  const disconnect = useCallback(() => {
    shouldReconnectRef.current = false;

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setIsConnected(false);
    setIsConnecting(false);
  }, []);

  const reconnect = useCallback(() => {
    disconnect();
    shouldReconnectRef.current = true;
    connect();
  }, [disconnect, connect]);

  const sendMessage = useCallback(
    (text: string) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        setError('WebSocket is not connected');
        return;
      }

      const message: WebSocketMessage = {
        type: 'user_message',
        text,
        conversation_id: conversationId,
      };

      try {
        wsRef.current.send(JSON.stringify(message));
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to send message');
      }
    },
    [conversationId]
  );

  useEffect(() => {
    isMountedRef.current = true;
    let cleanupTimer: number | null = null;

    // Conectar inmediatamente
    connect();

    return () => {
      // Limpiar timer de cleanup anterior si existe
      if (cleanupTimer !== null) {
        clearTimeout(cleanupTimer);
      }

      // Solo hacer cleanup si realmente se conectó (evita double invoke en desarrollo)
      if (!hasConnectedRef.current) {
        // Si nunca se conectó, probablemente es double invoke - solo limpiar refs
        isMountedRef.current = false;
        shouldReconnectRef.current = false;
        return;
      }

      isMountedRef.current = false;
      shouldReconnectRef.current = false;

      // Limpiar timeout de reconexión
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }

      // Cerrar WebSocket después de un pequeño delay para asegurar que no es double invoke
      cleanupTimer = setTimeout(() => {
        if (wsRef.current) {
          const ws = wsRef.current;
          wsRef.current = null;

          // Remover listeners para evitar errores
          ws.onopen = null;
          ws.onmessage = null;
          ws.onerror = null;
          ws.onclose = null;

          // Cerrar solo si está abierto o conectando
          if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
            try {
              ws.close(1000, 'Component unmounted');
            } catch {
              // Ignorar errores
            }
          }
        }
      }, 100);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Solo ejecutar una vez al montar

  return {
    sendMessage,
    isConnected,
    isConnecting,
    error,
    disconnect,
    reconnect,
  };
}

