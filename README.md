# 소상공인 창업 생존 기간 시뮬레이션 및 위험도 예측 시스템

이 프로젝트는 20년 치 실제 인허가/창업/폐업 데이터를 기반으로 디지털 트윈 환경을 구축하고, 특정 입지에서의 소상공인 생존 기간을 예측하는 XAI(설명 가능한 인공지능) 시스템입니다.

---

## 🏗️ 시스템 아키텍처

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   React (프론트) │────▶│ Spring Boot (API) │────▶│ FastAPI (ML서버)  │────▶│ PostGIS (DB)    │
│   Deck.gl/Leaflet│◀────│   REST API 제공   │◀────│ XGBoost + SHAP   │◀────│ 공간쿼리/격자   │
└─────────────────┘     └──────────────────┘     └──────────────────┘     └─────────────────┘
      :3000                   :8080                    :8000                    :5432
```

| 레이어                 | 기술                    | 포트 | 역할                              |
| ---------------------- | ----------------------- | ---- | --------------------------------- |
| **프론트엔드**   | React + Deck.gl/Leaflet | 3000 | 지도 대시보드, 결과 시각화        |
| **백엔드 API**   | Spring Boot (Java)      | 8080 | REST API, 비즈니스 로직, DB 통신  |
| **ML 예측 서버** | FastAPI (Python)        | 8000 | XGBoost AFT 예측, SHAP 해석       |
| **DB**           | PostgreSQL + PostGIS    | 5432 | 점포/POI 공간 데이터 저장 및 쿼리 |

---

## 🚀 기획 핵심 방향

1. **Fact 기반 예측**: 부정확한 매출 데이터가 아닌, **폐업 시점(생존 기간)**을 타겟으로 예측
2. **마이크로 데이터 임베딩**: 지하철역, 유치원, 경쟁 점포 등 수백 개 POI와의 거리/밀도를 피처화
3. **과거 시뮬레이션 검증 (Backtesting)**: 과거 데이터로 학습 → 미래 예측 → 실제와 비교하여 타당성 입증

---

## 📂 프로젝트 구조 (모노레포)

```
kw-capstone-2026/
│
├── frontend/                  ← React 프론트엔드
│   └── README.md              (세팅 가이드)
│
├── backend/                   ← Spring Boot API 서버
│   └── README.md              (세팅 가이드)
│
├── ml-server/                 ← FastAPI ML 예측 서버
│   ├── app.py                 (엔드포인트 스켈레톤)
│   └── README.md              (세팅 가이드)
│
├── src/                       ← 데이터 파이프라인 (Python)
│   ├── crawling/              마이크로 POI 데이터 수집 크롤러
│   ├── feature_engineering/   점포↔POI 공간 연산 및 피처 생성
│   ├── simulation/            백테스팅 시뮬레이션 로직
│   └── models/                XGBoost AFT + SHAP 모델 학습
│
├── database/                  ← PostGIS 스키마 및 SQL 스크립트
│   └── schema.sql
│
├── docs/                      ← 프로젝트 문서 (출처 명세 등)
├── environment.yml            ← Python(Anaconda) 환경 설정
├── .gitignore
└── README.md                  ← 지금 이 파일
```

---

## ⚙️ 시작하기 (Getting Started)

### 사전 준비

- [Git](https://git-scm.com/) 설치
- [Anaconda](https://www.anaconda.com/download) 또는 Miniconda 설치
- [JDK 17+](https://adoptium.net/) 설치 (Spring Boot용)
- [Node.js 18+](https://nodejs.org/) 설치 (React용)
- [PostgreSQL 15+](https://www.postgresql.org/) + PostGIS 확장 설치

### 1단계: 레포 클론

```bash
git clone https://github.com/kw-capstone-2026/main.git
cd main
```

### 2단계: Python 환경 세팅 (데이터 파이프라인 + ML 서버)

```bash
conda env create -f environment.yml
conda activate capstone
```

### 3단계: ML 서버 실행

```bash
cd ml-server
uvicorn app:app --reload --port 8000
```

### 4단계: Spring Boot 백엔드 실행

```bash
cd backend
./gradlew bootRun
# 서버가 http://localhost:8080 에서 실행됩니다
```

### 5단계: React 프론트 실행

```bash
cd frontend
npm install
npm start
# 브라우저에서 http://localhost:3000 열림
```

---

## 🛠 기술 스택 상세

### 데이터 파이프라인 (Python)

| 라이브러리                | 역할                                    |
| ------------------------- | --------------------------------------- |
| psycopg2 + sqlalchemy     | Python ↔ PostgreSQL DB 연결            |
| geopandas + shapely       | GPS 좌표 기반 공간 연산 (거리, 반경 등) |
| selenium + beautifulsoup4 | 웹 크롤링 (마이크로 POI 수집)           |
| xgboost (AFT)             | 생존 기간 예측 모델                     |
| lifelines                 | 생존 분석 통계 라이브러리               |
| shap                      | 변수별 기여도 시각화 (XAI)              |

### 백엔드 (Java)

| 기술              | 역할            |
| ----------------- | --------------- |
| Spring Boot 3.x   | REST API 서버   |
| Spring Data JPA   | DB ORM          |
| PostgreSQL Driver | PostGIS DB 연결 |

### 프론트엔드 (JavaScript)

| 기술              | 역할                       |
| ----------------- | -------------------------- |
| React             | UI 프레임워크              |
| Deck.gl / Leaflet | 지도 시각화 및 격자 렌더링 |

---

## 🤝 협업 규칙 (Git Convention)

### Branch 전략

```
main           ← 최종 배포 (직접 push 금지!)
  └── develop  ← 통합 개발 브랜치
       ├── feature/crawl-subway     ← 기능 개발
       ├── feature/spring-api       ← 기능 개발
       └── feature/react-map        ← 기능 개발
