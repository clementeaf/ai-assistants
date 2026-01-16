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
      {/* Top Header - Solo mostrar si no estamos en /flujos (Flows maneja su propio header) */}
      {location.pathname !== '/flujos' && (
        <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-6 shadow-sm z-10">
          <h2 className="text-xl font-bold text-slate-800">{getPageTitle()}</h2>
        </header>
      )}

      {/* Page Content Container */}
      <div className={`flex-1 overflow-hidden ${location.pathname === '/flujos' ? '' : 'p-6'}`}>
        <div className="h-full w-full">
          <Outlet />
        </div>
      </div>
    </main>
  );
}

export default MainContent;

