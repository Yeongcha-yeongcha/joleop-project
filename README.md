# Children English Story Learning Backend

FastAPI + PostgreSQL 기반 어린이 영어 동화 학습 서비스 백엔드입니다.

현재 MVP는 Kakao 부모 로그인, Parent/Profile JWT 인증, 아이 프로필, 온보딩, 홈/도서관, 학습 세션, Reading/Repeat/Description/Mock Roleplay 흐름을 제공합니다.

## Tech Stack

- Python 3.11+
- FastAPI
- Pydantic v2
- SQLAlchemy 2.x AsyncSession
- PostgreSQL 16
- asyncpg
- Alembic
- PyJWT
- Argon2 password hashing
- pytest / pytest-asyncio

## Directory Structure

```text
app/
  api/
    deps.py
    v1/
  core/
    config.py
    exceptions.py
    security.py
  db/
    base.py
    session.py
  models/
  schemas/
  seed/
  services/
alembic/
tests/
docker-compose.yml
requirements.txt
```

## Environment

```bash
cp .env.example .env
```

주요 설정:

```text
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/story_learning

JWT_SECRET_KEY=change-me
JWT_ALGORITHM=HS256
PARENT_ACCESS_TOKEN_EXPIRE_MINUTES=60
PARENT_REFRESH_TOKEN_EXPIRE_DAYS=14
PROFILE_ACCESS_TOKEN_EXPIRE_MINUTES=180

KAKAO_CLIENT_ID=
KAKAO_CLIENT_SECRET=
KAKAO_REDIRECT_URI=
KAKAO_TOKEN_URL=https://kauth.kakao.com/oauth/token
KAKAO_USER_INFO_URL=https://kapi.kakao.com/v2/user/me

CORS_ORIGINS=http://localhost:3000,http://localhost:5173
MAX_CHILD_PROFILES_PER_PARENT=5
PROFILE_IMAGE_BASE_URL=https://cdn.example.com/profiles
MAX_AUDIO_UPLOAD_BYTES=10485760
```

`JWT_SECRET_KEY`는 운영 환경에서 충분히 긴 랜덤 문자열로 설정해야 합니다.

## Run PostgreSQL

```bash
docker compose up -d
```

PostgreSQL 16이 `localhost:5432`에서 실행됩니다.

## Install Dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Alembic Migration

```bash
alembic upgrade head
```

새 모델을 추가한 경우:

```bash
alembic revision --autogenerate -m "message"
alembic upgrade head
```

## Seed Data

```bash
python -m app.seed.seed_data
```

Seed는 idempotent 방식입니다. 여러 번 실행해도 동일한 개발용 책/문항이 중복 생성되지 않습니다.

## Run FastAPI

```bash
uvicorn app.main:app --reload
```

- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- Health: `GET /health`
- Readiness: `GET /ready`

## Kakao OAuth

프론트엔드는 Kakao authorization code를 받은 뒤 백엔드로 전달합니다.

```http
POST /api/v1/auth/kakao
Content-Type: application/json

{
  "authorizationCode": "kakao_authorization_code",
  "redirectUri": "https://example.com/oauth/kakao/callback"
}
```

백엔드는 Kakao access token을 자체 API 인증에 사용하지 않습니다. Kakao user info에서 `kakaoId`를 확인한 뒤 서비스 자체 Parent Access Token과 Refresh Token을 발급합니다.

## Parent Token vs Profile Token

Parent Token:

- Kakao 로그인 후 발급
- 부모 API, 프로필 CRUD, 프로필 선택 로그인에 사용
- `tokenType=PARENT`

Profile Token:

- 부모가 아이 프로필 비밀번호를 입력하면 발급
- 홈, 도서관, 온보딩, 학습 API에 사용
- `tokenType=PROFILE`

Parent API에서 Profile Token은 거부되고, Profile API에서 Parent Token도 거부됩니다.

## Audio Upload

Repeat, Description, Roleplay 음성 제출 API는 JSON/base64가 아니라 `multipart/form-data`를 사용합니다.

예:

```http
POST /api/v1/learning-sessions/{sessionId}/repeat/attempts
Authorization: Bearer {profileAccessToken}
Content-Type: multipart/form-data

audio=@audio.wav
questionId=201
```

허용 MIME type:

- `audio/wav`
- `audio/x-wav`
- `audio/mpeg`
- `audio/mp4`
- `audio/webm`

현재 STT는 `MockSpeechToTextService`입니다. 원본 audio는 영구 저장하지 않고 transcript만 저장합니다.

## Tests

```bash
pytest
```

테스트에서는 Kakao, STT, Roleplay AI를 mock 처리합니다.

## Deployment

서버 배포 절차, Docker 없이 설치하는 방법, DB readiness 확인 방법은
[DEPLOYMENT.md](DEPLOYMENT.md)를 참고하세요.

## End-to-End Local Flow

```bash
docker compose up -d

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

alembic upgrade head
python -m app.seed.seed_data

uvicorn app.main:app --reload
```

Swagger:

```text
http://localhost:8000/docs
```
