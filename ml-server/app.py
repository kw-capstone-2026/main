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
    # TODO: 1) PostGIS에서 주변 피처 조회 (현재는 생략)
    # TODO: 2) XGBoost AFT 모델로 예측 (현재는 더미 데이터)
    
    # ── 테스트용 가짜 데이터 생성 ──
    # 실제로는 모델이 계산해야 하지만, 통신 확인을 위해 값을 임의로 넣습니다.
    mock_result = {
        "survival_months": 32.4,
        "survival_probability_1y": 0.85,
        "survival_probability_3y": 0.45,
        "risk_level": "보통"
    }
    
    print(f"입력 데이터 확인: {req}") # 서버 터미널에 출력됨
    return mock_result

@app.post("/explain")
def explain(req: PredictRequest):
    """예측 결과에 대한 SHAP 변수별 기여도를 반환합니다."""
    # TODO: SHAP 분석 결과를 dict로 반환
    return {
        "features": {
            "subway_dist": 0.45,
            "pop_density": 0.21,
            "competition": -0.15
        },
        "message": "SHAP 테스트 데이터입니다."
    }