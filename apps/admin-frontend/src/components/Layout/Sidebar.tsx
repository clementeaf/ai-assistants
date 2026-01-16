import { Link, useLocation } from 'react-router-dom';
import { MessageSquare, GitBranch, Calendar as CalendarIcon, LayoutDashboard, Users } from 'lucide-react';

/**
 * Componente de barra lateral con navegación moderna
 * @returns Componente Sidebar renderizado
 */
function Sidebar() {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Chat', icon: MessageSquare },
    { path: '/flujos', label: 'Flujos', icon: GitBranch },
    { path: '/calendario', label: 'Calendario', icon: CalendarIcon },
    { path: '/clientes', label: 'Clientes', icon: Users },
  ];

  const isActive = (path: string): boolean => {
    return location.pathname === path;
  };

  return (
    <aside className="w-56 bg-white text-slate-600 flex flex-col h-full shadow-md rounded-2xl">
      {/* Branding Header */}
      <div className="p-4 border-b border-slate-100 flex items-center gap-2">
        <div className="w-8 h-8 bg-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/20 flex-shrink-0">
          <LayoutDashboard className="text-white w-5 h-5" />
        </div>
        <div className="min-w-0">
          <h1 className="text-slate-900 font-bold text-sm leading-none truncate">AI Assistants</h1>
          <p className="text-slate-500 text-xs mt-0.5 uppercase tracking-wider font-semibold truncate">Admin Panel</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1 mt-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = isActive(item.path);

          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-2.5 px-3 py-2.5 rounded-xl transition-all duration-200 group border focus:outline-none ${active
                ? 'bg-blue-50 text-blue-600 border-blue-100'
                : 'border-transparent hover:bg-slate-50 hover:text-slate-900'
                }`}
            >
              <Icon className={`w-4.5 h-4.5 flex-shrink-0 ${active ? 'text-blue-600' : 'text-slate-400 group-hover:text-slate-600 transition-colors'}`} />
              <span className="font-medium text-sm truncate">{item.label}</span>
              {active && (
                <div className="ml-auto w-1.5 h-1.5 rounded-full bg-blue-600 shadow-lg shadow-blue-400/50 flex-shrink-0" />
              )}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}

export default Sidebar;

