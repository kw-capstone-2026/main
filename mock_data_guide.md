# CSI Platform 모크 데이터 가이드 (mock_data_guide.md)

## 개요
현재 프론트엔드는 실제 API 없이 하드코딩된 모크 데이터로 동작합니다.
실제 모델 연결 시 이 문서를 참고하여 데이터 구조를 맞춰주세요.

---

## 1. 블록 분기 기준

`getMockPrediction`, `getMockIndustry` 함수 모두 `block.csi` 값으로 분기합니다.

| 조건 | 해당 블록 | 설명 |
|---|---|---|
| `csi >= 8.0` | B01 홍대입구역 인근 | 안전 상권 |
| `csi < 8.0` | B09 상수동 카페거리 | 고위험 상권 |

---

## 2. Prediction 페이지 모크 데이터 구조

### 안전 상권 (B01, csi >= 8.0)
```javascript
{
  closureRate: 2.1,       // 최근 1년 폐업률
  openRate: 5.4,          // 최근 1년 개업률
  riskScore: 29,          // 종합 리스크 점수 (0~100)
  riskLevel: '낮음',      // 위험도 등급 텍스트
  riskColor: '#3B82F6',   // 파란색 (안전)
  badgeBg: '#EFF6FF',     // 배지 배경색
  survival6m: 81,         // 6개월 후 생존 확률 (%)
  survivalCurve: [        // 생존 확률 곡선 데이터
    { month: '3개월', rate: 92 },
    { month: '6개월', rate: 81 },
    { month: '9개월', rate: 73 },
    { month: '12개월', rate: 65 },
  ],
  shapData: [...]         // SHAP 기여도 데이터
}
```

### 고위험 상권 (B09, csi < 8.0)
```javascript
{
  closureRate: 14.8,
  openRate: 3.1,
  riskScore: 93,
  riskLevel: '높음',
  riskColor: '#EF4444',   // 빨간색 (위험)
  badgeBg: '#FEE2E2',
  survival6m: 23,
  survivalCurve: [
    { month: '3개월', rate: 45 },
    { month: '6개월', rate: 23 },
    { month: '9개월', rate: 12 },
    { month: '12개월', rate: 5 },
  ],
  shapData: [...]
}
```

---

## 3. SHAP 기여도 색상 판단 기준

현재는 모크 데이터라 `color` 값을 수동으로 지정합니다.

| 색상 | 의미 | 현재 방식 |
|---|---|---|
| `#EF4444` (빨간색) | 위험 요인 (폐업 위험 높이는 요인) | 수동 지정 |
| `#3B82F6` (파란색) | 완화 요인 (폐업 위험 낮추는 요인) | 수동 지정 |

### 실제 모델 연결 시 변경 방법
실제 SHAP value는 양수/음수로 구분됩니다.
```javascript
// 실제 모델 연결 후 아래처럼 자동 색상 처리
color: shapValue >= 0 ? '#EF4444' : '#3B82F6'
```

---

## 4. 6개월 후 생존 확률 색상 기준

```javascript
// 50% 미만 → 빨간색, 50% 이상 → 파란색
color: data.survival6m >= 50 ? '#3B82F6' : '#EF4444'
```
생존 확률 텍스트와 프로그레스 바 색상 모두 동일한 기준 적용.

---

## 5. Industry 페이지 모크 데이터 구조

### 안전 상권 (csi >= 8.0)
```javascript
{
  industryStats: [  // 업종 비율 파이 차트
    { name: '카페', count: 35, color: '#FFAF53' },
    { name: '음식점', count: 80, color: '#FF808B' },
    { name: '편의점', count: 45, color: '#8AF1B9' },
    { name: '술집', count: 25, color: '#F4BE5E' },
  ],
  survival: [       // 업종별 평균 생존 기간 (단위: 개월)
    { name: '편의점', days: 52, color: '#8AF1B9' },
    { name: '미용', days: 44, color: '#9698D6' },
    { name: '음식점', days: 38, color: '#FF808B' },
    { name: '술집', days: 32, color: '#F4BE5E' },
    { name: '카페', days: 28, color: '#FFAF53' },
  ],
  trend: [          // 월별 경쟁 점포 수 추이
    { month: '2024.01', count: 180 },
    ...
  ]
}
```

### 고위험 상권 (csi < 8.0)
```javascript
{
  survival: [       // 안전 상권 대비 생존 기간 절반 수준
    { name: '편의점', days: 28 },
    { name: '미용', days: 20 },
    { name: '음식점', days: 18 },
    { name: '술집', days: 14 },
    { name: '카페', days: 10 },
  ],
  trend: [          // 점포 수 증가 추세 (경쟁 심화)
    { month: '2024.01', count: 99 },
    { month: '2025.01', count: 260 },
  ]
}
```

---

## 6. 생존 기간 막대 그래프 YAxis 고정값

B01과 B09 비교 시 시각적 차이를 명확히 하기 위해 YAxis domain을 고정합니다.
```javascript
<YAxis domain={[0, 60]} tickCount={7} />
```
고정하지 않으면 각 블록 데이터 범위에 맞게 자동 스케일링되어 차이가 없어 보입니다.

---

## 7. 실제 API 연결 시 교체 포인트

| 파일 | 함수 | 교체 내용 |
|---|---|---|
| `Prediction.jsx` | `getMockPrediction` | 백엔드 `/api/prediction/:blockId` 응답으로 교체 |
| `Industry.jsx` | `getMockIndustry` | 백엔드 `/api/industry/:blockId` 응답으로 교체 |
| `blocks.js` | `MOCK_BLOCKS` | 백엔드 `/api/blocks` 응답으로 교체 |