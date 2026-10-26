import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { MapContainer, TileLayer, Rectangle, Tooltip, useMap } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import Sidebar from '../components/Sidebar'

const getRiskColor = (riskGrade, riskScore) => {
  if (riskScore >= 75 || riskGrade === '위험') return '#EF4444'
  if (riskScore >= 50 || riskGrade === '주의') return '#EAB308'
  return '#22C55E'
}

// 백엔드 팀원이 공유해 준 실제 시연용 3대 상권 ID 및 데이터
const DEMO_BLOCKS = [
  {
    id: 828,
    basId: '3110084_CS100010',
    name: '경리단길 북측',
    region: '골목상권',
    mainIndustry: '커피-음료',
    riskGrade: '위험',
    riskScore: 80,
    lat: 37.541737,
    lng: 126.99136
  },
  {
    id: 13982,
    basId: '3120052_CS100010',
    name: '연남동(홍대)',
    region: '발달상권',
    mainIndustry: '커피-음료',
    riskGrade: '주의',
    riskScore: 57,
    lat: 37.562145,
    lng: 126.923485
  },
  {
    id: 12396,
    basId: '3120053_CS100010',
    name: '성수역',
    region: '발달상권',
    mainIndustry: '커피-음료',
    riskGrade: '안전',
    riskScore: 19,
    lat: 37.544581,
    lng: 127.055961
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
      .catch(() => {})
  }, [query])
  return null
}

