import { useNavigate, useParams } from 'react-router-dom'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar, Cell, LabelList } from 'recharts'
import Sidebar from '../components/Sidebar'

import { MOCK_BLOCKS } from '../data/blocks'

const getMockPrediction = (blockId) => {
  const block = MOCK_BLOCKS.find(b => b.id === blockId) || MOCK_BLOCKS[9]
  return {
    blockId: block.id,
    blockName: block.name,
    industry: block.industry,
    csi: block.csi,
    closureRate: 12.4,
    openRate: 8.2,
    riskScore: 81,
    survival6m: 51,
    riskDescription: [
      '음식점 밀집도 매우 높아 신규 진입 어려움',
      '폐업률(12.4%)이 개업률(8.2%)보다 높음',
      '차별화 전략없이는 생존 가능성 낮음'
    ]
  }
}

// ✅ 나중에 API 연결할 때 이 부분 교체
// GET /api/v1/blocks/{blockId}/survivalcurve
const MOCK_SURVIVAL_CURVE = [
  { month: '3개월', rate: 85 },
  { month: '6개월', rate: 51 },
  { month: '9개월', rate: 38 },
  { month: '12개월', rate: 26 },
]

// ✅ 나중에 API 연결할 때 이 부분 교체
// GET /api/v1/blocks/{blockId}/shap
const MOCK_SHAP = [
  { name: '점포 연차', value: 52.9, color: '#EF4444' },
  { name: '경쟁 업체 수', value: 33.9, color: '#F97316' },
  { name: '상권 포화도', value: 4.9, color: '#22C55E' },
  { name: '유동인구', value: 4.1, color: '#94A3B8' },
]

