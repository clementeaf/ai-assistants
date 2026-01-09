import { useState } from 'react';
import Sidebar from './Sidebar';
import MainContent from './MainContent';
import { Menu, X } from 'lucide-react';

const MobileSidebarToggle = ({
  isOpen,
  onToggle
}: {
  isOpen: boolean;
  onToggle: () => void;
}) => (
  <button
    onClick={onToggle}
    className="lg:hidden fixed bottom-6 right-6 z-50 p-4 bg-blue-600 text-white rounded-full shadow-2xl hover:bg-blue-700 transition-all active:scale-95"
  >
    {isOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
  </button>
);

const SidebarOverlay = ({
  isOpen,
  onClose
}: {
  isOpen: boolean;
  onClose: () => void;
}) => (
  isOpen ? (
    <div
      className="lg:hidden fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-30 transition-opacity"
      onClick={onClose}
    />
  ) : null
);

function Layout() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen w-screen bg-slate-100 overflow-hidden p-4 gap-4">
      <MobileSidebarToggle
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
      />

      <SidebarOverlay
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
      />

      {/* Sidebar - Responsive behavior */}
      <div className={`
        fixed lg:static inset-y-0 left-0 z-40 transform transition-transform duration-300 ease-in-out
        ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        <Sidebar />
      </div>

      <MainContent />
    </div>
  );
}

export default Layout;

