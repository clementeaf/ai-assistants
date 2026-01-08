import { Link, useLocation } from 'react-router-dom';

/**
 * Componente de barra lateral con navegación
 * @returns Componente Sidebar renderizado
 */
function Sidebar() {
  const location = useLocation();

  const isActive = (path: string): boolean => {
    return location.pathname === path;
  };

  return (
    <aside className="w-64 bg-gray-100 border-r border-gray-200">
      <div className="p-4">
        <h2 className="text-lg font-semibold mb-4">AI Assistants</h2>
        <nav className="space-y-2">
          <Link
            to="/"
            className={`block px-4 py-2 rounded-lg transition-colors ${
              isActive('/')
                ? 'bg-blue-500 text-white'
                : 'text-gray-700 hover:bg-gray-200'
            }`}
          >
            Chat
          </Link>
          <Link
            to="/flujos"
            className={`block px-4 py-2 rounded-lg transition-colors ${
              isActive('/flujos')
                ? 'bg-blue-500 text-white'
                : 'text-gray-700 hover:bg-gray-200'
            }`}
          >
            Flujos
          </Link>
          <Link
            to="/calendario"
            className={`block px-4 py-2 rounded-lg transition-colors ${
              isActive('/calendario')
                ? 'bg-blue-500 text-white'
                : 'text-gray-700 hover:bg-gray-200'
            }`}
          >
            Calendario
          </Link>
        </nav>
      </div>
    </aside>
  );
}

export default Sidebar;