function Prediction() {
  const { blockId } = useParams()
  const data = getMockPrediction(blockId)
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
          예측 결과
        </h2>

        {/* 블록 카드 */}
<div style={{
  background: '#5E81F4', borderRadius: '12px',
  padding: '16px', marginBottom: '12px', color: 'white'
}}>
  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
    <div>
      <div style={{ fontSize: '14px', fontWeight: '700', textAlign: 'left', marginBottom: '2px' }}>{data.blockId}</div>
      <div style={{ fontSize: '18px', fontWeight: '700', marginBottom: '2px', textAlign: 'left' }}>{data.blockName}</div>
      <div style={{ fontSize: '13px', opacity: 0.8, textAlign: 'left' }}>{data.industry}</div>
    </div>
    <div style={{ 
      fontSize: '28px', fontWeight: '700', color: '#FFD700',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      alignSelf: 'center'
    }}>{data.csi}</div>
  </div>
</div>

        {/* 폐업률 */}
        <div style={{ border: '1px solid #E2E8F0', borderRadius: '12px', padding: '14px', marginBottom: '10px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontSize: '14px', fontWeight: '600', color: '#1E293B', textAlign: 'left' }}>폐업률</div>
              <div style={{ fontSize: '11px', color: '#94A3B8', textAlign: 'left' }}>최근1년간</div>
            </div>
            <div style={{ fontSize: '22px', fontWeight: '700', color: '#EF4444' }}>{data.closureRate}%</div>
          </div>
        </div>

        {/* 개업률 */}
        <div style={{ border: '1px solid #E2E8F0', borderRadius: '12px', padding: '14px', marginBottom: '10px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontSize: '14px', fontWeight: '600', color: '#1E293B', textAlign: 'left' }}>개업률</div>
              <div style={{ fontSize: '11px', color: '#94A3B8', textAlign: 'left' }}>최근1년간</div>
            </div>
            <div style={{ fontSize: '22px', fontWeight: '700', color: '#1E293B' }}>{data.openRate}%</div>
          </div>
        </div>

{/* 위험도 등급 */}
<div style={{ border: '1px solid #E2E8F0', borderRadius: '12px', padding: '14px', marginBottom: '10px' }}>
  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
    <div style={{ fontSize: '14px', fontWeight: '600', color: '#1E293B', textAlign: 'left' }}>위험도 등급</div>
    <div style={{
      background: '#FEE2E2', color: '#EF4444',
      fontSize: '13px', fontWeight: '700',
      padding: '12px 10px', borderRadius: '12px',
      textAlign: 'center', minWidth: '56px',
      display: 'flex', flexDirection: 'column',
      alignItems: 'center', gap: '4px'
    }}>
      <span style={{ fontSize: '11px' }}>위험도</span>
      <span style={{ fontSize: '18px' }}>높음</span>
    </div>
  </div>
</div>
        {/* 종합 리스크 */}
        <div style={{ border: '1px solid #E2E8F0', borderRadius: '12px', padding: '14px', marginBottom: '12px' }}>
          <div style={{ fontSize: '14px', fontWeight: '600', color: '#1E293B', marginBottom: '6px', textAlign: 'left' }}>종합 리스크 점수</div>
          <div style={{ fontSize: '28px', fontWeight: '700', color: '#EF4444', marginBottom: '6px', textAlign: 'left' }}>
            {data.riskScore}<span style={{ fontSize: '14px', color: '#94A3B8' }}>/100</span>
          </div>
          <div style={{ background: '#F1F5F9', borderRadius: '4px', height: '8px', marginBottom: '14px' }}>
            <div style={{ background: '#EF4444', width: `${data.riskScore}%`, height: '100%', borderRadius: '4px' }}></div>
          </div>
          <div style={{ fontSize: '14px', fontWeight: '600', color: '#1E293B', marginBottom: '6px', textAlign: 'left' }}>6개월 후 생존 확률</div>
          <div style={{ fontSize: '28px', fontWeight: '700', color: '#5E81F4', marginBottom: '6px', textAlign: 'left' }}>
            {data.survival6m}%
          </div>
          <div style={{ background: '#F1F5F9', borderRadius: '4px', height: '8px' }}>
            <div style={{ background: '#5E81F4', width: `${data.survival6m}%`, height: '100%', borderRadius: '4px' }}></div>
          </div>
        </div>

        <button
          onClick={() => navigate(`/industry/${blockId}`)}
          style={{
            width: '100%',
            background: '#5E81F4', color: 'white',
            border: 'none', padding: '10px',
            borderRadius: '8px', fontSize: '13px',
            fontWeight: '600', cursor: 'pointer'
          }}
        >
          업종 비교 바로가기 →
        </button>
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

          {/* 생존 확률 곡선 */}
          <div style={{ background: 'white', borderRadius: '12px', padding: '20px', border: '1px solid #E2E8F0' }}>
            <div style={{ fontSize: '14px', fontWeight: '600', color: '#5E81F4', marginBottom: '16px', textAlign: 'left' }}>
              생존 확률 곡선 그래프
            </div>
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={MOCK_SURVIVAL_CURVE}>
                <XAxis dataKey="month" fontSize={12} />
                <YAxis fontSize={12} domain={[0, 100]} />
                <Tooltip />
                <Area type="monotone" dataKey="rate" stroke="#EF4444" fill="#FEE2E2" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* SHAP 기여도 */}
          <div style={{ background: 'white', borderRadius: '12px', padding: '20px', border: '1px solid #E2E8F0' }}>
            <div style={{ fontSize: '14px', fontWeight: '600', color: '#5E81F4', marginBottom: '16px', textAlign: 'left' }}>
              SHAP 기여도 막대 차트
            </div>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={MOCK_SHAP} layout="vertical" margin={{ left: 80, right: 60, top: 5, bottom: 5 }}>
                <XAxis type="number" domain={[0, 60]} fontSize={12} hide />
                <YAxis type="category" dataKey="name" fontSize={12} width={100} tick={{ textAnchor: 'start', dx: -100 }} />
                <Tooltip />
                <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                  {MOCK_SHAP.map((item, i) => (
                    <Cell key={i} fill={item.color} />
                  ))}
                  <LabelList dataKey="value" position="right" formatter={(v) => `${v}%`} style={{ fontSize: '13px', fontWeight: '600' }} />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Prediction