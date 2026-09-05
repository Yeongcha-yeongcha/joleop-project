import { type CSSProperties, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppStore } from '../../store/useAppStore'
import StatsBar from '../../components/StatsBar/StatsBar'
import { ApiError, clearProfileSession, fetchHome, usesBackendApi } from '../../services/api'
import {
  DEFAULT_HOME_BACKGROUND_THEME_ID,
  HOME_BACKGROUND_THEMES,
} from '../../data/homeBackgroundThemes'
import {
  fallbackCoverImage,
  resolveHeroBackgroundImage,
} from '../../utils/bookAssets'
import styles from './HomePage.module.css'

const HOME_THEME_KEY = 'yeongcha:home-background-theme'
const POPO_CUSTOMIZATION_KEY = 'yeongcha:popo-customization'

interface PopoCustomization {
  hat?: string
  glasses?: string
  necklace?: string
  outfit?: string
}

function readSelectedThemeId(): string {
  return window.localStorage.getItem(HOME_THEME_KEY) || DEFAULT_HOME_BACKGROUND_THEME_ID
}

function readPopoCustomization(): PopoCustomization {
  try {
    return JSON.parse(window.localStorage.getItem(POPO_CUSTOMIZATION_KEY) || '{}')
  } catch {
    return {}
  }
}

export default function HomePage() {
  const navigate = useNavigate()
  const { selectedBook, userStats, loadUserStats, selectBook } = useAppStore()
  const [selectedThemeId, setSelectedThemeId] = useState(readSelectedThemeId)
  const [popoCustomization, setPopoCustomization] = useState(readPopoCustomization)

  useEffect(() => {
    if (!usesBackendApi()) {
      loadUserStats()
      return
    }
    fetchHome()
      .then((home) => {
        if (home.currentBook && !selectedBook) selectBook(home.currentBook)
        useAppStore.setState({ userStats: home.stats })
        if (home.customization) {
          setSelectedThemeId(home.customization.selectedThemeId)
          setPopoCustomization(home.customization.selectedPopo)
        }
      })
      .catch((err: unknown) => {
        if (err instanceof ApiError && err.status === 401) {
          clearProfileSession()
          navigate('/profiles', { replace: true })
          return
        }
        loadUserStats()
      })
  }, [loadUserStats, navigate, selectBook, selectedBook])

  useEffect(() => {
    const syncSelectedTheme = () => setSelectedThemeId(readSelectedThemeId())
    const syncCustomization = () => {
      if (usesBackendApi()) {
        fetchHome()
          .then((home) => {
            if (home.customization) {
              setSelectedThemeId(home.customization.selectedThemeId)
              setPopoCustomization(home.customization.selectedPopo)
            }
          })
          .catch(() => undefined)
        return
      }
      syncSelectedTheme()
      setPopoCustomization(readPopoCustomization())
    }
    window.addEventListener('storage', syncCustomization)
    window.addEventListener('focus', syncCustomization)
    return () => {
      window.removeEventListener('storage', syncCustomization)
      window.removeEventListener('focus', syncCustomization)
    }
  }, [])

  const selectedTheme = useMemo(() => (
    HOME_BACKGROUND_THEMES.find((theme) => theme.id === selectedThemeId) ??
    HOME_BACKGROUND_THEMES[0]
  ), [selectedThemeId])

  const selectedBookCover = selectedBook?.coverImage ?? fallbackCoverImage(selectedBook?.title)
  const bookBackground = resolveHeroBackgroundImage(selectedBook)
  const activeBackground = bookBackground ?? selectedTheme.background
  const activeThemeClass = bookBackground ? styles.theme_book : styles[`theme_${selectedTheme.id}`]
  const normalizedBookTitle = (selectedBook?.title ?? '').toLowerCase()
  const isDarkTheme =
    selectedTheme.id === 'night-star-room' ||
    selectedTheme.id === 'space-adventure-room' ||
    normalizedBookTitle.includes('dragon') ||
    normalizedBookTitle.includes('star') ||
    normalizedBookTitle.includes('moon') ||
    normalizedBookTitle.includes('space')

  const handleStart = () => {
    if (!selectedBook) return
    navigate(`/books/${selectedBook.id}/chapters`)
  }

  return (
    <div
      className={`${styles.page} ${activeThemeClass ?? styles.theme_cream}`}
      style={{ '--home-background': `url("${activeBackground}")` } as CSSProperties}
    >
      <header className={styles.header}>
        <StatsBar stats={userStats} tone={isDarkTheme ? 'dark' : 'light'} onCustomize={() => navigate('/customize')} />
      </header>

      <section className={styles.hero} aria-label="Home">
        <div className={styles.backgroundLayer} aria-hidden="true" />
        <div className={styles.mascotStage}>
          <img
            src="/images/HomeBearHands.png"
            alt=""
            className={styles.mascot}
            onError={(event) => {
              event.currentTarget.src = '/images/HomeLionBook.png'
            }}
          />
          {popoCustomization.outfit && <span className={`${styles.popoOutfit} ${styles[`outfit_${popoCustomization.outfit}`]}`} />}
          {popoCustomization.hat && <span className={`${styles.popoHat} ${styles[`hat_${popoCustomization.hat}`]}`} />}
          {popoCustomization.glasses && <span className={`${styles.popoGlasses} ${styles[`glasses_${popoCustomization.glasses}`]}`} />}
          {popoCustomization.necklace && <span className={`${styles.popoNecklace} ${styles[`necklace_${popoCustomization.necklace}`]}`} />}
        </div>
        <button
          className={styles.heldBook}
          data-tour="held-book"
          onClick={() => navigate('/books')}
          aria-label={selectedBook ? 'Change book' : 'Pick a book'}
        >
          <img src={selectedBookCover || '/images/BookBtn_unselected.png'} alt="" />
        </button>
      </section>

      <section className={styles.panel}>
        <button
          className={styles.bookCard}
          data-tour="book"
          onClick={() => navigate('/books')}
          aria-label={selectedBook ? 'Change book' : 'Pick a book'}
        >
          <img
            src={selectedBookCover || '/images/BookBtn_unselected.png'}
            alt=""
            className={styles.bookCover}
          />
          <span className={styles.bookMeta}>
            <em>{selectedBook ? 'Current Book' : 'Library'}</em>
            <strong>{selectedBook ? selectedBook.title : 'Choose a Book'}</strong>
            <span>{selectedBook ? selectedBook.currentText ?? 'Keep going!' : 'New stories are waiting.'}</span>
          </span>
        </button>

        <div className={styles.progressTrack}>
          <div
            className={styles.progressFill}
            style={{ width: `${selectedBook ? selectedBook.progress * 100 : 0}%` }}
          />
        </div>

        <button
          className={styles.startButton}
          data-tour="start-learning"
          onClick={handleStart}
          disabled={!selectedBook}
        >
          {selectedBook ? 'Start Adventure' : 'Choose Book First'}
        </button>
      </section>

    </div>
  )
}
