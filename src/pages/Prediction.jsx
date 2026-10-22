import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ResponsiveContainer, BarChart, Bar, Cell, LabelList, XAxis, YAxis, Tooltip } from 'recharts'
import Sidebar from '../components/Sidebar'

// 위험도 3단계 색상 및 배경 매핑
const getGradeStyle = (grade) => {
  switch (grade) {
    case '안전':
      return { color: '#22C55E', bg: '#DCFCE7' }
    case '주의':
      return { color: '#EAB308', bg: '#FEF9C3' }
    case '위험':
      return { color: '#EF4444', bg: '#FEE2E2' }
    default:
      return { color: '#EAB308', bg: '#FEF9C3' } // 기본값: 주의
  }
}

function Prediction() {
  const { blockId } = useParams()
  const navigate = useNavigate()

  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchPredictionData = async () => {
      setLoading(true)
      setError(null)
      try {
        const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080'
        const response = await fetch(`${baseUrl}/api/v1/blocks/${blockId}/prediction`)
        
        // API 연동 전 테스트용 fallback mock 데이터
        let resData = {}
        if (response.ok) {
          resData = await response.json()
        } else {
          console.warn(`API 응답 상태(${response.status}): Mock 데이터를 사용합니다.`)
          resData = {
            blockId: blockId,
            blockName: '시연용 상권',
            industry: '커피-음료',
            riskGrade: '주의',
            riskScore: 58,
            closureRate: 12.5,
            openRate: 8.3,
            shapData: [
              { name: '경쟁 점포 수', value: 35, actualValue: '58개', isRisk: true },
              { name: '평균 운영 기간(개월)', value: 20, actualValue: '24개월', isRisk: false },
              { name: '유동인구', value: 15, actualValue: '7만명/일', isRisk: false },
              { name: '임대료 수준', value: 12, actualValue: '평당 18만원', isRisk: true },
              { name: '동일 업종 밀집도', value: 8, actualValue: '높음', isRisk: true },
            ]
          }
        }

        const currentGrade = resData.riskGrade || resData.risk_grade || '주의'
        const gradeStyle = getGradeStyle(currentGrade)

        const rawShapList = resData.shapData || resData.shap_data || [
          { name: '경쟁 점포 수', value: 35, actualValue: '58개', isRisk: true },
          { name: '평균 운영 기간(개월)', value: 20, actualValue: '24개월', isRisk: false },
          { name: '유동인구', value: 15, actualValue: '7만명/일', isRisk: false },
          { name: '임대료 수준', value: 12, actualValue: '평당 18만원', isRisk: true },
          { name: '동일 업종 밀집도', value: 8, actualValue: '높음', isRisk: true },
        ]

        const formattedData = {
          blockId: resData.blockId || resData.block_id || blockId,
          blockName: resData.blockName || resData.block_name || '상권 정보',
          industry: resData.industry || '커피-음료',
          closureRate: resData.closureRate ?? resData.closure_rate ?? 0.0,
          openRate: resData.openRate ?? resData.open_rate ?? 0.0,
          riskScore: resData.riskScore ?? resData.risk_score ?? 0,
          riskGrade: currentGrade,
          riskColor: gradeStyle.color,
          badgeBg: gradeStyle.bg,
          shapData: rawShapList.map((item) => ({
            name: item.name === '운영 영업 개월 평균' ? '평균 운영 기간(개월)' : item.name,
            value: item.value ?? 0,
            actualValue: item.actualValue || item.actual_value || '-',
            color: item.isRisk ? '#EF4444' : '#3B82F6',
          })),
        }

        setData(formattedData)
      } catch (err) {
        console.error('API 연동 예외 발생:', err)
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    if (blockId) {
      fetchPredictionData()
    }
  }, [blockId])

  if (loading) {
    return (
      <div style={{ display: 'flex', height: '100vh', justifyContent: 'center', alignItems: 'center', background: '#F5F5FA' }}>
        <p style={{ fontSize: '16px', fontWeight: '600', color: '#64748B' }}>예측 데이터를 불러오는 중...</p>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div style={{ display: 'flex', height: '100vh', justifyContent: 'center', alignItems: 'center', background: '#F5F5FA', flexDirection: 'column', gap: '12px' }}>
        <p style={{ fontSize: '16px', fontWeight: '600', color: '#EF4444' }}>데이터를 불러오지 못했습니다. ({error})</p>
        <button onClick={() => window.location.reload()} style={{ padding: '8px 16px', background: '#5E81F4', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' }}>
          다시 시도
        </button>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', height: '100vh', background: '#F5F5FA' }}>
      <Sidebar />

      {/* 왼쪽 사이드바 */}
      <div style={{
        width: '280px', background: 'white',
        borderRight: '1px solid #E2E8F0',
        display: 'flex', flexDirection: 'column',
        padding: '20px', overflowY: 'auto'
      }}>
        <h2 style={{ fontSize: '20px', fontWeight: '700', marginBottom: '14px', color: '#1E293B', textAlign: 'left' }}>
          예측 결과
        </h2>

        {/* 상권 헤더 카드 */}
        <div style={{
          background: '#5E81F4', borderRadius: '12px',
          padding: '16px', marginBottom: '12px', color: 'white'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontSize: '13px', fontWeight: '700', textAlign: 'left', marginBottom: '2px' }}>{data.blockId}</div>
              <div style={{ fontSize: '17px', fontWeight: '700', marginBottom: '2px', textAlign: 'left' }}>{data.blockName}</div>
              <div style={{ fontSize: '12px', opacity: 0.8, textAlign: 'left' }}>업종: {data.industry}</div>
            </div>
          </div>
        </div>

        {/* 위험도 등급 */}
        <div style={{ border: '1px solid #E2E8F0', borderRadius: '12px', padding: '14px', marginBottom: '10px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ fontSize: '14px', fontWeight: '600', color: '#1E293B', textAlign: 'left' }}>위험도 등급</div>
            <div style={{
              background: data.badgeBg,
              color: data.riskColor,
              fontWeight: '700',
              padding: '6px 16px',
              borderRadius: '8px',
              fontSize: '18px'
            }}>
              {data.riskGrade}
            </div>
          </div>
        </div>

        {/* 종합 위험 점수 */}
        <div style={{ border: '1px solid #E2E8F0', borderRadius: '12px', padding: '14px', marginBottom: '10px' }}>
          <div style={{ fontSize: '14px', fontWeight: '600', color: '#1E293B', marginBottom: '4px', textAlign: 'left' }}>위험 점수 (Risk Score)</div>
          <div style={{ fontSize: '26px', fontWeight: '700', color: data.riskColor, marginBottom: '4px', textAlign: 'left' }}>
            {data.riskScore}<span style={{ fontSize: '13px', color: '#94A3B8' }}>/100</span>
          </div>
          <div style={{ background: '#F1F5F9', borderRadius: '4px', height: '6px' }}>
            <div style={{ background: data.riskColor, width: `${data.riskScore}%`, height: '100%', borderRadius: '4px' }}></div>
          </div>
        </div>

        {/* 폐업률 */}
        <div style={{ border: '1px solid #E2E8F0', borderRadius: '12px', padding: '14px', marginBottom: '10px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontSize: '14px', fontWeight: '600', color: '#1E293B', textAlign: 'left' }}>폐업률</div>
              <div style={{ fontSize: '11px', color: '#94A3B8', textAlign: 'left' }}>최근 1년간</div>
            </div>
            <div style={{ fontSize: '20px', fontWeight: '700', color: '#EF4444' }}>{data.closureRate}%</div>
          </div>
        </div>

        {/* 개업률 */}
        <div style={{ border: '1px solid #E2E8F0', borderRadius: '12px', padding: '14px', marginBottom: '12px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontSize: '14px', fontWeight: '600', color: '#1E293B', textAlign: 'left' }}>개업률</div>
              <div style={{ fontSize: '11px', color: '#94A3B8', textAlign: 'left' }}>최근 1년간</div>
            </div>
            <div style={{ fontSize: '20px', fontWeight: '700', color: '#1E293B' }}>{data.openRate}%</div>
          </div>
        </div>

        <button
          onClick={() => navigate('/')}
          style={{
            width: '100%', background: '#64748B', color: 'white',
            border: 'none', padding: '10px', borderRadius: '8px',
            fontSize: '13px', fontWeight: '600', cursor: 'pointer'
          }}
        >
          ← 메인 지도로 돌아가기
        </button>
      </div>

      {/* 오른쪽 메인 콘텐츠 */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <div style={{
          padding: '12px 20px', background: 'white',
          borderBottom: '1px solid #E2E8F0',
          display: 'flex', alignItems: 'center', gap: '12px'
        }}>
          <span style={{ fontSize: '15px', fontWeight: '600', color: '#1E293B' }}>대시보드 / 위험 요인 분석</span>
        </div>

        <div style={{ flex: 1, padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px', overflowY: 'auto' }}>

          {/* SHAP 기여도 차트 */}
          <div style={{ background: 'white', borderRadius: '12px', padding: '20px', border: '1px solid #E2E8F0' }}>
            <div style={{ fontSize: '16px', fontWeight: '700', color: '#1E293B', marginBottom: '16px', textAlign: 'left' }}>
              위험 요인 Top 5 (SHAP 기여도 및 실제 지표값)
            </div>
            
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={data.shapData} layout="vertical" margin={{ left: 60, right: 100, top: 5, bottom: 5 }}>
                <XAxis type="number" domain={[0, 60]} fontSize={12} hide />
                <YAxis
                  type="category"
                  dataKey="name"
                  fontSize={12}
                  width={180}
                  tick={{ fill: '#475569', fontWeight: '600' }}
                />
                <Tooltip
                  formatter={(value, name, props) => [`기여도: ${value}% (실제값: ${props.payload.actualValue})`, '요인']}
                  contentStyle={{ fontSize: '12px', borderRadius: '8px', border: '1px solid #E2E8F0' }}
                />
                <Bar dataKey="value" radius={[0, 6, 6, 0]} barSize={36}>
                  {data.shapData.map((item, i) => (
                    <Cell key={i} fill={item.color} />
                  ))}
                  <LabelList
                    dataKey="value"
                    position="right"
                    formatter={(v, entry) => `${v}% (실제: ${entry.payload?.actualValue})`}
                    style={{ fontSize: '12px', fontWeight: '700', fill: '#1E293B' }}
                  />
                </Bar>
              </BarChart>
            </ResponsiveContainer>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '16px', paddingTop: '12px', borderTop: '1px solid #F1F5F9' }}>
              <div style={{ display: 'flex', gap: '16px' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: '#64748B' }}>
                  <span style={{ width: '12px', height: '12px', background: '#EF4444', borderRadius: '3px', display: 'inline-block' }}></span>
                  위험 증가 요인 (양수)
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: '#64748B' }}>
                  <span style={{ width: '12px', height: '12px', background: '#3B82F6', borderRadius: '3px', display: 'inline-block' }}></span>
                  위험 완화 요인 (음수)
                </span>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}

export default Prediction