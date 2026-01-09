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
import FlowEditor from '../components/Flows/FlowEditor';
import WhatsAppConnection from '../components/Flows/WhatsAppConnection';
import FlowLinkGenerator from '../components/Flows/FlowLinkGenerator';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';


/**
 * Página para gestionar flujos de conversación
 * @returns Componente de gestión de flujos renderizado
 */
function Flows() {
  const [flows, setFlows] = useState<Flow[]>([]);
  const [selectedFlow, setSelectedFlow] = useState<Flow | null>(null);
  const [stages, setStages] = useState<FlowStage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCreateFlow, setShowCreateFlow] = useState(false);
  const [showAddModule, setShowAddModule] = useState(false);
  const [whatsAppConnected, setWhatsAppConnected] = useState(false);
  const [testingFlow, setTestingFlow] = useState(false);

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

  const loadStages = async (flowId: string): Promise<void> => {
    setLoading(true);
    setError(null);
    try {
      const response = await getFlowStages(flowId);
      setStages(response.stages);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al cargar etapas');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectFlow = async (flow: Flow): Promise<void> => {
    setSelectedFlow(flow);
    await loadStages(flow.flow_id);
  };

  const handleCreateFlow = async (e: React.FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const request: CreateFlowRequest = {
      name: formData.get('name') as string,
      description: formData.get('description') as string || undefined,
      domain: formData.get('domain') as string || 'bookings',
    };

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

  const handleAddModuleClick = (): void => {
    setShowAddModule(true);
  };

  const handleAddModule = async (moduleType: string): Promise<void> => {
    if (!selectedFlow) return;
    
    setShowAddModule(false);

    const nextOrder = stages.length > 0 ? Math.max(...stages.map((s) => s.stage_order)) + 1 : 1;

    let request: AddStageRequest;
    
    switch (moduleType) {
      case 'greeting':
        request = {
          flow_id: selectedFlow.flow_id,
          stage_order: nextOrder,
          stage_name: 'greeting',
          stage_type: 'greeting',
          prompt_text: 'Hola! Buenos días, ¿en qué puedo ayudarte?',
        };
        break;
      case 'input_date':
        request = {
          flow_id: selectedFlow.flow_id,
          stage_order: nextOrder,
          stage_name: 'get_date',
          stage_type: 'input',
          prompt_text: 'Por favor, ingresa una fecha para la cual quieras consultar reserva',
          field_name: 'date',
          field_type: 'date',
          is_required: true,
        };
        break;
      case 'input_time':
        request = {
          flow_id: selectedFlow.flow_id,
          stage_order: nextOrder,
          stage_name: 'get_time',
          stage_type: 'input',
          prompt_text: '¿A qué hora prefieres?',
          field_name: 'time',
          field_type: 'time',
          is_required: true,
        };
        break;
      case 'input_text':
        request = {
          flow_id: selectedFlow.flow_id,
          stage_order: nextOrder,
          stage_name: 'get_text',
          stage_type: 'input',
          prompt_text: 'Por favor, proporciona la siguiente información',
          field_name: 'text',
          field_type: 'text',
          is_required: true,
        };
        break;
      case 'input_name':
        request = {
          flow_id: selectedFlow.flow_id,
          stage_order: nextOrder,
          stage_name: 'get_name',
          stage_type: 'input',
          prompt_text: 'Por favor, dime tu nombre completo.\n\nNota: El sistema obtiene automáticamente tu nombre de WhatsApp. Solo te lo pedimos si no lo encontramos cuando accediste al chatbot.',
          field_name: 'customer_name',
          field_type: 'text',
          is_required: true,
        };
        break;
      case 'input_email':
        request = {
          flow_id: selectedFlow.flow_id,
          stage_order: nextOrder,
          stage_name: 'get_email',
          stage_type: 'input',
          prompt_text: 'Por favor, ingresa tu email',
          field_name: 'email',
          field_type: 'email',
          is_required: true,
        };
        break;
      case 'input_number':
        request = {
          flow_id: selectedFlow.flow_id,
          stage_order: nextOrder,
          stage_name: 'get_number',
          stage_type: 'input',
          prompt_text: 'Por favor, ingresa un número',
          field_name: 'number',
          field_type: 'number',
          is_required: true,
        };
        break;
      case 'confirmation':
        request = {
          flow_id: selectedFlow.flow_id,
          stage_order: nextOrder,
          stage_name: 'confirm',
          stage_type: 'confirmation',
          prompt_text: '¿Confirmas esta información?',
        };
        break;
      default:
        return;
    }

    setLoading(true);
    setError(null);
    try {
      await addStage(request);
      await loadStages(selectedFlow.flow_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al agregar módulo');
    } finally {
      setLoading(false);
    }
  };

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

  const handleMoveStage = async (stageId: string, direction: 'up' | 'down'): Promise<void> => {
    const stage = stages.find((s) => s.stage_id === stageId);
    if (!stage || !selectedFlow) return;

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

  const handleDeleteStage = async (stageId: string): Promise<void> => {
    if (!confirm('¿Estás seguro de eliminar esta etapa?')) return;

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

  const handleDeleteFlow = async (flowId: string, flowName: string): Promise<void> => {
    if (!confirm(`¿Estás seguro de eliminar el flujo "${flowName}"? Esta acción eliminará el flujo y todas sus etapas.`)) return;

    setLoading(true);
    setError(null);
    try {
      await deleteFlow(flowId);
      // Si el flujo eliminado era el seleccionado, limpiar la selección
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
   * Prueba el flujo seleccionado enviando un mensaje de prueba
   */
  const handleTestFlow = async (): Promise<void> => {
    if (!selectedFlow) {
      setError('Selecciona un flujo para probar');
      return;
    }

    if (!whatsAppConnected) {
      setError('WhatsApp no está conectado. Por favor, escanea el código QR primero.');
      return;
    }

    setTestingFlow(true);
    setError(null);

    try {
      // Enviar mensaje de prueba al backend
      const testNumber = '56959263366'; // Número de prueba
      const testMessage = 'Hola'; // Mensaje inicial para iniciar el flujo

      const response = await axios.post(
        `${API_BASE_URL}/v1/channels/whatsapp/inbound`,

        {
          from_number: testNumber,
          text: testMessage,
        },
        {
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (response.data.response_text) {
        alert(`Flujo iniciado correctamente!\n\nRespuesta del asistente:\n${response.data.response_text}\n\nAhora puedes enviar mensajes desde WhatsApp al número ${testNumber} para continuar probando el flujo.`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : `Error al probar el flujo. Verifica que el backend esté corriendo en ${API_BASE_URL}`);
    } finally {
      setTestingFlow(false);
    }
  };

  useEffect(() => {
    loadFlows();
  }, []);

  return (
    <div className="flex flex-col h-full">
      {/* Header fijo */}
      <div className="flex-shrink-0 flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold text-gray-800">Flujos de Conversación</h1>
        <div className="flex gap-2">
          {selectedFlow && (
            <button
              onClick={handleTestFlow}
              disabled={testingFlow || !whatsAppConnected}
              className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:bg-gray-300 transition-colors"
              title={!whatsAppConnected ? 'Conecta WhatsApp primero para probar el flujo' : 'Probar el flujo seleccionado'}
            >
              {testingFlow ? 'Probando...' : 'Probar Flujo'}
            </button>
          )}
          <button
            onClick={() => setShowCreateFlow(true)}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            Crear Flujo
          </button>
          <button
            onClick={loadFlows}
            disabled={loading}
            className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 disabled:bg-gray-300 transition-colors"
          >
            Actualizar
          </button>
        </div>
      </div>

      {/* Estado de WhatsApp */}
      <div className="flex-shrink-0 mb-4">
        <WhatsAppConnection onConnected={() => setWhatsAppConnected(true)} />
      </div>

      {error && (
        <div className="flex-shrink-0 p-4 bg-red-100 border border-red-300 text-red-800 rounded-lg mb-4">
          {error}
        </div>
      )}

      {/* Contenido principal con altura fija */}
      <div className="flex-1 min-h-0 grid grid-cols-4 gap-6">
        {/* Panel izquierdo - Flujos disponibles */}
        <div className="col-span-1 flex flex-col bg-white rounded-lg shadow">
          <div className="flex-shrink-0 p-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold">Flujos Disponibles</h2>
          </div>
          <div className="flex-1 overflow-y-auto p-4">
            {loading && flows.length === 0 ? (
              <div className="text-gray-500">Cargando...</div>
            ) : flows.length === 0 ? (
              <div className="text-gray-500">No hay flujos disponibles</div>
            ) : (
              <div className="space-y-2">
                {flows.map((flow) => (
                  <div
                    key={flow.flow_id}
                    className={`p-3 rounded-lg transition-colors ${
                      selectedFlow?.flow_id === flow.flow_id
                        ? 'bg-blue-100 border-2 border-blue-500'
                        : 'bg-gray-50 hover:bg-gray-100 border-2 border-transparent'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div
                        className="flex-1 cursor-pointer"
                        onClick={() => handleSelectFlow(flow)}
                      >
                        <div className="font-semibold text-sm">{flow.name}</div>
                        <div className="text-xs text-gray-600">{flow.description || 'Sin descripción'}</div>
                        <div className="text-xs text-gray-500 mt-1">
                          {flow.domain} | {flow.is_active ? 'Activo' : 'Inactivo'}
                        </div>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteFlow(flow.flow_id, flow.name);
                        }}
                        className="p-1 text-red-500 hover:text-red-700 hover:bg-red-50 rounded transition-colors"
                        title="Eliminar flujo"
                      >
                        X
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Panel derecho - Editor de flujo */}
        <div className="col-span-3 flex flex-col min-h-0 space-y-4">
          {selectedFlow ? (
            <>
              {/* Generador de links */}
              <div className="flex-shrink-0 space-y-4">
                {/* Link genérico para menú */}
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-semibold text-purple-900">Link Genérico - Menú de Flujos</h3>
                    <span className="text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded">
                      MENU
                    </span>
                  </div>
                  <div className="space-y-2">
                    <div>
                      <label className="text-sm font-medium text-gray-700">Código de activación:</label>
                      <code className="block mt-1 bg-white px-3 py-2 rounded border text-sm font-mono">
                        MENU_INIT
                      </code>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-700">Link de WhatsApp:</label>
                      <div className="flex gap-2 mt-1">
                        <input
                          type="text"
                          value={`https://wa.me/56959263366?text=${encodeURIComponent('MENU_INIT')}`}
                          readOnly
                          className="flex-1 px-3 py-2 border rounded text-sm bg-white"
                        />
                        <button
                          onClick={async () => {
                            const link = `https://wa.me/56959263366?text=${encodeURIComponent('MENU_INIT')}`;
                            await navigator.clipboard.writeText(link);
                            alert('Link copiado al portapapeles');
                          }}
                          className="px-4 py-2 bg-purple-500 text-white rounded font-medium hover:bg-purple-600 transition-colors"
                        >
                          Copiar
                        </button>
                      </div>
                    </div>
                    <div className="text-xs text-gray-600 bg-white p-3 rounded border">
                      <p className="font-medium mb-1">Este link muestra el menú de todos los flujos disponibles</p>
                      <p>El usuario puede seleccionar un flujo escribiendo el número correspondiente</p>
                    </div>
                  </div>
                </div>
                
                {/* Link específico del flujo */}
                <FlowLinkGenerator 
                  flow={selectedFlow} 
                  whatsappNumber="56959263366"
                />
              </div>
              
              {/* Editor de flujo */}
              <div className="flex-1 min-h-0">
                <FlowEditor
                  flowName={selectedFlow.name}
                  stages={stages}
                  loading={loading}
                  onUpdateStage={handleUpdateStagePrompt}
                  onDeleteStage={handleDeleteStage}
                  onMoveStage={handleMoveStage}
                  onAddModule={handleAddModuleClick}
                  onAddModuleConfirm={handleAddModule}
                  showAddModule={showAddModule}
                  onCloseAddModule={() => setShowAddModule(false)}
                />
              </div>
            </>
          ) : (
            <div className="flex-1 bg-white rounded-lg shadow flex items-center justify-center">
              <div className="text-center text-gray-500">
                <div className="text-lg mb-2">Selecciona un flujo para comenzar</div>
                <div className="text-sm">Elige un flujo de la lista para visualizar y editar su estructura</div>
              </div>
            </div>
          )}
        </div>
      </div>

      {showCreateFlow && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96">
            <h2 className="text-xl font-semibold mb-4">Crear Nuevo Flujo</h2>
            <form onSubmit={handleCreateFlow}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Nombre</label>
                  <input
                    type="text"
                    name="name"
                    required
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Descripción</label>
                  <textarea
                    name="description"
                    className="w-full px-3 py-2 border rounded-lg"
                    rows={3}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Dominio</label>
                  <select name="domain" className="w-full px-3 py-2 border rounded-lg" defaultValue="bookings">
                    <option value="bookings">Reservas</option>
                    <option value="purchases">Compras</option>
                    <option value="claims">Reclamos</option>
                  </select>
                </div>
              </div>
              <div className="flex gap-2 mt-6">
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 transition-colors"
                >
                  Crear
                </button>
                <button
                  type="button"
                  onClick={() => setShowCreateFlow(false)}
                  className="flex-1 px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
                >
                  Cancelar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
}

export default Flows;
