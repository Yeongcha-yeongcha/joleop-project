import type { Book } from '../types'
import { BOOKS } from '../data/books'
import { IMAGES } from '../constants/assets'

export function normalizeBookTitle(title: string): string {
  return title.toLowerCase().replace(/^the\s+/, '').replace(/[^a-z0-9]/g, '')
}

export function localBookFor(book: Pick<Book, 'id' | 'title'>): Book | undefined {
  const normalizedTitle = normalizeBookTitle(book.title)
  return BOOKS.find((localBook) => (
    localBook.id === book.id ||
    normalizeBookTitle(localBook.title) === normalizedTitle
  ))
}

export function fallbackCoverImage(title?: string): string | undefined {
  if (!title) return undefined
  return BOOKS.find((book) => normalizeBookTitle(book.title) === normalizeBookTitle(title))?.coverImage
}

export function resolveBookCover(book?: Pick<Book, 'id' | 'title' | 'coverImage'> | null): string {
  if (!book) return IMAGES.bookBtnUnselected
  const localCover = localBookFor(book)?.coverImage
  return book.coverImage?.trim() || localCover || IMAGES.bookBtnUnselected
}

export function resolveHeroBackgroundImage(book?: Pick<Book, 'title'> | null): string | undefined {
  const normalized = normalizeBookTitle(book?.title ?? '')
  if (normalized.includes('dragon')) return IMAGES.bookBackgrounds.dragon
  if (normalized.includes('lemonade')) return IMAGES.bookBackgrounds.lemonade
  if (normalized.includes('snack')) return IMAGES.bookBackgrounds.snack
  if (normalized.includes('ocean') || normalized.includes('sea')) return IMAGES.bookBackgrounds.ocean
  if (normalized.includes('forest') || normalized.includes('jungle')) return IMAGES.bookBackgrounds.forest
  if (normalized.includes('star') || normalized.includes('moon') || normalized.includes('space')) return IMAGES.bookBackgrounds.space
  return undefined
}
