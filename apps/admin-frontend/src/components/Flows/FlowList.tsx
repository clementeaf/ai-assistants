import type { Flow } from '../../lib/api/flows';

interface FlowListProps {
  flows: Flow[];
  selectedFlow: Flow | null;
  loading: boolean;
  onSelectFlow: (flow: Flow) => void;
  onDeleteFlow: (flowId: string, flowName: string) => void;
}

/**
 * Componente para mostrar la lista de flujos disponibles
 * @param flows - Lista de flujos
 * @param selectedFlow - Flujo actualmente seleccionado
 * @param loading - Estado de carga
 * @param onSelectFlow - Callback al seleccionar un flujo
 * @param onDeleteFlow - Callback al eliminar un flujo
 * @returns Componente FlowList renderizado
 */
function FlowList({ flows, selectedFlow, loading, onSelectFlow, onDeleteFlow }: FlowListProps) {
  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow">
      <div className="flex-shrink-0 p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold">Flujos Disponibles</h2>
      </div>
      <div className="flex-1 overflow-y-auto p-4">
        {loading && flows.length === 0 ? (
          <div className="text-gray-500 text-center py-8">Cargando...</div>
        ) : flows.length === 0 ? (
          <div className="text-gray-500 text-center py-8">No hay flujos disponibles</div>
        ) : (
          <div className="space-y-2">
            {flows.map((flow) => (
              <div
                key={flow.flow_id}
                className={`p-3 rounded-lg transition-colors cursor-pointer ${
                  selectedFlow?.flow_id === flow.flow_id
                    ? 'bg-blue-100 border-2 border-blue-500'
                    : 'bg-gray-50 hover:bg-gray-100 border-2 border-transparent'
                }`}
                onClick={() => onSelectFlow(flow)}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="font-semibold text-sm truncate">{flow.name}</div>
                    <div className="text-xs text-gray-600 truncate">{flow.description || 'Sin descripción'}</div>
                    <div className="text-xs text-gray-500 mt-1">
                      {flow.domain} | {flow.is_active ? 'Activo' : 'Inactivo'}
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteFlow(flow.flow_id, flow.name);
                    }}
                    className="p-1 text-red-500 hover:text-red-700 hover:bg-red-50 rounded transition-colors flex-shrink-0"
                    title="Eliminar flujo"
                  >
                    ×
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default FlowList;
