import { useNavigate, useParams, useLocation } from 'react-router-dom'

function Sidebar() {
  const navigate = useNavigate()
  const { blockId } = useParams()
  const location = useLocation()

  // 1. 현재 URL 주소(예: /prediction/4 또는 /industry/4)에서 blockId를 추출
  // 2. 만약 상세 페이지가 아니라면 localStorage나 기본값(예: 상수동 '5')을 참조하되, 현재 blockId가 있으면 최우선으로 사용
  const currentBlockId = blockId && blockId !== 'undefined' && blockId !== 'null' ? blockId : (localStorage.getItem('selectedBlockId') || '5')

  const isActive = (path) => location.pathname.startsWith(path)

  return (
    <div style={{
      width: '64px', background: '#4F46E5', display: 'flex', flexDirection: 'column',
      alignItems: 'center', padding: '16px 0', gap: '20px', zIndex: 100
    }}>
      {/* 로고 */}
      <div style={{
        width: '36px', height: '36px', background: 'white', color: '#4F46E5',
        borderRadius: '8px', display: 'flex', justifyContent: 'center', alignItems: 'center',
        fontWeight: '800', fontSize: '18px'
      }}>
        C
      </div>

      {/* 1. 지도 이동 버튼 */}
      <button
        onClick={() => navigate('/map')}
        title="상권 과포화 지도"
        style={{
          width: '40px', height: '40px', border: 'none', borderRadius: '8px',
          background: isActive('/map') ? 'rgba(255,255,255,0.25)' : 'transparent',
          cursor: 'pointer', color: 'white', fontSize: '18px'
        }}
      >
        🗺️
      </button>

      {/* 2. 위험 진단 및 SHAP 분석 버튼 (현재 선택된 blockId 유지) */}
      <button
        onClick={() => navigate(`/prediction/${currentBlockId}`)}
        title="위험 진단 및 SHAP 분석"
        style={{
          width: '40px', height: '40px', border: 'none', borderRadius: '8px',
          background: isActive('/prediction') ? 'rgba(255,255,255,0.25)' : 'transparent',
          cursor: 'pointer', color: 'white', fontSize: '18px'
        }}
      >
        📊
      </button>

      {/* 3. 상권 업종 분석 버튼 (현재 선택된 blockId 유지) */}
      <button
        onClick={() => navigate(`/industry/${currentBlockId}`)}
        title="상권 업종 분석"
        style={{
          width: '40px', height: '40px', border: 'none', borderRadius: '8px',
          background: isActive('/industry') ? 'rgba(255,255,255,0.25)' : 'transparent',
          cursor: 'pointer', color: 'white', fontSize: '18px'
        }}
      >
        📋
      </button>
    </div>
  )
}

export default Sidebar