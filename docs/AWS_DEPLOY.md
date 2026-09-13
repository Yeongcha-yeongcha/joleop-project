# AWS Deploy

이 저장소는 AWS에서 아래 조합으로 배포하는 것을 기본 경로로 둡니다.

- Backend: AWS App Runner + Dockerfile
- Database: Amazon RDS PostgreSQL
- Frontend: AWS Amplify Hosting

## 1. RDS PostgreSQL

RDS에서 PostgreSQL DB를 만든 뒤 보안 그룹에서 App Runner가 접근할 수 있게 설정합니다.
RDS를 private subnet에 두는 경우 App Runner에 VPC Connector를 연결하고, RDS 보안 그룹 inbound에 해당 VPC/subnet 대역 또는 App Runner 연결용 보안 그룹을 허용합니다.

앱에서 사용하는 DB URL 형식:

```env
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@RDS_ENDPOINT:5432/story_learning
```

새 DB를 만든 뒤 백엔드 컨테이너에서 초기 테이블을 생성합니다.

```bash
python -m app.seed.init_db
```

기존 DB를 업데이트할 때는 `backend/db_migrations/`의 SQL을 적용합니다.

## 2. Backend: App Runner

App Runner 서비스를 만들 때 GitHub 저장소를 연결하고 다음 값을 지정합니다.

- Build source: repository source code
- Dockerfile path: `backend/Dockerfile`
- Build context: repository root
- Port: `8000`
- Health check path: `/health`
- Start command: Dockerfile `CMD` 사용
- Network: private RDS를 사용하면 VPC Connector 연결

App Runner 환경변수는 `backend/env.production.example`을 복사해서 실제 값으로 채웁니다.
비밀값은 저장소에 커밋하지 말고 App Runner 환경변수나 Secrets Manager를 사용하세요.

필수 값:

```env
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@RDS_ENDPOINT:5432/story_learning
JWT_SECRET_KEY=replace-with-a-long-random-secret-at-least-32-characters
CORS_ORIGINS=https://YOUR_AMPLIFY_DOMAIN
KAKAO_CLIENT_ID=
KAKAO_CLIENT_SECRET=
KAKAO_REDIRECT_URI=https://YOUR_AMPLIFY_DOMAIN/oauth/kakao/callback
EDGE_TTS_CACHE_DIR=/tmp/tts-cache
```

배포 후 App Runner 도메인의 `/health`가 `{"status":"ok"}`를 반환하는지 확인합니다.

```bash
curl https://YOUR_APP_RUNNER_DOMAIN/health
```

DB 연결까지 확인하려면 `/ready`를 확인합니다.

```bash
curl https://YOUR_APP_RUNNER_DOMAIN/ready
```

## 3. Frontend: Amplify Hosting

Amplify에서 같은 GitHub 저장소를 연결합니다. 이 저장소에는 모노레포용 `amplify.yml`이 포함되어 있고 `frontend` 앱을 빌드합니다.

Amplify 환경변수는 `frontend/env.production.example`을 기준으로 설정합니다.

```env
VITE_API_BASE_URL=https://YOUR_APP_RUNNER_DOMAIN/api/v1
VITE_KAKAO_CLIENT_ID=
VITE_KAKAO_REDIRECT_URI=https://YOUR_AMPLIFY_DOMAIN/oauth/kakao/callback
```

React Router SPA 라우팅을 위해 Amplify Rewrites and redirects에 아래 규칙을 추가합니다.

```txt
Source address: </^[^.]+$|\.(?!(css|gif|ico|jpg|jpeg|js|png|txt|svg|woff|woff2|ttf|map|json)$)([^.]+$)/>
Target address: /index.html
Type: 200 (Rewrite)
```

프론트 배포가 끝난 뒤 생성된 Amplify 도메인을 App Runner의 `CORS_ORIGINS`와 Kakao redirect URI에 다시 반영합니다.

## 4. Local verification

백엔드 컨테이너 빌드:

```bash
docker build -f backend/Dockerfile -t yeongcha-backend .
docker run --env-file backend/env.production.example -p 8000:8000 yeongcha-backend
```

프론트 프로덕션 빌드:

```bash
cd frontend
npm ci
npm run build
```

## Deployment order

1. RDS 생성
2. App Runner 백엔드 배포
3. App Runner 도메인을 넣어 Amplify 프론트 배포
4. Amplify 도메인을 App Runner `CORS_ORIGINS`와 Kakao 설정에 반영
5. DB 초기화와 seed/import 실행
