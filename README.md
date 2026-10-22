# 🚀 CSI Platform - 프론트엔드 (csi-platform)

상권 분석 및 위험도 예측을 위한 프론트엔드 대시보드 플랫폼입니다.

## 🔗 라이브 배포 링크 (Live Demo)
- **Production URL**: [https://csi-platform.vercel.app](https://csi-platform.vercel.app)

---

## 📌 주요 업데이트 및 수정 사항

1. **위험도 등급 및 시각화 체계 개선**
   - 기존 수치(8.0) 기반 구분에서 `risk_grade` (`안전` / `주의` / `위험`) 3색 시스템으로 전면 전환
   - 지도 마커 중첩 해결을 위한 **업종 선택 드롭다운 필터** 및 3색 범례 추가

2. **UI/UX 및 차트 보완**
   - **SHAP 위험요인 차트**: 요인별 기여도 색상(양수: 빨강 / 음수: 파랑) 유지 및 실제 지표값(Value) 병기
   - **데이터 미제공 영역 숨김 처리**: 404 에러를 유발하던 생존곡선(`/survival-curve`) 및 빈 차트 영역 화면에서 배제

3. **안전성 및 예외 처리 (Fallback Data)**
   - 백엔드 API 서버 미연동/비활성화 상태 시에도 브라우저 시연이 정상 동작하도록 **Mock Data 예외 처리** 적용

---

## 🛠️ 기술 스택 (Tech Stack)
- **Frontend**: React, Vite, JavaScript
- **Styling**: Tailwind CSS / CSS Modules
- **Deployment**: Vercel CLI / Vercel Production

---

## 💻 로컬 개발 환경 실행 방법

1. 레포지토리 클론 (Repository Clone)
   ```bash
   git clone [https://github.com/사용자계정/csi-platform.git](https://github.com/사용자계정/csi-platform.git)
   cd csi-platform