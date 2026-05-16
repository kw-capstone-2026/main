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

## 사전 준비

- Docker Desktop 설치 및 실행
- Java 22 이상 설치 (로컬 개발 시에만 필요)

---

## 환경변수 설정

프로젝트 루트의 `.env`에 아래 항목이 있는지 확인하세요.  
(없으면 추가)

```env
DB_USERNAME=capstone_user
DB_PASSWORD=capstone1234
JWT_SECRET=capstone-survival-api-secret-key-must-be-at-least-256-bits-long!!
```

로컬에서 `./gradlew bootRun`으로 직접 실행하는 경우 `backend/survival-api/.env`도 필요합니다.

```env
DB_URL=jdbc:postgresql://localhost:5432/survival_db
DB_USERNAME=capstone_user
DB_PASSWORD=capstone1234
JWT_SECRET=capstone-survival-api-secret-key-must-be-at-least-256-bits-long!!
```

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

## API 동작 확인

```bash
# 블록 목록 조회 (마포구 일대)
curl "http://localhost:8080/api/v1/blocks?swLat=37.54&swLng=126.90&neLat=37.57&neLng=126.93"

# 블록 상세 조회
curl "http://localhost:8080/api/v1/blocks/1"

# 예측 결과 조회
curl "http://localhost:8080/api/v1/blocks/1/prediction"
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
- `http://localhost:5173` (로컬 개발)
- `http://localhost:3000`
