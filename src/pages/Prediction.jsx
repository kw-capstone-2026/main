import { useNavigate, useParams } from 'react-router-dom'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar, Cell, LabelList } from 'recharts'
import Sidebar from '../components/Sidebar'
import { MOCK_BLOCKS } from '../data/blocks'

const getMockPrediction = (blockId) => {
  const block = MOCK_BLOCKS.find((b) => b.id === blockId) || MOCK_BLOCKS[9]

  if (block.csi >= 8.0) {
    return {
      blockId: block.id,
      blockName: block.name,
      industry: block.industry,
      csi: block.csi,
      closureRate: 2.1,
      openRate: 5.4,
      riskScore: 29,
      riskLevel: '낮음',
      riskColor: '#3B82F6',
      badgeBg: '#EFF6FF',
      survival6m: 81,
      survivalCurve: [
        { month: '3개월', rate: 92 },
        { month: '6개월', rate: 81 },
        { month: '9개월', rate: 73 },
        { month: '12개월', rate: 65 },
      ],
      shapData: [
        { name: '전년 대비 폐업 증감률', value: 25.4, color: '#3B82F6', label: '-0.82 (안정적)' },
        { name: '점포당 평균 매출', value: 23.2, color: '#3B82F6', label: '4,751만 원 (매우 높음)' },
        { name: '당월 매출 금액', value: 12.4, color: '#3B82F6', label: '5,420만 원 (상권 활성)' },
        { name: '운영 영업 개월 평균', value: 9.3, color: '#3B82F6', label: '45.2개월 (장기 운영)' },
        { name: '집객시설 밀도', value: 4.6, color: '#3B82F6', label: '12.4 (집객력 풍부)' },
      ],
    }
  } else {
    return {
      blockId: block.id,
      blockName: block.name,
      industry: block.industry,
      csi: block.csi,
      closureRate: 14.8,
      openRate: 3.1,
      riskScore: 93,
      riskLevel: '높음',
      riskColor: '#EF4444',
      badgeBg: '#FEE2E2',
      survival6m: 23,
      survivalCurve: [
        { month: '3개월', rate: 45 },
        { month: '6개월', rate: 23 },
        { month: '9개월', rate: 12 },
        { month: '12개월', rate: 5 },
      ],
      shapData: [
        { name: '전년 대비 폐업 증감률', value: 43.8, color: '#EF4444', label: '+2.18 (2배 폭증)' },
        { name: '점포당 평균 매출', value: 20.1, color: '#EF4444', label: '91만 원 (최저 수준)' },
        { name: '운영 영업 개월 평균', value: 9.0, color: '#EF4444', label: '24.5개월 (단기 생존)' },
        { name: '집객시설 밀도', value: 3.0, color: '#EF4444', label: '3.2 (집객시설 부족)' },
        { name: '당월 매출 금액', value: 4.0, color: '#3B82F6', label: '638만 원 (완화 요인)' },
      ],
    }
  }
}

