# **FastAPI 연동 방식**

당장은 사전 계산 캐시 방식으로 구현, 최종 발표 후 A안으로 변경 제안

이유는 현재 Spring Boot가 CORS·JWT 인증을 전담하고 있어서, FastAPI를 외부에 직접 노출하면 인증 처리를 FastAPI에도 별도 구현해야 해요. Spring Boot에서 `/api/v1/predict`로 받아서 내부적으로 FastAPI에 전달하면 프론트는 Spring Boot 하나만 바라보면 되고, 인증·에러 처리도 일관되게 유지됩니다.

다만 일주일 안에 실시간 연동까지 하기엔 빡빡할 수 있어서, **현실적인 방향으로 사전 계산된 캐시 데이터를 메인으로 가고 FastAPI 연동은 시간 여유가 생기면 추가**하는 걸 제안합니다. 현재 DB에 `predictions`, `shap_features`, `survival_curve` 테이블에 블록별 예측 결과를 미리 저장하는 구조로 Spring Boot API가 이미 완성되어 있어서, ML 팀이 계산한 결과를 DB에 밀어넣기만 하면 프론트에 바로 연동 가능합니다.

### 사전 계산 캐시 방식 (현재 구조, 권장)

```java
[ML팀] 예측 실행 → DB 적재 → Spring Boot가 DB에서 읽어서 반환 → 프론트
```

**장점:** FastAPI 서버 불필요, 이미 API 완성됨, 응답 빠름
**단점:** 실시간 예측 불가 (블록 단위 배치 결과만 제공)

# 앞으로 필요한 작업 내용

- **[백엔드] 백엔드 서버 외부 배포**
- **[백엔드] 데이터 연동 (AI팀 협업)**
- **[AI팀 요청] 실 ML 결과 DB 적재**
  - `blocks` → `predictions` → `shap_features` → `survival_curve` → `industry_stats` 순서로 적재
  - 더미 데이터 삭제 후 실 데이터로 교체
  - `risk_grade` 분류 기준 확정 (risk_score 임계값)
- **[백엔드] 적재 결과 검증**
  - 전체 API 11개 실 데이터 기준 응답 확인
- **[프론트엔드] 프론트엔드 API 연동**

### 현재 테이블 구조와 필요한 데이터

**① `blocks` 테이블** — 상권 격자 기본 정보

ML팀이 예측한 블록의 BAS_ID(격자코드)를 기준으로 먼저 blocks를 채워야 함.

| 컬럼            | 타입          | 설명           | ML팀 데이터 매핑     |
| --------------- | ------------- | -------------- | -------------------- |
| `bas_id`        | VARCHAR(20)   | 격자 고유코드  | BAS_AR 코드          |
| `name`          | VARCHAR(100)  | 블록 표시명    | 상권명 또는 행정동명 |
| `region`        | VARCHAR(100)  | 지역명         | 자치구명             |
| `main_industry` | VARCHAR(50)   | 주 업종        | 최다 업종            |
| `csi_score`     | NUMERIC(4,2)  | 상권안전지수   | CSI 점수             |
| `lat`,`lng`     | NUMERIC(10,7) | 블록 중심 좌표 | 격자 중심점          |
| `area`          | NUMERIC(12,2) | 블록 면적(㎡)  | BAS_AR               |

**② \*\***predictions\*\*

테이블 — 예측 결과 (블록당 1행)

| 컬럼           | 타입         | 설명                       | ML팀 데이터 매핑  |
| -------------- | ------------ | -------------------------- | ----------------- |
| `block_id`     | BIGINT       | blocks.id 참조             |                   |
| `csi_score`    | NUMERIC(4,2) | 상권안전지수               |                   |
| `risk_grade`   | VARCHAR(20)  | `'위험'`/`'주의'`/`'안전'` | 임계값 기준 분류  |
| `closure_rate` | NUMERIC(5,2) | 폐업률 (%)                 |                   |
| `open_rate`    | NUMERIC(5,2) | 개업률 (%)                 |                   |
| `survival_6m`  | NUMERIC(5,2) | 6개월 생존 확률 (%)        | 모델 예측값 × 100 |
| `risk_score`   | INTEGER      | 종합 리스크 0~100          |                   |

**③ \*\***shap_features\*\*

테이블 — SHAP 기여도 (블록당 5행)

| 컬럼         | 설명              | 예시        |
| ------------ | ----------------- | ----------- |
| `block_id`   |                   |             |
| `rank`       | 기여도 순위 (1~5) | 1           |
| `name`       | 피처 영문명       | `store_age` |
| `shap_value` | SHAP 값           | 0.3371      |
| `label`      | 한글 표시명       | `점포 연령` |

**④ `survival_curve` 테이블** — 생존 확률 곡선 (블록당 5행)

| `month` | `survival_rate` |
| ------- | --------------- |
| 0       | 100.0           |
| 3       | 82.0            |
| 6       | 51.0            |
| 9       | 38.0            |
| 12      | 28.0            |

**⑤ `industry_stats` 테이블** — 업종 통계 (블록당 N행)

| 컬럼                | 설명                     |
| ------------------- | ------------------------ |
| `industry_name`     | 업종명 (카페, 음식점 등) |
| `store_count`       | 해당 업종 점포 수        |
| `avg_survival_days` | 평균 생존 일수           |
| `ratio`             | 전체 대비 비율 (%)       |
| `recorded_at`       | 기준일 (예: 2024-01-01)  |
