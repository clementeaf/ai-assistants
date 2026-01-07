import { useState, useRef, useEffect } from 'react';
import { useWebSocket } from '../../lib/websocket/useWebSocket';

interface Message {
  id: string;
  text: string;
  timestamp: Date;
  type: 'user' | 'assistant' | 'error';
}

/**
 * Componente de chat con zona de mensajes e input para enviar
 * Conectado a WebSocket para comunicación en tiempo real
 * @returns Componente de chat renderizado
 */
function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [conversationId] = useState(() => `web:${Date.now()}`);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { sendMessage, isConnected, isConnecting, error: wsError } = useWebSocket({
    conversationId,
    onMessage: (wsMessage) => {
      if (wsMessage.type === 'assistant_message' && wsMessage.text) {
        const newMessage: Message = {
          id: Date.now().toString(),
          text: wsMessage.text,
          timestamp: new Date(wsMessage.timestamp || Date.now()),
          type: 'assistant',
        };
        setMessages(prev => [...prev, newMessage]);
      } else if (wsMessage.type === 'error' && wsMessage.error) {
        const errorMessage: Message = {
          id: Date.now().toString(),
          text: wsMessage.error,
          timestamp: new Date(),
          type: 'error',
        };
        setMessages(prev => [...prev, errorMessage]);
      }
    },
    onError: () => {
      const errorMessage: Message = {
        id: Date.now().toString(),
        text: 'Error de conexión con el servidor',
        timestamp: new Date(),
        type: 'error',
      };
      setMessages(prev => [...prev, errorMessage]);
    },
    autoReconnect: true,
  });

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = () => {
    if (inputText.trim() === '' || !isConnected) {
      return;
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputText.trim(),
      timestamp: new Date(),
      type: 'user',
    };

    setMessages(prev => [...prev, userMessage]);
    sendMessage(inputText.trim());
    setInputText('');
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="w-[800px] h-[600px] bg-gray-300 flex flex-col">
      {/* Estado de conexión */}
      <div className="border-b border-gray-400 px-4 py-2 bg-gray-200">
        <div className="flex items-center gap-2 text-sm">
          <div
            className={`w-2 h-2 rounded-full ${
              isConnected ? 'bg-green-500' : isConnecting ? 'bg-yellow-500' : 'bg-red-500'
            }`}
          />
          <span className="text-gray-700">
            {isConnected
              ? 'Conectado'
              : isConnecting
                ? 'Conectando...'
                : 'Desconectado'}
          </span>
          {wsError && <span className="text-red-600 text-xs">({wsError})</span>}
        </div>
      </div>

      {/* Zona de mensajes */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {messages.length === 0 ? (
          <div className="text-gray-500 text-center mt-4">
            {isConnecting ? 'Conectando...' : 'No hay mensajes aún'}
          </div>
        ) : (
          messages.map(message => (
            <div
              key={message.id}
              className={`rounded-lg p-3 shadow-sm ${
                message.type === 'user'
                  ? 'bg-blue-500 text-white ml-auto max-w-[80%]'
                  : message.type === 'error'
                    ? 'bg-red-100 text-red-800 border border-red-300'
                    : 'bg-white text-gray-700'
              }`}
            >
              <div className="text-sm">{message.text}</div>
              <div
                className={`text-xs mt-1 ${
                  message.type === 'user' ? 'text-blue-100' : 'text-gray-400'
                }`}
              >
                {message.timestamp.toLocaleTimeString()}
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input y botón de enviar */}
      <div className="border-t border-gray-400 p-4 flex gap-2">
        <input
          type="text"
          value={inputText}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
            setInputText(e.target.value)
          }
          onKeyPress={handleKeyPress}
          placeholder={isConnected ? 'Escribe un mensaje...' : 'Conectando...'}
          disabled={!isConnected}
          className="flex-1 px-4 py-2 rounded-lg border border-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-200 disabled:cursor-not-allowed"
        />
        <button
          onClick={handleSend}
          disabled={inputText.trim() === '' || !isConnected}
          className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          Enviar
        </button>
      </div>
    </div>
  );
}

export default Chat;

