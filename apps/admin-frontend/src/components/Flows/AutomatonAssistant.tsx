import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, X, Sparkles } from 'lucide-react';
import { apiClient } from '../../lib/api/client';
import { getDomainTools, getDomainMetadata, type DomainTool } from '../../lib/api/automata';

interface Message {
  id: string;
  text: string;
  timestamp: Date;
  type: 'user' | 'assistant';
}

import type { Flow, FlowStage } from '../../lib/api/flows';

interface AutomatonAssistantProps {
  onGeneratePrompt: (prompt: string) => void;
  onClose: () => void;
  flow: Flow;
  currentPrompt: string;
  stages: FlowStage[];
}

/**
 * Asistente especializado para evaluar y mejorar autómatas existentes
 * Analiza el prompt actual, etapas, herramientas y tests para sugerir mejoras
 * @param onGeneratePrompt - Callback cuando se genera un prompt mejorado
 * @param onClose - Callback para cerrar el asistente
 * @param flow - Flujo actual con su información
 * @param currentPrompt - Prompt actual del sistema
 * @param stages - Todas las etapas del flujo
 * @returns Componente AutomatonAssistant renderizado
 */
function AutomatonAssistant({ onGeneratePrompt, onClose, flow, currentPrompt, stages }: AutomatonAssistantProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [generatedPrompt, setGeneratedPrompt] = useState<string | null>(null);
  const [domainTools, setDomainTools] = useState<DomainTool[]>([]);
  const [domainMetadata, setDomainMetadata] = useState<{ display_name: string; description: string } | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const conversationIdRef = useRef(`automaton-assistant-${Date.now()}`);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Cargar herramientas y metadata del dominio dinámicamente
    const loadDomainInfo = async (): Promise<void> => {
      try {
        const [toolsResponse, metadataResponse] = await Promise.all([
          getDomainTools(flow.domain),
          getDomainMetadata(flow.domain).catch(() => null),
        ]);
        setDomainTools(toolsResponse.tools);
        if (metadataResponse) {
          setDomainMetadata({
            display_name: metadataResponse.display_name,
            description: metadataResponse.description,
          });
        }
      } catch (error) {
        console.error('Error loading domain info:', error);
        // Continuar sin herramientas si falla
      }
    };
    loadDomainInfo();
  }, [flow.domain]);

  useEffect(() => {
    // Obtener mensaje inicial del backend/LLM
    const loadInitialMessage = async (): Promise<void> => {
      setIsLoading(true);
      try {
        const regularStages = stages
          .filter((s) => s.stage_type !== 'system_prompt')
          .sort((a, b) => a.stage_order - b.stage_order);
        
        // Construir información de herramientas dinámicamente
        const toolsInfo = domainTools.length > 0 ? {
          tools: domainTools.map((tool) => ({
            name: tool.name,
            description: tool.description,
            input: tool.input,
            output: tool.output,
          })),
        } : {};
        
        const automatonContext = {
          flow: {
            flow_id: flow.flow_id,
            name: flow.name,
            description: flow.description,
            domain: flow.domain,
            is_active: flow.is_active,
          },
          current_prompt: currentPrompt,
          stages: regularStages.map((s) => ({
            stage_id: s.stage_id,
            stage_order: s.stage_order,
            stage_name: s.stage_name,
            stage_type: s.stage_type,
            prompt_text: s.prompt_text,
            field_name: s.field_name,
            field_type: s.field_type,
            validation_rules: s.validation_rules,
            is_required: s.is_required,
          })),
          ...toolsInfo,
        };

        const response = await apiClient.getInstance().post(
          '/v1/automaton-assistant/evaluate',
          {
            conversation_id: conversationIdRef.current,
            message: '__INIT__',
            automaton_context: automatonContext,
          }
        );

        const assistantText = response.data.response || response.data.message || 'No se pudo obtener respuesta';
        
        const initialMessage: Message = {
          id: 'initial',
          text: assistantText,
          timestamp: new Date(),
          type: 'assistant',
        };
        setMessages([initialMessage]);
      } catch (error) {
        const errorMessage: Message = {
          id: 'initial-error',
          text: error instanceof Error ? `Error al cargar el asistente: ${error.message}` : 'Error al comunicarse con el asistente',
          timestamp: new Date(),
          type: 'assistant',
        };
        setMessages([errorMessage]);
      } finally {
        setIsLoading(false);
      }
    };

    // Solo cargar mensaje inicial si ya tenemos las herramientas
    if (domainTools.length > 0 || flow.domain) {
      loadInitialMessage();
    }
  }, [flow, currentPrompt, stages, domainTools]);

  const scrollToBottom = (): void => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const sendMessage = async (): Promise<void> => {
    if (inputText.trim() === '' || isLoading) {
      return;
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputText.trim(),
      timestamp: new Date(),
      type: 'user',
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);

    try {
      // Construir contexto completo del autómata
      const regularStages = stages
        .filter((s) => s.stage_type !== 'system_prompt')
        .sort((a, b) => a.stage_order - b.stage_order);
      
      // Usar herramientas cargadas dinámicamente
      const toolsInfo = domainTools.length > 0 ? {
        tools: domainTools.map((tool) => ({
          name: tool.name,
          description: tool.description,
          input: tool.input,
          output: tool.output,
        })),
      } : {};
      
      const automatonContext = {
        flow: {
          flow_id: flow.flow_id,
          name: flow.name,
          description: flow.description,
          domain: flow.domain,
          is_active: flow.is_active,
        },
        current_prompt: currentPrompt,
        stages: regularStages.map((s) => ({
          stage_id: s.stage_id,
          stage_order: s.stage_order,
          stage_name: s.stage_name,
          stage_type: s.stage_type,
          prompt_text: s.prompt_text,
          field_name: s.field_name,
          field_type: s.field_type,
          validation_rules: s.validation_rules,
            is_required: s.is_required,
          })),
        ...toolsInfo,
      };

      const response = await apiClient.getInstance().post(
        '/v1/automaton-assistant/evaluate',
        {
          conversation_id: conversationIdRef.current,
          message: userMessage.text,
          automaton_context: automatonContext,
        }
      );

      const assistantText = response.data.response || response.data.message || 'No se pudo obtener respuesta';
      const isPromptGenerated = response.data.prompt_generated === true;

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: assistantText,
        timestamp: new Date(),
        type: 'assistant',
      };

      setMessages((prev) => [...prev, assistantMessage]);

      if (isPromptGenerated && response.data.prompt) {
        setGeneratedPrompt(response.data.prompt);
      }
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: error instanceof Error ? `Error: ${error.message}` : 'Error al comunicarse con el asistente',
        timestamp: new Date(),
        type: 'assistant',
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent): void => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleUsePrompt = (): void => {
    if (generatedPrompt) {
      onGeneratePrompt(generatedPrompt);
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-500 rounded-lg">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-gray-800">Asistente de Evaluación y Mejora</h3>
              <p className="text-xs text-gray-600">Analizo tu autómata y sugiero mejoras en prompt, etapas y tests</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded transition-colors"
            title="Cerrar asistente"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
          {messages.map((message) => {
            const isUser = message.type === 'user';
            return (
              <div
                key={message.id}
                className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'} items-start`}
              >
                {/* Avatar */}
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                    isUser ? 'bg-blue-600' : 'bg-indigo-500'
                  }`}
                >
                  {isUser ? (
                    <User className="w-4 h-4 text-white" />
                  ) : (
                    <Bot className="w-4 h-4 text-white" />
                  )}
                </div>

                {/* Message Bubble */}
                <div className={`max-w-[75%] ${isUser ? 'items-end' : 'items-start'}`}>
                  <div
                    className={`px-4 py-3 rounded-2xl text-sm ${
                      isUser
                        ? 'bg-blue-600 text-white rounded-br-none'
                        : 'bg-white text-gray-800 border border-gray-200 rounded-bl-none shadow-sm'
                    }`}
                  >
                    <div className="whitespace-pre-wrap">{message.text}</div>
                  </div>
                  <p className="text-[10px] text-gray-400 mt-1 px-1">
                    {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
              </div>
            );
          })}
          {isLoading && (
            <div className="flex gap-3 items-start">
              <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 bg-indigo-500">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div className="bg-white border border-gray-200 rounded-2xl rounded-bl-none px-4 py-3">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Generated Prompt Preview */}
        {generatedPrompt && (
          <div className="border-t border-gray-200 p-4 bg-yellow-50">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-semibold text-gray-800">Prompt Generado</h4>
              <button
                onClick={handleUsePrompt}
                className="px-3 py-1.5 bg-green-500 text-white text-xs rounded-lg hover:bg-green-600 transition-colors"
              >
                Usar este Prompt
              </button>
            </div>
            <div className="bg-white border border-gray-200 rounded-lg p-3 max-h-32 overflow-y-auto">
              <pre className="text-xs font-mono text-gray-700 whitespace-pre-wrap">
                {generatedPrompt.substring(0, 300)}...
              </pre>
            </div>
          </div>
        )}

        {/* Input Area */}
        <div className="p-4 border-t border-gray-200 bg-white">
          <div className="flex gap-3 items-end">
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={isLoading ? 'El asistente está pensando...' : 'Escribe tu respuesta aquí...'}
              disabled={isLoading}
              rows={2}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm resize-none disabled:opacity-50"
            />
            <button
              onClick={sendMessage}
              disabled={inputText.trim() === '' || isLoading}
              className={`p-3 rounded-lg transition-all ${
                inputText.trim() !== '' && !isLoading
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'bg-gray-200 text-gray-400 cursor-not-allowed'
              }`}
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
          <p className="text-[10px] text-gray-400 mt-2 text-center">
            Presiona Enter para enviar · Shift+Enter para nueva línea
          </p>
        </div>
      </div>
    </div>
  );
}

export default AutomatonAssistant;
