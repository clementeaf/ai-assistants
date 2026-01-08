import { useState } from 'react';
import type { FlowStage } from '../../lib/api/flows';

interface FlowEditorProps {
  stages: FlowStage[];
  onStageSelect?: (stage: FlowStage | null) => void;
  onStageReorder?: (stageId: string, newOrder: number) => void;
}

/**
 * Editor visual de flujo de conversación en formato columna
 * Permite visualizar y editar la estructura de diálogo como una lista vertical
 * @param stages - Etapas del flujo
 * @param onStageSelect - Callback cuando se selecciona una etapa
 * @param onStageReorder - Callback cuando se reordena una etapa
 * @returns Componente FlowEditor renderizado
 */
function FlowEditor({ stages, onStageSelect, onStageReorder }: FlowEditorProps) {
  const [selectedStageId, setSelectedStageId] = useState<string | null>(null);

  const handleStageClick = (stage: FlowStage): void => {
    if (selectedStageId === stage.stage_id) {
      setSelectedStageId(null);
      onStageSelect?.(null);
    } else {
      setSelectedStageId(stage.stage_id);
      onStageSelect?.(stage);
    }
  };

  const getStageTypeColor = (type: string): string => {
    switch (type) {
      case 'greeting':
        return 'bg-green-500';
      case 'input':
        return 'bg-blue-500';
      case 'confirmation':
        return 'bg-yellow-500';
      case 'action':
        return 'bg-purple-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getStageTypeLabel = (type: string): string => {
    switch (type) {
      case 'greeting':
        return 'Saludo';
      case 'input':
        return 'Entrada';
      case 'confirmation':
        return 'Confirmación';
      case 'action':
        return 'Acción';
      default:
        return type;
    }
  };

  const sortedStages = [...stages].sort((a, b) => a.stage_order - b.stage_order);

  return (
    <div className="w-full h-full bg-gray-50 border-2 border-gray-300 rounded-lg p-4 overflow-y-auto">
      <div className="max-w-2xl mx-auto space-y-4">
        {sortedStages.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <div className="text-lg mb-2">No hay etapas en este flujo</div>
            <div className="text-sm">Agrega etapas para definir qué información obtener del cliente</div>
          </div>
        ) : (
          <>
            <div className="mb-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-2">
                Información a Obtener del Cliente:
              </h3>
              <div className="text-xs text-gray-600">
                {sortedStages.filter((s) => s.stage_type === 'input' && s.field_name).length} campo(s) requerido(s)
              </div>
            </div>

            {sortedStages.map((stage, index) => {
              const isSelected = selectedStageId === stage.stage_id;
              const isInputStage = stage.stage_type === 'input' && stage.field_name;

              return (
                <div key={stage.stage_id} className="relative">
                  {/* Conector vertical */}
                  {index < sortedStages.length - 1 && (
                    <div className="absolute left-6 top-16 w-0.5 h-4 bg-gray-400 z-0" />
                  )}

                  {/* Nodo de etapa */}
                  <div
                    className={`relative rounded-lg shadow-md border-2 transition-all cursor-pointer ${
                      isSelected
                        ? 'border-blue-600 ring-2 ring-blue-300 scale-105'
                        : 'border-gray-400 hover:border-gray-500'
                    }`}
                    onClick={() => handleStageClick(stage)}
                  >
                    {/* Header con tipo y orden */}
                    <div className={`${getStageTypeColor(stage.stage_type)} text-white px-4 py-3 rounded-t-lg`}>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-semibold bg-white bg-opacity-20 px-2 py-1 rounded">
                            {stage.stage_order}
                          </span>
                          <span className="font-semibold text-sm">{stage.stage_name}</span>
                        </div>
                        <span className="text-xs bg-white bg-opacity-20 px-2 py-1 rounded">
                          {getStageTypeLabel(stage.stage_type)}
                        </span>
                      </div>
                    </div>

                    {/* Contenido */}
                    <div className="bg-white px-4 py-3 rounded-b-lg">
                      {stage.prompt_text && (
                        <div className="text-sm text-gray-700 mb-2">
                          <span className="font-semibold">Prompt:</span> {stage.prompt_text}
                        </div>
                      )}

                      {isInputStage && (
                        <div className="mt-2 p-2 bg-blue-50 rounded border border-blue-200">
                          <div className="flex items-center gap-2 text-xs">
                            <span className="font-semibold text-blue-900">Campo a obtener:</span>
                            <span className="text-blue-700">{stage.field_name}</span>
                            {stage.field_type && (
                              <>
                                <span className="text-blue-500">•</span>
                                <span className="text-blue-600">({stage.field_type})</span>
                              </>
                            )}
                            {stage.is_required && (
                              <span className="ml-auto bg-red-500 text-white px-2 py-0.5 rounded text-xs font-semibold">
                                REQUERIDO
                              </span>
                            )}
                          </div>
                        </div>
                      )}

                      {stage.validation_rules && (
                        <div className="mt-2 text-xs text-gray-600">
                          <span className="font-semibold">Validación:</span> {stage.validation_rules}
                        </div>
                      )}

                      {stage.stage_type === 'confirmation' && (
                        <div className="mt-2 p-2 bg-yellow-50 rounded border border-yellow-200">
                          <div className="text-xs text-yellow-900">
                            <span className="font-semibold">Confirmación:</span> El usuario debe confirmar antes de continuar
                          </div>
                        </div>
                      )}

                      {stage.stage_type === 'action' && (
                        <div className="mt-2 p-2 bg-purple-50 rounded border border-purple-200">
                          <div className="text-xs text-purple-900">
                            <span className="font-semibold">Acción:</span> Se ejecutará una acción del sistema
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </>
        )}
      </div>
    </div>
  );
}

export default FlowEditor;
