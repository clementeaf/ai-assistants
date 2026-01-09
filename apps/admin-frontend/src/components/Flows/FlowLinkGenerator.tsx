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
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-blue-900">Link de Activación</h3>
        <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
          {flow.domain}
        </span>
      </div>

      <div className="space-y-2">
        <div>
          <label className="text-sm font-medium text-gray-700">Código de activación:</label>
          <code className="block mt-1 bg-white px-3 py-2 rounded border text-sm font-mono">
            {activationCode}
          </code>
        </div>

        <div>
          <label className="text-sm font-medium text-gray-700">Link de WhatsApp:</label>
          <div className="flex gap-2 mt-1">
            <input
              type="text"
              value={whatsappLink}
              readOnly
              className="flex-1 px-3 py-2 border rounded text-sm bg-white"
            />
            <button
              onClick={copyToClipboard}
              className={`px-4 py-2 rounded font-medium transition-colors ${
                copied
                  ? 'bg-green-500 text-white'
                  : 'bg-blue-500 text-white hover:bg-blue-600'
              }`}
            >
              {copied ? '✓ Copiado' : 'Copiar'}
            </button>
          </div>
        </div>
      </div>

      <div className="text-xs text-gray-600 bg-white p-3 rounded border">
        <p className="font-medium mb-1">¿Cómo funciona?</p>
        <ul className="list-disc list-inside space-y-1">
          <li>El usuario hace clic en el link</li>
          <li>WhatsApp se abre con el código pre-escrito</li>
          <li>Al enviar, el sistema activa automáticamente este flujo</li>
          <li>El usuario recibe el saludo inicial del flujo</li>
        </ul>
        <p className="font-medium mt-2 mb-1">Palabras reservadas:</p>
        <ul className="list-disc list-inside space-y-1">
          <li><code className="bg-gray-100 px-1 rounded">menu</code> o <code className="bg-gray-100 px-1 rounded">menú</code> - Muestra el menú de flujos</li>
          <li><code className="bg-gray-100 px-1 rounded">MENU_INIT</code> - Activa el menú desde un link</li>
        </ul>
      </div>
    </div>
  );
}
