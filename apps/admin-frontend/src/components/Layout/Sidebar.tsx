import { Link, useLocation } from 'react-router-dom';
import { MessageSquare, GitBranch, Calendar as CalendarIcon, LayoutDashboard } from 'lucide-react';

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
  ];

  const isActive = (path: string): boolean => {
    return location.pathname === path;
  };

  return (
    <aside className="w-72 bg-white text-slate-600 flex flex-col h-full shadow-md rounded-2xl">
      {/* Branding Header */}
      <div className="p-6 border-b border-slate-100 flex items-center gap-3">
        <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/20">
          <LayoutDashboard className="text-white w-6 h-6" />
        </div>
        <div>
          <h1 className="text-slate-900 font-bold text-lg leading-none">AI Assistants</h1>
          <p className="text-slate-500 text-xs mt-1 uppercase tracking-wider font-semibold">Admin Panel</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1 mt-4">
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = isActive(item.path);

          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group border focus:outline-none ${active
                ? 'bg-blue-50 text-blue-600 border-blue-100'
                : 'border-transparent hover:bg-slate-50 hover:text-slate-900'
                }`}
            >
              <Icon className={`w-5 h-5 ${active ? 'text-blue-600' : 'text-slate-400 group-hover:text-slate-600 transition-colors'}`} />
              <span className="font-medium">{item.label}</span>
              {active && (
                <div className="ml-auto w-1.5 h-1.5 rounded-full bg-blue-600 shadow-lg shadow-blue-400/50" />
              )}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}

export default Sidebar;

