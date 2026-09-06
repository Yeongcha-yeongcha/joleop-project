# Dino Linkgo — 프론트엔드 → 백엔드 API 명세

> 현재 프론트엔드는 **목업 데이터**로 동작합니다.
> 아래 API가 구현되면 각 파일의 `TODO` 주석 위치에서 교체하면 됩니다.

---

## 1. 사용자 통계

### `GET /users/me/stats`
사용자의 학습 통계를 반환합니다.

**Response**
```json
{
  "streak": 15,
  "hearts": 210,
  "xpPercent": 0.7
}
```

**연결 위치** : `src/store/useAppStore.ts` → `userStats` 초기값

---

## 2. 책 목록

### `GET /books`
전체 책 목록을 반환합니다.

**Response**
```json
[
  {
    "id": "dragon-story",
    "title": "The Dragon Story",
    "coverColor": "#D94F4F",
    "coverImage": "https://cdn.example.com/covers/dragon-story.png",
    "level": 1,
    "totalLessons": 5,
    "currentLesson": 1,
    "progress": 0.3,
    "status": "reading",
    "currentText": "I'm reading a book"
  }
]
```

**status 값**
| 값 | 의미 |
|---|---|
| `reading` | 진행 중 |
| `done` | 완료 |
| `available` | 시작 가능 |
| `locked` | 잠김 (클릭 불가) |

**연결 위치** : `src/data/books.ts` → `BOOKS` 배열

---

## 3. 레슨 콘텐츠

### `GET /books/:bookId/lessons/:lessonId`
해당 레슨의 페이지(씬) 목록을 반환합니다.

**Response**
```json
{
  "id": "dragon-story-lesson-1",
  "bookId": "dragon-story",
  "title": "The Dragon Story - lesson 1",
  "pages": [
    {
      "id": "p1",
      "text": "I'm reading a book.",
      "imageColor": "#B8D4E8",
      "imageUrl": "https://cdn.example.com/illustrations/p1.png"
    }
  ]
}
```

**연결 위치** : `src/data/lessons.ts` → `LESSONS` 배열, `getLessonByBookId()`

---

## 4. 학습 완료 처리

### `POST /users/me/progress`
레슨 완료 시 진도를 기록합니다.

**Request Body**
```json
{
  "bookId": "dragon-story",
  "lessonId": "dragon-story-lesson-1",
  "completedAt": "2026-05-20T12:00:00Z"
}
```

**연결 위치** : `src/pages/LearnPage/LearnPage.tsx` → `goToNextScene()` 마지막 씬 완료 분기

---

## 5. 음성 인식 (따라말하기)

### `POST /speech/recognize`
녹음 데이터를 전송하고 정답 여부를 반환합니다.

**Request** : `multipart/form-data`
| 필드 | 타입 | 설명 |
|---|---|---|
| `audio` | File | 녹음 파일 (webm / wav) |
| `expected` | string | 정답 문장 |

**Response**
```json
{
  "recognized": "I'm reading a book.",
  "correct": true,
  "score": 0.95
}
```

**연결 위치** : `src/pages/LearnPage/LearnPage.tsx` → `handleMicTap()` 내 `setTimeout` 제거 후 교체

---

## 6. 타입 정의 위치

백엔드 응답 스펙과 맞춰야 하는 인터페이스는 모두 아래 파일에 있습니다.

```
src/types/index.ts
```

---

## 7. 에셋 경로 규칙

```
public/
├── images/   ← 앱 이미지 (PNG)
└── fonts/    ← KCC-Ganpan 폰트
```

이미지 경로 상수는 `src/constants/assets.ts`에서 관리합니다.
CDN 이미지로 교체 시 이 파일의 값만 수정하면 됩니다.
