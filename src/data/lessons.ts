/**
 * 레슨(학습 콘텐츠) 목업 데이터
 * TODO: 백엔드 연동 시 GET /books/:bookId/lessons/:lessonId API 응답으로 교체
 *
 * 페이지(씬) 구조:
 *   - text      : 화면에 표시되고 따라 말할 영어 문장
 *   - imageColor: 일러스트 영역 배경색 (실제 이미지 연동 전 임시값)
 *   - imageUrl  : 실제 일러스트 이미지 URL (백엔드 연동 후 사용)
 */

import type { Lesson } from '../types'

export const LESSONS: Lesson[] = [
  {
    id: 'dragon-story-lesson-1',
    bookId: 'dragon-story',
    title: 'The Dragon Story - lesson 1',
    pages: [
      { id: 'p1', text: "I'm reading a book.",  imageColor: '#B8D4E8' },
      { id: 'p2', text: 'She is reading a book.', imageColor: '#E8C4A0' },
      { id: 'p3', text: 'He is a dragon.',        imageColor: '#C4D4B8' },
      { id: 'p4', text: 'The dragon is flying.',  imageColor: '#D4B8E8' },
    ],
  },
]

/** bookId로 해당 책의 첫 번째 레슨을 반환합니다. */
export function getLessonByBookId(bookId: string): Lesson | undefined {
  return LESSONS.find((l) => l.bookId === bookId)
}
