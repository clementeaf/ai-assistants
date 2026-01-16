import { useState } from 'react';
import type { Flow, FlowStage, AddStageRequest } from '../../lib/api/flows';
import SystemPromptViewer from './SystemPromptViewer';
import StageCard from './StageCard';
import AddStageButton from './AddStageButton';

interface FlowDetailsProps {
  flow: Flow;
  stages: FlowStage[];
  loading: boolean;
  onUpdateStagePrompt: (stageId: string, promptText: string) => Promise<void>;
  onUpdateStageRules: (stageId: string, validationRules: string) => Promise<void>;
  onDeleteStage: (stageId: string) => Promise<void>;
  onMoveStage: (stageId: string, direction: 'up' | 'down') => Promise<void>;
  onAddStage: (request: AddStageRequest) => Promise<void>;
  onBack: () => void;
}

/**
 * Componente principal para mostrar los detalles de un flujo
 * Incluye el prompt del autónomo y las etapas que debe respetar
 * @param flow - Flujo seleccionado
 * @param stages - Etapas del flujo
 * @param loading - Estado de carga
 * @param onUpdateStagePrompt - Callback para actualizar el prompt de una etapa
 * @param onUpdateStageRules - Callback para actualizar las reglas de una etapa
 * @param onDeleteStage - Callback para eliminar una etapa
 * @param onMoveStage - Callback para mover una etapa
 * @param onAddStage - Callback para agregar una etapa
 * @returns Componente FlowDetails renderizado
 */
function FlowDetails({
  flow,
  stages,
  loading,
  onUpdateStagePrompt,
  onUpdateStageRules,
  onDeleteStage,
  onMoveStage,
  onAddStage,
  onBack,
}: FlowDetailsProps) {
  const [activeTab, setActiveTab] = useState<'prompt' | 'stages'>('prompt');
  const [showAddStage, setShowAddStage] = useState(false);

  const systemPromptStage = stages.find((s) => s.stage_type === 'system_prompt');
  const regularStages = stages
    .filter((s) => s.stage_type !== 'system_prompt')
    .sort((a, b) => a.stage_order - b.stage_order);

  const [domainMetadata, setDomainMetadata] = useState<{ display_name: string; description: string } | null>(null);

  useEffect(() => {
    const loadMetadata = async (): Promise<void> => {
      try {
        const metadata = await getDomainMetadata(flow.domain);
        setDomainMetadata({
          display_name: metadata.display_name,
          description: metadata.description,
        });
      } catch (error) {
        console.error('Error loading domain metadata:', error);
        // Usar valores por defecto si falla
        setDomainMetadata({
          display_name: flow.name,
          description: flow.description || 'Flujo de conversación configurable',
        });
      }
    };
    loadMetadata();
  }, [flow.domain, flow.name, flow.description]);

  const getFlowDisplayName = (): string => {
    return domainMetadata?.display_name || flow.name;
  };

  const getFlowDescription = (): string => {
    return domainMetadata?.description || flow.description || 'Flujo de conversación configurable';
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow overflow-hidden">
      {/* Header */}
      <div className="flex-shrink-0 p-3 border-b border-gray-200">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-3">
            <button
              onClick={onBack}
              className="p-1.5 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded transition-colors"
              title="Volver a la lista de flujos"
            >
              ←
            </button>
            <div>
              <h2 className="text-lg font-bold text-gray-800">{getFlowDisplayName()}</h2>
              <p className="text-xs text-gray-600 mt-0.5">{getFlowDescription()}</p>
              <div className="flex items-center gap-1.5 mt-1.5">
                <span className="text-[10px] px-1.5 py-0.5 bg-blue-100 text-blue-800 rounded">
                  {flow.domain}
                </span>
                <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                  flow.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                }`}>
                  {flow.is_active ? 'Activo' : 'Inactivo'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex-shrink-0 border-b border-gray-200">
        <div className="flex">
          <button
            onClick={() => setActiveTab('prompt')}
            className={`px-6 py-3 font-medium text-sm transition-colors ${
              activeTab === 'prompt'
                ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
            }`}
          >
            Prompt del Sistema
          </button>
          <button
            onClick={() => setActiveTab('stages')}
            className={`px-6 py-3 font-medium text-sm transition-colors ${
              activeTab === 'stages'
                ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
            }`}
          >
            Etapas a Respetar
          </button>
        </div>
      </div>

      {/* Contenido con scroll según tab activo */}
      <div className="flex-1 overflow-y-auto p-6">
        {activeTab === 'prompt' && (
          <div>
            {systemPromptStage ? (
              <SystemPromptViewer
                stage={systemPromptStage}
                flow={flow}
                allStages={stages}
                onUpdate={(promptText: string) => onUpdateStagePrompt(systemPromptStage.stage_id, promptText)}
                loading={loading}
              />
            ) : (
              <div className="text-center py-8 text-gray-500">
                <p className="mb-2">No hay prompt del sistema configurado</p>
                <p className="text-sm">El prompt del sistema autónomo no está disponible</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'stages' && (
          <div>
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-gray-800">
                Etapas que el Autónomo debe Respetar
              </h3>
              <AddStageButton
                flowId={flow.flow_id}
                currentStagesCount={regularStages.length}
                onAdd={onAddStage}
                onClose={() => setShowAddStage(false)}
                show={showAddStage}
                onShow={() => setShowAddStage(true)}
              />
            </div>

            {loading && regularStages.length === 0 ? (
              <div className="text-center py-8 text-gray-500">Cargando etapas...</div>
            ) : regularStages.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <p className="mb-2">No hay etapas configuradas</p>
                <p className="text-sm">Agrega etapas para definir el flujo de conversación</p>
              </div>
            ) : (
              <div className="space-y-4">
                {regularStages.map((stage, index) => (
                  <StageCard
                    key={stage.stage_id}
                    stage={stage}
                    index={index}
                    totalStages={regularStages.length}
                    onUpdatePrompt={(promptText: string) => onUpdateStagePrompt(stage.stage_id, promptText)}
                    onUpdateRules={(rules: string) => onUpdateStageRules(stage.stage_id, rules)}
                    onDelete={() => onDeleteStage(stage.stage_id)}
                    onMoveUp={() => onMoveStage(stage.stage_id, 'up')}
                    onMoveDown={() => onMoveStage(stage.stage_id, 'down')}
                    loading={loading}
                  />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default FlowDetails;
