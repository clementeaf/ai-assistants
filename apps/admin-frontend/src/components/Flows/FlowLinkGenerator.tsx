import { useState } from 'react';
import { type Flow } from '../../lib/api/flows';

interface FlowLinkGeneratorProps {
  flow: Flow;
  whatsappNumber: string;
}

/**
 * Componente para generar links de WhatsApp que activan flujos automáticamente
 */
export default function FlowLinkGenerator({ flow, whatsappNumber }: FlowLinkGeneratorProps) {
  const [copied, setCopied] = useState(false);

  // Generar código de activación basado en el dominio del flujo
  const getActivationCode = (): string => {
    const domainMap: Record<string, string> = {
      'bookings': 'RESERVA',
      'purchases': 'COMPRA',
      'claims': 'RECLAMO',
    };
    const domainKey = domainMap[flow.domain] || 'RESERVA';
    return `FLOW_${domainKey}_INIT`;
  };

  const activationCode = getActivationCode();
  const whatsappLink = `https://wa.me/${whatsappNumber}?text=${encodeURIComponent(activationCode)}`;

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(whatsappLink);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Error al copiar:', err);
    }
  };

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-semibold text-blue-900 text-sm">Link de Activación</h3>
        <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
          {flow.domain}
        </span>
      </div>

      <div className="space-y-2">
        <div>
          <label className="text-xs font-medium text-gray-700">Código de activación:</label>
          <code className="block mt-1 bg-white px-2 py-1 rounded border text-xs font-mono">
            {activationCode}
          </code>
        </div>

        <div>
          <label className="text-xs font-medium text-gray-700">Link de WhatsApp:</label>
          <div className="flex gap-2 mt-1">
            <input
              type="text"
              value={whatsappLink}
              readOnly
              className="flex-1 px-2 py-1 border rounded text-xs bg-white"
            />
            <button
              onClick={copyToClipboard}
              className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                copied
                  ? 'bg-green-500 text-white'
                  : 'bg-blue-500 text-white hover:bg-blue-600'
              }`}
            >
              {copied ? '✓' : 'Copiar'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
