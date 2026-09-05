import type { Book } from '../types'

export interface BookChapter {
  chapterNumber: number
  label: string
  theme: string
}

const levelOneThemes = [
  'Popo and friends hear a tiny bird in Sunflower Meadow.',
  'The friends find the baby bird trapped in the thorny bush.',
  'Popo tries to help, but gets stuck too.',
  'Toto uses quick thinking to free Popo.',
  'The friends build a pulley together.',
  'Strong winds make the rescue harder.',
  'Pipi spots a safer path in the tree.',
  'Momo digs a small trench to protect the bird.',
  'The baby bird returns to its family.',
  'Popo and friends make a birdhouse for the meadow.',
]

export function chaptersForBook(book?: Book | null): BookChapter[] {
  const total = book?.totalLessons ?? 10
  return Array.from({ length: total }, (_, index) => {
    const chapterNumber = index + 1
    return {
      chapterNumber,
      label: `Chapter ${chapterNumber}`,
      theme: levelOneThemes[index] ?? `Chapter ${chapterNumber}`,
    }
  })
}
