import { create } from 'zustand'
import type { Book, UserStats } from '../types'
import { fetchUserStats } from '../services/api'

interface AppStore {
  selectedBook: Book | null
  userStats: UserStats
  selectBook: (book: Book) => void
  clearBook: () => void
  loadUserStats: () => Promise<void>
}

export const useAppStore = create<AppStore>((set) => ({
  selectedBook: null,
  userStats: { streak: 0, hearts: 0, xpPercent: 0 },

  selectBook: (book) => set({ selectedBook: book }),
  clearBook: () => set({ selectedBook: null }),

  loadUserStats: async () => {
    try {
      const stats = await fetchUserStats()
      set({ userStats: stats })
    } catch {
      // stats 실패 시 기본값 유지 — 홈 화면 자체는 정상 작동
    }
  },
}))
