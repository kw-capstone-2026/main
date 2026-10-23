# 프론트엔드 전달 사항 — 실데이터 API 연동

2026-10-23 확인 기준입니다. AI팀의 2024년 4분기 데이터가 저장소의 초기화 파일에 포함되어 있습니다. 현재 방식은 사전 계산된 결과를 조회하는 방식이며, 프론트는 Spring Boot API를 호출하면 됩니다.

## 1. 연결 주소와 개발 환경

- 로컬 API: `http://localhost:8080`
- Swagger: `http://localhost:8080/swagger-ui/index.html`
- 공유·배포 API 주소: 별도 전달 필요

각자 PC의 localhost는 서로 다른 서버입니다. 실행 전에 다음을 준비합니다.

1. `database/seed-ai-2024q4.sql.gz`와 수정된 `docker-compose.yml`이 포함된 최신 코드
2. 백엔드 담당자에게 별도로 전달받은 `.env` 파일: `docker-compose.yml`과 같은 프로젝트 루트에 배치
3. 실행 중인 Docker Desktop

`.env`에는 `DB_NAME`, `DB_USERNAME`, `DB_PASSWORD`, `DOCKER_DB_URL`, `JWT_SECRET`이 모두 필요합니다. `DOCKER_DB_URL`은 호스트가 `db`인 Docker 내부용 주소입니다. 프론트의 `.env`에 이 비밀번호·JWT 키를 넣지 않습니다.

**이미 로컬 테스트 DB가 있고 그 데이터를 삭제해도 되는 경우**, 프로젝트 루트에서 아래 명령을 한 번 실행합니다. `down -v`는 이 프로젝트의 기존 DB 볼륨을 삭제하므로 사용자 계정과 로컬 변경도 함께 삭제됩니다. 필요한 데이터는 먼저 백업합니다.

```bash
docker compose down -v
docker compose up -d --build
```