function Prediction() {
  const { blockId } = useParams()
  const data = getMockPrediction(blockId)
  const navigate = useNavigate()

  return (
    <div style={{ display: 'flex', height: '100vh', background: '#F5F5FA' }}>
      <Sidebar />

      {/* 왼쪽 사이드바 */}
      <div style={{
        width: '280px', background: 'white',
        borderRight: '1px solid #E2E8F0',
        display: 'flex', flexDirection: 'column',
        padding: '20px', overflowY: 'hidden'
      }}>
        <h2 style={{ fontSize: '20px', fontWeight: '700', marginBottom: '14px', color: '#1E293B', textAlign: 'left' }}>
          예측 결과
        </h2>

        {/* 블록 카드 */}
        <div style={{
          background: '#5E81F4', borderRadius: '12px',
          padding: '16px', marginBottom: '12px', color: 'white'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontSize: '13px', fontWeight: '700', textAlign: 'left', marginBottom: '2px' }}>{data.blockId}</div>
              <div style={{ fontSize: '17px', fontWeight: '700', marginBottom: '2px', textAlign: 'left' }}>{data.blockName}</div>
              <div style={{ fontSize: '12px', opacity: 0.8, textAlign: 'left' }}>{data.industry}</div>
            </div>
            <div style={{ fontSize: '26px', fontWeight: '700', color: '#FFD700' }}>{data.csi}</div>
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
              background: data.badgeBg,
              color: data.riskColor,
              fontSize: '12px', fontWeight: '700',
              padding: '6px 10px', borderRadius: '10px',
              textAlign: 'center', minWidth: '52px',
              display: 'flex', flexDirection: 'column',
              alignItems: 'center', gap: '2px'
            }}>
              <span style={{ fontSize: '10px' }}>위험도</span>
              <span style={{ fontSize: '16px' }}>{data.riskLevel}</span>
            </div>
          </div>
        </div>

        {/* 종합 리스크 */}
        <div style={{ border: '1px solid #E2E8F0', borderRadius: '12px', padding: '14px', marginBottom: '12px' }}>
          <div style={{ fontSize: '14px', fontWeight: '600', color: '#1E293B', marginBottom: '4px', textAlign: 'left' }}>종합 리스크 점수</div>
          <div style={{ fontSize: '26px', fontWeight: '700', color: data.riskColor, marginBottom: '4px', textAlign: 'left' }}>
            {data.riskScore}<span style={{ fontSize: '13px', color: '#94A3B8' }}>/100</span>
          </div>
          <div style={{ background: '#F1F5F9', borderRadius: '4px', height: '6px', marginBottom: '10px' }}>
            <div style={{ background: data.riskColor, width: `${data.riskScore}%`, height: '100%', borderRadius: '4px' }}></div>
          </div>
          <div style={{ fontSize: '14px', fontWeight: '600', color: '#1E293B', marginBottom: '4px', textAlign: 'left' }}>6개월 후 생존 확률</div>
          <div style={{ fontSize: '26px', fontWeight: '700', color: '#5E81F4', marginBottom: '4px', textAlign: 'left' }}>
            {data.survival6m}%
          </div>
          <div style={{ background: '#F1F5F9', borderRadius: '4px', height: '6px' }}>
            <div style={{ background: '#5E81F4', width: `${data.survival6m}%`, height: '100%', borderRadius: '4px' }}></div>
          </div>
        </div>

        <button
          onClick={() => navigate(`/industry/${blockId}`)}
          style={{
            width: '100%', background: '#5E81F4', color: 'white',
            border: 'none', padding: '10px', borderRadius: '8px',
            fontSize: '13px', fontWeight: '600', cursor: 'pointer'
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
              <AreaChart data={data.survivalCurve}>
                <XAxis dataKey="month" fontSize={12} />
                <YAxis fontSize={12} domain={[0, 100]} />
                <Tooltip />
                <Area type="monotone" dataKey="rate" stroke={data.riskColor} fill={data.badgeBg} strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* SHAP 기여도 */}
          <div style={{ background: 'white', borderRadius: '12px', padding: '20px', border: '1px solid #E2E8F0' }}>
            <div style={{ fontSize: '14px', fontWeight: '600', color: '#5E81F4', marginBottom: '16px', textAlign: 'left' }}>
              SHAP 기여도 막대 차트
            </div>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={data.shapData} layout="vertical" margin={{ left: 80, right: 120, top: 5, bottom: 5 }}>
                <XAxis type="number" domain={[0, 60]} fontSize={12} hide />
                <YAxis type="category" dataKey="name" fontSize={12} width={100} tick={{ textAnchor: 'start', dx: -100 }} />
                <Tooltip formatter={(value, name, props) => [`기여도: ${value}% (${props.payload.label})`, '요인']} />
                <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                  {data.shapData.map((item, i) => (
                    <Cell key={i} fill={item.color} />
                  ))}
                  <LabelList
                    dataKey="value"
                    position="right"
                    formatter={(v, entry) => `${v}%`}
                    style={{ fontSize: '11px', fontWeight: '600' }}
                  />
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