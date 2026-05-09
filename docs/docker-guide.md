# 🐳 Docker 초보자 가이드 (팀원용)

이 문서는 Docker를 처음 쓰는 팀원을 위한 가이드입니다.
우리 프로젝트에서는 **PostgreSQL + PostGIS 데이터베이스를 Docker로 실행**합니다.

---

## Docker란?

**"내 컴퓨터 안에서 미니 가상 컴퓨터를 돌리는 프로그램"** 입니다.

PostgreSQL을 직접 설치하면 팀원마다 버전이 다르고, 윈도우/맥 설정이 달라서 문제가 생깁니다.
Docker를 쓰면 **팀원 전원이 동일한 DB 환경**을 명령어 한 줄로 구성할 수 있습니다.

---

## 1단계: Docker Desktop 설치

### Windows
1. https://www.docker.com/products/docker-desktop/ 접속
2. **"Download for Windows"** 클릭
3. 다운로드된 설치 파일 실행
4. 설치 중 **"Use WSL 2"** 옵션이 체크되어 있는지 확인
5. 설치 완료 후 **PC를 재부팅**합니다
6. 재부팅 후 Docker Desktop이 자동으로 실행됨
7. 작업표시줄에 🐳 고래 아이콘이 보이면 성공!

> **WSL2 관련 오류가 뜨는 경우**
> 1. PowerShell을 **관리자 권한**으로 실행
> 2. `wsl --install` 입력 후 엔터
> 3. PC 재부팅 후 다시 Docker Desktop 실행

### Mac
1. 같은 사이트에서 "Download for Mac" 클릭
2. .dmg 파일 실행 → Applications 폴더로 드래그
3. Docker Desktop 실행

---

## 2단계: 설치 확인

PowerShell(또는 터미널)을 열고:

```bash
docker --version
```

아래처럼 뜨면 성공입니다:
```
Docker version 24.0.7, build afdd53b
```

만약 "'docker'는 인식할 수 없는 명령입니다" 가 뜨면:
- Docker Desktop이 실행 중인지 확인 (작업표시줄 🐳 아이콘)
- PC를 재부팅한 후 다시 시도

---

## 3단계: DB 실행하기

프로젝트 폴더로 이동 후 명령어 한 줄 입력:

```bash
cd e:\capstone\kw-capstone-2026
docker compose up -d
```

**처음 실행 시** 이미지를 다운로드하므로 1~3분 정도 걸립니다.
아래와 같이 뜨면 성공:
```
✔ Container capstone-db  Started
```

---

## 4단계: DB 접속 확인

### 방법 A: 터미널에서 직접 접속
```bash
docker exec -it capstone-db psql -U postgres -d capstone
```
```
capstone=# \dt
```
→ stores, poi 테이블이 보이면 schema.sql이 정상 적용된 것!
→ `\q`로 나가기

### 방법 B: DBeaver 등 GUI 툴로 접속
| 항목 | 값 |
|---|---|
| Host | `localhost` |
| Port | `5432` |
| Database | `capstone` |
| Username | `postgres` |
| Password | `capstone1234` |

### 방법 C: Python에서 접속
```python
from sqlalchemy import create_engine
engine = create_engine("postgresql://postgres:capstone1234@localhost:5432/capstone")
print(engine.connect())  # 연결 성공!
```

---

## 자주 쓰는 명령어 정리

| 명령어 | 의미 |
|---|---|
| `docker compose up -d` | DB 시작 (백그라운드) |
| `docker compose down` | DB 종료 |
| `docker compose down -v` | DB 종료 + **데이터 전부 삭제** (초기화) |
| `docker ps` | 실행 중인 컨테이너 확인 |
| `docker logs capstone-db` | DB 로그 확인 (오류 발생 시) |

---

## 자주 발생하는 문제

### ❌ "port 5432 already in use"
→ 이미 PostgreSQL이 로컬에 설치되어 5432 포트를 사용 중
→ 해결: 로컬 PostgreSQL 서비스를 중지하거나, docker-compose.yml에서 포트를 변경
```yaml
ports:
  - "5433:5432"   # 5433으로 변경
```

### ❌ "Cannot connect to the Docker daemon"
→ Docker Desktop이 실행 중이 아님
→ 해결: Docker Desktop 앱을 실행한 후 다시 시도

### ❌ "WSL 2 installation is incomplete"
→ WSL2가 설치되지 않음
→ 해결: PowerShell(관리자) → `wsl --install` → 재부팅
