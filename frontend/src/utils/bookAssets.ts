import type { Book } from '../types'
import { IMAGES } from '../constants/assets'

export function normalizeBookTitle(title: string): string {
  return title.toLowerCase().replace(/^the\s+/, '').replace(/[^a-z0-9]/g, '')
}

export function resolveBookCover(book?: Pick<Book, 'id' | 'title' | 'coverImage'> | null): string {
  if (!book) return IMAGES.bookBtnUnselected
  return book.coverImage?.trim() || IMAGES.bookBtnUnselected
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
