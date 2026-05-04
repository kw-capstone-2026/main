import React, { useState } from 'react';

function App() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const testPredict = async () => {
    setLoading(true);
    try {
      // 우리 백엔드(8080)의 /api/predict 엔드포인트 호출
      const response = await fetch('/api/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          lat: 37.5665,         // 서울 시청 위도
          lng: 126.9780,        // 서울 시청 경도
          business_type: "카페" // 테스트 업종
        })
      });

      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error("테스트 실패:", error);
      alert("서버 연결에 실패했습니다.");
    }
    setLoading(false);
  };

  return (
    <div style={{ padding: '20px', textAlign: 'center' }}>
      <h1>🚀 시스템 통합 테스트</h1>
      <p>React(3000) → Spring(8080) → FastAPI(8000) 연결 확인</p>
      
      <button 
        onClick={testPredict} 
        style={{ padding: '10px 20px', fontSize: '16px', cursor: 'pointer' }}
        disabled={loading}
      >
        {loading ? "예측 중..." : "예측 시뮬레이션 시작"}
      </button>

      {result && (
        <div style={{ marginTop: '20px', border: '1px solid #ccc', padding: '10px' }}>
          <h3>분석 결과</h3>
          <pre style={{ textAlign: 'left', display: 'inline-block' }}>
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

export default App;