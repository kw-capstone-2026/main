"""
ml-server/app.py
-----------------
FastAPI 기반 ML 예측 서버 스켈레톤

Spring Boot 백엔드에서 HTTP 요청을 받아
XGBoost AFT 모델로 생존 기간을 예측하고
SHAP 기여도를 JSON으로 반환합니다.
"""

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="소상공인 생존 예측 API", version="0.1.0")


# ── 요청/응답 스키마 ──
class PredictRequest(BaseModel):
    lat: float           # 점포 위도
    lng: float           # 점포 경도
    business_type: str   # 업종 (예: "치킨", "카페")


class PredictResponse(BaseModel):
    survival_months: float          # 예상 생존 기간 (개월)
    survival_probability_1y: float  # 1년 생존 확률
    survival_probability_3y: float  # 3년 생존 확률
    risk_level: str                 # 위험 등급 (상/중/하)


# ── 엔드포인트 ──
@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    """위치와 업종을 받아 생존 기간을 예측합니다."""
    # TODO: 1) PostGIS에서 주변 피처 조회
    # TODO: 2) XGBoost AFT 모델로 예측
    # TODO: 3) 결과 반환
    raise NotImplementedError("predict() 구현 필요")


@app.post("/explain")
def explain(req: PredictRequest):
    """예측 결과에 대한 SHAP 변수별 기여도를 반환합니다."""
    # TODO: SHAP 분석 결과를 dict로 반환
    raise NotImplementedError("explain() 구현 필요")
