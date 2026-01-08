import { useState, useEffect } from 'react';
import {
  createFlow,
  listFlows,
  getFlowStages,
  addStage,
  updateStage,
  deleteStage,
  type Flow,
  type FlowStage,
  type CreateFlowRequest,
  type AddStageRequest,
  type UpdateStageRequest,
} from '../lib/api/flows';
import FlowEditor from '../components/Flows/FlowEditor';
import PromptEditor from '../components/Flows/PromptEditor';

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
  const [showAddStage, setShowAddStage] = useState(false);
  const [editingStage, setEditingStage] = useState<FlowStage | null>(null);
  const [selectedStage, setSelectedStage] = useState<FlowStage | null>(null);
  const [systemPrompt, setSystemPrompt] = useState('');

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
    setSelectedStage(null);
    setSystemPrompt('');
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

  const handleAddStage = async (e: React.FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    if (!selectedFlow) return;

    const formData = new FormData(e.currentTarget);
    const request: AddStageRequest = {
      flow_id: selectedFlow.flow_id,
      stage_order: parseInt(formData.get('stage_order') as string, 10),
      stage_name: formData.get('stage_name') as string,
      stage_type: formData.get('stage_type') as string,
      prompt_text: formData.get('prompt_text') as string || undefined,
      field_name: formData.get('field_name') as string || undefined,
      field_type: formData.get('field_type') as string || undefined,
      validation_rules: formData.get('validation_rules') as string || undefined,
      is_required: formData.get('is_required') === 'true',
    };

    setLoading(true);
    setError(null);
    try {
      await addStage(request);
      setShowAddStage(false);
      await loadStages(selectedFlow.flow_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al agregar etapa');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateStage = async (e: React.FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    if (!editingStage) return;

    const formData = new FormData(e.currentTarget);
    const request: UpdateStageRequest = {
      stage_id: editingStage.stage_id,
      stage_order: formData.get('stage_order') ? parseInt(formData.get('stage_order') as string, 10) : undefined,
      stage_name: formData.get('stage_name') as string || undefined,
      prompt_text: formData.get('prompt_text') as string || undefined,
      field_name: formData.get('field_name') as string || undefined,
      field_type: formData.get('field_type') as string || undefined,
      validation_rules: formData.get('validation_rules') as string || undefined,
      is_required: formData.get('is_required') ? formData.get('is_required') === 'true' : undefined,
    };

    setLoading(true);
    setError(null);
    try {
      await updateStage(request);
      setEditingStage(null);
      if (selectedFlow) {
        await loadStages(selectedFlow.flow_id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al actualizar etapa');
    } finally {
      setLoading(false);
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

  useEffect(() => {
    loadFlows();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-800">Flujos de Conversación</h1>
        <div className="flex gap-2">
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

      {error && (
        <div className="p-4 bg-red-100 border border-red-300 text-red-800 rounded-lg">
          {error}
        </div>
      )}

      <div className="grid grid-cols-4 gap-6">
        <div className="col-span-1 bg-white rounded-lg shadow p-4">
          <h2 className="text-lg font-semibold mb-4">Flujos Disponibles</h2>
          {loading && flows.length === 0 ? (
            <div className="text-gray-500">Cargando...</div>
          ) : flows.length === 0 ? (
            <div className="text-gray-500">No hay flujos disponibles</div>
          ) : (
            <div className="space-y-2">
              {flows.map((flow) => (
                <div
                  key={flow.flow_id}
                  onClick={() => handleSelectFlow(flow)}
                  className={`p-3 rounded-lg cursor-pointer transition-colors ${
                    selectedFlow?.flow_id === flow.flow_id
                      ? 'bg-blue-100 border-2 border-blue-500'
                      : 'bg-gray-50 hover:bg-gray-100 border-2 border-transparent'
                  }`}
                >
                  <div className="font-semibold text-sm">{flow.name}</div>
                  <div className="text-xs text-gray-600">{flow.description || 'Sin descripción'}</div>
                  <div className="text-xs text-gray-500 mt-1">
                    {flow.domain} | {flow.is_active ? 'Activo' : 'Inactivo'}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="col-span-3 space-y-6">
          {selectedFlow ? (
            <>
              <div className="bg-white rounded-lg shadow p-4">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-lg font-semibold">Editor de Flujo: {selectedFlow.name}</h2>
                  <button
                    onClick={() => setShowAddStage(true)}
                    className="px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600 text-sm transition-colors"
                  >
                    Agregar Etapa
                  </button>
                </div>
                <div className="min-h-96 border-2 border-gray-300 rounded-lg overflow-hidden">
                  <FlowEditor
                    stages={stages}
                    onStageSelect={(stage) => {
                      setSelectedStage(stage);
                    }}
                  />
                </div>
              </div>

              <div className="bg-white rounded-lg shadow">
                <div className="h-96">
                  <PromptEditor
                    flow={selectedFlow}
                    stages={stages}
                    initialPrompt={systemPrompt}
                    onPromptChange={(prompt) => setSystemPrompt(prompt)}
                  />
                </div>
              </div>

              {selectedStage && (
                <div className="bg-white rounded-lg shadow p-4">
                  <h3 className="text-lg font-semibold mb-2">Etapa Seleccionada</h3>
                  <div className="space-y-2">
                    <div>
                      <span className="font-semibold">Nombre:</span> {selectedStage.stage_name}
                    </div>
                    <div>
                      <span className="font-semibold">Tipo:</span> {selectedStage.stage_type}
                    </div>
                    <div>
                      <span className="font-semibold">Orden:</span> {selectedStage.stage_order}
                    </div>
                    {selectedStage.prompt_text && (
                      <div>
                        <span className="font-semibold">Prompt:</span> {selectedStage.prompt_text}
                      </div>
                    )}
                    {selectedStage.field_name && (
                      <div>
                        <span className="font-semibold">Campo:</span> {selectedStage.field_name} (
                        {selectedStage.field_type})
                        {selectedStage.is_required && <span className="text-red-500"> *</span>}
                      </div>
                    )}
                    <div className="flex gap-2 mt-4">
                      <button
                        onClick={() => setEditingStage(selectedStage)}
                        className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm transition-colors"
                      >
                        Editar
                      </button>
                      <button
                        onClick={() => handleDeleteStage(selectedStage.stage_id)}
                        className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600 text-sm transition-colors"
                      >
                        Eliminar
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
              <div className="text-lg mb-2">Selecciona un flujo para comenzar</div>
              <div className="text-sm">Elige un flujo de la lista para visualizar y editar su estructura</div>
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

      {showAddStage && selectedFlow && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-semibold mb-4">Agregar Etapa</h2>
            <form onSubmit={handleAddStage}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Orden</label>
                  <input
                    type="number"
                    name="stage_order"
                    required
                    min="1"
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Nombre</label>
                  <input
                    type="text"
                    name="stage_name"
                    required
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Tipo</label>
                  <select name="stage_type" className="w-full px-3 py-2 border rounded-lg" required>
                    <option value="greeting">Saludo</option>
                    <option value="input">Entrada</option>
                    <option value="confirmation">Confirmación</option>
                    <option value="action">Acción</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Texto del Prompt</label>
                  <textarea
                    name="prompt_text"
                    className="w-full px-3 py-2 border rounded-lg"
                    rows={3}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Nombre del Campo</label>
                  <input
                    type="text"
                    name="field_name"
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Tipo de Campo</label>
                  <select name="field_type" className="w-full px-3 py-2 border rounded-lg">
                    <option value="">Seleccionar...</option>
                    <option value="text">Texto</option>
                    <option value="date">Fecha</option>
                    <option value="time">Hora</option>
                    <option value="email">Email</option>
                    <option value="number">Número</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Reglas de Validación (JSON)</label>
                  <textarea
                    name="validation_rules"
                    className="w-full px-3 py-2 border rounded-lg"
                    rows={2}
                  />
                </div>
                <div>
                  <label className="flex items-center gap-2">
                    <input type="checkbox" name="is_required" value="true" />
                    <span className="text-sm">Campo requerido</span>
                  </label>
                </div>
              </div>
              <div className="flex gap-2 mt-6">
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:bg-gray-300 transition-colors"
                >
                  Agregar
                </button>
                <button
                  type="button"
                  onClick={() => setShowAddStage(false)}
                  className="flex-1 px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
                >
                  Cancelar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {editingStage && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-semibold mb-4">Editar Etapa</h2>
            <form onSubmit={handleUpdateStage}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Orden</label>
                  <input
                    type="number"
                    name="stage_order"
                    defaultValue={editingStage.stage_order}
                    min="1"
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Nombre</label>
                  <input
                    type="text"
                    name="stage_name"
                    defaultValue={editingStage.stage_name}
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Texto del Prompt</label>
                  <textarea
                    name="prompt_text"
                    defaultValue={editingStage.prompt_text || ''}
                    className="w-full px-3 py-2 border rounded-lg"
                    rows={3}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Nombre del Campo</label>
                  <input
                    type="text"
                    name="field_name"
                    defaultValue={editingStage.field_name || ''}
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Tipo de Campo</label>
                  <select
                    name="field_type"
                    defaultValue={editingStage.field_type || ''}
                    className="w-full px-3 py-2 border rounded-lg"
                  >
                    <option value="">Seleccionar...</option>
                    <option value="text">Texto</option>
                    <option value="date">Fecha</option>
                    <option value="time">Hora</option>
                    <option value="email">Email</option>
                    <option value="number">Número</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Reglas de Validación (JSON)</label>
                  <textarea
                    name="validation_rules"
                    defaultValue={editingStage.validation_rules || ''}
                    className="w-full px-3 py-2 border rounded-lg"
                    rows={2}
                  />
                </div>
                <div>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      name="is_required"
                      value="true"
                      defaultChecked={editingStage.is_required}
                    />
                    <span className="text-sm">Campo requerido</span>
                  </label>
                </div>
              </div>
              <div className="flex gap-2 mt-6">
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 transition-colors"
                >
                  Guardar
                </button>
                <button
                  type="button"
                  onClick={() => setEditingStage(null)}
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
