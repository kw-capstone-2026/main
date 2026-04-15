# backend (Spring Boot)
이 디렉토리는 Spring Boot 프로젝트가 위치할 곳입니다.

## 초기 세팅 방법
[Spring Initializr](https://start.spring.io/)에서 아래 설정으로 프로젝트를 생성하세요.

| 항목 | 설정 |
|---|---|
| Project | Gradle - Groovy |
| Language | Java |
| Spring Boot | 3.x (최신 안정 버전) |
| Group | com.capstone |
| Artifact | survival-api |
| Dependencies | Spring Web, Spring Data JPA, PostgreSQL Driver |

생성된 프로젝트를 이 `backend/` 폴더 안에 풀어주세요.

## 주요 역할
- REST API 엔드포인트 제공 (`/api/predict`, `/api/stores`, `/api/grid` 등)
- React 프론트엔드의 요청을 받아 ML 서버(FastAPI)로 전달
- PostGIS DB와 직접 통신하여 점포/POI 데이터 CRUD 처리
