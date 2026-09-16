import type { Book } from '../types'
import { IMAGES } from '../constants/assets'

export function resolveBookCover(book?: Pick<Book, 'id' | 'title' | 'coverImage'> | null): string {
  if (!book) return IMAGES.bookBtnUnselected
  return book.coverImage?.trim() || IMAGES.bookBtnUnselected
}
