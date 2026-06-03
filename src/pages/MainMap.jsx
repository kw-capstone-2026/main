import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { MapContainer, TileLayer, Rectangle, Tooltip, useMap } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import { MOCK_BLOCKS, BLOCKS_BY_DISTRICT } from '../data/blocks'
import Sidebar from '../components/Sidebar'

const getColor = (csi) => {
  if (csi >= 8) return '#3B82F6'
  if (csi >= 6) return '#22C55E'
  if (csi >= 4) return '#EAB308'
  if (csi >= 2) return '#F97316'
  return '#EF4444'
}

function MoveToLocation({ query, onMove }) {
  const map = useMap()
  useEffect(() => {
    if (!query) return
    fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query + ' 서울')}&format=json&limit=1`)
      .then(res => res.json())
      .then(data => {
        if (data.length > 0) {
          const lat = parseFloat(data[0].lat)
          const lon = parseFloat(data[0].lon)
          map.setView([lat, lon], 14)
          onMove(lat, lon, query)
        }
      })
  }, [query])
  return null
}

function MainMap() {
  const [selectedBlock, setSelectedBlock] = useState(MOCK_BLOCKS[9])
  const [searchInput, setSearchInput] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [baseCoord, setBaseCoord] = useState({ lat: 37.5537, lon: 126.9236 })
  const [blocks, setBlocks] = useState(MOCK_BLOCKS)
  const navigate = useNavigate()

  const getDynamicCoords = (blockIndex, lat, lon) => {
    const offsets = [
      [0.002, 0.002], [0.002, -0.002], [-0.002, 0.002], [-0.002, -0.002],
      [0.004, 0.004], [0.004, -0.004], [-0.004, 0.004], [-0.004, -0.004],
      [0.006, 0.000], [-0.006, 0.000], [0.000, 0.006], [0.000, -0.006],
      [0.006, 0.004], [-0.006, 0.004], [0.004, 0.006],
    ]
    const [dlat, dlon] = offsets[blockIndex]
    return [
      [lat + dlat, lon + dlon],
      [lat + dlat + 0.003, lon + dlon + 0.003]
    ]
  }

  return (
    <div style={{ display: 'flex', height: '100vh', background: '#F5F5FA' }}>
      <Sidebar />

      {/* 왼쪽 사이드바 */}
      <div style={{
        width: '280px', background: 'white',
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
            }}>총 {blocks.length}개</span>
          </div>
          <div style={{ overflowY: 'auto', flex: 1 }}>
            {[...blocks].sort((a, b) => b.csi - a.csi).map(block => (
              <div
                key={block.id}
                onClick={() => setSelectedBlock(block)}
                style={{
                  display: 'flex', justifyContent: 'space-between',
                  padding: '8px 4px', borderBottom: '1px solid #F1F5F9',
                  cursor: 'pointer',
                  background: selectedBlock?.id === block.id ? '#F0F7FF' : 'transparent',
                  borderRadius: '6px'
                }}
              >
                <div>
                  <span style={{ fontSize: '11px', color: '#94A3B8', marginRight: '6px' }}>{block.id}</span>
                  <span style={{ fontSize: '13px' }}>{block.name}</span>
                </div>
                <span style={{ fontSize: '13px', fontWeight: '600', color: block.color }}>{block.csi}</span>
              </div>
            ))}
          </div>
        </div>

        {/* 선택 블록 */}
        {selectedBlock && (
          <div style={{ border: '1px solid #E2E8F0', borderRadius: '12px', padding: '12px' }}>
            <div style={{ marginBottom: '8px', textAlign: 'left' }}>
              <span style={{ fontSize: '13px', color: '#64748B' }}>선택 블록</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <span style={{ fontSize: '15px', fontWeight: '700', color: '#1E293B' }}>{selectedBlock.id} {selectedBlock.name}</span>
              <span style={{ fontSize: '16px', fontWeight: '700', color: selectedBlock.color }}>{selectedBlock.csi}</span>
            </div>
            {[
              ['CSI 점수', `${selectedBlock.csi} / 10`],
              ['상권 지역', selectedBlock.region],
              ['주 업종', selectedBlock.industry],
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
              onClick={() => navigate(`/prediction/${selectedBlock.id}`)}
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
            블록 색상은 CSI(상권 안전 지수)를 나타냅니다. 클릭하면 분석이 시작됩니다.
          </span>
        </div>
        <div style={{
          padding: '12px 20px', background: '#F8FAFC',
          borderBottom: '1px solid #E2E8F0',
          display: 'flex', gap: '12px', alignItems: 'center'
        }}>
          <input
            type="text"
            placeholder="구 이름 검색 후 Enter (예: 강남구)"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && setSearchQuery(searchInput)}
            style={{
              flex: 1, maxWidth: '320px', padding: '8px 12px',
              border: '1px solid #E2E8F0', borderRadius: '8px',
              fontSize: '13px', outline: 'none'
            }}
          />
          <select
            onChange={(e) => {
              const district = e.target.value
              if (BLOCKS_BY_DISTRICT[district]) {
                setBlocks(BLOCKS_BY_DISTRICT[district])
                setSelectedBlock(BLOCKS_BY_DISTRICT[district][0])
                setSearchQuery(district)
              }
            }}
            style={{ padding: '8px 12px', border: '1px solid #E2E8F0', borderRadius: '8px', fontSize: '13px' }}
          >
            <option>지역 전체</option>
            <option>마포구</option>
            <option>강남구</option>
            <option>종로구</option>
            <option>용산구</option>
          </select>
          <select style={{ padding: '8px 12px', border: '1px solid #E2E8F0', borderRadius: '8px', fontSize: '13px' }}>
            <option>CSI 범위 전체</option>
            <option>최적 8-10</option>
            <option>안전 6-8</option>
            <option>주의 4-6</option>
            <option>위험 2-4</option>
            <option>고위험 0-2</option>
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
              onMove={(lat, lon, query) => {
                setBaseCoord({ lat, lon })
                const district = Object.keys(BLOCKS_BY_DISTRICT).find(d => query.includes(d))
                if (district) {
                  setBlocks(BLOCKS_BY_DISTRICT[district])
                  setSelectedBlock(BLOCKS_BY_DISTRICT[district][0])
                }
              }}
            />
            {blocks.map((block, index) => {
              const coords = getDynamicCoords(index, baseCoord.lat, baseCoord.lon)
              return (
               <Rectangle
  key={`${block.id}-${index}-${baseCoord.lat}`}
  bounds={coords}
  pathOptions={{
    color: selectedBlock?.id === block.id ? 'white' : getColor(block.csi),
    fillColor: getColor(block.csi),
    fillOpacity: 0.7,
    weight: selectedBlock?.id === block.id ? 3 : 1
  }}
  eventHandlers={{
    click: () => setSelectedBlock(block)
  }}
>
  <Tooltip permanent direction="center" className="block-label">
    <span style={{ fontWeight: '700', fontSize: '11px', color: 'white', textShadow: '1px 1px 2px rgba(0,0,0,0.8)' }}>{block.id}<br />{block.csi}</span>
  </Tooltip>
</Rectangle>
              )
            })}
          </MapContainer>

          {/* 범례 */}
          <div style={{
            position: 'absolute', bottom: '16px', left: '16px',
            background: 'white', borderRadius: '10px',
            padding: '8px 14px', border: '1px solid #E2E8F0',
            display: 'flex', gap: '14px', fontSize: '11px',
            zIndex: 1000
          }}>
            {[
              ['#3B82F6', '최적 8-10'],
              ['#22C55E', '안전 6-8'],
              ['#EAB308', '주의 4-6'],
              ['#F97316', '위험 2-4'],
              ['#EF4444', '고위험 0-2'],
            ].map(([color, label]) => (
              <span key={label} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <span style={{ width: '10px', height: '10px', background: color, borderRadius: '2px', display: 'inline-block' }}></span>
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