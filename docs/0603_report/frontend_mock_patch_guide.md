# React Prediction.jsx 모크 데이터 패치 가이드 (frontend_mock_patch_guide.md)

본 문서는 `Prediction.jsx` 파일의 하드코딩된 모크 데이터를 교체하여, 사용자가 **고위험 블록(예: B09 상수동 카페거리)**과 **안전 블록(예: B01 홍대입구역 인근)**을 클릭했을 때 각각 다른 실제 분석 결과 그래프와 점수가 동적으로 렌더링되도록 구현하는 패치 가이드라인입니다.

기존 UI 마크업 구조를 해치지 않으면서 코드 몇 줄만 복사-붙여넣기하여 반영할 수 있도록 작성되었습니다.

---

## 1. MOCK 데이터 및 함수 교체 (Prediction.jsx 파일 상단)

`Prediction.jsx` 기존에 선언된 `getMockPrediction` 함수, `MOCK_SURVIVAL_CURVE`, `MOCK_SHAP` 변수를 아래 코드로 참고해 넣어주세요

```javascript
// ✅ [교체 코드] e:\capstone\kw-capstone-2026\src\pages\Prediction.jsx 상단

const getMockPrediction = (blockId) => {
  const block = MOCK_BLOCKS.find((b) => b.id === blockId) || MOCK_BLOCKS[9];

  // B01 (홍대입구역 인근) 혹은 csi가 8점 이상인 안전 상권인 경우
  if (blockId === "B01" || block.csi >= 8.0) {
    return {
      blockId: block.id,
      blockName: block.name,
      industry: block.industry,
      csi: block.csi,
      closureRate: 2.1, // 최근 1년 폐업률
      openRate: 5.4, // 최근 1년 개업률
      riskScore: 29, // Log-odds 위험 점수
      riskLevel: "낮음", // 위험 등급
      riskColor: "#3B82F6", // 안전 색상 (Blue)
      badgeBg: "#EFF6FF", // 배경 색상
      survival6m: 81, // 6개월 후 생존 확률
      survivalCurve: [
        { month: "3개월", rate: 92 },
        { month: "6개월", rate: 81 },
        { month: "9개월", rate: 73 },
        { month: "12개월", rate: 65 },
      ],
      shapData: [
        {
          name: "전년 대비 폐업 증감률",
          value: 25.4,
          color: "#3B82F6",
          label: "-0.82 (안정적)",
        },
        {
          name: "점포당 평균 매출",
          value: 23.2,
          color: "#3B82F6",
          label: "4,751만 원 (매우 높음)",
        },
        {
          name: "당월 매출 금액",
          value: 12.4,
          color: "#3B82F6",
          label: "5,420만 원 (상권 활성)",
        },
        {
          name: "운영 영업 개월 평균",
          value: 9.3,
          color: "#3B82F6",
          label: "45.2개월 (장기 운영)",
        },
        {
          name: "집객시설 밀도",
          value: 4.6,
          color: "#3B82F6",
          label: "12.4 (집객력 풍부)",
        },
      ],
    };
  } else {
    // B09 (상수동 카페거리) 등 csi가 낮은 일반/고위험 상권인 경우
    return {
      blockId: block.id,
      blockName: block.name,
      industry: block.industry,
      csi: block.csi,
      closureRate: 14.8, // 최근 1년 폐업률
      openRate: 3.1, // 최근 1년 개업률
      riskScore: 93, // Log-odds 위험 점수
      riskLevel: "높음", // 위험 등급
      riskColor: "#EF4444", // 위험 색상 (Red)
      badgeBg: "#FEE2E2", // 배경 색상
      survival6m: 23, // 6개월 후 생존 확률
      survivalCurve: [
        { month: "3개월", rate: 45 },
        { month: "6개월", rate: 23 },
        { month: "9개월", rate: 12 },
        { month: "12개월", rate: 5 },
      ],
      shapData: [
        {
          name: "전년 대비 폐업 증감률",
          value: 43.8,
          color: "#EF4444",
          label: "+2.18 (2배 폭증)",
        },
        {
          name: "점포당 평균 매출",
          value: 20.1,
          color: "#EF4444",
          label: "91만 원 (최저 수준)",
        },
        {
          name: "운영 영업 개월 평균",
          value: 9.0,
          color: "#EF4444",
          label: "24.5개월 (단기 생존)",
        },
        {
          name: "집객시설 밀도",
          value: 3.0,
          color: "#EF4444",
          label: "3.2 (집객시설 부족)",
        },
        {
          name: "당월 매출 금액",
          value: 4.0,
          color: "#3B82F6",
          label: "638만 원 (완화 요인)",
        },
      ],
    };
  }
};
```

---

## 2. JSX 렌더링 코드 연동 수정

데이터가 각 컴포넌트에 동적으로 흐르도록 기존 JSX 마크업 중 일부 하드코딩된 변수들을 수정해야 합니다.

### ① 위험도 등급 배지 수정 (Prediction.jsx)

- **기존 코드**:
  ```javascript
  <div style={{
    background: '#FEE2E2', color: '#EF4444',
    ...
  }}>
    <span style={{ fontSize: '10px' }}>위험도</span>
    <span style={{ fontSize: '16px' }}>높음</span>
  </div>
  ```
- **수정 코드** (배경색, 텍스트 색상, 등급 텍스트 동적 변경):
  ```javascript
  <div
    style={{
      background: data.badgeBg,
      color: data.riskColor,
      fontSize: "12px",
      fontWeight: "700",
      padding: "6px 10px",
      borderRadius: "10px",
      textAlign: "center",
      minWidth: "52px",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      gap: "2px",
    }}
  >
    <span style={{ fontSize: "10px" }}>위험도</span>
    <span style={{ fontSize: "16px" }}>{data.riskLevel}</span>
  </div>
  ```

---

### ② 생존 확률 곡선 그래프 데이터 소스 변경 (Prediction.jsx 160행 부근)

- **기존 코드**:
  ```javascript
  <AreaChart data={MOCK_SURVIVAL_CURVE}>
  ```
- **수정 코드**:
  ```javascript
  <AreaChart data={data.survivalCurve}>
  ```

---

### ③ SHAP 기여도 차트 데이터 소스 변경 (Prediction.jsx)

- **기존 코드**:
  ```javascript
  <BarChart data={MOCK_SHAP} ...>
  ...
    <Bar dataKey="value" ...>
      {MOCK_SHAP.map((item, i) => ( ... ))}
    </Bar>
  ```
- **수정 코드**:
  ```javascript
  <BarChart
    data={data.shapData}
    layout="vertical"
    margin={{ left: 80, right: 60, top: 5, bottom: 5 }}
  >
    <XAxis type="number" domain={[0, 60]} fontSize={12} hide />
    <YAxis
      type="category"
      dataKey="name"
      fontSize={12}
      width={100}
      tick={{ textAnchor: "start", dx: -100 }}
    />
    <Tooltip
      formatter={(value, name, props) => [
        `기여도: ${value}% (${props.payload.label})`,
        "요인",
      ]}
    />
    <Bar dataKey="value" radius={[0, 4, 4, 0]}>
      {data.shapData.map((item, i) => (
        <Cell key={i} fill={item.color} />
      ))}
      <LabelList
        dataKey="value"
        position="right"
        formatter={(v, entry) => `${v}% (${entry.payload.label})`}
        style={{ fontSize: "11px", fontWeight: "600" }}
      />
    </Bar>
  </BarChart>
  ```
