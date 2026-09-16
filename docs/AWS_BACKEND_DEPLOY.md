# AWS 백엔드 배포

현재 POPO 백엔드는 App Runner가 아니라 **Amazon ECR + Amazon ECS Express Mode**로 배포합니다.

Git 푸시, CloudShell Docker 빌드, ECR 푸시, ECS 서비스 개정 배포, 상태 확인, DB seed 실행을 포함한 최신 절차는 [AWS_DEPLOY.md](./AWS_DEPLOY.md)를 따르세요.

핵심 배포 단위:

```txt
Dockerfile: backend/Dockerfile
Docker build context: 저장소 루트
ECR repository: yeongcha-backend
ECS cluster: default
ECS Express service: yeongcha-backend
Container port: 8000
Health check: /health
Readiness check: /ready
```
