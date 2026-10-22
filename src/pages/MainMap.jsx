import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { MapContainer, TileLayer, Rectangle, Tooltip, useMap } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import Sidebar from '../components/Sidebar'

// 1. 위험도 3단계 색상 매핑 (안전/주의/위험)
const getRiskColor = (riskGrade) => {
  switch (riskGrade) {
    case '안전':
      return '#22C55E' // 초록
    case '주의':
      return '#EAB308' // 노랑
    case '위험':
      return '#EF4444' // 빨강
    default:
      return '#94A3B8'
  }
}

// 시연 3개 블록 포함 기본 테스트 데이터 구조
const INITIAL_BLOCKS = [
  {
    block_id: 'B01',
    block_name: '연남동(홍대)',
    region: '마포구 연남동',
    industry: '커피-음료',
    risk_grade: '안전',
    risk_score: 82,
    population: '평일 7만명/일',
    stores: '85개'
  },
  {
    block_id: 'B02',
    block_name: '경리단길북측',
    region: '용산구 이태원동',
    industry: '커피-음료',
    risk_grade: '주의',
    risk_score: 54,
    population: '평일 3만명/일',
    stores: '42개'
  },
  {
    block_id: 'B03',
    block_name: '성수역',
    region: '성동구 성수동',
    industry: '커피-음료',
    risk_grade: '위험',
    risk_score: 28,
    population: '평일 9만명/일',
    stores: '120개'
  }
]