```

**작업 흐름:**

1. `develop`에서 `feature/기능명` 브랜치 생성
2. 작업 후 `develop`으로 PR(Pull Request)
3. 최소 1명 리뷰 후 머지
4. 안정화된 `develop`을 `main`에 머지

### Commit Message 규약

| 태그           | 용도             | 예시                                 |
| -------------- | ---------------- | ------------------------------------ |
| `[Feat]`     | 새로운 기능 추가 | `[Feat] 지하철역 크롤러 구현`      |
| `[Fix]`      | 버그 수정        | `[Fix] 좌표 변환 오류 수정`        |
| `[Docs]`     | 문서 작업        | `[Docs] API 명세 추가`             |
| `[Refactor]` | 코드 개선        | `[Refactor] 공간 쿼리 성능 최적화` |
| `[Style]`    | 코드 포맷팅      | `[Style] 린트 적용`                |
| `[Test]`     | 테스트 코드      | `[Test] 백테스팅 유닛 테스트 추가` |

---

## 📡 API 통신 흐름 예시

```
1. 사용자가 React 지도에서 위치 클릭 + 업종 "치킨" 선택
2. React → Spring Boot:  POST /api/predict { lat: 37.56, lng: 126.97, type: "치킨" }
3. Spring Boot → FastAPI: POST /predict { lat: 37.56, lng: 126.97, business_type: "치킨" }
4. FastAPI 내부:
   - PostGIS에서 반경 500m 내 경쟁점포 수, 가장 가까운 지하철 거리 등 피처 조회
   - XGBoost AFT 모델로 생존 기간 예측
   - SHAP으로 기여도 분석
5. FastAPI → Spring Boot → React: JSON 응답
   {
     "survival_months": 14.2,
     "risk_level": "높음",
     "shap_factors": { "경쟁점포_500m": -3.2, "지하철_거리": +1.8, ... }
   }
6. React가 생존 곡선 그래프 + SHAP 차트를 화면에 렌더링
```
