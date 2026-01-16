import { Outlet, useLocation } from 'react-router-dom';

function MainContent() {
  const location = useLocation();

  const getPageTitle = () => {
    switch (location.pathname) {
      case '/': return 'Panel de Control / Chat';
      case '/flujos': return 'Gestión de Flujos';
      case '/calendario': return 'Calendario de Reservas';
      default: return 'AI Assistants';
    }
  };

  return (
    <main className="flex-1 flex flex-col min-h-0 bg-white shadow-md overflow-hidden rounded-2xl">
      {/* Top Header */}
      <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-6 shadow-sm z-10">
        <h2 className="text-xl font-bold text-slate-800">{getPageTitle()}</h2>
        {location.pathname === '/flujos' && (
          <button
            onClick={() => {
              const event = new CustomEvent('createFlow');
              window.dispatchEvent(event);
            }}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors text-sm"
          >
            Crear Flujo
          </button>
        )}
      </header>

      {/* Page Content Container */}
      <div className="flex-1 overflow-hidden p-6">
        <div className="h-full w-full">
          <Outlet />
        </div>
      </div>
    </main>
  );
}

export default MainContent;

