import { useState, useEffect } from 'react';
import { type Flow } from '../../lib/api/flows';
import { getDomainMetadata } from '../../lib/api/automata';

interface FlowLinkGeneratorProps {
  flow: Flow;
  whatsappNumber?: string;
}

/**
 * Componente para generar links de WhatsApp que activan flujos automáticamente
 * Obtiene el código de activación dinámicamente desde el backend
 */
export default function FlowLinkGenerator({ flow, whatsappNumber }: FlowLinkGeneratorProps) {
  const [copied, setCopied] = useState(false);
  const [activationCode, setActivationCode] = useState<string>('');

  // Obtener número de WhatsApp desde variable de entorno o prop
  const whatsappNum = whatsappNumber || import.meta.env.VITE_WHATSAPP_NUMBER || '';

  useEffect(() => {
    const loadActivationCode = async (): Promise<void> => {
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
  }, [flow.domain]);

  const whatsappLink = activationCode && whatsappNum ? `https://wa.me/${whatsappNum}?text=${encodeURIComponent(activationCode)}` : '';

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
