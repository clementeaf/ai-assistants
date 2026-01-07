import { useState, useRef, useEffect } from 'react';

interface Message {
  id: string;
  text: string;
  timestamp: Date;
}

/**
 * Componente de chat con zona de mensajes e input para enviar
 * @returns Componente de chat renderizado
 */
function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = () => {
    if (inputText.trim() === '') {
      return;
    }

    const newMessage: Message = {
      id: Date.now().toString(),
      text: inputText.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, newMessage]);
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
      {/* Zona de mensajes */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {messages.length === 0 ? (
          <div className="text-gray-500 text-center mt-4">
            No hay mensajes aún
          </div>
        ) : (
          messages.map(message => (
            <div
              key={message.id}
              className="bg-white rounded-lg p-3 shadow-sm"
            >
              <div className="text-sm text-gray-700">{message.text}</div>
              <div className="text-xs text-gray-400 mt-1">
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
          placeholder="Escribe un mensaje..."
          className="flex-1 px-4 py-2 rounded-lg border border-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={handleSend}
          disabled={inputText.trim() === ''}
          className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          Enviar
        </button>
      </div>
    </div>
  );
}

export default Chat;

