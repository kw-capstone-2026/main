# Backend — Spring Boot API 서버

## 기술 스택

| 항목      | 내용                        |
| --------- | --------------------------- |
| Language  | Java 22                     |
| Framework | Spring Boot 3.5             |
| DB        | PostgreSQL 15 (Docker)      |
| ORM       | Spring Data JPA / Hibernate |
| 인증      | JWT (jjwt 0.12)             |
| 환경변수  | spring-dotenv               |

---

## ERD

<img width="644" height="449" alt="스크린샷 2026-05-16 오후 5 58 14" src="https://github.com/user-attachments/assets/a9cf023f-430f-4c35-ab4f-b31144634d0e" />

---

## 사전 준비

- Docker Desktop 설치 및 실행
- Java 22 이상 설치 (로컬 개발 시에만 필요)

---

## 실행 방법

### Docker로 실행 (권장)

프로젝트 루트(`capstone/main/`)에서 실행합니다.

```bash
docker compose up -d
```

DB + Spring Boot가 한 번에 실행됩니다.  
최초 실행 시 `database/schema.sql` → `database/seed.sql` 순서로 자동 적용됩니다.  
서버가 뜨면 `http://localhost:8080` 에서 응답을 확인할 수 있습니다.

DB를 완전히 초기화하려면:

```bash
docker compose down -v && docker compose up -d
```

### 로컬에서 직접 실행 (개발 시)

```bash
docker compose up -d db        # DB만 먼저 실행
cd backend/survival-api
./gradlew bootRun
```

---

## SHAP 최종 표시명 적용

새 DB는 `database/seed-ai-2024q4.sql.gz`에서 최종 표시명을 자동 적재합니다. 기존 DB는 프로젝트 루트에서 아래 SQL만 적용하면 됩니다. 피처명과 SHAP 수치, 사용자 계정은 유지합니다.

```bash
docker compose up -d --wait db
docker compose cp database/migrations/002_finalize_shap_labels.sql db:/tmp/update_shap_labels.sql
docker compose exec -T db sh -c 'psql -X -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /tmp/update_shap_labels.sql'
```

최종 32개 표시명은 [feature_labels_final.csv](../database/feature_labels_final.csv)에 있습니다. 초안 대비 9개를 수정했으며 현재 4분기 데이터의 대상은 64,216행입니다.

---

## swagger

```bash
http://localhost:8080/swagger-ui/index.html
```

---

## 패키지 구조

```
backend/survival-api/src/main/java/com/capstone/survival_api/
├── SurvivalApiApplication.java
├── config/          # SecurityConfig (CORS, JWT 필터)
├── controller/      # AuthController, BlockController, PredictionController, IndustryController
├── domain/
│   ├── entity/      # User, Block, Prediction, Store, IndustryStat, ShapFeature, SurvivalCurvePoint
│   └── repository/  # JPA Repository 인터페이스
├── dto/
│   ├── request/     # SignupRequest, LoginRequest
│   └── response/    # 각 API 응답 DTO
├── exception/       # ErrorCode, AppException, GlobalExceptionHandler
├── security/        # JwtProvider, JwtAuthFilter, CustomUserDetailsService
└── service/         # AuthService, BlockService, PredictionService, IndustryService
```

---

## API 목록

| Method | URL                                            | 설명                    | 인증 |
| ------ | ---------------------------------------------- | ----------------------- | ---- |
| POST   | `/api/v1/auth/signup`                          | 회원가입                | ❌   |
| POST   | `/api/v1/auth/login`                           | 로그인                  | ❌   |
| POST   | `/api/v1/auth/logout`                          | 로그아웃                | ✅   |
| GET    | `/api/v1/blocks`                               | 전체 블록 목록 (히트맵) | ❌   |
| GET    | `/api/v1/blocks/{blockId}`                     | 블록 상세               | ❌   |
| GET    | `/api/v1/blocks/{blockId}/prediction`          | 예측 결과               | ❌   |
| GET    | `/api/v1/blocks/{blockId}/survival-curve`      | 생존 확률 곡선          | ❌   |
| GET    | `/api/v1/blocks/{blockId}/shap`                | SHAP 기여도             | ❌   |
| GET    | `/api/v1/blocks/{blockId}/industry-stats`      | 업종 비율               | ❌   |
| GET    | `/api/v1/blocks/{blockId}/industry-survival`   | 업종별 생존 기간        | ❌   |
| GET    | `/api/v1/blocks/{blockId}/monthly-competitors` | 월별 경쟁 점포 추이     | ❌   |

---

## CORS 허용 출처

- `https://csi-platform.vercel.app` (프로덕션)
- `http://localhost:5174` (로컬 개발)
- `http://localhost:3000`
