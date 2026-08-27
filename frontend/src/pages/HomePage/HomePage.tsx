import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppStore } from '../../store/useAppStore'
import StatsBar from '../../components/StatsBar/StatsBar'
import BottomNav from '../../components/BottomNav/BottomNav'
import styles from './HomePage.module.css'

export default function HomePage() {
  const navigate = useNavigate()
  const { selectedBook, userStats, loadUserStats } = useAppStore()

  useEffect(() => { loadUserStats() }, [loadUserStats])

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
            src="/images/HomeLionBook.png"
            alt=""
            className={styles.lionImg}
            onError={(event) => {
              event.currentTarget.src = '/images/StartLion.png'
            }}
          />
          <button
            className={`${styles.heldBook} ${selectedBook?.coverImage ? styles.heldBookSelected : ''}`}
            onClick={() => navigate('/books')}
            aria-label={selectedBook ? '책 바꾸기' : '책 선택하기'}
          >
            {selectedBook?.coverImage ? (
              <img src={selectedBook.coverImage} alt="" />
            ) : (
              <span>?</span>
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
          {selectedBook?.coverImage ? (
            <img src={selectedBook.coverImage} alt="" className={styles.bookCover} />
          ) : (
            <div className={styles.emptyCover}>
              <span>+</span>
            </div>
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
