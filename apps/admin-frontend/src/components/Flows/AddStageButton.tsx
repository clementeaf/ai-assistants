import { useState } from 'react';
import type { AddStageRequest } from '../../lib/api/flows';

interface AddStageButtonProps {
  flowId: string;
  currentStagesCount: number;
  onAdd: (request: AddStageRequest) => Promise<void>;
  onClose: () => void;
  show: boolean;
  onShow: () => void;
}

/**
 * Componente para agregar nuevas etapas al flujo
 * @param flowId - ID del flujo
 * @param currentStagesCount - Cantidad actual de etapas
 * @param onAdd - Callback para agregar la etapa
 * @param onClose - Callback para cerrar el modal
 * @param show - Si el modal está visible
 * @param onShow - Callback para mostrar el modal
 * @returns Componente AddStageButton renderizado
 */
function AddStageButton({ flowId, currentStagesCount, onAdd, onClose, show, onShow }: AddStageButtonProps) {
  const [stageType, setStageType] = useState<string>('');
  const [promptText, setPromptText] = useState('');
  const [fieldName, setFieldName] = useState('');
  const [fieldType, setFieldType] = useState<string>('');
  const [isRequired, setIsRequired] = useState(true);

  const stageTypes = [
    { value: 'greeting', label: 'Saludo', description: 'Mensaje de bienvenida inicial' },
    { value: 'input', label: 'Solicitar Información', description: 'El asistente pedirá información al usuario' },
    { value: 'confirmation', label: 'Confirmación', description: 'El asistente pedirá confirmar antes de continuar' },
  ];

  const fieldTypes = [
    { value: 'text', label: 'Texto' },
    { value: 'date', label: 'Fecha' },
    { value: 'time', label: 'Hora' },
    { value: 'email', label: 'Email' },
    { value: 'number', label: 'Número' },
  ];

  const handleSubmit = async (): Promise<void> => {
    if (!stageType) {
      return;
    }

    const request: AddStageRequest = {
      flow_id: flowId,
      stage_order: currentStagesCount + 1,
      stage_name: `stage_${currentStagesCount + 1}`,
      stage_type: stageType,
      prompt_text: promptText || undefined,
      field_name: fieldName || undefined,
      field_type: fieldType || undefined,
      is_required: isRequired,
    };

    await onAdd(request);
    handleReset();
  };

  const handleReset = (): void => {
    setStageType('');
    setPromptText('');
    setFieldName('');
    setFieldType('');
    setIsRequired(true);
    onClose();
  };

  const handleStageTypeChange = (type: string): void => {
    setStageType(type);
    if (type === 'input' && !fieldType) {
      setFieldType('text');
    }
  };

  return (
    <>
      <button
        onClick={onShow}
        className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors text-sm font-medium"
      >
        + Agregar Etapa
      </button>

      {show && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-semibold">Agregar Nueva Etapa</h3>
              <button
                onClick={handleReset}
                className="text-gray-500 hover:text-gray-700 text-2xl"
              >
                ×
              </button>
            </div>

            <div className="space-y-4">
              {/* Tipo de etapa */}
              <div>
                <label className="block text-sm font-medium mb-2">Tipo de Etapa</label>
                <div className="grid grid-cols-3 gap-2">
                  {stageTypes.map((type) => (
                    <button
                      key={type.value}
                      onClick={() => handleStageTypeChange(type.value)}
                      className={`p-3 text-left border-2 rounded-lg transition-colors ${
                        stageType === type.value
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-blue-300'
                      }`}
                    >
                      <div className="font-semibold text-sm">{type.label}</div>
                      <div className="text-xs text-gray-600 mt-1">{type.description}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Prompt de la etapa */}
              <div>
                <label className="block text-sm font-medium mb-2">Prompt de la Etapa</label>
                <textarea
                  value={promptText}
                  onChange={(e) => setPromptText(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={3}
                  placeholder="Texto que dirá el asistente en esta etapa..."
                />
              </div>

              {/* Campos adicionales para tipo input */}
              {stageType === 'input' && (
                <>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-2">Nombre del Campo</label>
                      <input
                        type="text"
                        value={fieldName}
                        onChange={(e) => setFieldName(e.target.value)}
                        className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Ej: customer_name, date, time"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">Tipo de Campo</label>
                      <select
                        value={fieldType}
                        onChange={(e) => setFieldType(e.target.value)}
                        className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="">Seleccionar...</option>
                        {fieldTypes.map((type) => (
                          <option key={type.value} value={type.value}>
                            {type.label}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                  <div>
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={isRequired}
                        onChange={(e) => setIsRequired(e.target.checked)}
                        className="rounded"
                      />
                      <span className="text-sm">Campo requerido</span>
                    </label>
                  </div>
                </>
              )}

              {/* Botones */}
              <div className="flex gap-2 pt-4 border-t">
                <button
                  onClick={handleSubmit}
                  disabled={!stageType}
                  className="flex-1 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:bg-gray-300 transition-colors"
                >
                  Agregar Etapa
                </button>
                <button
                  onClick={handleReset}
                  className="flex-1 px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
                >
                  Cancelar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default AddStageButton;
