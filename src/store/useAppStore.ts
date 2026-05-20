/**
 * 앱 전역 상태 (Zustand)
 *
 * - selectedBook : 홈 화면에서 선택된 책. 학습 시작 / 진도 표시에 사용.
 * - userStats    : 스탯 바(🔥 💜 ⚡)에 표시되는 사용자 통계.
 *                  → 백엔드 연동 시 로그인 후 API로 받아와 초기화합니다.
 */

import { create } from 'zustand'
import type { Book, UserStats } from '../types'

interface AppStore {
  selectedBook: Book | null
  userStats: UserStats
  selectBook: (book: Book) => void
  clearBook: () => void
}

export const useAppStore = create<AppStore>((set) => ({
  // 초기값: 책 미선택
  selectedBook: null,

  // TODO: 백엔드 연동 시 GET /users/me/stats 응답으로 교체
  userStats: {
    streak: 15,
    hearts: 210,
    xpPercent: 0.7,
  },

  selectBook: (book) => set({ selectedBook: book }),
  clearBook: () => set({ selectedBook: null }),
}))
