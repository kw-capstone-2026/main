import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom' // react-router-dom으로 변경
import { PieChart, Pie, Cell } from 'recharts'
import Sidebar from '../components/Sidebar'

// 위험도 3단계 색상 매핑 (안전 / 주의 / 위험)
const getGradeStyle = (grade) => {
  switch (grade) {
    case '안전':
      return { color: '#22C55E', bg: '#DCFCE7' }
    case '주의':
      return { color: '#EAB308', bg: '#FEF9C3' }
    case '위험':
      return { color: '#EF4444', bg: '#FEE2E2' }
    default:
      return { color: '#EAB308', bg: '#FEF9C3' }
  }
}

function Industry() {
  const { blockId } = useParams()
  const navigate = useNavigate()

  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchIndustryData = async () => {
      setLoading(true)
      let resData = null

      try {
        const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080'
        const response = await fetch(`${baseUrl}/api/v1/blocks/${blockId}/industry`)
        if (response.ok) {
          resData = await response.json()
        }
      } catch (err) {
        console.warn('API 연결 실패: 시연용 업종 비율 데이터를 표시합니다.')
      }

      // API 미연동 시 기본 Fallback 데이터
      if (!resData) {
        resData = {
          blockId: blockId || 'B01',
          blockName: blockId === 'B02' ? '경리단길북측' : blockId === 'B03' ? '성수역' : '연남동(홍대)',
          riskGrade: '주의',
          industryStats: [
            { name: '커피-음료', count: 35, color: '#FFAF53' },
            { name: '한식식당', count: 80, color: '#FF808B' },
            { name: '편의점', count: 45, color: '#8AF1B9' },
            { name: '주점', count: 25, color: '#F4BE5E' },
          ]
        }
      }

      const currentGrade = resData.riskGrade || resData.risk_grade || '주의'
      const gradeStyle = getGradeStyle(currentGrade)

      setData({
        blockId: resData.blockId || resData.block_id || blockId,
        blockName: resData.blockName || resData.block_name || '상권 정보',
        riskGrade: currentGrade,
        riskColor: gradeStyle.color,
        badgeBg: gradeStyle.bg,
        industryStats: resData.industryStats || resData.industry_stats || [
          { name: '커피-음료', count: 35, color: '#FFAF53' },
          { name: '한식식당', count: 80, color: '#FF808B' },
          { name: '편의점', count: 45, color: '#8AF1B9' },
          { name: '주점', count: 25, color: '#F4BE5E' },
        ]
      })
      setLoading(false)
    }

    if (blockId) {
      fetchIndustryData()
    }
  }, [blockId])

  if (loading || !data) {
    return (
      <div style={{ display: 'flex', height: '100vh', justifyContent: 'center', alignItems: 'center', background: '#F8F9FA' }}>
        <p style={{ fontSize: '16px', fontWeight: '600', color: '#64748B' }}>업종 비교 데이터를 불러오는 중...</p>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', height: '100vh', background: '#F8F9FA' }}>
      <Sidebar />

      {/* 왼쪽 사이드바 */}
      <div style={{
        width: '300px', background: 'white',
        borderRight: '1px solid #E2E8F0',
        display: 'flex', flexDirection: 'column',
        padding: '20px', overflowY: 'auto'
      }}>
        <h2 style={{ fontSize: '20px', fontWeight: '700', marginBottom: '16px', color: '#1E293B', textAlign: 'left' }}>
          업종 비교
        </h2>

        {/* 상권 카드 (요구사항 1 & 2: risk_grade 안전/주의/위험 반영) */}
        <div style={{
          background: '#5E81F4', borderRadius: '12px',
          padding: '16px', marginBottom: '16px', color: 'white'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontSize: '13px', fontWeight: '700', textAlign: 'left', marginBottom: '2px' }}>{data.blockId}</div>
              <div style={{ fontSize: '18px', fontWeight: '700', marginBottom: '2px', textAlign: 'left' }}>{data.blockName}</div>
            </div>
            <div style={{
              background: data.badgeBg,
              color: data.riskColor,
              fontWeight: '700',
              padding: '4px 12px',
              borderRadius: '6px',
              fontSize: '14px'
            }}>
              {data.riskGrade}
            </div>
          </div>
        </div>

        {/* 업종 비율 차트 카드 */}
        <div style={{ border: '1px solid #E2E8F0', borderRadius: '12px', padding: '16px', background: 'white' }}>
          <div style={{ fontSize: '14px', fontWeight: '600', color: '#1E293B', marginBottom: '12px', textAlign: 'left' }}>
            상권 내 업종 비율
          </div>
          <div style={{ display: 'flex', justifyContent: 'center' }}>
            <PieChart width={220} height={180}>
              <Pie data={data.industryStats} dataKey="count" cx="50%" cy="50%" innerRadius={50} outerRadius={75}>
                {data.industryStats.map((item, i) => (
                  <Cell key={i} fill={item.color} />
                ))}
              </Pie>
            </PieChart>
          </div>
          <div style={{ marginTop: '12px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {data.industryStats.map((item, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', padding: '4px 0', borderBottom: '1px solid #F8FAFC' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: '500' }}>
                  <span style={{ width: '8px', height: '8px', background: item.color, borderRadius: '50%', display: 'inline-block' }}></span>
                  {item.name}
                </span>
                <span style={{ color: '#64748B', fontWeight: '600' }}>{item.count}개</span>
              </div>
            ))}
          </div>
        </div>

        {/* 메인 지도로 돌아가기 */}
        <div style={{ marginTop: 'auto', paddingTop: '20px' }}>
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
      </div>

      {/* 오른쪽 메인 콘텐츠 (요구사항 7: 데이터 없는 생존기간/월별경쟁점포 그래프 전면 숨김) */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', background: '#F5F5FA' }}>
        <div style={{
          padding: '12px 20px', background: 'white',
          borderBottom: '1px solid #E2E8F0',
          display: 'flex', alignItems: 'center', gap: '12px'
        }}>
          <span style={{ fontSize: '15px', fontWeight: '600', color: '#1E293B' }}>대시보드 / 상권 업종 분석</span>
        </div>

        <div style={{ flex: 1, padding: '24px', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          <div style={{
            background: 'white', border: '1px solid #E2E8F0', borderRadius: '12px',
            padding: '40px', textAlign: 'center', maxWidth: '480px'
          }}>
            <div style={{ fontSize: '40px', marginBottom: '12px' }}>📊</div>
            <h3 style={{ fontSize: '18px', fontWeight: '700', color: '#1E293B', marginBottom: '8px' }}>
              상권 업종 분포 정보
            </h3>
            <p style={{ fontSize: '13px', color: '#64748B', lineHeight: '1.5' }}>
              좌측 패널에서 <strong>{data.blockName}</strong> 상권의 업종별 분포 수치를 확인하실 수 있습니다.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Industry