import { useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { CheckCircle2, XCircle } from 'lucide-react';

/**
 * Página de callback de OAuth2 que notifica al padre cuando la autorización es exitosa
 * @returns Componente de callback renderizado
 */
function OAuthCallback() {
  const [searchParams] = useSearchParams();
  const status = searchParams.get('status');
  const customerId = searchParams.get('customer_id');
  const calendarEmail = searchParams.get('calendar_email');
  const error = searchParams.get('error');

  useEffect(() => {
    // Notificar a la ventana padre que la autorización se completó
    const notifyParent = () => {
      if (window.opener && !window.opener.closed) {
        if (status === 'success' && customerId) {
          console.log('[OAuthCallback] Sending success message to parent:', { customerId, calendarEmail });
          window.opener.postMessage(
            {
              type: 'OAUTH_SUCCESS',
              customer_id: customerId,
              calendar_email: calendarEmail,
            },
            window.location.origin
          );
        } else if (error) {
          console.log('[OAuthCallback] Sending error message to parent:', error);
          window.opener.postMessage(
            {
              type: 'OAUTH_ERROR',
              error: error,
            },
            window.location.origin
          );
        }
      } else {
        console.warn('[OAuthCallback] window.opener is null or closed, cannot notify parent');
        // Fallback: usar localStorage como alternativa
        if (status === 'success' && customerId) {
          localStorage.setItem('oauth_success', JSON.stringify({ customer_id: customerId, calendar_email: calendarEmail }));
          // Disparar evento personalizado
          window.dispatchEvent(new StorageEvent('storage', { key: 'oauth_success' }));
        }
      }
    };

    // Notificar inmediatamente
    notifyParent();
    
    // También intentar después de un pequeño delay por si acaso
    const timeoutId = setTimeout(notifyParent, 100);
    
    // Cerrar esta ventana después de un breve delay
    const closeTimeout = setTimeout(() => {
      window.close();
    }, 2000);

    return () => {
      clearTimeout(timeoutId);
      clearTimeout(closeTimeout);
    };
  }, [status, customerId, calendarEmail, error]);

  if (status === 'success') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full mx-4 text-center">
          <CheckCircle2 className="w-16 h-16 text-green-500 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-slate-900 mb-2">
            ¡Autorización Exitosa!
          </h1>
          <p className="text-slate-600 mb-4">
            El calendario de Google se ha conectado correctamente.
          </p>
          {calendarEmail && (
            <p className="text-sm text-slate-500">
              Calendario: {calendarEmail}
            </p>
          )}
          <p className="text-sm text-slate-400 mt-4">
            Esta ventana se cerrará automáticamente...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full mx-4 text-center">
        <XCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
        <h1 className="text-2xl font-bold text-slate-900 mb-2">
          Error de Autorización
        </h1>
        <p className="text-slate-600 mb-4">
          {error || 'Ocurrió un error al autorizar el calendario.'}
        </p>
        <p className="text-sm text-slate-400 mt-4">
          Esta ventana se cerrará automáticamente...
        </p>
      </div>
    </div>
  );
}

export default OAuthCallback;
