import type { Lesson } from '../types'

export const LESSONS: Lesson[] = [
  {
    id: 'dragon-story-lesson-1',
    bookId: 'dragon-story',
    title: 'The Dragon Story - lesson 1',
    pages: [
      { id: 'p1', text: "I'm reading a book.", imageColor: '#B8D4E8' },
      { id: 'p2', text: 'She is reading a book.', imageColor: '#E8C4A0' },
      { id: 'p3', text: 'He is a dragon.', imageColor: '#C4D4B8' },
      { id: 'p4', text: 'The dragon is flying.', imageColor: '#D4B8E8' },
    ],
  },
]

export function getLessonByBookId(bookId: string): Lesson | undefined {
  return LESSONS.find((l) => l.bookId === bookId)
}
