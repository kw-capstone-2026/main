import { useNavigate, useParams } from 'react-router-dom'
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts'
import Sidebar from '../components/Sidebar'
import { MOCK_BLOCKS } from '../data/blocks'

const getMockIndustry = (blockId) => {
  const block = MOCK_BLOCKS.find(b => b.id === blockId) || MOCK_BLOCKS[9]

  if (block.csi >= 8.0) {
    return {
      industryStats: [
        { name: '카페', count: 35, color: '#FFAF53' },
        { name: '음식점', count: 80, color: '#FF808B' },
        { name: '편의점', count: 45, color: '#8AF1B9' },
        { name: '술집', count: 25, color: '#F4BE5E' },
      ],
      survival: [
        { name: '편의점', days: 52, color: '#8AF1B9' },
        { name: '미용', days: 44, color: '#9698D6' },
        { name: '음식점', days: 38, color: '#FF808B' },
        { name: '술집', days: 32, color: '#F4BE5E' },
        { name: '카페', days: 28, color: '#FFAF53' },
      ],
      trend: [
        { month: '2024.01', count: 180 },
        { month: '2024.04', count: 190 },
        { month: '2024.07', count: 195 },
        { month: '2024.10', count: 200 },
        { month: '2025.01', count: 205 },
      ],
    }
  } else {
    return {
      industryStats: [
        { name: '카페', count: 95, color: '#FFAF53' },
        { name: '음식점', count: 40, color: '#FF808B' },
        { name: '편의점', count: 15, color: '#8AF1B9' },
        { name: '술집', count: 20, color: '#F4BE5E' },
      ],
      survival: [
        { name: '편의점', days: 28, color: '#8AF1B9' },
        { name: '미용', days: 20, color: '#9698D6' },
        { name: '음식점', days: 18, color: '#FF808B' },
        { name: '술집', days: 14, color: '#F4BE5E' },
        { name: '카페', days: 10, color: '#FFAF53' },
      ],
      trend: [
        { month: '2024.01', count: 99 },
        { month: '2024.04', count: 130 },
        { month: '2024.07', count: 175 },
        { month: '2024.10', count: 220 },
        { month: '2025.01', count: 260 },
      ],
    }
  }
}

function Industry() {
  const { blockId } = useParams()
  const block = MOCK_BLOCKS.find(b => b.id === blockId) || MOCK_BLOCKS[9]
  const data = getMockIndustry(blockId)
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
          업종 비교
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
            <Pie data={data.industryStats} dataKey="count" cx="50%" cy="50%" innerRadius={45} outerRadius={70}>
              {data.industryStats.map((item, i) => (
                <Cell key={i} fill={item.color} />
              ))}
            </Pie>
          </PieChart>
          {data.industryStats.map((item, i) => (
            <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', padding: '3px 0' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ width: '8px', height: '8px', background: item.color, borderRadius: '50%', display: 'inline-block' }}></span>
                {item.name}
              </span>
              <span style={{ color: '#64748B' }}>{item.count}개</span>
            </div>
          ))}
        </div>
        {/* 메인 지도로 돌아가기 버튼 */}
<div style={{ marginTop: 'auto', paddingTop: '16px' }}>
<button
          onClick={() => navigate('/map')}
          style={{
            width: '100%', background: '#5E81F4', color: 'white',
            border: 'none', padding: '10px', borderRadius: '8px',
            fontSize: '13px', fontWeight: '600', cursor: 'pointer'
          }}
        >
          메인 지도로 돌아가기 ←
        </button>
</div>
      </div>

      {/* 오른쪽 */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', background: '#F5F5FA' }}>
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
            <ResponsiveContainer width="80%" height={200}>
              <BarChart data={data.survival} barSize={100}>
                <XAxis dataKey="name" fontSize={12} />
                {/* ✅ 고정 domain으로 B01/B09 비교 가능하게 */}
                <YAxis fontSize={12} domain={[0, 60]} tickCount={7} />
                <Tooltip formatter={(value) => [`${value}개월`, '평균 생존 기간']} />
                <Bar dataKey="days" radius={[4, 4, 0, 0]}>
                  {data.survival.map((item, i) => (
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
              <LineChart data={data.trend}>
                <XAxis dataKey="month" fontSize={12} />
                {/* ✅ domain 제거 → 데이터 범위에 맞게 자동 조정 */}
                <YAxis fontSize={12} />
                <Tooltip formatter={(value) => [`${value}개`, '점포 수']} />
                <Line
                  type="monotone"
                  dataKey="count"
                  stroke={block.csi >= 8.0 ? '#3B82F6' : '#F97316'}
                  strokeWidth={2}
                  dot={{ fill: block.csi >= 8.0 ? '#3B82F6' : '#F97316' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

        </div>
      </div>
    </div>
  )
}

export default Industry