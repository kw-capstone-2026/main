import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ResponsiveContainer, BarChart, Bar, Cell, LabelList, XAxis, YAxis, Tooltip } from 'recharts'
import Sidebar from '../components/Sidebar'

// 단위 변환 및 포맷 함수
function formatFeatureValue(name, label, v) {
  if (v === null || v === undefined || v === '' || Number.isNaN(Number(v))) {
    return '-'
  }
  const num = Number(v)

  // 가이드라인 및 스크린샷 기준에 맞춘 포맷팅
  if (label?.includes('매출') || name?.includes('매출')) {
    if (Math.abs(num) >= 1e8) return `${(num / 1e8).toFixed(1)}억 원`
    if (Math.abs(num) >= 1e4) return `${Math.round(num / 1e4).toLocaleString('ko-KR')}만 원`
    return `${Math.round(num).toLocaleString('ko-KR')}원`
  }
  if (label?.includes('건수') || name?.includes('건수')) {
    if (Math.abs(num) >= 1e4) return `${(num / 1e4).toFixed(1)}만 건`
    return `${Math.round(num).toLocaleString('ko-KR')}건`
  }
  if (label?.includes('폐업') || label?.includes('증감') || name?.includes('증감')) {
    let t = Math.abs(num).toFixed(2)
    if (t.endsWith('0')) t = t.slice(0, -1)
    return (num < 0 ? '−' : '') + t
  }
  if (label?.includes('비율') || label?.includes('적합도') || label?.includes('폐업률')) {
    return `${(num < 1 ? num * 100 : num).toFixed(1)}%` // 깨진 오타 수정
  }
  if (label?.includes('개월') || name?.includes('개월')) {
    return `${Math.round(num)}개월`
  }
  if (label?.includes('밀도')) {
    return `점포 100개당 ${(num * 100).toFixed(1)}개` // 깨진 오타 수정
  }

  return num >= 1e4 ? num.toLocaleString('ko-KR', { maximumFractionDigits: 1 }) : String(num)
}

const getGradeStyle = (grade, score) => {
  if (score >= 75 || grade === '위험') return { color: '#EF4444', bg: '#FEE2E2' }
  if (score >= 50 || grade === '주의') return { color: '#EAB308', bg: '#FEF9C3' }
  return { color: '#22C55E', bg: '#DCFCE7' }
}