function MainMap() {
  const [blocks] = useState(DEMO_BLOCKS)
  const [selectedBlock, setSelectedBlock] = useState(DEMO_BLOCKS[0])
  const [selectedIndustry, setSelectedIndustry] = useState('커피-음료')
  const [selectedRegionFilter, setSelectedRegionFilter] = useState('전체')
  const [selectedRiskFilter, setSelectedRiskFilter] = useState('전체')
  const [searchInput, setSearchInput] = useState('')
  const [searchQuery, setSearchQuery] = useState('')

  const navigate = useNavigate()

  const filteredBlocks = blocks.filter(block => {
    const matchRegion = selectedRegionFilter === '전체' || block.region === selectedRegionFilter
    const matchRisk = selectedRiskFilter === '전체' || block.riskGrade === selectedRiskFilter
    const matchIndustry = !selectedIndustry || (block.mainIndustry ? block.mainIndustry.includes(selectedIndustry) : true)
    const matchSearch = !searchQuery || block.name.toLowerCase().includes(searchQuery.toLowerCase())
    return matchRegion && matchRisk && matchIndustry && matchSearch
  })

  // 🔥 피드백 4번: 검색어 및 필터가 바뀔 때, 선택된 블록(좌측 하단 정보)을 검색 결과의 첫 번째 상권으로 자동 업데이트
  useEffect(() => {
    if (filteredBlocks.length > 0) {
      const isCurrentlySelectedValid = filteredBlocks.some(b => b.id === selectedBlock?.id)
      if (!isCurrentlySelectedValid) {
        handleSelectBlock(filteredBlocks[0])
      }
    } else {
      setSelectedBlock(null)
    }
  }, [searchQuery, selectedRegionFilter, selectedRiskFilter])

  // 🔥 피드백 1번: 지도 위 마커(사각형) 크기를 2배로 키움 (0.0015 -> 0.003)
  const getBlockBounds = (lat, lng) => {
    const delta = 0.01 
    return [
      [lat - delta, lng - delta],
      [lat + delta, lng + delta]
    ]
  }

  const getDisplayScore = (block) => {
    if (!block) return '-'
    const score = block.riskScore
    return score !== undefined && score !== null ? `${score}점` : '-점'
  }

  const handleSelectBlock = (block) => {
    setSelectedBlock(block)
    if (block?.id) {
      localStorage.setItem('selectedBlockId', block.id)
    }
  }

  return (
    <div style={{ display: 'flex', height: '100vh', background: '#F5F5FA' }}>
      <Sidebar />

      <div style={{
        width: '320px', background: 'white',
        borderRight: '1px solid #E2E8F0',
        display: 'flex', flexDirection: 'column',
        padding: '20px', overflow: 'hidden'
      }}>
        <h2 style={{ fontSize: '20px', fontWeight: '700', marginBottom: '16px', color: '#1E293B', textAlign: 'left' }}>
          상권 과포화 지도
        </h2>

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
            }}>
              총 {filteredBlocks.length}개
            </span>
          </div>
          
          <div style={{ overflowY: 'auto', flex: 1 }}>
            {filteredBlocks.map(block => {
              const score = block.riskScore
              const color = getRiskColor(block.riskGrade, score)
              const isSelected = selectedBlock?.id === block.id

              return (
                <div
                  key={block.id || block.basId}
                  onClick={() => handleSelectBlock(block)}
                  style={{
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    padding: '10px 8px', borderBottom: '1px solid #F1F5F9',
                    cursor: 'pointer',
                    background: isSelected ? '#F0F7FF' : 'transparent',
                    borderRadius: '6px'
                  }}
                >
                  <div style={{ textAlign: 'left', flex: 1, paddingRight: '8px' }}>
                    <div style={{ fontSize: '11px', color: '#94A3B8' }}>{block.region}</div>
                    <div style={{ fontSize: '13px', fontWeight: '600', color: '#1E293B' }}>{block.name}</div>
                  </div>
                  <span style={{
                    fontSize: '11px', fontWeight: '700', color: 'white',
                    backgroundColor: color, padding: '2px 8px', borderRadius: '4px'
                  }}>
                    {block.riskGrade}
                  </span>
                </div>
              )
            })}
          </div>
        </div>

        {selectedBlock && (
          <div style={{ border: '1px solid #E2E8F0', borderRadius: '12px', padding: '14px', background: '#FAFAFA' }}>
            <div style={{ marginBottom: '6px', textAlign: 'left' }}>
              <span style={{ fontSize: '12px', color: '#64748B', fontWeight: '600' }}>선택 블록 정보</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
              <span style={{ fontSize: '15px', fontWeight: '700', color: '#1E293B', textAlign: 'left' }}>
                {selectedBlock.name}
              </span>
              <span style={{
                fontSize: '12px', fontWeight: '700', color: 'white',
                backgroundColor: getRiskColor(selectedBlock.riskGrade, selectedBlock.riskScore),
                padding: '3px 8px', borderRadius: '4px'
              }}>
                {selectedBlock.riskGrade}
              </span>
            </div>

            {[
              ['상권 유형', selectedBlock.region || '-'],
              ['위험 점수', getDisplayScore(selectedBlock)],
              ['업종명', selectedBlock.mainIndustry || selectedIndustry],
            ].map(([label, value]) => (
              <div key={label} style={{
                display: 'flex', justifyContent: 'space-between',
                padding: '5px 0', fontSize: '12px',
                borderBottom: '1px solid #E2E8F0'
              }}>
                <span style={{ color: '#64748B' }}>{label}</span>
                <span style={{ fontWeight: '600', color: '#1E293B' }}>{value}</span>
              </div>
            ))}

            <button
              onClick={() => {
                navigate(`/prediction/${selectedBlock.id}`);
              }}
              style={{
                width: '100%', marginTop: '12px',
                background: '#5E81F4', color: 'white',
                border: 'none', padding: '10px',
                borderRadius: '8px', fontSize: '13px',
                fontWeight: '600', cursor: 'pointer'
              }}
            >
              예측 결과 상세 분석 →
            </button>
          </div>
        )}
      </div>

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <div style={{
          padding: '12px 20px', background: 'white',
          borderBottom: '1px solid #E2E8F0',
          display: 'flex', gap: '12px', alignItems: 'center'
        }}>
          <span style={{ fontSize: '15px', fontWeight: '700', color: '#5E81F4' }}>상권 위험 지도</span>
          <span style={{ fontSize: '12px', color: '#94A3B8', flex: 1, textAlign: 'right' }}>
            위험등급 (안전 0~49 / 주의 50~74 / 위험 75~100점). 클릭하면 왼쪽에 정보가 표시됩니다.
          </span>
        </div>

        <div style={{
          padding: '12px 20px', background: '#F8FAFC',
          borderBottom: '1px solid #E2E8F0',
          display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap'
        }}>
          <input
            type="text"
            placeholder="상권 검색 (예: 경리단길북측, 연남동)"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && setSearchQuery(searchInput)}
            style={{
              flex: 1, minWidth: '200px', maxWidth: '260px', padding: '8px 12px',
              border: '1px solid #CBD5E1', borderRadius: '8px',
              fontSize: '13px', outline: 'none'
            }}
          />

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '12px', fontWeight: '600', color: '#475569' }}>업종:</span>
            {/* 🔥 피드백 5번: 커피-음료 하나만 남기고 disabled 속성 추가하여 클릭 불가능하게 고정 */}
            <select
              value={selectedIndustry}
              disabled
              style={{ padding: '8px 12px', border: '1px solid #CBD5E1', borderRadius: '8px', fontSize: '13px', backgroundColor: '#F1F5F9', color: '#64748B', cursor: 'not-allowed' }}
            >
              <option value="커피-음료">커피-음료</option>
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '12px', fontWeight: '600', color: '#475569' }}>상권 유형:</span>
            <select
              value={selectedRegionFilter}
              onChange={(e) => setSelectedRegionFilter(e.target.value)}
              style={{ padding: '8px 12px', border: '1px solid #CBD5E1', borderRadius: '8px', fontSize: '13px' }}
            >
              <option value="전체">상권 유형 전체</option>
              <option value="골목상권">골목상권</option>
              <option value="발달상권">발달상권</option>
              <option value="전통시장">전통시장</option>
              <option value="관광특구">관광특구</option>
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '12px', fontWeight: '600', color: '#475569' }}>위험도:</span>
            <select
              value={selectedRiskFilter}
              onChange={(e) => setSelectedRiskFilter(e.target.value)}
              style={{ padding: '8px 12px', border: '1px solid #CBD5E1', borderRadius: '8px', fontSize: '13px' }}
            >
              <option value="전체">위험도 전체</option>
              <option value="안전">안전 (0~49)</option>
              <option value="주의">주의 (50~74)</option>
              <option value="위험">위험 (75~100)</option>
            </select>
          </div>
        </div>

        <div style={{ flex: 1, position: 'relative' }}>
          {/* 🔥 피드백 1번: 3대 상권이 모두 한눈에 크게 들어오도록 초기 중앙 좌표 조정 및 zoom=12 적용 */}
          <MapContainer
            center={[37.55, 126.99]} 
            zoom={12}
            style={{ height: '100%', width: '100%' }}
          >
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; OpenStreetMap contributors'
            />
            <MoveToLocation
              query={searchQuery}
              onMove={() => {}}
            />
            {filteredBlocks.map((block) => {
              const lat = block.lat
              const lng = block.lng
              const bounds = getBlockBounds(lat, lng)
              const score = block.riskScore
              const color = getRiskColor(block.riskGrade, score)
              const isSelected = selectedBlock?.id === block.id

              return (
                <Rectangle
                  key={block.id || block.basId}
                  bounds={bounds}
                  pathOptions={{
                    color: isSelected ? '#1E293B' : color,
                    fillColor: color,
                    fillOpacity: 0.75,
                    weight: isSelected ? 3 : 1
                  }}
                  eventHandlers={{
                    click: () => handleSelectBlock(block)
                  }}
                >
                  <Tooltip permanent direction="center" className="block-label">
                    <div style={{ textAlign: 'center', fontWeight: '700', fontSize: '11px', color: 'white', textShadow: '1px 1px 2px rgba(0,0,0,0.8)' }}>
                      <div>{block.name}</div>
                      <div>({block.riskGrade})</div>
                    </div>
                  </Tooltip>
                </Rectangle>
              )
            })}
          </MapContainer>

          <div style={{
            position: 'absolute', bottom: '16px', left: '16px',
            background: 'white', borderRadius: '10px',
            padding: '8px 14px', border: '1px solid #E2E8F0',
            display: 'flex', gap: '14px', fontSize: '12px', fontWeight: '600',
            zIndex: 1000
          }}>
            {[
              ['#22C55E', '안전 (0~49)'],
              ['#EAB308', '주의 (50~74)'],
              ['#EF4444', '위험 (75~100)'],
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