function MoveToLocation({ query, onMove }) {
  const map = useMap()
  useEffect(() => {
    if (!query) return
    fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query + ' 서울')}&format=json&limit=1`)
      .then(res => res.json())
      .then(data => {
        if (data && data.length > 0) {
          const lat = parseFloat(data[0].lat)
          const lon = parseFloat(data[0].lon)
          map.setView([lat, lon], 14)
          onMove(lat, lon)
        }
      })
  }, [query])
  return null
}

function MainMap() {
  const [blocks, setBlocks] = useState(INITIAL_BLOCKS)
  const [selectedBlock, setSelectedBlock] = useState(INITIAL_BLOCKS[0])
  const [selectedIndustry, setSelectedIndustry] = useState('커피-음료')
  const [selectedRiskFilter, setSelectedRiskFilter] = useState('전체')
  const [searchInput, setSearchInput] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [baseCoord, setBaseCoord] = useState({ lat: 37.5537, lon: 126.9236 })
  const navigate = useNavigate()

  // 백엔드 API 연동 위치 (HANDOFF.md 5장 API 참고)
  useEffect(() => {
    /* 실제 API 연동 시 주석 해제하여 사용:
    fetch(`/api/blocks?industry=${encodeURIComponent(selectedIndustry)}`)
      .then(res => res.json())
      .then(data => {
        setBlocks(data);
        if(data.length > 0) setSelectedBlock(data[0]);
      })
      .catch(err => console.error("API Fetch Error:", err));
    */
  }, [selectedIndustry])

  const getDynamicCoords = (blockIndex, lat, lon) => {
    const offsets = [
      [0.002, 0.002], [-0.002, 0.002], [0.004, -0.002],
      [-0.004, 0.004], [0.006, 0.000], [-0.006, 0.000]
    ]
    const [dlat, dlon] = offsets[blockIndex % offsets.length]
    return [
      [lat + dlat, lon + dlon],
      [lat + dlat + 0.003, lon + dlon + 0.003]
    ]
  }

  // 위험도 필터링
  const filteredBlocks = blocks.filter(block => {
    if (selectedRiskFilter === '전체') return true
    return block.risk_grade === selectedRiskFilter
  })

  return (
    <div style={{ display: 'flex', height: '100vh', background: '#F5F5FA' }}>
      <Sidebar />

      {/* 왼쪽 사이드바 */}
      <div style={{
        width: '300px', background: 'white',
        borderRight: '1px solid #E2E8F0',
        display: 'flex', flexDirection: 'column',
        padding: '20px', overflow: 'hidden'
      }}>
        <h2 style={{ fontSize: '20px', fontWeight: '700', marginBottom: '16px', color: '#1E293B', textAlign: 'left' }}>
          메인 지도
        </h2>

        {/* 블록 목록 */}
        <div style={{
          border: '1px solid #E2E8F0', borderRadius: '12px',
          padding: '12px', marginBottom: '16px',
          flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <span style={{ fontSize: '14px', fontWeight: '600' }}>블록 목록</span>
            <span style={{
              background: '#EFF6FF', color: '#1D4ED8',
              fontSize: '11px', padding: '2px 8px', borderRadius: '20px'
            }}>총 {filteredBlocks.length}개</span>
          </div>
          <div style={{ overflowY: 'auto', flex: 1 }}>
            {filteredBlocks.map(block => {
              const color = getRiskColor(block.risk_grade)
              return (
                <div
                  key={block.block_id}
                  onClick={() => setSelectedBlock(block)}
                  style={{
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    padding: '8px 6px', borderBottom: '1px solid #F1F5F9',
                    cursor: 'pointer',
                    background: selectedBlock?.block_id === block.block_id ? '#F0F7FF' : 'transparent',
                    borderRadius: '6px'
                  }}
                >
                  <div>
                    <span style={{ fontSize: '11px', color: '#94A3B8', marginRight: '6px' }}>{block.block_id}</span>
                    <span style={{ fontSize: '13px', fontWeight: '500' }}>{block.block_name}</span>
                  </div>
                  <span style={{
                    fontSize: '11px', fontWeight: '700', color: 'white',
                    backgroundColor: color, padding: '2px 6px', borderRadius: '4px'
                  }}>
                    {block.risk_grade}
                  </span>
                </div>
              )
            })}
          </div>
        </div>

        {/* 선택 블록 */}
        {selectedBlock && (
          <div style={{ border: '1px solid #E2E8F0', borderRadius: '12px', padding: '12px' }}>
            <div style={{ marginBottom: '8px', textAlign: 'left' }}>
              <span style={{ fontSize: '13px', color: '#64748B' }}>선택 블록</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <span style={{ fontSize: '15px', fontWeight: '700', color: '#1E293B' }}>
                {selectedBlock.block_id} {selectedBlock.block_name}
              </span>
              <span style={{
                fontSize: '12px', fontWeight: '700', color: 'white',
                backgroundColor: getRiskColor(selectedBlock.risk_grade),
                padding: '3px 8px', borderRadius: '4px'
              }}>
                {selectedBlock.risk_grade}
              </span>
            </div>
            {[
              ['위험도 등급', selectedBlock.risk_grade],
              ['위험 점수', `${selectedBlock.risk_score ?? '-'}점`],
              ['상권 지역', selectedBlock.region],
              ['선택 업종', selectedIndustry],
              ['유동인구', selectedBlock.population],
              ['경쟁 점포', selectedBlock.stores],
            ].map(([label, value]) => (
              <div key={label} style={{
                display: 'flex', justifyContent: 'space-between',
                padding: '4px 0', fontSize: '12px',
                borderBottom: '1px solid #F1F5F9'
              }}>
                <span style={{ color: '#64748B' }}>{label}</span>
                <span style={{ fontWeight: '500' }}>{value}</span>
              </div>
            ))}
            <button
              onClick={() => navigate(`/prediction/${selectedBlock.block_id}`)}
              style={{
                width: '100%', marginTop: '12px',
                background: '#5E81F4', color: 'white',
                border: 'none', padding: '10px',
                borderRadius: '8px', fontSize: '13px',
                fontWeight: '600', cursor: 'pointer'
              }}
            >
              예측 결과 바로가기 →
            </button>
          </div>
        )}
      </div>

      {/* 오른쪽 지도 */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <div style={{
          padding: '12px 20px', background: 'white',
          borderBottom: '1px solid #E2E8F0',
          display: 'flex', gap: '12px', alignItems: 'center'
        }}>
          <span style={{ fontSize: '14px', fontWeight: '600', color: '#5E81F4' }}>상권 히트맵</span>
          <span style={{ fontSize: '12px', color: '#94A3B8', flex: 1, textAlign: 'right' }}>
            마커 색상은 상권 위험도(안전/주의/위험)를 나타냅니다. 클릭하면 상세 분석으로 이동합니다.
          </span>
        </div>

        {/* 상단 검색 및 필터Bar */}
        <div style={{
          padding: '12px 20px', background: '#F8FAFC',
          borderBottom: '1px solid #E2E8F0',
          display: 'flex', gap: '12px', alignItems: 'center'
        }}>
          <input
            type="text"
            placeholder="상권 또는 구 이름 검색 (예: 연남동)"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && setSearchQuery(searchInput)}
            style={{
              flex: 1, maxWidth: '280px', padding: '8px 12px',
              border: '1px solid #E2E8F0', borderRadius: '8px',
              fontSize: '13px', outline: 'none'
            }}
          />

          {/* 요구사항 5: 업종 선택 필터 추가 */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '12px', fontWeight: '600', color: '#475569' }}>업종 선택:</span>
            <select
              value={selectedIndustry}
              onChange={(e) => setSelectedIndustry(e.target.value)}
              style={{ padding: '8px 12px', border: '1px solid #E2E8F0', borderRadius: '8px', fontSize: '13px' }}
            >
              <option value="커피-음료">커피-음료</option>
              <option value="한식식당">한식식당</option>
              <option value="양식음식점">양식음식점</option>
              <option value="일식음식점">일식음식점</option>
              <option value="화장품">화장품</option>
            </select>
          </div>

          {/* 요구사항 1 & 6: 위험도 등급 필터 */}
          <select
            value={selectedRiskFilter}
            onChange={(e) => setSelectedRiskFilter(e.target.value)}
            style={{ padding: '8px 12px', border: '1px solid #E2E8F0', borderRadius: '8px', fontSize: '13px' }}
          >
            <option value="전체">위험도 전체</option>
            <option value="안전">안전</option>
            <option value="주의">주의</option>
            <option value="위험">위험</option>
          </select>
        </div>

        {/* 지도 */}
        <div style={{ flex: 1, position: 'relative' }}>
          <MapContainer
            center={[37.5537, 126.9236]}
            zoom={13}
            style={{ height: '100%', width: '100%' }}
          >
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; OpenStreetMap contributors'
            />
            <MoveToLocation
              query={searchQuery}
              onMove={(lat, lon) => setBaseCoord({ lat, lon })}
            />
            {filteredBlocks.map((block, index) => {
              const coords = getDynamicCoords(index, baseCoord.lat, baseCoord.lon)
              const color = getRiskColor(block.risk_grade)
              const isSelected = selectedBlock?.block_id === block.block_id

              return (
                <Rectangle
                  key={`${block.block_id}-${index}`}
                  bounds={coords}
                  pathOptions={{
                    color: isSelected ? '#1E293B' : color,
                    fillColor: color,
                    fillOpacity: 0.75,
                    weight: isSelected ? 3 : 1
                  }}
                  eventHandlers={{
                    click: () => setSelectedBlock(block)
                  }}
                >
                  <Tooltip permanent direction="center" className="block-label">
                    <div style={{ textAlign: 'center', fontWeight: '700', fontSize: '11px', color: 'white', textShadow: '1px 1px 2px rgba(0,0,0,0.8)' }}>
                      <div>{block.block_name}</div>
                      <div>({block.risk_grade})</div>
                    </div>
                  </Tooltip>
                </Rectangle>
              )
            })}
          </MapContainer>

          {/* 요구사항 6: 3색 범례 */}
          <div style={{
            position: 'absolute', bottom: '16px', left: '16px',
            background: 'white', borderRadius: '10px',
            padding: '8px 14px', border: '1px solid #E2E8F0',
            display: 'flex', gap: '14px', fontSize: '12px', fontWeight: '600',
            zIndex: 1000
          }}>
            {[
              ['#22C55E', '안전'],
              ['#EAB308', '주의'],
              ['#EF4444', '위험'],
            ].map(([color, label]) => (
              <span key={label} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ width: '12px', height: '12px', background: color, borderRadius: '3px', display: 'inline-block' }}></span>
                {label}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default MainMap