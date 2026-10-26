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