import Sidebar from './Sidebar';
import MainContent from './MainContent';

function Layout() {
  return (
    <div className="flex h-screen">
      <Sidebar />
      <MainContent />
    </div>
  );
}

export default Layout;

