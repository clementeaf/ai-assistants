import { useState, useEffect } from 'react';
import { getDomainMetadata } from '../../lib/api/automata';
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
  flow?: { flow_id: string; domain: string } | null;
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
  flow,
}: FlowEditorProps) {
  const [showLinks, setShowLinks] = useState(false);
  const [activationCode, setActivationCode] = useState<string>('');

  // Obtener número de WhatsApp desde variable de entorno
  const whatsappNumber = import.meta.env.VITE_WHATSAPP_NUMBER || '56959263366';

  useEffect(() => {
    const loadActivationCode = async (): Promise<void> => {
      if (!flow) return;
      try {
        const metadata = await getDomainMetadata(flow.domain);
        setActivationCode(metadata.activation_code);
      } catch (error) {
        console.error('Error loading activation code:', error);
        // Fallback si falla
        setActivationCode(`FLOW_${flow.domain.toUpperCase()}_INIT`);
      }
    };
    loadActivationCode();
  }, [flow]);

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow overflow-hidden">
      {/* Header fijo */}
      <div className="flex-shrink-0 flex justify-between items-center p-4 border-b border-gray-200 gap-2">
        <h2 className="text-lg font-semibold flex-1">Editor de Flujo: {flowName}</h2>
        <div className="flex gap-2">
          {flow && (
            <button
              onClick={() => setShowLinks(!showLinks)}
              className="px-3 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors text-sm"
              title="Mostrar links de activación"
            >
              {showLinks ? 'Ocultar Links' : 'Links'}
            </button>
          )}
          <button
            onClick={onAddModule}
            className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors text-sm"
          >
            + Agregar Módulo
          </button>
        </div>
      </div>

      {/* Panel de links colapsable */}
      {showLinks && flow && (
        <div className="flex-shrink-0 border-b border-gray-200 bg-gray-50 p-3">
          <div className="grid grid-cols-2 gap-3">
            {/* Link genérico para menú */}
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-2">
              <div className="flex items-center justify-between mb-1">
                <h3 className="font-semibold text-purple-900 text-xs">Menú de Flujos</h3>
                <span className="text-xs bg-purple-100 text-purple-800 px-1.5 py-0.5 rounded">MENU</span>
              </div>
              <div className="space-y-1">
                <div>
                  <label className="text-xs font-medium text-gray-700">Código:</label>
                  <code className="block mt-0.5 bg-white px-1.5 py-0.5 rounded border text-xs font-mono">MENU_INIT</code>
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-700">Link:</label>
                  <div className="flex gap-1 mt-0.5">
                    <input
                      type="text"
                      value={`https://wa.me/${whatsappNumber}?text=${encodeURIComponent('MENU_INIT')}`}
                      readOnly
                      className="flex-1 px-1.5 py-0.5 border rounded text-xs bg-white"
                    />
                    <button
                      onClick={async () => {
                        const link = `https://wa.me/${whatsappNumber}?text=${encodeURIComponent('MENU_INIT')}`;
                        await navigator.clipboard.writeText(link);
                        alert('Link copiado');
                      }}
                      className="px-2 py-0.5 bg-purple-500 text-white rounded text-xs hover:bg-purple-600"
                    >
                      Copiar
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Link específico del flujo */}
            {flow && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-2">
                <div className="flex items-center justify-between mb-1">
                  <h3 className="font-semibold text-blue-900 text-xs">Link de Activación</h3>
                  <span className="text-xs bg-blue-100 text-blue-800 px-1.5 py-0.5 rounded">{flow.domain}</span>
                </div>
                <div className="space-y-1">
                  <div>
                    <label className="text-xs font-medium text-gray-700">Código:</label>
                    <code className="block mt-0.5 bg-white px-1.5 py-0.5 rounded border text-xs font-mono">
                      {activationCode || 'Cargando...'}
                    </code>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-700">Link:</label>
                    <div className="flex gap-1 mt-0.5">
                      <input
                        type="text"
                        value={activationCode ? `https://wa.me/${whatsappNumber}?text=${encodeURIComponent(activationCode)}` : ''}
                        readOnly
                        className="flex-1 px-1.5 py-0.5 border rounded text-xs bg-white"
                      />
                      <button
                        onClick={async () => {
                          if (!activationCode) return;
                          const link = `https://wa.me/${whatsappNumber}?text=${encodeURIComponent(activationCode)}`;
                          await navigator.clipboard.writeText(link);
                          alert('Link copiado');
                        }}
                        disabled={!activationCode}
                        className="px-2 py-0.5 bg-blue-500 text-white rounded text-xs hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
                      >
                        Copiar
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Contenido con scroll */}
      <div className="flex-1 overflow-y-auto p-4 min-h-0">
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
