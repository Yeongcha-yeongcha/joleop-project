export type BookStatus = 'reading' | 'done' | 'locked' | 'available'

export interface LessonPage {
  id: string
  text: string
  imageColor: string // 임시: 실제 이미지로 교체 예정
  imageUrl?: string
}

export interface Lesson {
  id: string
  bookId: string
  title: string        // e.g. "Snow white - lesson 1"
  pages: LessonPage[]
}

export interface Book {
  id: string
  title: string
  coverColor: string
  coverImage?: string
  level: number
  totalLessons: number
  currentLesson: number
  progress: number // 0~1
  status: BookStatus
  currentText?: string
}

export interface UserStats {
  streak: number
  hearts: number
  xpPercent: number // 0~1
}
