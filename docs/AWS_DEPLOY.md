# POPO AWS 배포 실행 문서

이 문서는 `daeun` 브랜치의 변경 사항을 GitHub에 푸시한 뒤 POPO의 프론트엔드와 백엔드를 AWS에 재배포하는 전체 절차입니다.

## 현재 배포 구성

| 구분 | 값 |
| --- | --- |
| GitHub 저장소 | `daeunpk/joleop-project` |
| 배포 브랜치 | `daeun` |
| AWS 리전 | `ap-southeast-2` (시드니) |
| AWS 계정 | `054422645032` |
| 데이터베이스 | Amazon RDS PostgreSQL |
| 백엔드 이미지 | Amazon ECR `yeongcha-backend:latest` |
| 백엔드 실행 | Amazon ECS Express Mode `yeongcha-backend` |
| ECS 클러스터 | `default` |
| 프론트엔드 | AWS Amplify Hosting `POPO` |
| 백엔드 URL | `https://ye-2469ae51f7464062b89344750f333459.ecs.ap-southeast-2.on.aws` |
| 프론트엔드 URL | `https://daeun.d2pvyyx48vb41m.amplifyapp.com` |

비밀번호, JWT 비밀키, Kakao REST API 키는 Git이나 이 문서에 기록하지 않습니다. AWS 환경 변수에서만 관리합니다.

## 1. 배포 전 로컬 검증

저장소 루트에서 현재 브랜치와 변경 파일을 확인합니다.

```bash
cd ~/yeongcha
git branch --show-current
git status --short
git diff --check
```

브랜치 결과는 `daeun`이어야 합니다. 다른 브랜치라면 작업 내용을 확인한 후 `daeun`으로 이동합니다.

백엔드 테스트를 실행합니다.

```bash
cd ~/yeongcha/backend
.venv/bin/pytest -q
```

프론트엔드 프로덕션 빌드를 확인합니다.

```bash
cd ~/yeongcha/frontend
npm run build
```

현재 `.env` 파일은 `.gitignore`에 포함되어 있습니다. 그래도 커밋 전에 비밀값이 스테이징되지 않았는지 반드시 확인합니다.

## 2. Git 커밋 및 푸시

저장소 루트로 돌아가 변경 사항을 스테이징합니다.

```bash
cd ~/yeongcha
git add -A
git status --short
git diff --cached --name-only
```

목록에 `backend/.env` 또는 `frontend/.env`가 없어야 합니다. 비밀번호나 API 키가 있는 파일이 보이면 커밋하지 않습니다.

변경 사항을 커밋합니다.

```bash
git commit -m "Fix points and review scheduling"
```

원격 변경 사항을 먼저 반영한 후 푸시합니다.

```bash
git pull --rebase origin daeun
git push origin daeun
```

푸시가 완료되면 Amplify의 `daeun` 브랜치 자동 빌드가 시작됩니다. 백엔드는 Git 푸시만으로 갱신되지 않으므로 아래 ECR/ECS 절차가 추가로 필요합니다.

## 3. CloudShell에서 최신 코드 받기

AWS 콘솔 상단의 CloudShell을 열고 다음 명령을 실행합니다.

```bash
cd ~/joleop-project
git status --short
git pull origin daeun
git rev-parse --short HEAD
```

CloudShell 저장소가 없다면 처음 한 번만 다음과 같이 복제합니다.

```bash
cd ~
git clone https://github.com/daeunpk/joleop-project.git
cd joleop-project
git checkout daeun
```

`git pull` 결과에 방금 푸시한 커밋이 포함됐는지 확인합니다.

## 4. 백엔드 Docker 이미지 빌드 및 ECR 푸시

CloudShell의 저장소 루트에서 ECR에 다시 로그인합니다. 인증 토큰은 만료되므로 배포할 때마다 실행하는 것이 안전합니다.

```bash
aws ecr get-login-password --region ap-southeast-2 \
  | docker login --username AWS --password-stdin \
    054422645032.dkr.ecr.ap-southeast-2.amazonaws.com
```

백엔드 이미지를 빌드합니다. Docker 빌드 컨텍스트는 반드시 저장소 루트 `.`이어야 합니다.

```bash
docker build \
  -f backend/Dockerfile \
  -t 054422645032.dkr.ecr.ap-southeast-2.amazonaws.com/yeongcha-backend:latest \
  .
```

빌드가 성공하면 ECR에 푸시합니다.

```bash
docker push \
  054422645032.dkr.ecr.ap-southeast-2.amazonaws.com/yeongcha-backend:latest
```

마지막 줄에 `latest: digest: sha256:...`가 나오면 푸시 성공입니다. `authorization token has expired`가 나오면 ECR 로그인 명령부터 다시 실행합니다.

## 5. ECS Express Mode 백엔드 재배포

1. AWS 콘솔에서 **Amazon Elastic Container Service**로 이동합니다.
2. 왼쪽 메뉴에서 **Express Mode**를 선택합니다.
3. 서비스 **yeongcha-backend**를 선택합니다.
4. 서비스의 **업데이트**, **새 배포** 또는 **새 서비스 개정 생성** 버튼을 선택합니다. 콘솔 버전에 따라 이름이 다를 수 있습니다.
5. 이미지 URI가 아래 값인지 확인합니다.

