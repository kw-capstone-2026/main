import { useNavigate, useParams, useLocation } from 'react-router-dom'

function Sidebar() {
  const navigate = useNavigate()
  const { blockId } = useParams()
  const location = useLocation()

  // 1. 현재 URL에서 blockId를 우선 가져오고, 없으면 localStorage, 그것도 없으면 시연 기본값 '828'(경리단길) 사용
  let currentBlockId = blockId && blockId !== 'undefined' && blockId !== 'null' ? blockId : null

  if (!currentBlockId) {
    currentBlockId = localStorage.getItem('selectedBlockId') || '828'
  }

  // 만약 지도 페이지나 다른 곳에서 상권을 클릭해 localStorage가 업데이트되었다면 동기화 반영
  const isActive = (path) => location.pathname.startsWith(path)

  const handleNavigation = (basePath) => {
    // 이동할 때 최신 localStorage 값이나 현재 blockId를 반영
    const targetId = blockId && blockId !== 'undefined' && blockId !== 'null' 
      ? blockId 
      : (localStorage.getItem('selectedBlockId') || '828')
    
    navigate(`${basePath}/${targetId}`)
  }

  return (
    <div style={{
      width: '64px', background: '#4F46E5', display: 'flex', flexDirection: 'column',
      alignItems: 'center', padding: '16px 0', gap: '20px', zIndex: 100
    }}>
      {/* 3번 요구사항: 3줄 정중앙 정렬 완성 코드 */}
<div 
  title="상권 과포화 위험 진단 · 팀 이음"
  onClick={() => navigate('/map')}
  style={{
    width: '52px',
    height: '52px',
    background: 'white',
    borderRadius: '10px',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    cursor: 'pointer',
    boxShadow: '0 2px 6px rgba(0,0,0,0.15)',
    padding: '0',
    boxSizing: 'border-box'
  }}
>
  <div style={{
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: '2px' /* 수직 시각적 밸런스 미세 조정 */
  }}>
    <span style={{ 
      fontSize: '10px', 
      fontWeight: '800', 
      color: '#6366F1', 
      lineHeight: '1.2',
      letterSpacing: '-0.5px',
      margin: '0',
      padding: '0'
    }}>
      상권 과포화
    </span>
    <span style={{ 
      fontSize: '10px', 
      fontWeight: '800', 
      color: '#6366F1', 
      lineHeight: '1.2',
      letterSpacing: '-0.5px',
      margin: '0 0 3px 0',
      padding: '0'
    }}>
      위험 진단
    </span>
    <span style={{ 
      fontSize: '8px', 
      fontWeight: '900', 
      color: '#1E1B4B', 
      lineHeight: '1',
      margin: '0',
      padding: '0'
    }}>
      팀 이음
    </span>
  </div>
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

      {/* 2. 위험 진단 및 SHAP 분석 버튼 */}
      <button
        onClick={() => handleNavigation('/prediction')}
        title="위험 진단 및 SHAP 분석"
        style={{
          width: '40px', height: '40px', border: 'none', borderRadius: '8px',
          background: isActive('/prediction') ? 'rgba(255,255,255,0.25)' : 'transparent',
          cursor: 'pointer', color: 'white', fontSize: '18px'
        }}
      >
        📊
      </button>

      {/* 3. 상권 업종 분석 버튼 */}
      <button
        onClick={() => handleNavigation('/industry')}
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