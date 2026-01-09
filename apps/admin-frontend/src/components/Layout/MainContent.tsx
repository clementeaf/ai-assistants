import { Outlet, useLocation } from 'react-router-dom';
import { Search, Bell } from 'lucide-react';

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
    <main className="flex-1 flex flex-col min-h-0 bg-slate-50 overflow-hidden">
      {/* Top Header */}
      <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-6 shadow-sm z-10">
        <h2 className="text-xl font-bold text-slate-800">{getPageTitle()}</h2>

        <div className="flex items-center gap-4">
          <div className="relative group">
            <Search className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-500 transition-colors" />
            <input
              type="text"
              placeholder="Buscar..."
              className="pl-10 pr-4 py-2 bg-slate-100 border-none rounded-xl text-sm w-64 focus:ring-2 focus:ring-blue-500/20 focus:bg-white transition-all outline-none"
            />
          </div>

          <button className="p-2.5 rounded-xl bg-slate-100 text-slate-500 hover:bg-slate-200 transition-colors relative">
            <Bell className="w-5 h-5" />
            <span className="absolute top-2 right-2.5 w-2 h-2 bg-blue-500 rounded-full border-2 border-white" />
          </button>
        </div>
      </header>

      {/* Page Content Container */}
      <div className="flex-1 overflow-hidden p-2">
        <div className="h-full w-full">
          <Outlet />
        </div>
      </div>
    </main>
  );
}

export default MainContent;

