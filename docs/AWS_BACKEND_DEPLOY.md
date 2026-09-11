# AWS Backend Deploy

이 문서는 FastAPI 백엔드를 AWS App Runner에 올리기 위한 최소 절차입니다.

## 배포 단위

- Dockerfile: `backend/Dockerfile`
- Docker build context: repository root
- Container port: `8000`
- Health check path: `/health`
- Start command: Dockerfile의 `CMD` 사용

로컬에서 이미지 빌드를 확인할 때:

```bash
docker build -f backend/Dockerfile -t yeongcha-backend .
docker run --env-file backend/env.production.example -p 8000:8000 yeongcha-backend
```

실제 실행에는 `backend/env.production.example` 값을 복사해서 AWS App Runner 환경변수로 넣습니다. 예시 파일 자체는 비밀값 없이 유지하세요.

## 필수 환경변수

```env
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@RDS_ENDPOINT:5432/story_learning
JWT_SECRET_KEY=replace-with-a-long-random-secret-at-least-32-characters
CORS_ORIGINS=https://YOUR_FRONTEND_DOMAIN
KAKAO_CLIENT_ID=
KAKAO_CLIENT_SECRET=
KAKAO_REDIRECT_URI=https://YOUR_FRONTEND_DOMAIN/oauth/kakao/callback
```

`JWT_SECRET_KEY`는 32자 이상 랜덤 문자열로 설정합니다.

## App Runner 설정

1. App Runner에서 GitHub repository를 연결합니다.
2. Deployment source는 Container registry가 아니라 Source code repository를 사용해도 됩니다.
3. Dockerfile path는 `backend/Dockerfile`로 지정합니다.
4. Port는 `8000`으로 설정합니다.
5. Health check path는 `/health`로 설정합니다.
6. Environment variables에 `backend/env.production.example`의 실제 값을 등록합니다.

App Runner URL이 생성되면 프론트엔드의 `VITE_API_BASE_URL`은 다음 형식입니다.

```env
VITE_API_BASE_URL=https://YOUR_APP_RUNNER_DOMAIN/api/v1
```

## Database

이 앱은 PostgreSQL을 사용합니다. AWS에서는 RDS PostgreSQL을 만들고 `DATABASE_URL`에 RDS endpoint를 넣습니다.

새 RDS DB를 처음 만들 때는 현재 SQLAlchemy 모델 기준으로 테이블을 생성합니다.

```bash
python -m app.seed.init_db
```

로컬 Docker 이미지 안에서 실행할 때는:

```bash
docker run --env-file backend/env.production.example yeongcha-backend python -m app.seed.init_db
```

현재 저장소에는 추가 수동 SQL migration 파일도 있습니다.

```txt
backend/db_migrations/
```

기존 DB를 업데이트할 때는 `backend/db_migrations/`의 SQL을 적용하세요. 신선한 RDS에는 `init_db` 실행 후 필요한 콘텐츠 seed/import 작업을 이어서 실행합니다.
