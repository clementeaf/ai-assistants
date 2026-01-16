import { useState, useEffect } from 'react';
import {
  createFlow,
  listFlows,
  getFlowStages,
  addStage,
  updateStage,
  deleteStage,
  deleteFlow,
  type Flow,
  type FlowStage,
  type CreateFlowRequest,
  type AddStageRequest,
  type UpdateStageRequest,
} from '../lib/api/flows';
import FlowCard from '../components/Flows/FlowCard';
import FlowDetails from '../components/Flows/FlowDetails';
import CreateFlowModal from '../components/Flows/CreateFlowModal';

/**
 * Página para gestionar flujos de conversación
 * Maneja el estado y la lógica de negocio, delega la UI a componentes especializados
 * @returns Componente de gestión de flujos renderizado
 */
function Flows() {
  const [flows, setFlows] = useState<Flow[]>([]);
  const [selectedFlow, setSelectedFlow] = useState<Flow | null>(null);
  const [stages, setStages] = useState<FlowStage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCreateFlow, setShowCreateFlow] = useState(false);

  /**
   * Carga todos los flujos disponibles
   */
  const loadFlows = async (): Promise<void> => {
    setLoading(true);
    setError(null);
    try {
      const response = await listFlows();
      setFlows(response.flows);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al cargar flujos');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Carga las etapas de un flujo específico
   * @param flowId - ID del flujo
   */
  const loadStages = async (flowId: string): Promise<void> => {
    setLoading(true);
    setError(null);
    try {
      const response = await getFlowStages(flowId);
      setStages(response.stages);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error al cargar etapas';
      if (errorMessage.includes('ECONNREFUSED') || errorMessage.includes('Network Error') || errorMessage.includes('No se pudo conectar')) {
        setError('No se pudo conectar al servidor MCP de flujos. Asegúrate de que el servidor esté corriendo en el puerto 60006.');
      } else {
        setError(errorMessage);
      }
    } finally {
      setLoading(false);
    }
  };

  /**
   * Maneja la selección de un flujo
   * @param flow - Flujo seleccionado
   */
  const handleSelectFlow = async (flow: Flow): Promise<void> => {
    setSelectedFlow(flow);
    await loadStages(flow.flow_id);
  };

  /**
   * Maneja la creación de un nuevo flujo
   * @param request - Datos del flujo a crear
   */
  const handleCreateFlow = async (request: CreateFlowRequest): Promise<void> => {
    setLoading(true);
    setError(null);
    try {
      await createFlow(request);
      setShowCreateFlow(false);
      await loadFlows();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al crear flujo');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Maneja la eliminación de un flujo
   * @param flowId - ID del flujo a eliminar
   * @param flowName - Nombre del flujo (para confirmación)
   */
  const handleDeleteFlow = async (flowId: string, flowName: string): Promise<void> => {
    if (!confirm(`¿Estás seguro de eliminar el flujo "${flowName}"? Esta acción eliminará el flujo y todas sus etapas.`)) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      await deleteFlow(flowId);
      if (selectedFlow?.flow_id === flowId) {
        setSelectedFlow(null);
        setStages([]);
      }
      await loadFlows();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al eliminar flujo');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Maneja la actualización del prompt de una etapa
   * @param stageId - ID de la etapa
   * @param promptText - Nuevo texto del prompt
   */
  const handleUpdateStagePrompt = async (stageId: string, promptText: string): Promise<void> => {
    setLoading(true);
    setError(null);
    try {
      await updateStage({
        stage_id: stageId,
        prompt_text: promptText,
      });
      if (selectedFlow) {
        await loadStages(selectedFlow.flow_id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al actualizar prompt');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Maneja la actualización de reglas de validación de una etapa
   * @param stageId - ID de la etapa
   * @param validationRules - Nuevas reglas de validación
   */
  const handleUpdateStageRules = async (stageId: string, validationRules: string): Promise<void> => {
    setLoading(true);
    setError(null);
    try {
      await updateStage({
        stage_id: stageId,
        validation_rules: validationRules,
      });
      if (selectedFlow) {
        await loadStages(selectedFlow.flow_id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al actualizar reglas');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Maneja la eliminación de una etapa
   * @param stageId - ID de la etapa a eliminar
   */
  const handleDeleteStage = async (stageId: string): Promise<void> => {
    if (!confirm('¿Estás seguro de eliminar esta etapa?')) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      await deleteStage(stageId);
      if (selectedFlow) {
        await loadStages(selectedFlow.flow_id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al eliminar etapa');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Maneja el movimiento de una etapa (arriba/abajo)
   * @param stageId - ID de la etapa
   * @param direction - Dirección del movimiento
   */
  const handleMoveStage = async (stageId: string, direction: 'up' | 'down'): Promise<void> => {
    const stage = stages.find((s) => s.stage_id === stageId);
    if (!stage || !selectedFlow) {
      return;
    }

    const sortedStages = [...stages].sort((a, b) => a.stage_order - b.stage_order);
    const currentIndex = sortedStages.findIndex((s) => s.stage_id === stageId);

    if (direction === 'up' && currentIndex > 0) {
      const prevStage = sortedStages[currentIndex - 1];
      const newOrder = prevStage.stage_order;
      const prevNewOrder = stage.stage_order;

      setLoading(true);
      setError(null);
      try {
        await updateStage({ stage_id: stageId, stage_order: newOrder });
        await updateStage({ stage_id: prevStage.stage_id, stage_order: prevNewOrder });
        await loadStages(selectedFlow.flow_id);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Error al reordenar etapa');
      } finally {
        setLoading(false);
      }
    } else if (direction === 'down' && currentIndex < sortedStages.length - 1) {
      const nextStage = sortedStages[currentIndex + 1];
      const newOrder = nextStage.stage_order;
      const nextNewOrder = stage.stage_order;

      setLoading(true);
      setError(null);
      try {
        await updateStage({ stage_id: stageId, stage_order: newOrder });
        await updateStage({ stage_id: nextStage.stage_id, stage_order: nextNewOrder });
        await loadStages(selectedFlow.flow_id);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Error al reordenar etapa');
      } finally {
        setLoading(false);
      }
    }
  };

  /**
   * Maneja la adición de una nueva etapa
   * @param request - Datos de la etapa a agregar
   */
  const handleAddStage = async (request: AddStageRequest): Promise<void> => {
    if (!selectedFlow) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      await addStage(request);
      await loadStages(selectedFlow.flow_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al agregar etapa');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFlows();

    const handleCreateFlow = (): void => {
      setShowCreateFlow(true);
    };

    window.addEventListener('createFlow', handleCreateFlow);
    return () => {
      window.removeEventListener('createFlow', handleCreateFlow);
    };
  }, []);

  return (
    <div className="flex flex-col h-full gap-4">

      {/* Mensaje de error */}
      {error && (
        <div className="p-4 bg-red-100 border border-red-300 text-red-800 rounded-lg">
          {error}
        </div>
      )}

      {/* Contenido principal */}
      <div className="flex-1 min-h-0 overflow-hidden">
        {selectedFlow ? (
          <FlowDetails
            flow={selectedFlow}
            stages={stages}
            loading={loading}
            onUpdateStagePrompt={handleUpdateStagePrompt}
            onUpdateStageRules={handleUpdateStageRules}
            onDeleteStage={handleDeleteStage}
            onMoveStage={handleMoveStage}
            onAddStage={handleAddStage}
            onBack={() => setSelectedFlow(null)}
          />
        ) : (
          <div className="h-full overflow-y-auto">
            {loading && flows.length === 0 ? (
              <div className="text-center py-12 text-gray-500">Cargando flujos...</div>
            ) : flows.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-lg text-gray-500 mb-2">No hay flujos creados</div>
                <div className="text-sm text-gray-400">Crea tu primer flujo para comenzar</div>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {flows.map((flow) => (
                  <FlowCard
                    key={flow.flow_id}
                    flow={flow}
                    onSelect={handleSelectFlow}
                    onDelete={handleDeleteFlow}
                  />
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Modal de crear flujo */}
      {showCreateFlow && (
        <CreateFlowModal
          onClose={() => setShowCreateFlow(false)}
          onCreate={handleCreateFlow}
          loading={loading}
        />
      )}
    </div>
  );
}

export default Flows;
