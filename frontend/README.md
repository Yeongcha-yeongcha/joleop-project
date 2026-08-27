# 라이온 — 프론트엔드

## 기술 스택

- React 19 + TypeScript
- Vite
- Zustand (전역 상태)
- React Router v7
- CSS Modules

## 시작하기

```bash
npm install
npm run dev
```

브라우저에서 `http://localhost:5173` 열기 (모바일 사이즈 430px 권장)

## 백엔드 연동

### 1. 환경 변수 설정

```bash
cp .env.example .env.local
# .env.local 에서 VITE_API_BASE_URL 값을 백엔드 주소로 변경
```

### 2. API 연결 지점

모든 API 호출은 **`src/services/api.ts`** 한 파일에 모여 있습니다.
각 함수의 `TODO:` 주석 아래 mock return을 실제 fetch로 교체하면 됩니다.

| 함수 | 메서드 | 엔드포인트 |
|---|---|---|
| `fetchUserStats` | GET | `/users/me/stats` |
| `fetchBooks` | GET | `/books` |
| `fetchLesson` | GET | `/books/:bookId/lessons/:lessonId` |
| `postProgress` | POST | `/users/me/progress` |
| `postSpeechRecognize` | POST | `/speech/recognize` |

자세한 요청/응답 스펙은 **`API_SPEC.md`** 를 참고하세요.

## 폴더 구조

```
src/
├── services/       ← API 호출 (백엔드 연동 지점)
├── types/          ← API 응답과 맞춰야 하는 인터페이스
├── store/          ← Zustand 전역 상태
├── pages/          ← 화면 단위 컴포넌트
│   ├── HomePage/
│   ├── BookChoicePage/
│   └── LearnPage/
├── components/     ← 재사용 컴포넌트
│   ├── StatsBar/
│   ├── BookCard/
│   └── LessonHeader/
├── data/           ← 목업 데이터 (API 연동 전 임시)
├── constants/      ← 이미지·에셋 경로 상수
└── index.css       ← 전역 스타일 + 폰트

public/
├── images/         ← PNG 에셋
└── fonts/          ← KCC-Ganpan 폰트 (eot / woff / woff2)
```

## 빌드

```bash
npm run build
# dist/ 폴더 결과물을 정적 서버에 배포
```
