import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout/Layout';
import Home from './pages/Home';
import Flows from './pages/Flows';
import Calendar from './pages/Calendar';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="flujos" element={<Flows />} />
          <Route path="calendario" element={<Calendar />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
