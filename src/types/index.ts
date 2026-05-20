// ─────────────────────────────────────────
// 앱 전역 타입 정의
// 백엔드 API 응답 스펙과 맞춰야 하는 핵심 인터페이스입니다.
// ─────────────────────────────────────────

/** 책의 진행 상태 */
export type BookStatus = 'reading' | 'done' | 'locked' | 'available'

/** 레슨 내 개별 페이지 (씬) */
export interface LessonPage {
  id: string
  text: string           // 화면에 표시되는 영어 문장
  imageColor: string     // 일러스트 배경색 (임시 — 실제 imageUrl로 교체 예정)
  imageUrl?: string      // 일러스트 이미지 URL (백엔드 연동 후 사용)
}

/** 레슨 (책 한 권의 학습 단위) */
export interface Lesson {
  id: string
  bookId: string
  title: string          // e.g. "The Dragon Story - lesson 1"
  pages: LessonPage[]
}

/** 책 한 권의 메타 정보 */
export interface Book {
  id: string
  title: string
  coverColor: string     // 커버 대표 색상 (이미지 로딩 전 placeholder)
  coverImage?: string    // 커버 이미지 URL
  level: number          // 난이도 (1~N)
  totalLessons: number
  currentLesson: number  // 현재 진행 중인 레슨 번호
  progress: number       // 0~1 (전체 진도율)
  status: BookStatus
  currentText?: string   // 홈 카드에 표시되는 한 줄 설명
}

/** 사용자 학습 통계 */
export interface UserStats {
  streak: number         // 연속 학습 일수
  hearts: number         // 보유 하트
  xpPercent: number      // XP 진행률 (0~1)
}
