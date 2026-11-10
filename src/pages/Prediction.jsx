import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ResponsiveContainer, BarChart, Bar, Cell, LabelList, XAxis, YAxis, Tooltip } from 'recharts'
import Sidebar from '../components/Sidebar'

const FORMAT = {
  '당월_매출_금액': ['won', ''],
  '당월_매출_건수': ['count', '건'],
  '점포_수_y': ['avg', '개'],
  '유사_업종_점포_수_y': ['avg', '개'],
  '개업_률_y': ['pct', '%'],
  '폐업_률_y': ['pct', '%'],
  '프랜차이즈_점포_수_y': ['avg', '개'],
  '프랜차이즈점포비율(%)': ['pct', '%'],
  '개인점포비율(%)': ['pct', '%'],
  '상권_전체점포_수': ['count', '개'],
  '상권 내부 업종 점유율(%)': ['pct', '%'],
  '상권_내부_업종_점유율(%)': ['pct', '%'],
  '운영_영업_개월_평균': ['months', '개월'],
  '폐업_영업_개월_평균': ['months', '개월'],
  '유효_수요_전환율': ['index', ''],
  '점포당_평균_매출': ['won', ''],
  '전년_동기_대비_폐업_증감률': ['yoy', ''],
  '소득_구간_코드': ['code', '구간'],
  '상권_업종_적합도': ['share', '%'],
  '총_아파트_세대수': ['count', '세대'],
  '아파트_평균_시가': ['won', ''],
  '총_직장_인구_수': ['count', '명'],
  '남성_직장_인구_수': ['count', '명'],
  '여성_직장_인구_수': ['count', '명'],
  '직장인구_100명당_점포수': ['per100', '개'],
  '아파트_100세대당_점포수': ['per100', '개'],
  '유사업종_점포비율': ['pct', '%'],
  '직장인구_100명당_유사업종수': ['per100', '개'],
  '점포당_매출_밀도': ['won', ''],
  '직장인구_1인당_매출': ['won', ''],
  '아파트세대당_매출': ['won', ''],
  '집객시설_수': ['count', '개'],
  '집객시설_밀도': ['density', '개'],
}

const ZERO_MISSING = {
  '소득_구간_코드': '자료 없음',
  '상권_업종_적합도': '해당 소비 항목 없음',
  '총_아파트_세대수': '아파트 없음',
  '아파트_평균_시가': '아파트 없음',
  '아파트_100세대당_점포수': '아파트 없음',
  '아파트세대당_매출': '아파트 없음',
}

const LABEL_TO_NAME = {
  '작년 같은 분기 대비 폐업 증감': '전년_동기_대비_폐업_증감률',
  '점포당 평균 매출': '점포당_평균_매출',
  '이번 분기 매출액': '당월_매출_금액',
  '이번 분기 결제 건수': '당월_매출_건수',
  '상권 평균 폐업률': '폐업_률_y',
  '주변 집객시설 밀집도': '집객시설_밀도',
  '상권 운영 점포 평균 영업기간': '운영_영업_개월_평균',
  '업종·상권 적합도': '상권_업종_적합도',
  '평균 점포 수 대비 매출': '점포당_매출_밀도',
}

const GRADE_DESCRIPTIONS = {
  '위험': '위험 등급은 실제 과포화 비율이 평균의 약 10배인 구간입니다. 최근 개폐업 흐름과 매출 추이를 먼저 확인해 보시길 권합니다.',
  '주의': '주의 등급은 실제 과포화 비율이 평균의 약 2배인 구간입니다. 다음 분기 흐름을 함께 지켜볼 필요가 있습니다.',
  '안전': '안전 등급은 실제 과포화 비율이 평균보다 낮은 구간입니다. 다만 이번 분기 기준 진단이라 흐름은 바뀔 수 있습니다.',
}

