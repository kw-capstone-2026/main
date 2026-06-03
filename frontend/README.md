# frontend (React)
이 디렉토리는 React 프론트엔드 프로젝트가 위치할 곳입니다.

## 초기 세팅 방법
```bash
cd frontend
npx create-react-app . --template typescript
# 또는 Vite 사용 시:
# npm create vite@latest . -- --template react-ts
```

## 주요 역할
- 사용자 인터페이스 (지도 기반 대시보드)
- Spring Boot API와 통신하여 예측 결과를 시각화
- Deck.gl 또는 Leaflet을 이용한 격자 히트맵 렌더링

## 핵심 페이지 구성
| 페이지 | 기능 |
|---|---|
| 메인 지도 | 서울 격자 히트맵 (위험도 색상 표시) |
| 예측 결과 | 생존 확률 곡선 + SHAP 기여도 차트 |
| 업종 비교 | 동일 위치에서 업종별 생존 기간 비교 |

## 통신 예시
```javascript
// Spring Boot API 호출
const response = await fetch('/api/predict', {
  method: 'POST',
  body: JSON.stringify({ lat: 37.56, lng: 126.97, business_type: '치킨' })
});
const result = await response.json();
// result = { survival_months: 14.2, risk_level: "상", ... }
```
