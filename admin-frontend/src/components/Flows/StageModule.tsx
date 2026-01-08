import { useState } from 'react';
import type { FlowStage } from '../../lib/api/flows';

interface StageModuleProps {
  stage: FlowStage;
  onUpdate: (stageId: string, promptText: string) => void;
  onDelete: (stageId: string) => void;
  onMoveUp?: () => void;
  onMoveDown?: () => void;
  canMoveUp: boolean;
  canMoveDown: boolean;
}

/**
 * Módulo preformulado de etapa del flujo
 * Permite editar solo el texto del asistente, el formato está preconfigurado
 * @param stage - Etapa del flujo
 * @param onUpdate - Callback para actualizar el texto del prompt
 * @param onDelete - Callback para eliminar la etapa
 * @param onMoveUp - Callback para mover hacia arriba
 * @param onMoveDown - Callback para mover hacia abajo
 * @param canMoveUp - Si se puede mover hacia arriba
 * @param canMoveDown - Si se puede mover hacia abajo
 * @returns Componente StageModule renderizado
 */
function StageModule({
  stage,
  onUpdate,
  onDelete,
  onMoveUp,
  onMoveDown,
  canMoveUp,
  canMoveDown,
}: StageModuleProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [promptText, setPromptText] = useState(stage.prompt_text || '');

  const handleSave = (): void => {
    onUpdate(stage.stage_id, promptText);
    setIsEditing(false);
  };

  const handleCancel = (): void => {
    setPromptText(stage.prompt_text || '');
    setIsEditing(false);
  };

  const getModuleTypeLabel = (): string => {
    if (stage.stage_type === 'greeting') return 'Saludo';
    if (stage.stage_type === 'input') {
      if (stage.field_type === 'date') return 'Solicitar Fecha';
      if (stage.field_type === 'time') return 'Solicitar Hora';
      if (stage.field_type === 'email') return 'Solicitar Email';
      if (stage.field_type === 'number') return 'Solicitar Número';
      return 'Solicitar Texto';
    }
    if (stage.stage_type === 'confirmation') return 'Confirmación';
    if (stage.stage_type === 'action') return 'Acción';
    return stage.stage_type;
  };

  const getFormatInfo = (): string => {
    if (stage.field_type === 'date') return 'Formato: Fecha (YYYY-MM-DD)';
    if (stage.field_type === 'time') return 'Formato: Hora (HH:MM)';
    if (stage.field_type === 'email') return 'Formato: Email';
    if (stage.field_type === 'number') return 'Formato: Número';
    if (stage.field_type === 'text') return 'Formato: Texto';
    return '';
  };

  return (
    <div className="bg-white rounded-lg border-2 border-gray-300 shadow-sm hover:shadow-md transition-shadow">
      <div className="p-4">
        {/* Header */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-gray-500">#{stage.stage_order}</span>
            <span className="text-sm font-semibold text-blue-600 bg-blue-50 px-2 py-1 rounded">
              {getModuleTypeLabel()}
            </span>
            {getFormatInfo() && (
              <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                {getFormatInfo()}
              </span>
            )}
          </div>
          <div className="flex items-center gap-1">
            {canMoveUp && onMoveUp && (
              <button
                onClick={onMoveUp}
                className="p-1 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded"
                title="Mover arriba"
              >
                ↑
              </button>
            )}
            {canMoveDown && onMoveDown && (
              <button
                onClick={onMoveDown}
                className="p-1 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded"
                title="Mover abajo"
              >
                ↓
              </button>
            )}
            <button
              onClick={() => {
                if (confirm('¿Estás seguro de eliminar esta etapa?')) {
                  onDelete(stage.stage_id);
                }
              }}
              className="p-1 text-red-500 hover:text-red-700 hover:bg-red-50 rounded"
              title="Eliminar"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Contenido editable */}
        {isEditing ? (
          <div className="space-y-2">
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">
                Asistente:
              </label>
              <textarea
                value={promptText}
                onChange={(e) => setPromptText(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                rows={3}
                placeholder="Escribe lo que dirá el asistente..."
              />
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleSave}
                className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm transition-colors"
              >
                Guardar
              </button>
              <button
                onClick={handleCancel}
                className="px-3 py-1 bg-gray-500 text-white rounded hover:bg-gray-600 text-sm transition-colors"
              >
                Cancelar
              </button>
            </div>
          </div>
        ) : (
          <div>
            <div className="mb-2">
              <span className="text-xs font-semibold text-gray-700">Asistente:</span>
            </div>
            <div
              className="p-3 bg-gray-50 rounded-lg border border-gray-200 cursor-pointer hover:bg-gray-100 transition-colors"
              onClick={() => setIsEditing(true)}
            >
              {promptText || (
                <span className="text-gray-400 italic">Click para editar el texto del asistente...</span>
              )}
            </div>
            {getFormatInfo() && (
              <div className="mt-2 text-xs text-gray-500">
                {getFormatInfo()}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default StageModule;
