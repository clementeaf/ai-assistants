import { useState, useRef, useEffect } from 'react';
import { useWebSocket } from '../../lib/websocket/useWebSocket';
import { Send, Bot, User, AlertCircle, MessageSquare } from 'lucide-react';

interface Message {
  id: string;
  text: string;
  timestamp: Date;
  type: 'user' | 'assistant' | 'error';
}

/**
 * Componente de chat optimizado con diseño moderno
 * Adaptado para resoluciones desde 1024x600
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
        text: 'Error de conexión con el servidor de Chat',
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
    <div className="flex flex-col h-full w-full bg-white rounded-2xl shadow-xl overflow-hidden border border-slate-200">
      {/* Header / Connection Status */}
      <div className="px-6 py-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${isConnected ? 'bg-blue-100 text-blue-600' : 'bg-slate-200 text-slate-500'}`}>
            <MessageSquare className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-semibold text-slate-800 text-sm">Asistente Virtual</h3>
            <div className="flex items-center gap-1.5 mt-0.5">
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-400'}`} />
              <span className="text-[10px] uppercase tracking-wider font-bold text-slate-500">
                {isConnected ? 'En línea' : isConnecting ? 'Conectando...' : 'Desconectado'}
              </span>
            </div>
          </div>
        </div>

        {wsError && (
          <div className="flex items-center gap-2 px-3 py-1 bg-red-50 text-red-600 rounded-full text-xs font-medium border border-red-100">
            <AlertCircle className="w-3.5 h-3.5" />
            <span>Error de red</span>
          </div>
        )}
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-3 space-y-4 custom-scrollbar bg-slate-50/50">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-slate-400 space-y-4">
            <div className="w-16 h-16 bg-white rounded-2xl shadow-md flex items-center justify-center border border-slate-100">
              <Bot className="w-8 h-8 text-blue-500" />
            </div>
            <div className="text-center">
              <p className="font-medium text-slate-600">¡Hola! Soy tu asistente de IA</p>
              <p className="text-sm mt-1">¿En qué puedo ayudarte hoy?</p>
            </div>
          </div>
        ) : (
          <>
            {messages.map((message) => {
              const isUser = message.type === 'user';
              const isError = message.type === 'error';

              return (
                <div
                  key={message.id}
                  className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'} items-end animate-in fade-in slide-in-from-bottom-2 duration-300`}
                >
                  {/* Avatar */}
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 shadow-sm border ${isUser ? 'bg-blue-600 border-blue-500' : 'bg-white border-slate-200'
                    }`}>
                    {isUser ? <User className="w-4 h-4 text-white" /> : <Bot className="w-4 h-4 text-blue-500" />}
                  </div>

                  {/* Bubble */}
                  <div className={`max-w-[75%] space-y-1 ${isUser ? 'items-end' : 'items-start'}`}>
                    <div className={`px-4 py-3 rounded-2xl text-sm shadow-sm ${isUser
                      ? 'bg-blue-600 text-white rounded-br-none'
                      : isError
                        ? 'bg-red-50 text-red-700 border border-red-100 rounded-bl-none'
                        : 'bg-white text-slate-700 border border-slate-200 rounded-bl-none'
                      }`}>
                      {message.text}
                    </div>
                    <p className="text-[10px] text-slate-400 px-1">
                      {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                </div>
              );
            })}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input Area */}
      <div className="p-2.5 bg-white border-t border-slate-200">
        <div className="flex gap-3 items-center w-full relative">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={isConnected ? 'Escribe aquí tu mensaje...' : 'Esperando conexión...'}
            disabled={!isConnected}
            className="flex-1 px-4 py-2.5 bg-slate-100 border-none rounded-xl text-sm focus:ring-2 focus:ring-blue-500/20 focus:bg-white transition-all outline-none placeholder:text-slate-400 disabled:opacity-50"
          />
          <button
            onClick={handleSend}
            disabled={inputText.trim() === '' || !isConnected}
            className={`p-2.5 rounded-xl transition-all shadow-md active:scale-95 ${inputText.trim() !== '' && isConnected
              ? 'bg-blue-600 text-white shadow-blue-500/30 hover:bg-blue-700'
              : 'bg-slate-200 text-slate-400 shadow-none cursor-not-allowed'
              }`}
          >
            <Send className="w-5 h-5 ml-0.5" />
          </button>
        </div>
        <p className="text-[10px] text-center text-slate-400 mt-1.5 font-medium tracking-tight">
          Presiona Enter para enviar · Potenciado por AI Assistants
        </p>
      </div>
    </div>
  );
}

export default Chat;
