import { Outlet } from 'react-router-dom';

function MainContent() {
  return (
    <main className="flex-1 overflow-auto">
      <div className="p-6">
        <Outlet />
      </div>
    </main>
  );
}

export default MainContent;

