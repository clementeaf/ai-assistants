import { useState } from 'react';
import type { Flow, FlowStage } from '../../lib/api/flows';
import AutomatonAssistant from './AutomatonAssistant';

interface SystemPromptViewerProps {
  stage: FlowStage;
  flow: Flow;
  allStages: FlowStage[];
  onUpdate: (promptText: string) => Promise<void>;
  loading: boolean;
}

/**
 * Componente para visualizar y editar el prompt del sistema autónomo
 * Este prompt define cómo el LLM conecta con Google Calendar
 * @param stage - Etapa de tipo system_prompt
 * @param onUpdate - Callback para actualizar el prompt
 * @param loading - Estado de carga
 * @returns Componente SystemPromptViewer renderizado
 */
function SystemPromptViewer({ stage, flow, allStages, onUpdate, loading }: SystemPromptViewerProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [promptText, setPromptText] = useState(stage.prompt_text || '');
  const [showAssistant, setShowAssistant] = useState(false);

  const handleSave = async (): Promise<void> => {
    await onUpdate(promptText);
    setIsEditing(false);
  };

  const handleCancel = (): void => {
    setPromptText(stage.prompt_text || '');
    setIsEditing(false);
  };

  const handleMainButtonClick = (): void => {
    if (isEditing) {
      handleSave();
    } else {
      setIsEditing(true);
    }
  };

  return (
    <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-200 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-blue-700">
          Este prompt define cómo el LLM conecta con Google Calendar y gestiona reservas
        </p>
        <button
          onClick={handleMainButtonClick}
          disabled={loading}
          className={`px-4 py-2 rounded-lg transition-colors text-sm ${
            isEditing
              ? 'bg-blue-600 text-white hover:bg-blue-700 disabled:bg-gray-300'
              : 'bg-white border border-gray-400 text-gray-700 hover:bg-gray-50'
          }`}
        >
          {loading ? 'Guardando...' : isEditing ? 'Guardar' : 'Editar'}
        </button>
      </div>

      {isEditing ? (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Prompt del Sistema (editable)
            </label>
            <textarea
              value={promptText}
              onChange={(e) => setPromptText(e.target.value)}
              className="w-full px-4 py-3 border-2 border-blue-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm font-mono bg-white"
              rows={20}
              placeholder="Prompt del sistema autónomo..."
            />
            <p className="text-xs text-gray-500 mt-2">
              Este prompt se usa para entrenar al autónomo sobre cómo interactuar con Google Calendar
            </p>
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-lg border border-blue-200 p-4">
          <pre className="text-xs font-mono text-gray-800 whitespace-pre-wrap overflow-x-auto">
            {stage.prompt_text || 'No hay prompt configurado'}
          </pre>
        </div>
      )}

      {showAssistant && (
        <AutomatonAssistant
          onGeneratePrompt={(generatedPrompt) => {
            setPromptText(generatedPrompt);
            setIsEditing(true);
            setShowAssistant(false);
          }}
          onClose={() => setShowAssistant(false)}
          flow={flow}
          currentPrompt={stage.prompt_text || ''}
          stages={allStages}
        />
      )}
    </div>
  );
}

export default SystemPromptViewer;
