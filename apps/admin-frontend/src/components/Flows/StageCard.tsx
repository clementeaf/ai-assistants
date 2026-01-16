import { useState } from 'react';
import type { FlowStage } from '../../lib/api/flows';

interface StageCardProps {
  stage: FlowStage;
  index: number;
  totalStages: number;
  onUpdatePrompt: (promptText: string) => Promise<void>;
  onUpdateRules: (validationRules: string) => Promise<void>;
  onDelete: () => Promise<void>;
  onMoveUp: () => Promise<void>;
  onMoveDown: () => Promise<void>;
  loading: boolean;
}

/**
 * Componente para mostrar y editar una etapa del flujo
 * Permite editar el prompt y las reglas de validación específicas de cada etapa
 * @param stage - Etapa a mostrar
 * @param index - Índice de la etapa
 * @param totalStages - Total de etapas
 * @param onUpdatePrompt - Callback para actualizar el prompt
 * @param onUpdateRules - Callback para actualizar las reglas
 * @param onDelete - Callback para eliminar la etapa
 * @param onMoveUp - Callback para mover hacia arriba
 * @param onMoveDown - Callback para mover hacia abajo
 * @param loading - Estado de carga
 * @returns Componente StageCard renderizado
 */
function StageCard({
  stage,
  index,
  totalStages,
  onUpdatePrompt,
  onUpdateRules,
  onDelete,
  onMoveUp,
  onMoveDown,
  loading,
}: StageCardProps) {
  const [isEditingPrompt, setIsEditingPrompt] = useState(false);
  const [isEditingRules, setIsEditingRules] = useState(false);
  const [promptText, setPromptText] = useState(stage.prompt_text || '');
  const [validationRules, setValidationRules] = useState(stage.validation_rules || '');

  const handleSavePrompt = async (): Promise<void> => {
    await onUpdatePrompt(promptText);
    setIsEditingPrompt(false);
  };

  const handleCancelPrompt = (): void => {
    setPromptText(stage.prompt_text || '');
    setIsEditingPrompt(false);
  };

  const handleSaveRules = async (): Promise<void> => {
    await onUpdateRules(validationRules);
    setIsEditingRules(false);
  };

  const handleCancelRules = (): void => {
    setValidationRules(stage.validation_rules || '');
    setIsEditingRules(false);
  };

  const getStageTypeLabel = (): string => {
    const typeMap: Record<string, string> = {
      greeting: 'Saludo',
      input: 'Solicitar Información',
      confirmation: 'Confirmación',
      action: 'Acción',
    };
    return typeMap[stage.stage_type] || stage.stage_type;
  };

  const getFieldTypeLabel = (): string => {
    if (stage.field_type) {
      const fieldMap: Record<string, string> = {
        text: 'Texto',
        date: 'Fecha',
        time: 'Hora',
        email: 'Email',
        number: 'Número',
      };
      return fieldMap[stage.field_type] || stage.field_type;
    }
    return '';
  };

  return (
    <div className="bg-white border-2 border-gray-200 rounded-lg p-5 hover:border-blue-300 transition-colors">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-8 h-8 bg-blue-500 text-white rounded-full font-bold text-sm">
            {index + 1}
          </div>
          <div>
            <h4 className="font-semibold text-gray-800">{stage.stage_name}</h4>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded">
                {getStageTypeLabel()}
              </span>
              {stage.field_type && (
                <span className="text-xs px-2 py-1 bg-green-100 text-green-800 rounded">
                  {getFieldTypeLabel()}
                </span>
              )}
              {stage.is_required && (
                <span className="text-xs px-2 py-1 bg-red-100 text-red-800 rounded">
                  Requerido
                </span>
              )}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {index > 0 && (
            <button
              onClick={onMoveUp}
              disabled={loading}
              className="p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
              title="Mover arriba"
            >
              ↑
            </button>
          )}
          {index < totalStages - 1 && (
            <button
              onClick={onMoveDown}
              disabled={loading}
              className="p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
              title="Mover abajo"
            >
              ↓
            </button>
          )}
          <button
            onClick={onDelete}
            disabled={loading}
            className="p-2 text-red-500 hover:text-red-700 hover:bg-red-50 rounded transition-colors"
            title="Eliminar etapa"
          >
            ×
          </button>
        </div>
      </div>

      {/* Prompt de la etapa */}
      <div className="mb-4">
        <div className="flex justify-between items-center mb-2">
          <label className="text-sm font-medium text-gray-700">Prompt de la Etapa</label>
          {!isEditingPrompt && (
            <button
              onClick={() => setIsEditingPrompt(true)}
              className="text-xs text-blue-600 hover:text-blue-800"
            >
              Editar
            </button>
          )}
        </div>
        {isEditingPrompt ? (
          <div className="space-y-2">
            <textarea
              value={promptText}
              onChange={(e) => setPromptText(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              rows={3}
              placeholder="Texto que dirá el asistente en esta etapa..."
            />
            <div className="flex gap-2">
              <button
                onClick={handleSavePrompt}
                disabled={loading}
                className="px-3 py-1 bg-green-500 text-white rounded text-sm hover:bg-green-600 disabled:bg-gray-300 transition-colors"
              >
                Guardar
              </button>
              <button
                onClick={handleCancelPrompt}
                disabled={loading}
                className="px-3 py-1 bg-gray-500 text-white rounded text-sm hover:bg-gray-600 disabled:bg-gray-300 transition-colors"
              >
                Cancelar
              </button>
            </div>
          </div>
        ) : (
          <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
            <p className="text-sm text-gray-700 whitespace-pre-wrap">
              {stage.prompt_text || <span className="text-gray-400 italic">Sin prompt configurado</span>}
            </p>
          </div>
        )}
      </div>

      {/* Reglas de validación específicas */}
      <div>
        <div className="flex justify-between items-center mb-2">
          <label className="text-sm font-medium text-gray-700">
            Reglas Específicas de esta Etapa
          </label>
          {!isEditingRules && (
            <button
              onClick={() => setIsEditingRules(true)}
              className="text-xs text-blue-600 hover:text-blue-800"
            >
              {stage.validation_rules ? 'Editar' : 'Agregar Reglas'}
            </button>
          )}
        </div>
        {isEditingRules ? (
          <div className="space-y-2">
            <textarea
              value={validationRules}
              onChange={(e) => setValidationRules(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm font-mono"
              rows={4}
              placeholder="Ejemplo:&#10;- El nombre debe tener al menos 3 caracteres&#10;- La fecha debe ser futura&#10;- El email debe tener formato válido"
            />
            <p className="text-xs text-gray-500">
              Especifica reglas particulares que el autónomo debe respetar en esta etapa
            </p>
            <div className="flex gap-2">
              <button
                onClick={handleSaveRules}
                disabled={loading}
                className="px-3 py-1 bg-green-500 text-white rounded text-sm hover:bg-green-600 disabled:bg-gray-300 transition-colors"
              >
                Guardar Reglas
              </button>
              <button
                onClick={handleCancelRules}
                disabled={loading}
                className="px-3 py-1 bg-gray-500 text-white rounded text-sm hover:bg-gray-600 disabled:bg-gray-300 transition-colors"
              >
                Cancelar
              </button>
            </div>
          </div>
        ) : (
          <div className="p-3 bg-yellow-50 rounded-lg border border-yellow-200">
            {stage.validation_rules ? (
              <pre className="text-xs font-mono text-gray-800 whitespace-pre-wrap">
                {stage.validation_rules}
              </pre>
            ) : (
              <p className="text-xs text-gray-400 italic">No hay reglas específicas configuradas</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default StageCard;
