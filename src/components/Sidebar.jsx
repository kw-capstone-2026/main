import { useNavigate, useLocation } from 'react-router-dom'

const MENU = [
  { icon: '🗺️', path: '/map', label: '메인 지도' },
  { icon: '📊', path: '/prediction/B01', label: '예측 결과' },
  { icon: '📋', path: '/industry/B01', label: '업종 비교' },
]

function Sidebar() {
  const navigate = useNavigate()
  const location = useLocation()

  return (
    <div style={{
      width: '48px', background: '#F5F5FA',
      borderRight: '1px solid #E2E8F0',
      display: 'flex', flexDirection: 'column',
      alignItems: 'center', padding: '12px 0', gap: '8px'
    }}>
      <div style={{
        width: '32px', height: '32px', background: '#5E81F4',
        borderRadius: '8px', display: 'flex',
        alignItems: 'center', justifyContent: 'center',
        color: 'white', fontSize: '16px', fontWeight: '700', marginBottom: '8px',
        cursor: 'pointer'
      }}
        onClick={() => navigate('/map')}
      >C</div>

      {MENU.map((item) => (
        <div
          key={item.path}
          onClick={() => navigate(item.path)}
          title={item.label}
          style={{
            width: '32px', height: '32px',
            display: 'flex', alignItems: 'center',
            justifyContent: 'center', fontSize: '18px',
            cursor: 'pointer', borderRadius: '6px',
            background: location.pathname.startsWith(item.path.split('/')[1] === 'prediction' ? '/prediction' : item.path.split('/')[1] === 'industry' ? '/industry' : item.path) ? '#EFF6FF' : 'transparent'
          }}
        >
          {item.icon}
        </div>
      ))}

      {/* 로그아웃 버튼 - 맨 아래 */}
      <div style={{ marginTop: 'auto' }}>
        <div
          onClick={() => navigate('/')}
          title="로그아웃"
          style={{
            width: '32px', height: '32px',
            display: 'flex', alignItems: 'center',
            justifyContent: 'center', fontSize: '18px',
            cursor: 'pointer', borderRadius: '6px'
          }}
        >
          🚪
        </div>
      </div>
    </div>
  )
}

export default Sidebar