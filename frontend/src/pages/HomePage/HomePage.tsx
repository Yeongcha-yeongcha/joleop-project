import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppStore } from '../../store/useAppStore'
import StatsBar from '../../components/StatsBar/StatsBar'
import BottomNav from '../../components/BottomNav/BottomNav'
import { BOOKS } from '../../data/books'
import { fetchHome, usesBackendApi } from '../../services/api'
import styles from './HomePage.module.css'

const CUSTOMIZATION_KEY = 'yeongcha:customization'

interface CustomizationState {
  characterItem?: string
  rug?: string
  lamp?: string
  roomItem?: string
}

function readCustomization(): CustomizationState {
  try {
    return JSON.parse(window.localStorage.getItem(CUSTOMIZATION_KEY) || '{}')
  } catch {
    return {}
  }
}

function normalizeBookTitle(title: string): string {
  return title.toLowerCase().replace(/^the\s+/, '').replace(/[^a-z0-9]/g, '')
}

function fallbackCoverImage(title?: string): string | undefined {
  if (!title) return undefined
  return BOOKS.find((book) => normalizeBookTitle(book.title) === normalizeBookTitle(title))?.coverImage
}

export default function HomePage() {
  const navigate = useNavigate()
  const { selectedBook, userStats, loadUserStats, selectBook } = useAppStore()
  const [customization, setCustomization] = useState<CustomizationState>(() => readCustomization())

  useEffect(() => {
    if (!usesBackendApi()) {
      loadUserStats()
      return
    }
    fetchHome()
      .then((home) => {
        if (home.currentBook && !selectedBook) selectBook(home.currentBook)
        useAppStore.setState({ userStats: home.stats })
      })
      .catch(() => {
        loadUserStats()
      })
  }, [loadUserStats, selectBook, selectedBook])

  useEffect(() => {
    const syncCustomization = () => setCustomization(readCustomization())
    window.addEventListener('storage', syncCustomization)
    window.addEventListener('focus', syncCustomization)
    return () => {
      window.removeEventListener('storage', syncCustomization)
      window.removeEventListener('focus', syncCustomization)
    }
  }, [])

  const selectedBookCover = selectedBook?.coverImage ?? fallbackCoverImage(selectedBook?.title)
  const roomClass = useMemo(() => [
    customization.rug ? styles[`rug_${customization.rug}`] : '',
    customization.lamp ? styles[`lamp_${customization.lamp}`] : '',
  ].filter(Boolean).join(' '), [customization.rug, customization.lamp])

  const handleStart = () => {
    if (!selectedBook) return
    navigate(`/learn/${selectedBook.id}`)
  }

  return (
    <div className={styles.page}>
      <div className={styles.scrim} />
      <header className={styles.header}>
        <StatsBar stats={userStats} onCustomize={() => navigate('/customize')} />
      </header>

      <section className={`${styles.hero} ${roomClass}`}>
        <div className={styles.room} aria-hidden="true">
          <div className={styles.wallArt} />
          <div className={styles.floorLamp} />
          <div className={styles.sofa} />
          <div className={styles.rug} />
          {customization.roomItem === 'bookcase' && <div className={styles.bookcase} />}
          {customization.roomItem === 'mirror' && <div className={styles.mirror} />}
          {customization.roomItem === 'plant' && <div className={styles.bigPlant} />}
          {customization.roomItem === 'puppy' && <div className={styles.puppy} />}
        </div>
        <div className={styles.lionStage}>
          <img
            src="/images/HomeBearHands.png"
            alt=""
            className={styles.lionImg}
            onError={(event) => {
              event.currentTarget.src = '/images/HomeLionBook.png'
            }}
          />
          {customization.characterItem === 'hat' && <span className={styles.hat} aria-hidden="true" />}
          {customization.characterItem === 'sunglasses' && <span className={styles.sunglasses} aria-hidden="true" />}
          {customization.characterItem === 'necklace' && <span className={styles.necklace} aria-hidden="true" />}
          {customization.characterItem === 'earrings' && <span className={styles.earrings} aria-hidden="true" />}
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
