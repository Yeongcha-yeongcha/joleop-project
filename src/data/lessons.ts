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
    quiz: {
      question: 'Q. 드래곤은 무엇을 하고 있나요?',
      sentence: 'The dragon is',
      answer: 'flying.',
      imageColor: '#D4B8E8',
    },
    roleplay: {
      thumbnailColor: '#C4D4B8',
      mission: '거울이 되어, 여왕님이 화내지 않도록\n예쁘다고 칭찬해주기',
      missionSummary: '거울이 되어 여왕님 칭찬해주기',
      turns: [
        {
          npc: 'Mirror mirror on the wall, who is the most beautiful of them all?',
          user: 'Of course it\'s you, Queen!',
        },
        {
          npc: 'Really? Am I truly more beautiful than Snow White?',
          user: 'Yes! You are the most beautiful in the whole world!',
        },
        {
          npc: 'Ha ha ha! That\'s exactly what I wanted to hear!',
          user: 'You are the fairest of them all, my Queen!',
        },
      ],
      finalNpc: 'Ha ha ha! I knew it! Now go away, mirror!',
    },
  },
]

/** bookId로 해당 책의 첫 번째 레슨을 반환합니다. */
export function getLessonByBookId(bookId: string): Lesson | undefined {
  return LESSONS.find((l) => l.bookId === bookId)
}
