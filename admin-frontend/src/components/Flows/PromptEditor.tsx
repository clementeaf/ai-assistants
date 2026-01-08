import { useState, useEffect } from 'react';
import type { Flow, FlowStage } from '../../lib/api/flows';

interface PromptEditorProps {
  flow: Flow | null;
  stages: FlowStage[];
  initialPrompt?: string;
  onPromptChange?: (prompt: string) => void;
  onSave?: (prompt: string) => Promise<void>;
}

/**
 * Editor de prompt del sistema para el LLM
 * Permite generar y editar el prompt que se le pasará al LLM
 * @param flow - Flujo actual
 * @param stages - Etapas del flujo
 * @param initialPrompt - Prompt inicial
 * @param onPromptChange - Callback cuando cambia el prompt
 * @param onSave - Callback para guardar el prompt
 * @returns Componente PromptEditor renderizado
 */
function PromptEditor({
  flow,
  stages,
  initialPrompt = '',
  onPromptChange,
  onSave,
}: PromptEditorProps) {
  const [prompt, setPrompt] = useState(initialPrompt);
  const [isSaving, setIsSaving] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [showRecommendations, setShowRecommendations] = useState(true);

  useEffect(() => {
    if (initialPrompt) {
      setPrompt(initialPrompt);
    } else {
      generateDefaultPrompt();
    }
  }, [flow, stages]);

  const generateDefaultPrompt = (): void => {
    if (!flow || stages.length === 0) {
      setPrompt('');
      return;
    }

    const sortedStages = [...stages].sort((a, b) => a.stage_order - b.stage_order);
    
    let generatedPrompt = `Eres un asistente de conversación para el dominio "${flow.domain}".\n\n`;
    generatedPrompt += `Tu objetivo es guiar al usuario a través de un flujo de conversación estructurado.\n\n`;
    generatedPrompt += `FLUJO DE CONVERSACIÓN:\n\n`;

    sortedStages.forEach((stage, index) => {
      generatedPrompt += `${index + 1}. ${stage.stage_name.toUpperCase()} (${stage.stage_type})\n`;
      if (stage.prompt_text) {
        generatedPrompt += `   Prompt: "${stage.prompt_text}"\n`;
      }
      if (stage.field_name) {
        generatedPrompt += `   Campo: ${stage.field_name} (${stage.field_type || 'text'})`;
        if (stage.is_required) {
          generatedPrompt += ' [REQUERIDO]';
        }
        generatedPrompt += '\n';
      }
      if (stage.validation_rules) {
        generatedPrompt += `   Validación: ${stage.validation_rules}\n`;
      }
      generatedPrompt += '\n';
    });

    generatedPrompt += `INSTRUCCIONES:\n`;
    generatedPrompt += `- Sigue el flujo en el orden especificado\n`;
    generatedPrompt += `- Usa los prompts indicados para cada etapa\n`;
    generatedPrompt += `- Valida los campos según las reglas especificadas\n`;
    generatedPrompt += `- Mantén un tono profesional y amigable\n`;
    generatedPrompt += `- Si el usuario intenta saltar etapas, guíalo de vuelta al flujo correcto\n`;

    setPrompt(generatedPrompt);
    onPromptChange?.(generatedPrompt);
  };

  const handlePromptChange = (value: string): void => {
    setPrompt(value);
    onPromptChange?.(value);
  };

  const handleSave = async (): Promise<void> => {
    if (!onSave) return;
    setIsSaving(true);
    try {
      await onSave(prompt);
    } catch (error) {
      console.error('Error saving prompt:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleGenerate = (): void => {
    generateDefaultPrompt();
  };

  const recommendations = [
    {
      title: 'Estructura Clara',
      description: 'Define claramente el rol del asistente y el objetivo del flujo de conversación al inicio del prompt.',
      example: 'Eres un asistente de reservas profesional. Tu objetivo es...',
    },
    {
      title: 'Instrucciones Específicas',
      description: 'Proporciona instrucciones detalladas sobre cómo debe comportarse el asistente en cada etapa.',
      example: 'En la etapa de confirmación, siempre repite la información recopilada antes de proceder.',
    },
    {
      title: 'Validaciones',
      description: 'Especifica cómo validar la información del usuario según el tipo de campo.',
      example: 'Para fechas, valida que estén en formato YYYY-MM-DD y que no sean en el pasado.',
    },
    {
      title: 'Manejo de Errores',
      description: 'Define cómo debe responder el asistente cuando el usuario proporciona información inválida.',
      example: 'Si la información es inválida, explica amablemente el error y solicita la información nuevamente.',
    },
    {
      title: 'Tono y Estilo',
      description: 'Especifica el tono de comunicación que debe usar el asistente.',
      example: 'Mantén un tono profesional pero amigable, usando un lenguaje claro y directo.',
    },
    {
      title: 'Contexto del Flujo',
      description: 'Incluye información sobre el orden de las etapas y cómo transicionar entre ellas.',
      example: 'Sigue el flujo en el orden especificado. No saltes etapas a menos que el usuario lo solicite explícitamente.',
    },
  ];

  return (
    <div className="flex flex-col h-full bg-white rounded-lg border border-gray-300">
      <div className="flex justify-between items-center p-4 border-b border-gray-300">
        <h3 className="text-lg font-semibold">Prompt del Sistema</h3>
        <div className="flex gap-2">
          <button
            onClick={() => setShowRecommendations(!showRecommendations)}
            className="px-3 py-1 bg-amber-500 text-white rounded hover:bg-amber-600 text-sm transition-colors"
          >
            {showRecommendations ? 'Ocultar' : 'Mostrar'} Recomendaciones
          </button>
          <button
            onClick={handleGenerate}
            className="px-3 py-1 bg-gray-500 text-white rounded hover:bg-gray-600 text-sm transition-colors"
            disabled={!flow || stages.length === 0}
          >
            Generar Automático
          </button>
          {onSave && (
            <button
              onClick={handleSave}
              disabled={isSaving || !prompt.trim()}
              className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-300 text-sm transition-colors"
            >
              {isSaving ? 'Guardando...' : 'Guardar'}
            </button>
          )}
          <button
            onClick={() => setShowPreview(!showPreview)}
            className="px-3 py-1 bg-purple-500 text-white rounded hover:bg-purple-600 text-sm transition-colors"
          >
            {showPreview ? 'Ocultar' : 'Vista'} Previa
          </button>
        </div>
      </div>

      {showRecommendations && (
        <div className="p-4 bg-amber-50 border-b border-amber-200">
          <h4 className="font-semibold text-amber-900 mb-3 flex items-center gap-2">
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
              />
            </svg>
            Recomendaciones para Generar el Prompt
          </h4>
          <div className="grid grid-cols-2 gap-3 max-h-64 overflow-y-auto">
            {recommendations.map((rec, index) => (
              <div
                key={index}
                className="bg-white rounded-lg p-3 border border-amber-200 shadow-sm"
              >
                <div className="font-semibold text-sm text-amber-900 mb-1">
                  {rec.title}
                </div>
                <div className="text-xs text-gray-700 mb-2">{rec.description}</div>
                <div className="text-xs text-amber-800 bg-amber-100 p-2 rounded font-mono">
                  {rec.example}
                </div>
              </div>
            ))}
          </div>
          <div className="mt-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
            <div className="text-sm text-blue-900">
              <span className="font-semibold">💡 Tip:</span> Usa el botón "Generar Automático" para crear un prompt base basado en las etapas de tu flujo, luego personalízalo siguiendo estas recomendaciones.
            </div>
          </div>
        </div>
      )}

      <div className="flex-1 flex flex-col overflow-hidden">
        {showPreview ? (
          <div className="flex-1 overflow-auto p-4 bg-gray-50">
            <div className="prose max-w-none">
              <pre className="whitespace-pre-wrap text-sm font-mono bg-white p-4 rounded border">
                {prompt || 'No hay prompt generado'}
              </pre>
            </div>
          </div>
        ) : (
          <textarea
            value={prompt}
            onChange={(e) => handlePromptChange(e.target.value)}
            placeholder="Escribe aquí el prompt del sistema que se le pasará al LLM..."
            className="flex-1 w-full p-4 border-0 resize-none focus:outline-none font-mono text-sm"
            style={{ minHeight: '300px' }}
          />
        )}
      </div>

      <div className="p-4 border-t border-gray-300 bg-gray-50">
        <div className="text-xs text-gray-600">
          <div className="font-semibold mb-1">Información:</div>
          <div>• Este prompt se enviará al LLM como mensaje del sistema</div>
          <div>• Define el comportamiento esperado del asistente</div>
          <div>• Puedes usar "Generar Automático" para crear un prompt basado en las etapas del flujo</div>
          {flow && (
            <div className="mt-2">
              <span className="font-semibold">Flujo:</span> {flow.name} ({flow.domain})
            </div>
          )}
          {stages.length > 0 && (
            <div>
              <span className="font-semibold">Etapas:</span> {stages.length}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default PromptEditor;
