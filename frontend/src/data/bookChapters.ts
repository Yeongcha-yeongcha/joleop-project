import type { Book } from '../types'

export interface BookChapter {
  chapterNumber: number
  label: string
  theme: string
}

export function chaptersForBook(book?: Book | null): BookChapter[] {
  const total = book?.totalLessons ?? 10
  return Array.from({ length: total }, (_, index) => {
    const chapterNumber = index + 1
    return {
      chapterNumber,
      label: `Chapter ${chapterNumber}`,
      theme: `Chapter ${chapterNumber}`,
    }
  })
}