function getFeaturePhrase(featureKey, shapVal, rawValue, displayName) {
  const numVal = Number(rawValue) || 0
  const labelText = displayName || featureKey || '해당 지표'

  if (shapVal > 0) {
    switch (featureKey) {
      case '전년_동기_대비_폐업_증감률': return '작년 같은 분기보다 폐업이 늘어난 것'
      case '점포당_평균_매출': return '점포당 평균 매출이 낮은 것'
      case '폐업_률_y': return '상권 평균 폐업률이 높은 것'
      case '당월_매출_금액': return '이번 분기 매출 규모가 큰 것'
      case '당월_매출_건수': return '이번 분기 결제 건수가 적은 것'
      case '운영_영업_개월_평균': return '상권 점포들의 평균 영업기간이 짧은 것'
      case '집객시설_밀도': return '주변 집객시설이 적은 것'
      default: return `${labelText} 수준`
    }
  } else {
    switch (featureKey) {
      case '전년_동기_대비_폐업_증감률':
        if (numVal < 0) return '작년 같은 분기보다 폐업이 줄어든 것'
        if (numVal === 0) return '작년 같은 분기보다 폐업이 늘지 않은 것'
        return '작년 같은 분기보다 폐업 증가 폭이 작은 것'
      case '점포당_평균_매출': return '점포당 평균 매출이 높은 것'
      case '폐업_률_y': return '상권 평균 폐업률이 낮은 것'
      case '당월_매출_금액': return '이번 분기 매출 규모가 작은 것'
      case '당월_매출_건수': return '이번 분기 결제 건수가 많은 것'
      case '운영_영업_개월_평균': return '상권 점포들의 평균 영업기간이 긴 것'
      case '집객시설_밀도': return '주변 집객시설이 많은 것'
      default: return `${labelText} 수준`
    }
  }
}

function generateShapSummary(shapData, riskGrade) {
  if (!Array.isArray(shapData) || shapData.length < 2) {
    return { line1: '', line2: '' }
  }

  const sorted = [...shapData].sort((a, b) => Math.abs(b?.value || 0) - Math.abs(a?.value || 0))
  const top1 = sorted[0]
  const top2 = sorted[1]

  if (!top1 || !top2) return { line1: '', line2: '' }

  const key1 = top1.rawName || LABEL_TO_NAME[top1.name] || top1.name || ''
  const key2 = top2.rawName || LABEL_TO_NAME[top2.name] || top2.name || ''

  const phrase1 = getFeaturePhrase(key1, top1.value || 0, top1.rawActualVal, top1.name)
  const dir1 = (top1.value || 0) > 0 ? '높였' : '낮췄'

  const phrase2 = getFeaturePhrase(key2, top2.value || 0, top2.rawActualVal, top2.name)
  const isSameDir = ((top1.value || 0) > 0 && (top2.value || 0) > 0) || ((top1.value || 0) < 0 && (top2.value || 0) < 0)
  const josa2 = isSameDir ? '도' : '은'
  const dir2 = (top2.value || 0) > 0 ? '높였습니다' : '낮췄습니다'

  const line1 = `${phrase1}이 위험을 가장 크게 ${dir1}고, ${phrase2}${josa2} 위험을 ${dir2}.`
  const line2 = GRADE_DESCRIPTIONS[riskGrade] || GRADE_DESCRIPTIONS['안전']

  return { line1, line2 }
}

