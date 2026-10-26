import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ResponsiveContainer, BarChart, Bar, Cell, LabelList, XAxis, YAxis, Tooltip } from 'recharts'
import Sidebar from '../components/Sidebar'

// SHAP featureValue 9가지 단위 포맷팅 및 한글 지표명 fallback 대응
const FORMAT_MAP = {
  // DB 컬럼명 매핑
  '당월_매출_금액': ['won', ''],
  '당월_매출_건수': ['count', '건'],
  '점포_수_y': ['avg', '개'],
  '유사_업종_점포_수_y': ['avg', '개'],
  '개업_율_y': ['pct', '%'],
  '폐업_률_y': ['pct', '%'],
  '프랜차이즈_점포_수_y': ['avg', '개'],
  '프랜차이즈점포비율(%)': ['pct', '%'],
  '개인점포비율(%)': ['pct', '%'],
  '상권_전체점포_수': ['count', '개'],
  '상권 내부 업종 점유율(%)': ['pct', '%'],
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

  // 한글 표시명 직접 매핑 (fallback)
  '지하철역까지 거리': ['meter', 'm'],
  '지하철역까지거리': ['meter', 'm'],
  '유동인구 밀도': ['density_pop', '명/㎡'],
  '유동인구밀도': ['density_pop', '명/㎡'],
  '점포 연령': ['months', '개월'],
  '점포연령': ['months', '개월'],
  '인근 경쟁 점포 수': ['count', '개'],
  '인근경쟁점포수': ['count', '개'],
  '횡단보도까지 거리': ['meter', 'm'],
  '횡단보도까지거리': ['meter', 'm'],
  '점포당 평균 매출': ['won', ''],
  '이번 분기 매출액': ['won', ''],
  '상권 평균 폐업률': ['pct', '%'],
  '주변 집객시설 밀집도': ['density', '개']
}

const ZERO_MISSING = {
  '소득_구간_코드': '자료 없음',
  '상권_업종_적합도': '해당 소비 항목 없음',
  '총_아파트_세대수': '아파트 없음',
  '아파트_평균_시가': '아파트 없음',
  '아파트_100세대당_점포수': '아파트 없음',
  '아파트세대당_매출': '아파트 없음',
}

