import type { Book } from '../types'

export type ChapterStars = Record<string, number>

export interface ChapterResult {
  bookId: string
  chapterNumber: number
  stars: number
  totalScore: number
  message: string
  completedAt: string
  breakdown: {
    repeat: number | null
    description: number | null
    roleplay: number | null
  }
}

function activeProfileKey() {
  try {
    const profile = JSON.parse(window.localStorage.getItem('yeongcha:active-profile') || 'null') as {
      profileId?: number | string
    } | null
    return String(profile?.profileId ?? 'guest')
  } catch {
    return 'guest'
  }
}

export function chapterStarsKey(bookId: string) {
  return `yeongcha:chapter-stars:${activeProfileKey()}:${bookId}`
}

export function readChapterStars(bookId: string): ChapterStars {
  try {
    return JSON.parse(window.localStorage.getItem(chapterStarsKey(bookId)) || '{}') as ChapterStars
  } catch {
    return {}
  }
}

export function saveChapterStars(bookId: string, chapterNumber: number, stars: number) {
  const current = readChapterStars(bookId)
  const previous = current[String(chapterNumber)] ?? 0
  current[String(chapterNumber)] = Math.max(previous, Math.max(0, Math.min(3, stars)))
  window.localStorage.setItem(chapterStarsKey(bookId), JSON.stringify(current))
}

export function chapterResultsKey(bookId: string) {
  return `yeongcha:chapter-results:${activeProfileKey()}:${bookId}`
}

export function readChapterResults(bookId: string): Record<string, ChapterResult> {
  try {
    return JSON.parse(window.localStorage.getItem(chapterResultsKey(bookId)) || '{}') as Record<string, ChapterResult>
  } catch {
    return {}
  }
}

export function messageForScore(score: number) {
  if (score >= 90) return 'Excellent!'
  if (score >= 75) return 'Great job!'
  if (score >= 60) return 'Good work!'
  if (score >= 40) return 'Nice try!'
  return 'Try again!'
}

export function starsForScore(score: number) {
  if (score <= 39) return 0
  if (score <= 59) return 1
  if (score <= 79) return 2
  return 3
}

export function saveChapterResult(result: ChapterResult) {
  const current = readChapterResults(result.bookId)
  const previous = current[String(result.chapterNumber)]
  const nextResult = previous && previous.totalScore > result.totalScore ? previous : result
  current[String(result.chapterNumber)] = nextResult
  window.localStorage.setItem(chapterResultsKey(result.bookId), JSON.stringify(current))
  saveChapterStars(result.bookId, result.chapterNumber, nextResult.stars)
}

export function isChapterUnlocked(
  book: Book,
  chapterNumber: number,
  stars: ChapterStars,
  results: Record<string, ChapterResult> = {},
) {
  if (book.status === 'locked') return false
  if (chapterNumber === 1) return true
  const previousChapter = String(chapterNumber - 1)
  return previousChapter in results || (stars[previousChapter] ?? 0) > 0
}