처음 실행하는 팀원은 삭제할 DB가 없으므로 아래 실행 명령만 사용합니다. 기존 계정을 유지해야 한다면 초기화 대신 [기존 DB에 실데이터 적용하기](local-data.md#2-이미-db-볼륨이-있는-경우)의 계정 유지 절차를 진행합니다. 이 절차도 기존 분석 데이터는 교체합니다.

```bash
docker compose up -d --build
```

**새 DB 볼륨의 최초 실행 시 블록 21,664개와 동일한 예측·SHAP·업종 통계가 자동 적재됩니다.** ZIP 전달이나 Python 실행은 필요하지 않습니다. 이후에는 `docker compose up -d --build`로 실행하고, 매번 초기화하지 않습니다. 각자 DB에서 바꾼 내용은 자동 동기화되지 않습니다.

실행 후 아래 순서로 확인합니다.

1. `docker compose ps`에서 DB와 백엔드가 실행 중인지 확인합니다. 초기화가 끝나면 DB가 healthy 상태가 됩니다.
2. Swagger를 열고 `GET /api/v1/blocks/6/shap`에서 피처 5개와 `featureValue`를 확인합니다.
3. 프론트를 실행해 `/api/v1/...` 조회 API로 연동합니다. API가 아직 연결되지 않으면 `docker compose logs --tail=100 backend`로 기동 오류를 확인합니다.

현재 저장소의 `frontend/vite.config.ts`는 `/api`를 로컬 백엔드 8080으로 프록시합니다. Vite 개발 중에는 아래처럼 상대 경로를 사용할 수 있습니다.

```javascript
fetch('/api/v1/blocks?swLat=37.53&swLng=126.99&neLat=37.54&neLng=127.00');
```

Vite의 개발 프록시는 배포 빌드에 포함되지 않습니다. 배포 시에는 실제 API 주소나 별도 프록시 설정이 필요합니다.

백엔드 주소로 직접 요청하는 경우 현재 CORS 허용 출처는 다음과 같습니다.

- `http://localhost:5174`
- `http://localhost:3000`
- `https://csi-platform.vercel.app`

`http://localhost:5173`과 `127.0.0.1` 출처는 현재 허용되지 않습니다. 직접 호출할 경우 프론트를 `npm run dev -- --port 5174 --strictPort`로 실행하거나 사용할 출처를 백엔드 담당자에게 전달해 주세요.

현재 `frontend/src/App.tsx`의 `POST /api/predict`는 이전 설계 예제입니다. 이 엔드포인트는 구현되어 있지 않으므로 아래 GET API로 연동해 주세요.

## 2. 화면 연결 순서

1. 지도 표시 범위의 남서·북동 좌표로 블록 목록을 조회합니다.
2. 목록의 `id`를 선택한 항목의 `blockId`로 사용합니다. `basId`를 경로 ID에 넣지 않습니다.
3. 항목 선택 시 상세·예측·SHAP·업종 비율을 요청합니다.
4. 제공되지 않는 차트 데이터는 각 영역에서 “데이터 준비 중”으로 표시합니다. 한 차트의 404가 다른 정상 영역 표시를 막지 않도록 처리합니다.

전체 서울 21,664개를 조회하는 데 로컬에서 약 9.6초가 걸렸습니다. 현재 표시 범위 위주로 조회하고 지도 이동 종료 시 갱신해 주세요. 조회 성능 개선은 백엔드 수정 사항입니다.

## 3. 현재 사용할 수 있는 조회 API

아래 조회 API 8개는 로그인 없이 호출할 수 있습니다. 응답은 별도의 data 래퍼 없이 아래 객체가 바로 반환됩니다. JSON 필드는 camelCase입니다.

| GET 경로 | 파라미터 / 응답 |
|---|---|
| `/api/v1/blocks` | 필수 `swLat`, `swLng`, `neLat`, `neLng`; 선택 `region`, `csiMin`, `csiMax`. 응답 `{total, blocks:[{id, basId, name, region, csiScore, riskGrade, riskScore, lat, lng}]}` |
| `/api/v1/blocks/{blockId}` | `{id, basId, name, region, csiScore, riskGrade, mainIndustry, lat, lng, area, admDrCd, admDrNm}` |
| `/api/v1/blocks/{blockId}/prediction` | `{blockId, blockName, csiScore, riskGrade, closureRate, openRate, riskScore, survival6m, predictedAt}` |
| `/api/v1/blocks/{blockId}/shap` | `{blockId, features:[{rank, name, shapValue, featureValue, label}]}` |
| `/api/v1/blocks/{blockId}/industry-stats` | `{blockId, recordedAt, industries:[{industryName, storeCount, ratio}]}` |
| `/api/v1/blocks/{blockId}/survival-curve` | 데이터가 있으면 `{blockId, curve:[{month, survivalRate}]}`. 현재 데이터 없어 404 |
| `/api/v1/blocks/{blockId}/industry-survival` | `{blockId, survival:[{industryName, avgSurvivalDays, avgSurvivalMonths}]}`. 현재 일수 null, 개월 수 0으로 반환되는 문제 있음 |
| `/api/v1/blocks/{blockId}/monthly-competitors` | 선택 `months`: 기본 12, 1~60. 응답 `{blockId, months, trend:[{month, competitorCount}]}`. 현재 `trend: []` |

목록은 페이지네이션이 없으며 범위 안의 전체 항목을 반환합니다. 숫자는 JSON number, 빈 값은 null입니다. 일자 필드는 `YYYY-MM-DD`, 시각 필드는 시간대 오프셋이 없는 ISO 문자열입니다. `predictedAt`은 현재 DB 적재 시 기본값으로 생성됐으므로 원본 데이터 기준 분기와 구분해 주세요.

예시 요청:

```http
GET /api/v1/blocks?swLat=37.53&swLng=126.99&neLat=37.54&neLng=127.00
```

포함된 스냅샷의 예시 항목은 `id: 6`, `basId: "3001491_CS100001"`, 이름은 `이태원 관광특구 · 한식음식점`입니다. 스냅샷은 ID를 보존하지만 실제 화면에서는 목록 API가 반환한 ID를 사용하고 하드코딩하지 않습니다.

## 4. 지도·위험도 화면

- 지도 점수는 목록의 `riskScore`를 사용합니다. 현재 데이터는 0~100이며 높을수록 위험합니다. 등급과 색상은 서버의 `riskGrade`(`안전`, `주의`, `위험`)를 사용합니다.
- 블록 상세 응답에는 `riskScore`가 없습니다. 선택 항목의 점수는 목록에 있던 값을 사용하거나 `/prediction`에서 가져옵니다.
- `csiScore`는 전부 null입니다. CSI 점수·필터는 준비 중으로 처리하고 `csiMin`, `csiMax`는 요청에서 생략해 주세요. 위험점수와 CSI를 같은 지표로 표시하지 않습니다.
- 현재 `region`은 자치구가 아니라 `골목상권`, `발달상권`, `전통시장`, `관광특구`입니다. `region=마포구`로 요청하면 0건입니다. 필터 이름도 “상권 유형”으로 표시해 주세요.
- 데이터 한 행은 “상권×업종”입니다. 총 21,664개 행이 1,570개 위치를 공유하므로 같은 좌표에 여러 항목이 겹칩니다. 위치 선택 후 업종을 선택하는 등의 처리가 필요합니다. 해당 API에는 업종 필터 파라미터가 없습니다.
- 격자·상권 경계 polygon은 제공하지 않으며 `lat`, `lng`는 중심 좌표입니다. GeoJSON이 필요하면 별도 협의가 필요합니다.

## 5. SHAP 위험 이유 표시

SHAP은 rank 순으로 5개 반환됩니다. 현재 로컬 DB에서 첫 번째 항목의 예시는 다음과 같습니다.

```json
{
  "rank": 1,
  "name": "전년_동기_대비_폐업_증감률",
  "shapValue": 1.3041,
  "featureValue": 1.5,
  "label": "작년 같은 분기 대비 폐업 증감"
}
```

- `label`: AI팀 최종 확정 표시명입니다. 32개 피처 모두 20자 이내이며 최대 17자입니다. 응답의 label을 화면에 그대로 사용합니다.
- `featureValue`: 이유 옆에 표시할 실제 피처 값입니다. 원본 값이 그대로 들어갑니다.
- `shapValue`: 모델 예측에 대한 기여도입니다. 이번 데이터에서는 양수가 위험을 높이는 방향, 음수가 낮추는 방향입니다.

예를 들어 “작년 같은 분기 대비 폐업 증감: 1.5”로 표시할 수 있습니다. featureValue의 단위는 피처마다 다르므로 일괄적으로 %, 개, 원을 붙이거나 100을 곱하지 않습니다. 피처별 단위·표시 자릿수는 AI팀과 맞춰 주세요.

피처명 `name`, `shapValue`, `featureValue`는 바뀌지 않았습니다. 최종 표시명은 [피처 표시명 사전](../database/feature_labels_final.csv)에 정리했습니다. “상권”으로 시작하는 표시명은 상권 단위 값입니다.

새 DB에는 최종 표시명이 자동 적재됩니다. 기존 DB를 쓰는 팀원은 최신 코드를 받은 뒤 아래 SQL을 한 번 적용합니다. 전체 DB를 초기화할 필요 없이 표시명만 갱신합니다.

```bash
docker compose up -d --wait db
docker compose cp database/migrations/002_finalize_shap_labels.sql db:/tmp/update_shap_labels.sql
docker compose exec -T db sh -c 'psql -X -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /tmp/update_shap_labels.sql'
```

## 6. 차트·빈 값 처리

| 데이터 | 현재 상태 | 화면 처리 |
|---|---|---|
| 폐업률·개업률 | 값 있음, % 단위 | 3.0은 3%로 표시; 추가로 100을 곱하지 않음 |
| 업종 비율 | 상위 최대 5개 업종 | 전체 업종을 분모로 계산하므로 합계가 100%보다 작을 수 있음. 도넛 차트에 `기타 = max(0, 100 - 반환된 비율 합계)`를 추가하거나 상위 업종만 표시한다는 설명 필요 |
| CSI·6개월 생존확률 | null | `—` 또는 데이터 준비 중 |
| 생존 곡선 | 404, `PREDICTION_NOT_FOUND` | 데이터 준비 중 |
| 업종 평균 생존기간 | `avgSurvivalDays: null`, `avgSurvivalMonths: 0` | 실제 0개월이 아님. 당장은 days가 null이면 미제공 처리. 백엔드 수정 필요 |
| 월별 추이 | `trend: []` | 데이터 준비 중. 점포가 0개라고 단정하지 않음 |
| 면적·행정동 코드·이름 | null | 값이 필요한 영역은 미제공 처리 |

점수가 0인 경우는 유효한 값입니다. `value || '—'` 대신 `value ?? '—'`처럼 null과 0을 구분해 주세요.

월별 API는 현재 점포의 개업일 기준으로 전체 업종의 월별 개업 건수를 집계합니다. 영업 중인 경쟁점포 총수나 선택 업종만의 경쟁점포 수를 제공하는 기능은 아닙니다.

## 7. 회원가입·로그인·로그아웃

| POST 경로 | 요청 | 응답 |
|---|---|---|
| `/api/v1/auth/signup` | `{email, password, nickname}`; 비밀번호 8자 이상 | 201, `{id, email, nickname, createdAt}` |
| `/api/v1/auth/login` | `{email, password}` | 200, `{accessToken, tokenType:"Bearer", expiresIn:86400}`; expiresIn 단위는 초 |
| `/api/v1/auth/logout` | `Authorization: Bearer <accessToken>` 필요 | 200, `{message:"로그아웃 완료"}` |

로그아웃 시 프론트에서 토큰을 삭제합니다. 현재 서버는 토큰을 강제로 만료시키거나 블랙리스트로 관리하지 않습니다. 회원가입·로그인에는 토큰이 필요하지 않습니다.

## 8. 오류 처리와 확인 결과

애플리케이션 오류 예시:

```json
{"status":404,"code":"PREDICTION_NOT_FOUND","message":"해당 블록의 예측 결과가 없습니다."}
```

존재하지 않는 블록은 404, months 범위 오류·CSI 최솟값/최댓값 역전은 400, 이메일 중복은 409, 잘못된 비밀번호는 401입니다. 인증 없는 로그아웃은 현재 403이며 보안 단계의 응답은 위 JSON 형식이 보장되지 않습니다.

현재 필수 지도 좌표 누락, 문자 형태 blockId, `months=abc` 등은 400 대신 500을 반환하는 문제가 있습니다. 백엔드 수정 사항이며, 연동 시 필수 파라미터와 숫자 타입을 확인해 주세요.

실제 검증 결과: CSV 4종 전체 258,094행과 DB 값을 대조했고 불일치·외래키 누락·중복은 0건입니다. API 11개를 대상으로 정상·오류·CORS 요청 등 HTTP 검사 40건을 수행했습니다. 위에 적은 데이터 미제공 및 수정 사항을 제외하고 기본 연동을 확인했습니다.
