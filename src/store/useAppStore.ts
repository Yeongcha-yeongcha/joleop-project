import { create } from 'zustand'
import type { Book, UserStats } from '../types'

interface AppStore {
  selectedBook: Book | null
  userStats: UserStats
  selectBook: (book: Book) => void
  clearBook: () => void
}

export const useAppStore = create<AppStore>((set) => ({
  selectedBook: null,
  userStats: {
    streak: 15,
    hearts: 210,
    xpPercent: 0.7,
  },
  selectBook: (book) => set({ selectedBook: book }),
  clearBook: () => set({ selectedBook: null }),
}))
