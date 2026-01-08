import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout/Layout';
import Home from './pages/Home';
import Flows from './pages/Flows';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="flujos" element={<Flows />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
