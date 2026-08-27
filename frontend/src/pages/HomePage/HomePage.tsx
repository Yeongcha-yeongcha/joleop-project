import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppStore } from '../../store/useAppStore'
import StatsBar from '../../components/StatsBar/StatsBar'
import BottomNav from '../../components/BottomNav/BottomNav'
import { BOOKS } from '../../data/books'
import styles from './HomePage.module.css'

function normalizeBookTitle(title: string): string {
  return title.toLowerCase().replace(/^the\s+/, '').replace(/[^a-z0-9]/g, '')
}

function fallbackCoverImage(title?: string): string | undefined {
  if (!title) return undefined
  return BOOKS.find((book) => normalizeBookTitle(book.title) === normalizeBookTitle(title))?.coverImage
}

export default function HomePage() {
  const navigate = useNavigate()
  const { selectedBook, userStats, loadUserStats } = useAppStore()

  useEffect(() => { loadUserStats() }, [loadUserStats])

  const selectedBookCover = selectedBook?.coverImage ?? fallbackCoverImage(selectedBook?.title)

  const handleStart = () => {
    if (!selectedBook) return
    navigate(`/learn/${selectedBook.id}`)
  }

  return (
    <div className={styles.page}>
      <div className={styles.scrim} />
      <header className={styles.header}>
        <StatsBar stats={userStats} />
      </header>

      <section className={styles.hero}>
        <div className={styles.lionStage}>
          <img
            src="/images/HomeBearHands.png"
            alt=""
            className={styles.lionImg}
            onError={(event) => {
              event.currentTarget.src = '/images/HomeLionBook.png'
            }}
          />
          <button
            className={`${styles.heldBook} ${selectedBookCover ? styles.heldBookSelected : ''}`}
            onClick={() => navigate('/books')}
            aria-label={selectedBook ? '책 바꾸기' : '책 선택하기'}
          >
            {selectedBookCover ? (
              <img src={selectedBookCover} alt="" />
            ) : (
              <img src="/images/BookBtn_unselected.png" alt="" />
            )}
          </button>
        </div>
      </section>

      <section className={styles.panel}>
        <button
          className={`${styles.bookCard} ${!selectedBook ? styles.bookCardEmpty : ''}`}
          onClick={() => navigate('/books')}
          aria-label={selectedBook ? '책 바꾸기' : '책 선택하기'}
        >
          {selectedBookCover ? (
            <img src={selectedBookCover} alt="" className={styles.bookCover} />
          ) : (
            <img src="/images/BookBtn_unselected.png" alt="" className={styles.emptyCover} />
          )}
          <div className={styles.bookMeta}>
            <span className={styles.eyebrow}>{selectedBook ? 'Current Book' : 'Library'}</span>
            <strong>{selectedBook?.title ?? 'Choose a Book'}</strong>
            <span>{selectedBook ? `Lesson ${selectedBook.currentLesson} · ${selectedBook.currentText ?? 'Keep going!'}` : 'New stories are waiting.'}</span>
          </div>
        </button>

        <div className={styles.progressTrack}>
          <div
            className={styles.progressFill}
            style={{ width: `${selectedBook ? selectedBook.progress * 100 : 0}%` }}
          />
        </div>

        <button
          className={styles.startBtn}
          onClick={handleStart}
          disabled={!selectedBook}
        >
          {selectedBook ? 'Start Adventure' : 'Choose Book First'}
        </button>
      </section>
      <BottomNav />
    </div>
  )
}
