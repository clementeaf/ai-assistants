import { Outlet } from 'react-router-dom';

function MainContent() {
  return (
    <main className="flex-1 flex flex-col min-h-0 overflow-hidden">
      <div className="flex-1 flex flex-col min-h-0 p-6">
        <Outlet />
      </div>
    </main>
  );
}

export default MainContent;

