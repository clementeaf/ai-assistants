import { Link, useLocation } from 'react-router-dom';
import { MessageSquare, GitBranch, Calendar as CalendarIcon, LayoutDashboard, User, Settings, LogOut } from 'lucide-react';

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
    <aside className="w-72 bg-slate-900 text-slate-300 flex flex-col h-full shadow-xl">
      {/* Branding Header */}
      <div className="p-6 border-b border-slate-800 flex items-center gap-3">
        <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/20">
          <LayoutDashboard className="text-white w-6 h-6" />
        </div>
        <div>
          <h1 className="text-white font-bold text-lg leading-none">AI Assistants</h1>
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
              className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group ${active
                  ? 'bg-blue-600/10 text-blue-400 border border-blue-600/20'
                  : 'hover:bg-slate-800 hover:text-white'
                }`}
            >
              <Icon className={`w-5 h-5 ${active ? 'text-blue-400' : 'text-slate-500 group-hover:text-white transition-colors'}`} />
              <span className="font-medium">{item.label}</span>
              {active && (
                <div className="ml-auto w-1.5 h-1.5 rounded-full bg-blue-400 shadow-lg shadow-blue-400/50" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* Footer / User Profile */}
      <div className="p-4 border-t border-slate-800">
        <div className="flex items-center gap-4 px-4 py-4 rounded-2xl bg-slate-800/40 border border-slate-800/60 mb-2">
          <div className="w-10 h-10 rounded-full bg-slate-700 flex items-center justify-center border-2 border-slate-600 overflow-hidden">
            <User className="w-6 h-6 text-slate-400" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-white truncate">Admin User</p>
            <p className="text-xs text-slate-500 truncate">admin@ai-assistants.com</p>
          </div>
        </div>

        <div className="flex gap-2 mt-2 px-2">
          <button className="flex-1 flex items-center justify-center p-2 rounded-lg hover:bg-slate-800 transition-colors text-slate-500 hover:text-white" title="Settings">
            <Settings className="w-5 h-5" />
          </button>
          <button className="flex-1 flex items-center justify-center p-2 rounded-lg hover:bg-red-500/10 transition-colors text-slate-500 hover:text-red-400" title="Logout">
            <LogOut className="w-5 h-5" />
          </button>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;