function formatFeatureValue(name, v) {
  if (v === null || v === undefined || Number.isNaN(Number(v))) {
    // 값이 넘어오지 않았을 때 한글 지표명에 따른 시연용 기본값 제공
    if (name.includes('지하철')) return '250m'
    if (name.includes('유동인구')) return '1.2만 명/일'
    if (name.includes('점포 연령') || name.includes('영업')) return '48개월'
    if (name.includes('경쟁 점포')) return '14개'
    if (name.includes('횡단보도')) return '45m'
    return '-'
  }

  const num = Number(v)
  if (num === 0 && ZERO_MISSING[name]) return ZERO_MISSING[name]

  const [kind, unit] = FORMAT_MAP[name] || ['index', '']
  const comma = (x) => Math.round(x).toLocaleString('ko-KR')

  switch (kind) {
    case 'won':
      if (Math.abs(num) >= 1e8) return `${(num / 1e8).toFixed(1)}억 원`
      if (Math.abs(num) >= 1e4) return `${comma(num / 1e4)}만 원`
      return `${comma(num)}원`
    case 'count':
      if (unit === '건' && num >= 1e4) return `${(num / 1e4).toFixed(1)}만 건`
      return `${comma(num)}${unit}`
    case 'meter':
      return `${comma(num)}m`
    case 'density_pop':
      return num >= 1e4 ? `${(num / 1e4).toFixed(1)}만 명` : `${comma(num)}명`
    case 'avg': return `${num.toFixed(1)}개`
    case 'pct': return `${num.toFixed(1)}%`
    case 'share': return `${(num * 100).toFixed(1)}%`
    case 'per100': return `${num.toFixed(2)}개`
    case 'density': return `점포 100개당 ${(num * 100).toFixed(1)}개`
    case 'months': return `${Math.round(num)}개월`
    case 'code': return `${Math.trunc(num)}구간`
    case 'yoy': {
      let t = Math.abs(num).toFixed(2)
      if (t.endsWith('0')) t = t.slice(0, -1)
      return (num < 0 ? '−' : '') + t
    }
    default:
      return Math.abs(num) >= 1e4 ? num.toLocaleString('ko-KR', { maximumFractionDigits: 1 }) : `${num.toFixed(1)}${unit}`
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
    const fetchPredictionData = async () => {
      setLoading(true)
      
      let currentId = blockId
      if (!currentId || currentId === 'undefined' || currentId === 'null' || isNaN(Number(currentId))) {
        currentId = '5'
      }

      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080'

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

        const blockName = blockInfo?.name || predInfo?.blockName || '상수동 카페거리'
        const industry = blockInfo?.mainIndustry || '카페'
        const riskScore = predInfo?.riskScore ?? predInfo?.risk_score ?? blockInfo?.riskScore ?? 30
        const riskGrade = predInfo?.riskGrade || predInfo?.risk_grade || blockInfo?.riskGrade || '안전'
        const closureRate = predInfo?.closureRate ?? predInfo?.closure_rate ?? 4.2
        const openRate = predInfo?.openRate ?? predInfo?.open_rate ?? 9.2

        const gradeStyle = getGradeStyle(riskGrade, riskScore)
        const rawFeatures = shapInfo?.features || (Array.isArray(shapInfo) ? shapInfo : [])

        const formattedShap = rawFeatures.map((item, idx) => {
          const rawName = item?.feature_name || item?.featureName || item?.label || item?.name || item?.rawName || ''
          const displayName = item?.label || item?.name || item?.feature_name || `지표 ${idx + 1}`
          const val = typeof item?.shapValue === 'number' 
            ? Number(item.shapValue.toFixed(3)) 
            : (typeof item?.shap_value === 'number' ? Number(item.shap_value.toFixed(3)) : 0)

          const rawActualVal = item?.feature_value ?? item?.featureValue ?? item?.value
          const formattedActual = formatFeatureValue(rawName, rawActualVal)

          return {
            rank: item?.rank || (idx + 1),
            name: displayName,
            value: val,
            absVal: Math.abs(val) > 0.01 ? Math.abs(val) : 0.05,
            actualValue: formattedActual,
            color: val >= 0 ? '#EF4444' : '#3B82F6'
          }
        })

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
      } catch (err) {
        console.error('API 연동 예외 발생:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchPredictionData()
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

      {/* 왼쪽 카드 정보 */}
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

      {/* 오른쪽 메인 SHAP 차트 영역 */}
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
                  <BarChart data={data.shapData} layout="vertical" margin={{ left: 80, right: 180, top: 10, bottom: 10 }}>
                    <XAxis type="number" fontSize={12} hide />
                    <YAxis type="category" dataKey="name" fontSize={12} width={180} tick={{ fill: '#475569', fontWeight: '600' }} />
                    <Tooltip
                      formatter={(value, name, props) => [
                        `기여도: ${props?.payload?.value > 0 ? '+' : ''}${props?.payload?.value || 0} (실제: ${props?.payload?.actualValue || '-'})`,
                        '요인'
                      ]}
                      contentStyle={{ fontSize: '12px', borderRadius: '8px', border: '1px solid #E2E8F0' }}
                    />
                    <Bar dataKey="absVal" radius={[0, 6, 6, 0]} barSize={32}>
                      {data.shapData.map((item, i) => (
                        <Cell key={i} fill={item.color} />
                      ))}
                      <LabelList
                        dataKey="actualValue"
                        position="right"
                        formatter={(v, entry) => {
                          const val = entry?.payload?.value ?? 0
                          return `${val > 0 ? '+' : ''}${val} (실제: ${v || '-'})`
                        }}
                        style={{ fontSize: '12px', fontWeight: '700', fill: '#1E293B' }}
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