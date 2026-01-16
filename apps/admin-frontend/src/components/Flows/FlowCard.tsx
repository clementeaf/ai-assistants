import { useState, useEffect } from 'react';
import type { Flow } from '../../lib/api/flows';
import { getDomainMetadata, type DomainMetadata } from '../../lib/api/automata';

interface FlowCardProps {
  flow: Flow;
  onSelect: (flow: Flow) => void;
  onDelete: (flowId: string, flowName: string) => void;
}

/**
 * Tarjeta que representa un flujo creado
 * Obtiene información del autómata dinámicamente desde el backend
 * @param flow - Flujo a mostrar
 * @param onSelect - Callback al seleccionar el flujo
 * @param onDelete - Callback al eliminar el flujo
 * @returns Componente FlowCard renderizado
 */
function FlowCard({ flow, onSelect, onDelete }: FlowCardProps) {
  const [domainMetadata, setDomainMetadata] = useState<DomainMetadata | null>(null);

  useEffect(() => {
    const loadMetadata = async (): Promise<void> => {
      try {
        const metadata = await getDomainMetadata(flow.domain);
        setDomainMetadata(metadata);
      } catch (error) {
        console.error('Error loading domain metadata:', error);
        // Usar valores por defecto si falla
        setDomainMetadata({
          domain: flow.domain,
          display_name: flow.name,
          description: flow.description || 'Flujo de conversación configurable',
          activation_code: `FLOW_${flow.domain.toUpperCase()}_INIT`,
          is_enabled: true,
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
    <div
      className="bg-white rounded-lg shadow-md border-2 border-gray-200 hover:border-blue-400 hover:shadow-lg transition-all cursor-pointer p-4"
      onClick={() => onSelect(flow)}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1">
          <h3 className="text-lg font-bold text-gray-800 mb-1">{getFlowDisplayName()}</h3>
          <p className="text-xs text-gray-600 mb-2 line-clamp-2">{getFlowDescription()}</p>
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] px-1.5 py-0.5 bg-blue-100 text-blue-800 rounded font-medium">
              {flow.domain}
            </span>
            <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${
              flow.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
            }`}>
              {flow.is_active ? 'Activo' : 'Inactivo'}
            </span>
          </div>
        </div>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete(flow.flow_id, getFlowDisplayName());
          }}
          className="p-1.5 text-red-500 hover:text-red-700 hover:bg-red-50 rounded transition-colors flex-shrink-0 text-lg leading-none"
          title="Eliminar flujo"
        >
          ×
        </button>
      </div>
      <div className="text-[10px] text-gray-400">
        ID: {flow.flow_id}
      </div>
    </div>
  );
}

export default FlowCard;
