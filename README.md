# 🏙️ CSI Platform (상권 과포화 위험 진단 서비스)

## 🔗 배포 링크 (Live Demo)
* **웹 서비스 접속하기**: https://csi-platform.vercel.app/

---

## 🚀 프론트엔드 주요 진행 상황 및 구현 기능

1. **상권 과포화 위험 진단 지도 (MainMap)**
   - OpenStreetMap 및 Leaflet을 활용한 인터랙티브 상권 히트맵 시각화
   - 지역(골목상권, 발달상권 등), 업종(커피-음료, 한식식당 등), 위험도(안전, 주의, 위험)별 실시간 필터링 및 검색 기능 구현
   - 지도 마커 및 블록 목록 클릭 시 `localStorage`를 통한 선택 상권 ID 동기화 및 페이지 간 라우팅 유지 처리

2. **SHAP 기반 위험 요인 분석 (Prediction)**
   - 백엔드 API(`/api/v1/blocks/{blockId}/shap`) 연동 완료
   - AI팀 최종 확정 피처 라벨 및 실제 피처 값(`featureValue`), 기여도(`shapValue`)를 반영한 바 차트 및 상세 지표 시각화

3. **상권 업종 비교 분석 (Industry Stats)**
   - 도넛 차트(`PieChart`)를 이용한 상권 내 상위 업종 구성비 및 통계 시각화
   - 미구현 또는 누락된 백엔드 데이터(생존 곡선, 월별 추이 등)에 대한 안전한 예외 처리(Fallback UI 및 "데이터 준비 중" 안내 문구 적용)

4. **인증 및 회원가입 (Auth)**
   - 백엔드 스펙에 맞춘 로그인/회원가입 컴포넌트 구성 및 API 연동 준비 완료