```txt
054422645032.dkr.ecr.ap-southeast-2.amazonaws.com/yeongcha-backend:latest
```

6. 기존 환경 변수, VPC, 서브넷, 보안 그룹, 포트 설정은 유지합니다.
7. 새 개정을 저장하고 배포합니다.
8. 서비스 상태가 **활성**, 태스크가 `1 실행 중`, 배포 상태가 **성공**이 될 때까지 기다립니다.

현재 네트워크 값은 다음과 같습니다.

```txt
VPC: vpc-0e8636fa59689feb1
Security group: sg-074df223dbc17fc0c
Container port: 8000
Health check path: /health
```

백엔드 환경 변수의 핵심 값은 다음 형식이어야 합니다.

```env
DATABASE_URL=postgresql+asyncpg://postgres:RDS_PASSWORD@RDS_ENDPOINT:5432/story_learning
JWT_SECRET_KEY=32자 이상의 랜덤 문자열
JWT_ALGORITHM=HS256
CORS_ORIGINS=https://daeun.d2pvyyx48vb41m.amplifyapp.com
EDGE_TTS_CACHE_DIR=/tmp/tts-cache
TTS_PROVIDER=edge
EDGE_TTS_VOICE=en-US-JennyNeural
KAKAO_CLIENT_ID=Kakao REST API 키
KAKAO_CLIENT_SECRET=
KAKAO_REDIRECT_URI=https://daeun.d2pvyyx48vb41m.amplifyapp.com/oauth/kakao/callback
```

`DATABASE_URL`, `JWT_SECRET_KEY`, `KAKAO_CLIENT_ID`의 실제 값은 채팅, 문서, Git에 올리지 않습니다.

## 6. 백엔드 배포 확인

CloudShell에서 상태 API를 확인합니다.

```bash
curl -i \
  https://ye-2469ae51f7464062b89344750f333459.ecs.ap-southeast-2.on.aws/health
```

정상 응답:

```json
{"status":"ok"}
```

RDS 연결까지 확인합니다.

```bash
curl -i \
  https://ye-2469ae51f7464062b89344750f333459.ecs.ap-southeast-2.on.aws/ready
```

정상 응답:

```json
{"status":"ok","database":"ok"}
```

현재 적용된 태스크 정의 개정도 확인할 수 있습니다.

```bash
aws ecs describe-express-gateway-service \
  --region ap-southeast-2 \
  --service-arn arn:aws:ecs:ap-southeast-2:054422645032:service/default/yeongcha-backend \
  --query 'service.activeConfigurations[0].taskDefinitionArn' \
  --output text
```

## 7. Amplify 프론트엔드 배포 확인

GitHub `daeun` 브랜치에 푸시하면 Amplify가 자동으로 프론트엔드를 빌드합니다.

1. AWS 콘솔에서 **AWS Amplify**로 이동합니다.
2. 앱 **POPO**를 선택합니다.
3. 브랜치 **daeun**의 최신 배포를 선택합니다.
4. `Provision → Build → Deploy → Verify`가 모두 성공했는지 확인합니다.
5. 자동 빌드가 시작되지 않았다면 브랜치 화면에서 **이 버전 재배포**를 선택합니다.

Amplify 빌드 설정은 저장소 루트의 `amplify.yml`을 사용합니다. 모노레포 앱 루트는 `frontend`, 출력 디렉터리는 `dist`입니다.

Amplify 환경 변수:

```env
AMPLIFY_MONOREPO_APP_ROOT=frontend
VITE_API_BASE_URL=https://ye-2469ae51f7464062b89344750f333459.ecs.ap-southeast-2.on.aws/api/v1
VITE_KAKAO_CLIENT_ID=Kakao REST API 키
VITE_KAKAO_REDIRECT_URI=https://daeun.d2pvyyx48vb41m.amplifyapp.com/oauth/kakao/callback
```

`AMPLIFY_DIFF_DEPLOY=false`는 있어도 되지만 필수는 아닙니다. Amplify Gen 2 백엔드, SSR, 쿠키 캐시 옵션은 사용하지 않습니다.

React Router 경로에서 404가 발생하지 않도록 **호스팅 → 다시 쓰기 및 리디렉션**에 다음 규칙이 있어야 합니다.

```json
[
  {
    "source": "/<*>",
    "status": "404-200",
    "target": "/index.html"
  }
]
```

## 8. Kakao 로그인 설정 확인

Kakao Developers의 앱 설정에 다음 Redirect URI가 등록되어 있어야 합니다.

```txt
https://daeun.d2pvyyx48vb41m.amplifyapp.com/oauth/kakao/callback
```

프론트엔드 `VITE_KAKAO_REDIRECT_URI`, 백엔드 `KAKAO_REDIRECT_URI`, Kakao Developers의 Redirect URI 세 값이 글자 하나까지 같아야 합니다.

## 9. 브라우저 최종 점검

Amplify 배포가 끝나면 다음 주소를 새 탭 또는 시크릿 창에서 엽니다.

