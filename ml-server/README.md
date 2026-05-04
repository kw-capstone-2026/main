# ml-server (FastAPI - Python)
이 디렉토리는 ML 예측 엔진 API 서버입니다.

## 역할
- XGBoost AFT 모델을 로드하여 생존 기간 예측 결과를 JSON으로 반환
- SHAP 분석 결과(변수별 기여도)를 API로 제공
- Spring Boot 백엔드에서 HTTP 요청을 받아 처리

## 실행 방법
```bash
conda activate capstone
cd ml-server
uvicorn app:app --reload --port 8000
```

## API 엔드포인트 (설계 예시)
| Method | Endpoint | 설명 |
|---|---|---|
| POST | `/predict` | 위치 + 업종을 받아 생존 확률 곡선 반환 |
| POST | `/explain` | 예측 결과에 대한 SHAP 기여도 반환 |
| GET | `/health` | 서버 상태 체크 |
