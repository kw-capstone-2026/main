import { useNavigate, useParams } from 'react-router-dom'
import { PieChart, Pie, Cell, Legend, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts'
import Sidebar from '../components/Sidebar'
import { MOCK_BLOCKS } from '../data/blocks'

// ✅ 나중에 API 연결할 때 이 부분 교체
// GET /api/v1/blocks/{blockId}/industrystats
const MOCK_INDUSTRY_STATS = [
  { name: '카페', count: 9, color: '#EF4444' },
  { name: '음식점', count: 95, color: '#F97316' },
  { name: '편의점', count: 40, color: '#22C55E' },
  { name: '술집', count: 35, color: '#3B82F6' },
]

// ✅ 나중에 API 연결할 때 이 부분 교체
// GET /api/v1/blocks/{blockId}/industrysurvival
const MOCK_SURVIVAL = [
  { name: '편의점', days: 38, color: '#22C55E' },
  { name: '미용', days: 24, color: '#8B5CF6' },
  { name: '음식점', days: 22, color: '#F97316' },
  { name: '술집', days: 19, color: '#3B82F6' },
  { name: '카페', days: 14, color: '#EF4444' },
]

// ✅ 나중에 API 연결할 때 이 부분 교체
// GET /api/v1/blocks/{blockId}/competition-trend
const MOCK_TREND = [
  { month: '2026.05', count: 99 },
  { month: '2026.06', count: 160 },
  { month: '2026.07', count: 195 },
  { month: '2026.08', count: 250 },
  { month: '2026.09', count: 250 },
]

function Industry() {
  const { blockId } = useParams()
  const block = MOCK_BLOCKS.find(b => b.id === blockId) || MOCK_BLOCKS[9]
  const navigate = useNavigate()

  return (
    <div style={{ display: 'flex', height: '100vh', background: '#F8F9FA' }}>
      <Sidebar />

      {/* 왼쪽 사이드바 */}
      <div style={{
        width: '280px', background: 'white',
        borderRight: '1px solid #E2E8F0',
        display: 'flex', flexDirection: 'column',
        padding: '20px', overflowY: 'auto'
      }}>
        <h2 style={{ fontSize: '20px', fontWeight: '700', marginBottom: '16px', color: '#1E293B', textAlign: 'left' }}>
          상권 분석 플랫폼
        </h2>

        {/* 블록 카드 */}
        <div style={{
          background: '#5E81F4', borderRadius: '12px',
          padding: '16px', marginBottom: '12px', color: 'white'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontSize: '14px', fontWeight: '700', textAlign: 'left', marginBottom: '2px' }}>{block.id}</div>
              <div style={{ fontSize: '18px', fontWeight: '700', marginBottom: '2px', textAlign: 'left' }}>{block.name}</div>
              <div style={{ fontSize: '13px', opacity: 0.8, textAlign: 'left' }}>{block.industry}</div>
            </div>
            <div style={{ fontSize: '28px', fontWeight: '700', color: '#FFD700' }}>{block.csi}</div>
          </div>
        </div>

        {/* 업종 비율 차트 */}
        <div style={{ border: '1px solid #E2E8F0', borderRadius: '12px', padding: '14px' }}>
          <div style={{ fontSize: '14px', fontWeight: '600', color: '#1E293B', marginBottom: '8px', textAlign: 'left' }}>업종 비율 차트</div>
          <PieChart width={200} height={160}>
            <Pie data={MOCK_INDUSTRY_STATS} dataKey="count" cx="50%" cy="50%" innerRadius={45} outerRadius={70}>
              {MOCK_INDUSTRY_STATS.map((item, i) => (
                <Cell key={i} fill={item.color} />
              ))}
            </Pie>
          </PieChart>
          {MOCK_INDUSTRY_STATS.map((item, i) => (
            <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', padding: '3px 0' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ width: '8px', height: '8px', background: item.color, borderRadius: '50%', display: 'inline-block' }}></span>
                {item.name}
              </span>
              <span style={{ color: '#64748B' }}>{item.count}개</span>
            </div>
          ))}
        </div>
      </div>

      {/* 오른쪽 */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <div style={{
          padding: '12px 20px', background: 'white',
          borderBottom: '1px solid #E2E8F0',
          display: 'flex', alignItems: 'center', gap: '12px'
        }}>
          <span style={{ fontSize: '14px', color: '#94A3B8' }}>≡</span>
          <span style={{ fontSize: '15px', fontWeight: '600', color: '#1E293B' }}>Dashboard</span>
        </div>

        <div style={{ flex: 1, padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px', overflowY: 'auto' }}>

          {/* 업종별 평균 생존 기간 */}
          <div style={{ background: 'white', borderRadius: '12px', padding: '20px', border: '1px solid #E2E8F0' }}>
            <div style={{ fontSize: '14px', fontWeight: '600', color: '#5E81F4', marginBottom: '16px', textAlign: 'left' }}>
              업종별 평균 생존 기간 막대 그래프
            </div>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={MOCK_SURVIVAL}>
                <XAxis dataKey="name" fontSize={12} />
                <YAxis fontSize={12} />
                <Tooltip />
                <Bar dataKey="days" radius={[4, 4, 0, 0]}>
                  {MOCK_SURVIVAL.map((item, i) => (
                    <Cell key={i} fill={item.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* 월별 경쟁 점포 수 추이 */}
          <div style={{ background: 'white', borderRadius: '12px', padding: '20px', border: '1px solid #E2E8F0' }}>
            <div style={{ fontSize: '14px', fontWeight: '600', color: '#5E81F4', marginBottom: '4px', textAlign: 'left' }}>
              월별 경쟁 점포 수 추이 선 그래프
            </div>
            <div style={{ fontSize: '12px', color: '#94A3B8', marginBottom: '16px', textAlign: 'left' }}>
              향후 12개월간 상권 내 점포 수 변화 추이
            </div>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={MOCK_TREND}>
                <XAxis dataKey="month" fontSize={12} />
                <YAxis fontSize={12} />
                <Tooltip />
                <Line type="monotone" dataKey="count" stroke="#F97316" strokeWidth={2} dot={{ fill: '#F97316' }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Industry