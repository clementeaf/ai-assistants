import { useState, FormEvent } from 'react';
import type { CreateFlowRequest } from '../../lib/api/flows';

interface CreateFlowModalProps {
  onClose: () => void;
  onCreate: (request: CreateFlowRequest) => Promise<void>;
  loading: boolean;
}

/**
 * Modal para crear un nuevo flujo
 * @param onClose - Callback para cerrar el modal
 * @param onCreate - Callback para crear el flujo
 * @param loading - Estado de carga
 * @returns Componente CreateFlowModal renderizado
 */
function CreateFlowModal({ onClose, onCreate, loading }: CreateFlowModalProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [domain, setDomain] = useState<'bookings' | 'purchases' | 'claims'>('bookings');

  const handleSubmit = async (e: FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    await onCreate({
      name,
      description: description || undefined,
      domain,
    });
    setName('');
    setDescription('');
    setDomain('bookings');
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-96">
        <h2 className="text-xl font-semibold mb-4">Crear Nuevo Flujo</h2>
        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Nombre</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Ej: Flujo de Reservas"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Descripción</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={3}
                placeholder="Descripción del flujo (opcional)"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Dominio</label>
              <select
                value={domain}
                onChange={(e) => setDomain(e.target.value as 'bookings' | 'purchases' | 'claims')}
                className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
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
              {loading ? 'Creando...' : 'Crear'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
            >
              Cancelar
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default CreateFlowModal;