function formatFeatureValue(name, label, v) {
  if (v === null || v === undefined || v === '' || Number.isNaN(Number(v))) {
    return '-'
  }

  const num = Number(v)
  const featureKey = name || LABEL_TO_NAME[label] || label

  if (num === 0 && ZERO_MISSING[featureKey]) {
    return ZERO_MISSING[featureKey]
  }

  const [kind, unit] = FORMAT[featureKey] || ['index', '']
  const comma = (x) => Math.round(x).toLocaleString('ko-KR')

  switch (kind) {
    case 'won':
      if (Math.abs(num) >= 1e8) return `${(num / 1e8).toFixed(1)}억 원`
      if (Math.abs(num) >= 1e4) return `${comma(num / 1e4)}만 원`
      return `${comma(num)}원`

    case 'count':
      if (unit === '건' && Math.abs(num) >= 1e4) return `${(num / 1e4).toFixed(1)}만 건`
      return `${comma(num)}${unit}`

    case 'avg':
      return `${num.toFixed(1)}개`

    case 'pct':
      return `${num.toFixed(1)}%`

    case 'share':
      return `${(num * 100).toFixed(1)}%`

    case 'per100':
      return `${num.toFixed(2)}개`

    case 'density':
      return `점포 100개당 ${(num * 100).toFixed(1)}개`

    case 'months':
      return `${Math.round(num)}개월`

    case 'code':
      return `${Math.trunc(num)}구간`

    case 'yoy': {
      let t = Math.abs(num).toFixed(2)
      if (t.endsWith('0')) t = t.slice(0, -1)
      return (num < 0 ? '−' : '') + t
    }

    default:
      if (label?.includes('폐업률')) return `${num.toFixed(1)}%`
      if (label?.includes('집객시설') || label?.includes('밀집도')) {
        return `점포 100개당 ${(num < 1 ? num * 100 : num).toFixed(1)}개`
      }
      if (label?.includes('건수')) {
        return Math.abs(num) >= 1e4 ? `${(num / 1e4).toFixed(1)}만 건` : `${comma(num)}건`
      }
      if (label?.includes('매출')) {
        return Math.abs(num) >= 1e8 ? `${(num / 1e8).toFixed(1)}억 원` : `${comma(num / 1e4)}만 원`
      }

      return Math.abs(num) >= 1e4 ? num.toLocaleString('ko-KR', { maximumFractionDigits: 1 }) : num.toFixed(1)
  }
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
          const displayName = item?.label || item?.displayName || item?.name || `지표 ${idx + 1}`
          const rawName = item?.name || item?.feature_name || item?.feature || ''
          
          const rawVal = item?.shapValue ?? item?.shap_value ?? item?.value ?? 0
          const val = !isNaN(Number(rawVal)) ? Number(Number(rawVal).toFixed(3)) : 0
          const valStr = val > 0 ? `+${val}` : `${val}`

          const rawActualVal = item?.featureValue ?? item?.feature_value ?? item?.actualValue ?? item?.actual_value ?? item?.value_raw ?? 0
          const formattedActual = formatFeatureValue(rawName, displayName, rawActualVal)
          
          const displayLabel = `${valStr} (실제: ${formattedActual})`

          return {
            rank: item?.rank || (idx + 1),
            name: displayName,
            rawName: rawName,
            value: val,
            rawActualVal: rawActualVal,
            absVal: Math.abs(val) > 0.01 ? Math.abs(val) : 0.05,
            actualValue: formattedActual,
            displayLabel: displayLabel,
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

  const summaryTexts = generateShapSummary(data.shapData, data.riskGrade)

  return (
    <div style={{ display: 'flex', height: '100vh', background: '#F5F5FA' }}>
      <Sidebar />

      <div style={{
        width: '320px',
        background: 'white',
        borderRight: '1px solid #E2E8F0',
        display: 'flex',
        flexDirection: 'column',
        padding: '20px',
        overflowY: 'auto'
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
                        const rawPayload = Array.isArray(props?.payload) ? props.payload[0]?.payload : props?.payload
                        const itemData = rawPayload || props || {}
                        const labelStr = itemData.displayLabel || `${value > 0 ? '+' : ''}${value}`
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

            {summaryTexts.line1 && (
              <div style={{
                marginTop: '16px',
                padding: '14px 16px',
                backgroundColor: '#F8FAFC',
                borderRadius: '8px',
                border: '1px solid #E2E8F0',
                textAlign: 'left'
              }}>
                <div style={{ fontSize: '13px', fontWeight: '700', color: '#1E293B', marginBottom: '4px', lineHeight: '1.5' }}>
                  {summaryTexts.line1}
                </div>
                <div style={{ fontSize: '12px', color: '#64748B', lineHeight: '1.5' }}>
                  {summaryTexts.line2}
                </div>
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