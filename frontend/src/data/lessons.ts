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
      { id: 'p1', text: 'Dori is a little dragon with shiny yellow wings.', imageColor: '#B8D4E8' },
      { id: 'p2', text: 'He lives in a warm cave near the green forest.', imageColor: '#E8C4A0' },
      { id: 'p3', text: 'Today, Dori wants to fly above the tall trees.', imageColor: '#C4D4B8' },
      { id: 'p4', text: 'Mia says, "Take a deep breath and flap your wings."', imageColor: '#F6D98B' },
      { id: 'p5', text: 'Dori jumps, flaps, and flies over the sunny hill.', imageColor: '#D4B8E8' },
    ],
    quiz: {
      question: 'Q. Dori는 어디에 살고 있나요?',
      sentence: 'Dori lives in a warm',
      answer: 'cave.',
      imageColor: '#D4B8E8',
    },
    roleplay: {
      thumbnailColor: '#C4D4B8',
      mission: 'Dori가 날 수 있도록 영어로 용기를 주고 방법을 알려주기',
      missionSummary: 'Dori 날기 도와주기',
      turns: [
        {
          npc: 'I want to fly, but I feel a little scared.',
          user: 'You can do it, Dori!',
        },
        {
          npc: 'What should I do first?',
          user: 'Take a deep breath.',
        },
        {
          npc: 'Okay! What do I do next?',
          user: 'Flap your wings and try!',
        },
      ],
      finalNpc: 'I did it! Thank you for helping me fly!',
    },
  },
  {
    id: 'fresh-lemonade-lesson-1',
    bookId: 'fresh-lemonade',
    title: 'Fresh Lemonade! - lesson 1',
    pages: [
      { id: 'p1', text: 'Lina picks three lemons from a small tree.', imageColor: '#FFE07A' },
      { id: 'p2', text: 'She squeezes the lemons into a big glass jar.', imageColor: '#FFD2A1' },
      { id: 'p3', text: 'Her brother adds cold water and two spoons of sugar.', imageColor: '#AEE8FF' },
      { id: 'p4', text: 'They stir the lemonade until it tastes sweet.', imageColor: '#BFEA8A' },
    ],
    quiz: {
      question: 'Q. Lina는 무엇을 땄나요?',
      sentence: 'Lina picks three',
      answer: 'lemons.',
      imageColor: '#FFE07A',
    },
    roleplay: {
      thumbnailColor: '#FFE07A',
      mission: '레모네이드 가게에서 공손하게 주문하고 고맙다고 말하기',
      missionSummary: '레모네이드 주문하기',
      turns: [
        { npc: 'Welcome! Would you like some fresh lemonade?', user: 'Yes, please.' },
        { npc: 'How many cups would you like?', user: 'One lemonade, please.' },
        { npc: 'Here you go!', user: 'Thank you!' },
      ],
      finalNpc: 'You are welcome! Enjoy your lemonade.',
    },
  },
  {
    id: 'snack-museum-lesson-1',
    bookId: 'snack-museum',
    title: 'The Snack Museum - lesson 1',
    pages: [
      { id: 'p1', text: 'Momo visits a museum full of funny snacks.', imageColor: '#F8D2E5' },
      { id: 'p2', text: 'A cookie statue smiles beside a chocolate door.', imageColor: '#D8B08C' },
      { id: 'p3', text: 'Momo sees popcorn clouds above the tiny train.', imageColor: '#FFF0B5' },
      { id: 'p4', text: 'At the end, she draws her favorite snack.', imageColor: '#C8E7FF' },
    ],
    quiz: {
      question: 'Q. Momo는 무엇 구름을 봤나요?',
      sentence: 'Momo sees popcorn',
      answer: 'clouds.',
      imageColor: '#FFF0B5',
    },
    roleplay: {
      thumbnailColor: '#F8D2E5',
      mission: 'Momo에게 좋아하는 간식을 말하고 질문 하나 하기',
      missionSummary: '간식 박물관 대화하기',
      turns: [
        { npc: 'This museum is full of snacks! Which snack do you like?', user: 'I like cookies.' },
        { npc: 'Cookies are great! Do you have a question?', user: 'What is your favorite snack?' },
      ],
      finalNpc: 'My favorite snack is popcorn. Good question!',
    },
  },
]

/** bookId로 해당 책의 첫 번째 레슨을 반환합니다. */
export function getLessonByBookId(bookId: string): Lesson | undefined {
  return LESSONS.find((l) => l.bookId === bookId)
}
