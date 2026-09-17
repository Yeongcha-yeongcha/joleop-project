import type { Book } from '../types'
import { IMAGES } from '../constants/assets'

export function resolveBookCover(book?: Pick<Book, 'id' | 'title' | 'coverImage'> | null): string {
  if (!book) return IMAGES.bookBtnUnselected
  return book.coverImage?.trim() || IMAGES.bookBtnUnselected
}

function hashBookKey(book: Pick<Book, 'id' | 'title'>): number {
  const key = `${book.id}:${book.title}`
  let hash = 0
  for (let index = 0; index < key.length; index += 1) {
    hash = (hash * 31 + key.charCodeAt(index)) >>> 0
  }
  return hash
}

function pad2(value: number): string {
  return String(Math.max(1, value)).padStart(2, '0')
}

export function resolveBookSceneImage(book: Pick<Book, 'id' | 'title' | 'level' | 'currentLesson'>): string {
  const lessonNumber = pad2(book.currentLesson || 1)
  const pageNumber = pad2((hashBookKey(book) % 10) + 1)
  return `/images/pages/level${book.level}/lesson${lessonNumber}/p${pageNumber}.webp`
}

export function resolveBookSceneFallbacks(book: Pick<Book, 'id' | 'title' | 'level' | 'currentLesson'>): string[] {
  const pageNumber = pad2((hashBookKey(book) % 10) + 1)
  return [
    `/images/pages/level${book.level}/lesson01/p${pageNumber}.webp`,
    `/images/pages/level${book.level}/lesson01/p01.webp`,
  ]
}
