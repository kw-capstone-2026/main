import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import MainMap from "./pages/MainMap";
import Prediction from "./pages/Prediction";
import Industry from "./pages/Industry"; // 👈 Industry 컴포넌트 import 확인!

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* 루트 접속 시 메인 지도(/map)로 이동 */}
        <Route path="/" element={<Navigate to="/map" replace />} />

        {/* 1. 메인 지도 페이지 */}
        <Route path="/map" element={<MainMap />} />

        {/* 2. 상권 과포화 위험 진단 (SHAP 차트) */}
        <Route path="/prediction/:blockId" element={<Prediction />} />

        {/* 3. 업종 비교 분석 (도넛 차트) */}
        <Route path="/industry/:blockId" element={<Industry />} />

        {/* 그 외 예외 경로는 /map으로 이동 */}
        <Route path="*" element={<Navigate to="/map" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;