/**
 * 책 목록 목업 데이터
 * TODO: 백엔드 연동 시 GET /books API 응답으로 교체
 *
 * coverImage 경로 규칙:
 *   - 서비스 책: 백엔드에서 CDN URL로 제공
 *   - 샘플(현재): /images/BookSample_A·B·C.png
 *   - 잠금: coverImage 없음 → BookCard에서 /images/Book_locked.png 사용
 */

import type { Book } from '../types'
import { IMAGES } from '../constants/assets'

export const BOOKS: Book[] = [
  // ── 진행 중 / 완료 / 시작 가능 ──────────────────
  {
    id: 'dragon-story',
    title: 'The Dragon Story',
    coverColor: '#D94F4F',
    coverImage: IMAGES.bookSamples.A,
    level: 1,
    totalLessons: 5,
    currentLesson: 1,
    progress: 0.3,
    status: 'reading',
    currentText: "I'm reading a book",
  },
  {
    id: 'fresh-lemonade',
    title: 'Fresh Lemonade!',
    coverColor: '#5FC85A',
    coverImage: IMAGES.bookSamples.B,
    level: 1,
    totalLessons: 5,
    currentLesson: 5,
    progress: 1,
    status: 'done',
    currentText: 'Completed!',
  },
  {
    id: 'snack-museum',
    title: 'The Snack Museum',
    coverColor: '#F0D44A',
    coverImage: IMAGES.bookSamples.C,
    level: 1,
    totalLessons: 5,
    currentLesson: 1,
    progress: 0,
    status: 'available',
    currentText: 'Start reading',
  },

  // ── 잠금 (coverImage 없음) ───────────────────────
  { id: 'bad-morning',    title: 'Bad Morning',    coverColor: '#D94F4F', level: 1, totalLessons: 5, currentLesson: 1, progress: 0, status: 'locked' },
  { id: 'little-star',    title: 'Little Star',    coverColor: '#D94F4F', level: 1, totalLessons: 5, currentLesson: 1, progress: 0, status: 'locked' },
  { id: 'sunny-day',      title: 'Sunny Day',      coverColor: '#D94F4F', level: 1, totalLessons: 5, currentLesson: 1, progress: 0, status: 'locked' },
  { id: 'magic-forest',   title: 'Magic Forest',   coverColor: '#D94F4F', level: 1, totalLessons: 5, currentLesson: 1, progress: 0, status: 'locked' },
  { id: 'ocean-friends',  title: 'Ocean Friends',  coverColor: '#D94F4F', level: 1, totalLessons: 5, currentLesson: 1, progress: 0, status: 'locked' },
  { id: 'cloud-castle',   title: 'Cloud Castle',   coverColor: '#D94F4F', level: 1, totalLessons: 5, currentLesson: 1, progress: 0, status: 'locked' },
  { id: 'rainbow-bridge', title: 'Rainbow Bridge', coverColor: '#D94F4F', level: 1, totalLessons: 5, currentLesson: 1, progress: 0, status: 'locked' },
  { id: 'tiny-robot',     title: 'Tiny Robot',     coverColor: '#D94F4F', level: 1, totalLessons: 5, currentLesson: 1, progress: 0, status: 'locked' },
  { id: 'jungle-race',    title: 'Jungle Race',    coverColor: '#D94F4F', level: 1, totalLessons: 5, currentLesson: 1, progress: 0, status: 'locked' },
  { id: 'moon-cake',      title: 'Moon Cake',      coverColor: '#D94F4F', level: 1, totalLessons: 5, currentLesson: 1, progress: 0, status: 'locked' },
  { id: 'deep-sea',       title: 'Deep Sea',       coverColor: '#D94F4F', level: 1, totalLessons: 5, currentLesson: 1, progress: 0, status: 'locked' },
  { id: 'star-patrol',    title: 'Star Patrol',    coverColor: '#D94F4F', level: 1, totalLessons: 5, currentLesson: 1, progress: 0, status: 'locked' },
]
