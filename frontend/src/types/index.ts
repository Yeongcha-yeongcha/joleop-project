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
  audioUrl?: string      // 읽기/따라말하기 오디오 URL (백엔드 연동 후 사용)
}

/** 롤플레잉 대화 한 턴 */
export interface RoleplayTurn {
  npc: string    // 상대방 대사
  user: string   // 사용자 예시 대사
}

/** 레슨 말미 롤플레잉 미션 */
export interface RoleplayMission {
  thumbnailColor: string   // 썸네일 원형 배경색 (이미지 없을 때 플레이스홀더)
  thumbnailUrl?: string
  mission: string          // 인트로 카드 전체 미션 설명 (\n 사용 가능)
  missionSummary: string   // 채팅창 상단 한 줄 요약
  turns: RoleplayTurn[]    // 대화 턴 목록 (사용자 응답 포함)
  finalNpc: string         // 사용자 마지막 답변 후 상대방의 마지막 버블
}

/** 레슨 말미 묘사 퀴즈 */
export interface QuizQuestion {
  question: string       // "Q. 여왕의 옷 색이 무엇인가요?"
  sentence: string       // 빈칸 앞 문장 (e.g. "The color of the queen's clothes is")
  answer: string         // 빈칸 정답 (e.g. "red.")
  imageColor: string
  imageUrl?: string
}

/** 레슨 (책 한 권의 학습 단위) */
export interface Lesson {
  id: string
  bookId: string
  title: string          // e.g. "The Dragon Story - lesson 1"
  pages: LessonPage[]
  quiz?: QuizQuestion
  roleplay?: RoleplayMission
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
  energy?: number
  maxEnergy?: number
  energyRechargeMinutes?: number
  nextEnergyInSeconds?: number
  attendanceDates?: string[]
}
