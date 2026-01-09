import { useState, useEffect } from 'react';
import axios from 'axios';

const WHATSAPP_SERVICE_URL = import.meta.env.VITE_WHATSAPP_SERVICE_URL || 'http://localhost:60007';


interface WhatsAppConnectionProps {
  onConnected?: () => void;
}

/**
 * Componente para mostrar el estado de WhatsApp y el QR si es necesario
 * @param onConnected - Callback cuando WhatsApp se conecta
 * @returns Componente WhatsAppConnection renderizado
 */
function WhatsAppConnection({ onConnected }: WhatsAppConnectionProps) {
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [qrUrl, setQrUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const checkWhatsAppStatus = async (): Promise<void> => {
    try {
      const response = await axios.get(`${WHATSAPP_SERVICE_URL}/status`, {

        headers: {
          'Accept': 'application/json',
        },
      });

      const { connected, qr } = response.data;

      if (connected) {
        const wasConnected = isConnected;
        setIsConnected(true);
        setQrUrl(null);
        setError(null);
        if (onConnected && (!wasConnected || wasConnected === undefined)) {
          onConnected();
        }
      } else if (qr) {
        setQrUrl(qr);
        setIsConnected(false);
        setError(null);
      } else {
        setIsConnected(false);
        setQrUrl(null);
        setError(null);
      }
    } catch (err) {
      setError(`No se pudo conectar al servicio de WhatsApp. Verifica que esté corriendo en ${WHATSAPP_SERVICE_URL}`);

      setIsConnected(false);
      setQrUrl(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkWhatsAppStatus();
    const interval = setInterval(checkWhatsAppStatus, 2000); // Verificar cada 2 segundos
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (isConnected && onConnected) {
      onConnected();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isConnected]);

  if (loading) {
    return (
      <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <div className="text-sm text-blue-700">Verificando conexión de WhatsApp...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
        <div className="text-sm text-red-700">{error}</div>
        <button
          onClick={checkWhatsAppStatus}
          className="mt-2 px-3 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200"
        >
          Reintentar
        </button>
      </div>
    );
  }

  if (isConnected) {
    return (
      <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
        <div className="text-sm text-green-700 font-medium">WhatsApp conectado y listo</div>
      </div>
    );
  }

  if (qrUrl) {
    return (
      <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
        <div className="text-sm text-yellow-800 font-medium mb-2">Escanea el código QR para conectar WhatsApp</div>
        <div className="flex justify-center mb-2">
          <img src={qrUrl} alt="QR Code" className="max-w-xs border-2 border-gray-300 rounded" />
        </div>
        <div className="text-xs text-yellow-700">
          <ol className="list-decimal list-inside space-y-1">
            <li>Abre WhatsApp en tu teléfono</li>
            <li>Ve a Configuración → Dispositivos vinculados</li>
            <li>Presiona "Vincular un dispositivo"</li>
            <li>Escanea este código QR</li>
          </ol>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
      <div className="text-sm text-gray-700">Esperando código QR...</div>
    </div>
  );
}

export default WhatsAppConnection;