function Prediction() {
  const { blockId } = useParams()
  const navigate = useNavigate()

  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let isMounted = true 

    const fetchPredictionData = async () => {
      setLoading(true)
      
      let currentId = blockId
      if (!currentId || currentId === 'undefined' || currentId === 'null') {
        currentId = localStorage.getItem('selectedBlockId') || '828'
      }

      const baseUrl = 'http://localhost:8080'

      try {
        const [blockRes, predRes, shapRes] = await Promise.all([
          fetch(`${baseUrl}/api/v1/blocks/${currentId}`).catch(() => null),
          fetch(`${baseUrl}/api/v1/blocks/${currentId}/prediction`).catch(() => null),
          fetch(`${baseUrl}/api/v1/blocks/${currentId}/shap`).catch(() => null)
        ])

        let blockInfo = {}
        let predInfo = {}
        let shapInfo = { features: [] }

        if (blockRes && blockRes.ok) blockInfo = await blockRes.json()
        if (predRes && predRes.ok) predInfo = await predRes.json()
        if (shapRes && shapRes.ok) shapInfo = await shapRes.json()

        let defaultName = '경리단길 북측'
        let defaultScore = 80
        let defaultGrade = '위험'
        let defaultIndustry = '커피-음료'

        const strId = String(currentId)
        if (strId === '13982') {
          defaultName = '연남동(홍대)'
          defaultScore = 57
          defaultGrade = '주의'
        } else if (strId === '12396') {
          defaultName = '성수역'
          defaultScore = 19
          defaultGrade = '안전'
        }

        const blockName = defaultName
        const industry = blockInfo?.mainIndustry || defaultIndustry
        const riskScore = predInfo?.riskScore ?? predInfo?.risk_score ?? blockInfo?.riskScore ?? defaultScore
        const riskGrade = predInfo?.riskGrade || predInfo?.risk_grade || blockInfo?.riskGrade || defaultGrade
        const closureRate = predInfo?.closureRate ?? predInfo?.closure_rate ?? 6.5
        const openRate = predInfo?.openRate ?? predInfo?.open_rate ?? 8.8

        const gradeStyle = getGradeStyle(riskGrade, riskScore)
        const rawFeatures = shapInfo?.features || (Array.isArray(shapInfo) ? shapInfo : [])

        const formattedShap = rawFeatures.map((item, idx) => {
          const displayName = item?.label || item?.name || `지표 ${idx + 1}`
          const rawName = item?.name || ''
          
          const rawVal = item?.shapValue ?? item?.shap_value ?? item?.value ?? 0
          const val = !isNaN(Number(rawVal)) ? Number(Number(rawVal).toFixed(3)) : 0
          const valStr = val > 0 ? `+${val}` : `${val}` // 기여도 문자열 (+ 부호 포함)

          // 백엔드가 주는 featureValue를 확실하게 추출 후 포맷팅
          const rawActualVal = item?.featureValue ?? item?.feature_value ?? item?.actualValue ?? 0
          const formattedActual = formatFeatureValue(rawName, displayName, rawActualVal)
          
          // 🔥 차트 오류 원천 차단: 렌더링할 텍스트 전체를 여기서 완벽히 조립
          const displayLabel = `${valStr} (실제: ${formattedActual})`

          return {
            rank: item?.rank || (idx + 1),
            name: displayName,
            value: val,
            absVal: Math.abs(val) > 0.01 ? Math.abs(val) : 0.05,
            actualValue: formattedActual,
            displayLabel: displayLabel, // 조립된 텍스트
            color: val >= 0 ? '#EF4444' : '#3B82F6'
          }
        })

        if (isMounted) {
          setData({
            blockId: currentId,
            blockName,
            industry,
            closureRate,
            openRate,
            riskScore,
            riskGrade,
            riskColor: gradeStyle.color,
            badgeBg: gradeStyle.bg,
            shapData: formattedShap
          })
        }
      } catch (err) {
        console.error('API 연동 예외 발생:', err)
      } finally {
        if (isMounted) {
          setLoading(false)
        }
      }
    }

    fetchPredictionData()

    return () => {
      isMounted = false
    }
  }, [blockId])

  if (loading || !data) {
    return (
      <div style={{ display: 'flex', height: '100vh', justifyContent: 'center', alignItems: 'center', background: '#F5F5FA' }}>
        <p style={{ fontSize: '16px', fontWeight: '600', color: '#64748B' }}>예측 및 SHAP 데이터를 불러오는 중...</p>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', height: '100vh', background: '#F5F5FA' }}>
      <Sidebar />

      <div style={{
        width: '320px', background: 'white',
        borderRight: '1px solid #E2E8F0',
        display: 'flex', flexDirection: 'column',
        padding: '20px', overflowY: 'auto'
      }}>
        <h2 style={{ fontSize: '20px', fontWeight: '700', marginBottom: '14px', color: '#1E293B', textAlign: 'left' }}>
          상권 과포화 위험 진단
        </h2>

        <div style={{ background: '#5E81F4', borderRadius: '12px', padding: '16px', marginBottom: '12px', color: 'white' }}>
          <div style={{ fontSize: '11px', opacity: 0.8, textAlign: 'left', marginBottom: '2px' }}>ID: {data.blockId}</div>
          <div style={{ fontSize: '17px', fontWeight: '700', marginBottom: '2px', textAlign: 'left' }}>{data.blockName}</div>
          <div style={{ fontSize: '12px', opacity: 0.9, textAlign: 'left' }}>업종: {data.industry}</div>
        </div>

        <div style={{ border: '1px solid #E2E8F0', borderRadius: '12px', padding: '14px', marginBottom: '10px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ fontSize: '14px', fontWeight: '600', color: '#1E293B', textAlign: 'left' }}>위험도 등급</div>
            <div style={{ background: data.badgeBg, color: data.riskColor, fontWeight: '700', padding: '6px 16px', borderRadius: '8px', fontSize: '18px' }}>
              {data.riskGrade}
            </div>
          </div>
        </div>

        <div style={{ border: '1px solid #E2E8F0', borderRadius: '12px', padding: '14px', marginBottom: '10px' }}>
          <div style={{ fontSize: '14px', fontWeight: '600', color: '#1E293B', marginBottom: '4px', textAlign: 'left' }}>위험 점수 (Risk Score)</div>
          <div style={{ fontSize: '26px', fontWeight: '700', color: data.riskColor, marginBottom: '4px', textAlign: 'left' }}>
            {data.riskScore}<span style={{ fontSize: '13px', color: '#94A3B8' }}>/100</span>
          </div>
          <div style={{ background: '#F1F5F9', borderRadius: '4px', height: '6px' }}>
            <div style={{ background: data.riskColor, width: `${Math.min(Number(data.riskScore) || 0, 100)}%`, height: '100%', borderRadius: '4px' }}></div>
          </div>
        </div>

        <div style={{ border: '1px solid #E2E8F0', borderRadius: '12px', padding: '14px', marginBottom: '10px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontSize: '14px', fontWeight: '600', color: '#1E293B', textAlign: 'left' }}>폐업률</div>
              <div style={{ fontSize: '11px', color: '#94A3B8', textAlign: 'left' }}>해당 분기</div>
            </div>
            <div style={{ fontSize: '20px', fontWeight: '700', color: '#EF4444' }}>{data.closureRate}%</div>
          </div>
        </div>

        <div style={{ border: '1px solid #E2E8F0', borderRadius: '12px', padding: '14px', marginBottom: '12px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontSize: '14px', fontWeight: '600', color: '#1E293B', textAlign: 'left' }}>개업률</div>
              <div style={{ fontSize: '11px', color: '#94A3B8', textAlign: 'left' }}>해당 분기</div>
            </div>
            <div style={{ fontSize: '20px', fontWeight: '700', color: '#1E293B' }}>{data.openRate}%</div>
          </div>
        </div>

        <button
          onClick={() => navigate('/map')}
          style={{ width: '100%', background: '#64748B', color: 'white', border: 'none', padding: '10px', borderRadius: '8px', fontSize: '13px', fontWeight: '600', cursor: 'pointer' }}
        >
          ← 메인 지도로 돌아가기
        </button>
      </div>

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '12px 20px', background: 'white', borderBottom: '1px solid #E2E8F0', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '15px', fontWeight: '600', color: '#1E293B' }}>대시보드 / 위험 요인 분석</span>
        </div>

        <div style={{ flex: 1, padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px', overflowY: 'auto' }}>
          <div style={{ background: 'white', borderRadius: '12px', padding: '20px', border: '1px solid #E2E8F0' }}>
            <div style={{ fontSize: '16px', fontWeight: '700', color: '#1E293B', marginBottom: '16px', textAlign: 'left' }}>
              위험 요인 Top 5 (SHAP 기여도 및 실제 지표값)
            </div>
            
            {data.shapData && data.shapData.length > 0 ? (
              <div style={{ width: '100%', height: '320px' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.shapData} layout="vertical" margin={{ left: 10, right: 220, top: 10, bottom: 10 }}>
                    <XAxis type="number" fontSize={12} hide />
                    <YAxis type="category" dataKey="name" fontSize={12} width={230} tick={{ fill: '#475569', fontWeight: '600' }} />
                    <Tooltip
                      formatter={(value, name, props) => {
                        // 미리 만들어둔 displayLabel을 통째로 띄웁니다
                        const rawPayload = Array.isArray(props?.payload) ? props.payload[0]?.payload : props?.payload;
                        const itemData = rawPayload || props || {};
                        const labelStr = itemData.displayLabel || `${value > 0 ? '+' : ''}${value}`;
                        return [labelStr, '요인']
                      }}
                      contentStyle={{ fontSize: '12px', borderRadius: '8px', border: '1px solid #E2E8F0' }}
                    />
                    <Bar 
                      dataKey="absVal" 
                      radius={[0, 6, 6, 0]} 
                      barSize={32}
                      isAnimationActive={false}
                    >
                      {data.shapData.map((item, i) => (
                        <Cell key={i} fill={item.color} />
                      ))}
                      {/* 🔥 Recharts 버그 방지: formatter 없이 dataKey로 바로 꽂습니다 */}
                      <LabelList
                        dataKey="displayLabel"
                        position="right"
                        style={{ fontSize: '11px', fontWeight: '700', fill: '#1E293B' }}
                      />
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div style={{ padding: '60px 20px', textAlign: 'center', color: '#94A3B8', fontSize: '14px' }}>
                SHAP 분석 데이터가 준비 중입니다.
              </div>
            )}

            <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid #F1F5F9' }}>
              <div style={{ display: 'flex', gap: '16px', marginBottom: '14px' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: '#64748B' }}>
                  <span style={{ width: '12px', height: '12px', background: '#EF4444', borderRadius: '3px', display: 'inline-block' }}></span>
                  위험 증가 요인 (+ SHAP)
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: '#64748B' }}>
                  <span style={{ width: '12px', height: '12px', background: '#3B82F6', borderRadius: '3px', display: 'inline-block' }}></span>
                  위험 완화 요인 (- SHAP)
                </span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {data.shapData.map((item, idx) => (
                  <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', background: '#F8FAFC', borderRadius: '6px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontSize: '12px', fontWeight: '700', color: '#94A3B8' }}>{item.rank}위</span>
                      <span style={{ fontSize: '13px', fontWeight: '600', color: '#334155' }}>{item.name}</span>
                      <span style={{ fontSize: '12px', color: '#64748B', background: '#E2E8F0', padding: '2px 8px', borderRadius: '4px' }}>
                        실제값: {item.actualValue}
                      </span>
                    </div>
                    <span style={{ fontSize: '13px', fontWeight: '700', color: item.color }}>
                      {item.value > 0 ? `+${item.value}` : item.value}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Prediction