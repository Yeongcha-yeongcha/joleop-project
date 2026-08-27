# Yeongcha Workspace

This repository is arranged as a workspace with the backend and frontend kept in separate folders:

- `backend/`: FastAPI backend, synced with `project/backend`
- `frontend/`: Vite frontend, imported unchanged from `project/frontend`

## Syncing Branches

Use the helper scripts from the repository root:

```bash
./scripts/pull-backend.sh
./scripts/pull-frontend.sh
./scripts/push-backend.sh
./scripts/push-frontend.sh
```

The push scripts split the selected folder and push only that folder's contents back to the matching remote branch.
