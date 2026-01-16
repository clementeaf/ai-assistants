import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout/Layout';
import Home from './pages/Home';
import Flows from './pages/Flows';
import Calendar from './pages/Calendar';
import Customers from './pages/Customers';
import OAuthCallback from './pages/OAuthCallback';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="flujos" element={<Flows />} />
          <Route path="calendario" element={<Calendar />} />
          <Route path="clientes" element={<Customers />} />
        </Route>
        <Route path="/oauth-success" element={<OAuthCallback />} />
        <Route path="/oauth-error" element={<OAuthCallback />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
