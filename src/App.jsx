import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import MainMap from "./pages/MainMap";
import Prediction from "./pages/Prediction";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* 👇 http://localhost:5174/ 접속 시 자동으로 /map 으로 넘겨줍니다 */}
        <Route path="/" element={<Navigate to="/map" replace />} />

        {/* 메인 지도 및 예측 상세 페이지 */}
        <Route path="/map" element={<MainMap />} />
        <Route path="/prediction/:blockId" element={<Prediction />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;