import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Login from './pages/Login'
import MainMap from './pages/MainMap'
import Prediction from './pages/Prediction'
import Industry from './pages/Industry'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/map" element={<MainMap />} />
        <Route path="/prediction/:blockId" element={<Prediction />} />
        <Route path="/industry/:blockId" element={<Industry />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App