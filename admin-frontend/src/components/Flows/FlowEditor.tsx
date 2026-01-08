import { useState } from 'react';
import type { FlowStage } from '../../lib/api/flows';
import StageModule from './StageModule';
import AddStageModule from './AddStageModule';

interface FlowEditorProps {
  flowName: string;
  stages: FlowStage[];
  loading: boolean;
  onUpdateStage: (stageId: string, promptText: string) => void;
  onDeleteStage: (stageId: string) => void;
  onMoveStage: (stageId: string, direction: 'up' | 'down') => void;
  onAddModule: () => void;
  onAddModuleConfirm: (moduleType: string) => void;
  showAddModule: boolean;
  onCloseAddModule: () => void;
}

/**
 * Editor de flujo con scroll interno
 * Contiene todos los módulos del flujo y permite editarlos
 */
function FlowEditor({
  flowName,
  stages,
  loading,
  onUpdateStage,
  onDeleteStage,
  onMoveStage,
  onAddModule,
  onAddModuleConfirm,
  showAddModule,
  onCloseAddModule,
}: FlowEditorProps) {
  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow">
      {/* Header fijo */}
      <div className="flex-shrink-0 flex justify-between items-center p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold">Editor de Flujo: {flowName}</h2>
        <button
          onClick={onAddModule}
          className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors text-sm"
        >
          + Agregar Módulo
        </button>
      </div>

      {/* Contenido con scroll */}
      <div className="flex-1 overflow-y-auto p-4">
        {loading && stages.length === 0 ? (
          <div className="text-center py-12 text-gray-500">Cargando módulos...</div>
        ) : stages.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <div className="text-lg mb-2">No hay módulos en este flujo</div>
            <div className="text-sm mb-4">
              Agrega módulos preformulados para definir qué información obtener del cliente
            </div>
            <button
              onClick={onAddModule}
              className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
            >
              Agregar Primer Módulo
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {stages
              .sort((a, b) => a.stage_order - b.stage_order)
              .map((stage, index) => (
                <StageModule
                  key={stage.stage_id}
                  stage={stage}
                  onUpdate={onUpdateStage}
                  onDelete={onDeleteStage}
                  onMoveUp={index > 0 ? () => onMoveStage(stage.stage_id, 'up') : undefined}
                  onMoveDown={
                    index < stages.length - 1 ? () => onMoveStage(stage.stage_id, 'down') : undefined
                  }
                  canMoveUp={index > 0}
                  canMoveDown={index < stages.length - 1}
                />
              ))}
          </div>
        )}

        {showAddModule && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="max-w-2xl w-full mx-4">
              <AddStageModule
                onAddModule={(moduleType) => {
                  if (moduleType !== '') {
                    onAddModuleConfirm(moduleType);
                  }
                  onCloseAddModule();
                }}
                onClose={onCloseAddModule}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default FlowEditor;
