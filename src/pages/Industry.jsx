import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend } from 'recharts'
import Sidebar from '../components/Sidebar'

const COLORS = ['#5E81F4', '#22C55E', '#EAB308', '#EF4444', '#A855F7', '#64748B']

function Industry() {
  const { blockId } = useParams()
  const navigate = useNavigate()

  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchIndustryData = async () => {
      setLoading(true)

      // B01 등 문자열 ID 차단 -> 숫자 ID 사용
      let currentId = blockId
      if (!currentId || currentId === 'undefined' || currentId === 'null' || isNaN(Number(currentId))) {
        currentId = '5'
      }

      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080'

      try {
        const [blockRes, indRes] = await Promise.all([
          fetch(`${baseUrl}/api/v1/blocks/${currentId}`).catch(() => null),
          fetch(`${baseUrl}/api/v1/blocks/${currentId}/industry-stats`).catch(() => null)
        ])

        let blockInfo = {}
        let indInfo = []

        if (blockRes && blockRes.ok) blockInfo = await blockRes.json()
        if (indRes && indRes.ok) indInfo = await indRes.json()

        const blockName = blockInfo?.name || '상수동 카페거리'
        const mainIndustry = blockInfo?.mainIndustry || '커피-음료'

        // 백엔드 응답 배열 형식 유연 처리 및 시연용 기본 데이터 연동
        const rawList = Array.isArray(indInfo) ? indInfo : (indInfo?.industries || [])
        
        let formattedList = rawList.map(item => ({
          name: item.industryName || item.name || item.industry || '기타 업종',
          value: item.ratio ?? item.percentage ?? item.count ?? 10
        }))

        if (formattedList.length === 0) {
          formattedList = [
            { name: '커피-음료', value: 42.5 },
            { name: '한식식당', value: 24.1 },
            { name: '양식음식점', value: 15.3 },
            { name: '제과제빵', value: 10.2 },
            { name: '기타', value: 7.9 }
          ]
        }

        setData({
          blockId: currentId,
          blockName,
          mainIndustry,
          industries: formattedList
        })
      } catch (err) {
        console.error('업종 데이터 연동 예외:', err)
        setData({
          blockId: currentId,
          blockName: '상수동 카페거리',
          mainIndustry: '커피-음료',
          industries: [
            { name: '커피-음료', value: 42.5 },
            { name: '한식식당', value: 24.1 },
            { name: '양식음식점', value: 15.3 },
            { name: '기타', value: 18.1 }
          ]
        })
      } finally {
        setLoading(false)
      }
    }

    fetchIndustryData()
  }, [blockId])

  if (loading || !data) {
    return (
      <div style={{ display: 'flex', height: '100vh', justifyContent: 'center', alignItems: 'center', background: '#F5F5FA' }}>
        <p style={{ fontSize: '16px', fontWeight: '600', color: '#64748B' }}>상권 업종 데이터를 불러오는 중...</p>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', height: '100vh', background: '#F5F5FA' }}>
      <Sidebar />

      {/* 왼쪽 카드 */}
      <div style={{
        width: '320px', background: 'white',
        borderRight: '1px solid #E2E8F0',
        display: 'flex', flexDirection: 'column',
        padding: '20px', overflowY: 'auto'
      }}>
        <h2 style={{ fontSize: '20px', fontWeight: '700', marginBottom: '14px', color: '#1E293B', textAlign: 'left' }}>
          업종 비교 분석
        </h2>

        <div style={{ background: '#5E81F4', borderRadius: '12px', padding: '16px', marginBottom: '16px', color: 'white' }}>
          <div style={{ fontSize: '11px', opacity: 0.8, textAlign: 'left', marginBottom: '2px' }}>ID: {data.blockId}</div>
          <div style={{ fontSize: '17px', fontWeight: '700', marginBottom: '2px', textAlign: 'left' }}>{data.blockName}</div>
          <div style={{ fontSize: '12px', opacity: 0.9, textAlign: 'left' }}>주요 업종: {data.mainIndustry}</div>
        </div>

        <div style={{ border: '1px solid #E2E8F0', borderRadius: '12px', padding: '14px', marginBottom: '16px' }}>
          <div style={{ fontSize: '14px', fontWeight: '700', color: '#1E293B', marginBottom: '12px', textAlign: 'left' }}>
            상권 내 주요 업종 비율
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {data.industries.map((item, idx) => (
              <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                <span style={{ color: '#475569', fontWeight: '600' }}>{item.name}</span>
                <span style={{ fontWeight: '700', color: '#1E293B' }}>{item.value}%</span>
              </div>
            ))}
          </div>
        </div>

        <button
          onClick={() => navigate('/map')}
          style={{ width: '100%', background: '#64748B', color: 'white', border: 'none', padding: '10px', borderRadius: '8px', fontSize: '13px', fontWeight: '600', cursor: 'pointer' }}
        >
          ← 메인 지도로 돌아가기
        </button>
      </div>

      {/* 오른쪽 메인 업종 차트 영역 */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '12px 20px', background: 'white', borderBottom: '1px solid #E2E8F0', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '15px', fontWeight: '600', color: '#1E293B' }}>대시보드 / 상권 업종 분석</span>
        </div>

        <div style={{ flex: 1, padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px', overflowY: 'auto' }}>
          {/* 주요 업종 구성 도넛 차트 */}
          <div style={{ background: 'white', borderRadius: '12px', padding: '20px', border: '1px solid #E2E8F0' }}>
            <div style={{ fontSize: '16px', fontWeight: '700', color: '#1E293B', marginBottom: '4px', textAlign: 'left' }}>
              상권 업종 구성 및 비율
            </div>
            <div style={{ fontSize: '12px', color: '#64748B', marginBottom: '16px', textAlign: 'left' }}>
              선택한 상권 내 분포된 상위 업종 비율 현황입니다.
            </div>

            <div style={{ width: '100%', height: '300px' }}>
              <ResponsiveContainer width="100%" height="100%">
  <PieChart margin={{ top: 40, right: 20, bottom: 20, left: 20 }}>
    <Pie
      data={data.industries}
      cx="50%"
      cy="42%"
      innerRadius={65}  // 안쪽 원 크기 확대
      outerRadius={100} // 차트 원 크기를 105로 대폭 확대하여 보기 시원하게 변경
      paddingAngle={4}
      dataKey="value"
      // 선 길이를 짧게(8px) 고정하여 차트에 깔끔히 붙게 설정
      labelLine={({ cx, cy, midAngle, outerRadius }) => {
        const RADIAN = Math.PI / 180
        const sx = cx + outerRadius * Math.cos(-midAngle * RADIAN)
        const sy = cy + outerRadius * Math.sin(-midAngle * RADIAN)
        const ex = cx + (outerRadius + 8) * Math.cos(-midAngle * RADIAN)
        const ey = cy + (outerRadius + 8) * Math.sin(-midAngle * RADIAN)
        return <path d={`M${sx},${sy}L${ex},${ey}`} stroke="#94A3B8" strokeWidth={1} fill="none" />
      }}
      // 글자가 선 끝에서 살짝 떨어지도록 간격 조절
      label={({ cx, cy, midAngle, outerRadius, fill, name, value }) => {
        const RADIAN = Math.PI / 180
        const radius = outerRadius + 16
        const x = cx + radius * Math.cos(-midAngle * RADIAN)
        const y = cy + radius * Math.sin(-midAngle * RADIAN)
        const textAnchor = x > cx ? 'start' : 'end'

        return (
          <text
            x={x}
            y={y}
            fill={fill}
            textAnchor={textAnchor}
            dominantBaseline="central"
            style={{ fontSize: '11px', fontWeight: '700' }}
          >
            {`${name} (${value}%)`}
          </text>
        )
      }}
    >
      {data.industries.map((entry, index) => (
        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
      ))}
    </Pie>
    <Tooltip formatter={(value) => [`${value}%`, '비율']} />
    {/* 우측 하단 정렬 범례 */}
    <Legend
      align="right"
      verticalAlign="bottom"
      iconType="square"
      iconSize={10}
      wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }}
    />
  </PieChart>
</ResponsiveContainer>
            </div>
          </div>

          {/* 추이 및 준비중 안내 카드 */}
          <div style={{ border: '1px dashed #CBD5E1', borderRadius: '12px', padding: '30px', background: '#F8FAFC', textAlign: 'center' }}>
            <div style={{ fontSize: '24px', marginBottom: '8px' }}>📊</div>
            <div style={{ fontSize: '15px', fontWeight: '700', color: '#334155', marginBottom: '4px' }}>
              상권 업종 상세 추이 및 평균 생존기간
            </div>
            <div style={{ fontSize: '12px', color: '#94A3B8' }}>
              해당 분석 데이터는 현재 데이터 고도화 준비 중입니다.
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Industry