import { useState, useEffect } from 'react';
import {
  connectCustomerCalendar,
  getCustomerCalendarStatus,
  listCustomerCalendars,
  disconnectCustomerCalendar,
  type CustomerCalendar,
  type ConnectCustomerCalendarRequest,
} from '../lib/api/customers';
import { UserPlus, Calendar, CheckCircle2, XCircle, ExternalLink, Trash2 } from 'lucide-react';

/**
 * Página para gestionar clientes y sus conexiones de Google Calendar
 * @returns Componente de gestión de clientes renderizado
 */
function Customers() {
  const [customers, setCustomers] = useState<CustomerCalendar[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showAddCustomer, setShowAddCustomer] = useState(false);
  const [newCustomer, setNewCustomer] = useState<ConnectCustomerCalendarRequest>({
    customer_id: '',
    customer_email: '',
    customer_name: '',
  });
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authUrl, setAuthUrl] = useState<string | null>(null);
  const [checkingAuthStatus, setCheckingAuthStatus] = useState<string | null>(null); // customer_id que está siendo verificado

  const loadCustomers = async (): Promise<void> => {
    setLoading(true);
    setError(null);
    try {
      const response = await listCustomerCalendars();
      setCustomers(response.customers);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al cargar clientes');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCustomers();
  }, []);

  // Escuchar mensajes de la ventana de OAuth callback
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      // Verificar origen por seguridad
      if (event.origin !== window.location.origin) return;

      console.log('[Customers] Received message:', event.data);
      
      if (event.data.type === 'OAUTH_SUCCESS') {
        const { customer_id } = event.data;
        console.log('[Customers] OAuth success for:', customer_id);
        // Recargar clientes para actualizar el estado
        loadCustomers().then(() => {
          setCheckingAuthStatus(null);
        });
      } else if (event.data.type === 'OAUTH_ERROR') {
        console.error('[Customers] OAuth error:', event.data.error);
        setError(event.data.error || 'Error al autorizar el calendario');
        setCheckingAuthStatus(null);
      }
    };

    // Fallback: escuchar cambios en localStorage (por si el popup se cerró antes)
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'oauth_success') {
        const data = e.newValue ? JSON.parse(e.newValue) : null;
        if (data && data.customer_id) {
          console.log('[Customers] OAuth success via localStorage:', data);
          loadCustomers().then(() => {
            setCheckingAuthStatus(null);
          });
          localStorage.removeItem('oauth_success');
        }
      }
    };

    window.addEventListener('message', handleMessage);
    window.addEventListener('storage', handleStorageChange);
    
    // También verificar localStorage al montar (por si el evento ya ocurrió)
    const stored = localStorage.getItem('oauth_success');
    if (stored) {
      try {
        const data = JSON.parse(stored);
        if (data && data.customer_id) {
          console.log('[Customers] Found stored OAuth success:', data);
          loadCustomers().then(() => {
            setCheckingAuthStatus(null);
          });
          localStorage.removeItem('oauth_success');
        }
      } catch (e) {
        console.error('[Customers] Error parsing stored OAuth data:', e);
      }
    }
    
    return () => {
      window.removeEventListener('message', handleMessage);
      window.removeEventListener('storage', handleStorageChange);
    };
  }, [loadCustomers]);

  // Polling inteligente: solo cuando hay un checkingAuthStatus activo
  // Estrategia: esperar un delay inicial (dar tiempo al callback), luego polling menos frecuente
  useEffect(() => {
    if (!checkingAuthStatus) return;

    let attempts = 0;
    const maxAttempts = 10; // 10 intentos máximo
    const initialDelay = 2000; // Esperar 2 segundos antes de empezar (dar tiempo al callback)
    const pollingInterval = 2000; // Verificar cada 2 segundos (menos agresivo)
    
    // Delay inicial antes de empezar el polling
    const initialTimeout = setTimeout(() => {
      const checkStatus = async () => {
        attempts++;
        try {
          // Verificar si el cliente ahora está conectado
          const response = await listCustomerCalendars();
          const customer = response.customers.find(c => c.customer_id === checkingAuthStatus);
          
          if (customer?.calendar_connected) {
            console.log('[Customers] Customer is now connected!', customer.customer_id);
            // Recargar la lista completa para actualizar UI
            await loadCustomers();
            setCheckingAuthStatus(null);
            return true; // Indica que se encontró
          }
          
          if (attempts >= maxAttempts) {
            console.log('[Customers] Max attempts reached, stopping check');
            setCheckingAuthStatus(null);
            return true; // Indica que debe detenerse
          }
          
          return false; // Continuar
        } catch (err) {
          console.error('[Customers] Error checking auth status:', err);
          if (attempts >= maxAttempts) {
            setCheckingAuthStatus(null);
            return true; // Detener
          }
          return false; // Continuar
        }
      };

      // Primera verificación inmediata después del delay
      checkStatus().then((shouldStop) => {
        if (shouldStop) return;

        // Si no se encontró, continuar con polling menos frecuente
        const checkInterval = setInterval(async () => {
          const shouldStop = await checkStatus();
          if (shouldStop) {
            clearInterval(checkInterval);
          }
        }, pollingInterval);
      });
    }, initialDelay);
    
    return () => {
      clearTimeout(initialTimeout);
    };
  }, [checkingAuthStatus, loadCustomers]);

  const handleAddCustomer = async (e: React.FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await connectCustomerCalendar(newCustomer);
      const customerId = newCustomer.customer_id;
      setShowAddCustomer(false);
      setNewCustomer({ customer_id: '', customer_email: '', customer_name: '' });
      
      // Si hay URL de autorización, mostrar modal
      if (response.authorization_url || response.shareable_link) {
        const url = response.authorization_url || response.shareable_link;
        setAuthUrl(url);
        setShowAuthModal(true);
        // Guardar customer_id para verificación automática
        if (customerId) {
          // Se iniciará la verificación cuando se abra la ventana
        }
      }
      
      await loadCustomers();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al agregar cliente');
    } finally {
      setLoading(false);
    }
  };

  const handleDisconnect = async (customerId: string): Promise<void> => {
    if (!window.confirm('¿Estás seguro de que deseas desconectar el calendario de este cliente?')) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await disconnectCustomerCalendar(customerId);
      await loadCustomers();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al desconectar calendario');
    } finally {
      setLoading(false);
    }
  };

  const handleConnect = async (customer: CustomerCalendar): Promise<void> => {
    setLoading(true);
    setError(null);

    try {
      const response = await connectCustomerCalendar({
        customer_id: customer.customer_id,
        customer_email: customer.customer_email,
        customer_name: customer.customer_name || undefined,
      });
      
      // Si hay URL de autorización, mostrar modal
      if (response.authorization_url || response.shareable_link) {
        const url = response.authorization_url || response.shareable_link;
        setAuthUrl(url);
        setShowAuthModal(true);
        // Guardar customer_id para verificación automática cuando se abra
      }
      
      await loadCustomers();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al conectar calendario');
    } finally {
      setLoading(false);
    }
  };


  const handleOpenAuth = (customerId?: string): void => {
    if (authUrl) {
      // Determinar customer_id: puede venir como parámetro, del nuevo cliente, o del último cliente agregado
      const currentCustomerId = customerId || 
                                newCustomer.customer_id || 
                                (customers.length > 0 ? customers[customers.length - 1].customer_id : null);
      
      if (currentCustomerId) {
        setCheckingAuthStatus(currentCustomerId);
      }
      
      window.open(authUrl, '_blank', 'width=600,height=700');
      setShowAuthModal(false);
      setAuthUrl(null);
    }
  };

  const handleCopyAuth = async (): Promise<void> => {
    if (authUrl) {
      try {
        await navigator.clipboard.writeText(authUrl);
        setShowAuthModal(false);
        setAuthUrl(null);
        // Mostrar mensaje de éxito (puedes usar un toast si tienes)
        setError(null);
        setTimeout(() => {
          alert('Link copiado al portapapeles. Puedes compartirlo con el cliente por WhatsApp o email.');
        }, 100);
      } catch (err) {
        setError('Error al copiar el link al portapapeles');
      }
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Clientes y Calendarios</h1>
          <p className="text-slate-600 mt-1">
            Gestiona los clientes y conecta sus calendarios de Google Calendar
          </p>
        </div>
        <button
          onClick={() => setShowAddCustomer(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <UserPlus className="w-5 h-5" />
          Agregar Cliente
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {/* Modal de autorización OAuth2 */}
      {showAuthModal && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          onClick={() => {
            setShowAuthModal(false);
            setAuthUrl(null);
          }}
        >
          <div 
            className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6">
              <h2 className="text-xl font-semibold text-slate-900 mb-4">
                Autorización de Google Calendar
              </h2>
              <p className="text-slate-600 mb-6">
                ¿Quieres abrir la URL de autorización ahora?
              </p>
              <div className="space-y-3 mb-6">
                <div className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg">
                  <div className="flex-1">
                    <p className="font-medium text-slate-900">Sí</p>
                    <p className="text-sm text-slate-600">
                      Se abrirá en una nueva ventana para autorizar
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg">
                  <div className="flex-1">
                    <p className="font-medium text-slate-900">No</p>
                    <p className="text-sm text-slate-600">
                      Se copiará el link al portapapeles para compartirlo con el cliente
                    </p>
                  </div>
                </div>
              </div>
              <div className="flex gap-3">
                <button
                  onClick={handleCopyAuth}
                  className="flex-1 px-4 py-2 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 transition-colors"
                >
                  Copiar Link
                </button>
                <button
                  onClick={() => {
                    // Determinar customer_id antes de abrir
                    const currentCustomerId = newCustomer.customer_id || 
                                            (customers.length > 0 ? customers[customers.length - 1].customer_id : null);
                    handleOpenAuth(currentCustomerId || undefined);
                  }}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Abrir Ahora
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {showAddCustomer && (
        <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-slate-900 mb-4">Agregar Nuevo Cliente</h2>
          <form onSubmit={handleAddCustomer} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                ID del Cliente
              </label>
              <input
                type="text"
                required
                value={newCustomer.customer_id}
                onChange={(e) => setNewCustomer({ ...newCustomer, customer_id: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="ej: cliente-123"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Email del Cliente
              </label>
              <input
                type="email"
                required
                value={newCustomer.customer_email}
                onChange={(e) => setNewCustomer({ ...newCustomer, customer_email: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="cliente@ejemplo.com"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Nombre del Cliente (opcional)
              </label>
              <input
                type="text"
                value={newCustomer.customer_name || ''}
                onChange={(e) => setNewCustomer({ ...newCustomer, customer_name: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Juan Pérez"
              />
            </div>
            <div className="flex gap-3">
              <button
                type="submit"
                disabled={loading}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Conectando...' : 'Conectar Calendario'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowAddCustomer(false);
                  setNewCustomer({ customer_id: '', customer_email: '', customer_name: '' });
                }}
                className="px-4 py-2 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50"
              >
                Cancelar
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200">
          <h2 className="text-lg font-semibold text-slate-900">Clientes Registrados</h2>
        </div>
        {loading && !customers.length ? (
          <div className="p-8 text-center text-slate-500">Cargando clientes...</div>
        ) : customers.length === 0 ? (
          <div className="p-8 text-center text-slate-500">
            No hay clientes registrados. Agrega uno para comenzar.
          </div>
        ) : (
          <div className="divide-y divide-slate-200">
            {customers.map((customer) => (
              <div key={customer.customer_id} className="p-6 hover:bg-slate-50 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-semibold text-slate-900">
                        {customer.customer_name || customer.customer_id}
                      </h3>
                      {checkingAuthStatus === customer.customer_id ? (
                        <span className="flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-700 rounded text-sm">
                          <Calendar className="w-4 h-4 animate-spin" />
                          Verificando...
                        </span>
                      ) : customer.calendar_connected ? (
                        <span className="flex items-center gap-1 px-2 py-1 bg-green-100 text-green-700 rounded text-sm">
                          <CheckCircle2 className="w-4 h-4" />
                          Conectado
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 px-2 py-1 bg-yellow-100 text-yellow-700 rounded text-sm">
                          <XCircle className="w-4 h-4" />
                          No conectado
                        </span>
                      )}
                    </div>
                    <div className="space-y-1 text-sm text-slate-600">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">ID:</span>
                        <span>{customer.customer_id}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium">Email:</span>
                        <span>{customer.customer_email}</span>
                      </div>
                      {customer.calendar_email && (
                        <div className="flex items-center gap-2">
                          <Calendar className="w-4 h-4" />
                          <span className="font-medium">Calendario:</span>
                          <span>{customer.calendar_email}</span>
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {customer.calendar_connected ? (
                      <button
                        onClick={() => handleDisconnect(customer.customer_id)}
                        className="flex items-center gap-2 px-3 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                        title="Desconectar calendario"
                      >
                        <Trash2 className="w-4 h-4" />
                        Desconectar
                      </button>
                    ) : (
                      <button
                        onClick={() => handleConnect(customer)}
                        className="flex items-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                      >
                        <ExternalLink className="w-4 h-4" />
                        Conectar
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default Customers;