```txt
https://daeun.d2pvyyx48vb41m.amplifyapp.com/start
```

다음 순서로 확인합니다.

1. 일반 회원가입과 로그인
2. Kakao 로그인과 콜백 복귀
3. 프로필 선택
4. 메인 화면과 책 이미지
5. 학습 시작, 스킵, 학습 완료
6. 스타일 아이템 구매 및 적용 후 포인트 감소
7. 리뷰의 단어 5단계와 문장 5단계
8. iPad Safari에서 화면 비율과 마이크 권한

브라우저에 이전 JavaScript가 남아 있으면 강력 새로고침하거나 Safari 사이트 데이터를 지운 후 다시 확인합니다.

## 10. DB 초기화와 콘텐츠 가져오기

일반 코드 배포 때는 실행하지 않습니다. 새 RDS를 만들었거나 seed 코드가 변경된 경우에만 실행합니다.

먼저 최신 태스크 정의 ARN을 변수에 저장합니다.

```bash
TASK_DEFINITION=$(aws ecs describe-express-gateway-service \
  --region ap-southeast-2 \
  --service-arn arn:aws:ecs:ap-southeast-2:054422645032:service/default/yeongcha-backend \
  --query 'service.activeConfigurations[0].taskDefinitionArn' \
  --output text)

echo "$TASK_DEFINITION"
```

필요한 작업 하나를 실행합니다. 아래 예시는 콘텐츠 가져오기입니다.

```bash
TASK_ARN=$(aws ecs run-task \
  --region ap-southeast-2 \
  --cluster default \
  --launch-type FARGATE \
  --task-definition "$TASK_DEFINITION" \
  --network-configuration 'awsvpcConfiguration={subnets=[subnet-09fb3d798fb8acb54],securityGroups=[sg-074df223dbc17fc0c],assignPublicIp=ENABLED}' \
  --overrides '{"containerOverrides":[{"name":"Main","command":["python","-m","app.seed.import_ai_content"]}]}' \
  --query 'tasks[0].taskArn' \
  --output text)

echo "$TASK_ARN"
```

완료를 기다리고 종료 코드를 확인합니다.

```bash
aws ecs wait tasks-stopped \
  --region ap-southeast-2 \
  --cluster default \
  --tasks "$TASK_ARN"

aws ecs describe-tasks \
  --region ap-southeast-2 \
  --cluster default \
  --tasks "$TASK_ARN" \
  --query 'tasks[0].containers[0].{ExitCode:exitCode,Reason:reason}' \
  --output table
```

`ExitCode`가 `0`이면 성공입니다. 실행 가능한 작업은 다음과 같습니다.

```txt
app.seed.init_db
app.seed.import_ai_levels
app.seed.import_ai_content
app.seed.create_demo_library
```

`init_db`는 새 DB 테이블 생성용입니다. 기존 운영 DB에서 반복 실행하기 전에 코드의 멱등성을 확인합니다.

## 11. 이번 포인트·리뷰 수정 배포 시 참고

이번 변경은 프론트엔드와 백엔드가 모두 변경되었으므로 Amplify와 ECS를 둘 다 재배포해야 합니다. DB 마이그레이션과 seed 실행은 필요하지 않습니다.

배포 후 사용자가 리뷰 화면에 들어오면 이미 완료된 챕터의 리뷰 카드가 자동 보강됩니다. 아직 복습 예정 시간이 되지 않은 카드는 다시 나오지 않으며, 한 챕터에서 서로 다른 원문을 최대한 3개 확보해 단어·문장 복습을 구성합니다.

## 문제 해결

### ECR push 인증 만료

```txt
denied: Your authorization token has expired
```

4장의 ECR 로그인 명령을 다시 실행한 뒤 `docker push`를 재시도합니다.

### 백엔드는 정상인데 프론트 요청이 CORS로 차단됨

ECS 환경 변수 `CORS_ORIGINS`가 아래 값인지 확인하고 백엔드를 새로 배포합니다.

```txt
https://daeun.d2pvyyx48vb41m.amplifyapp.com
```

끝에 `/`를 붙이지 않습니다.

### `/start` 또는 Kakao callback이 404

Amplify의 다시 쓰기 및 리디렉션 규칙을 7장과 동일하게 저장한 후 다시 접속합니다.

### 백엔드가 새 코드로 바뀌지 않음

CloudShell에서 `git pull origin daeun`을 다시 확인하고, Docker 이미지를 다시 빌드·푸시한 뒤 ECS에서 새 서비스 개정을 배포합니다. ECR에 이미지를 푸시하는 것만으로 실행 중인 ECS 태스크가 자동 교체되지는 않습니다.

### 롤백

- Amplify: 브랜치의 이전 성공 빌드를 선택해 **이 버전 재배포**합니다.
- ECS: 서비스 업데이트에서 이전 서비스 개정 또는 이전 이미지 digest를 선택해 다시 배포합니다.
- DB: 코드 롤백과 DB 롤백은 별개입니다. 스키마 변경이 있었다면 해당 마이그레이션의 롤백 절차를 따릅니다.
