import { useState, useEffect, useCallback } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAppStore } from '../../store/useAppStore'
import { fetchLesson, postProgress, postSpeechRecognize } from '../../services/api'
import { IMAGES } from '../../constants/assets'
import LessonHeader from '../../components/LessonHeader/LessonHeader'
import StatusScreen from '../../components/StatusScreen/StatusScreen'
import type { Lesson } from '../../types'
import styles from './LearnPage.module.css'

type Phase = 'reading' | 'repeat'
type RepeatState = 'idle' | 'recording' | 'done'

export default function LearnPage() {
  const navigate = useNavigate()
  const { bookId } = useParams<{ bookId: string }>()
  const { selectedBook } = useAppStore()

  const [lesson, setLesson] = useState<Lesson | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [phase, setPhase] = useState<Phase>('reading')
  const [pageIndex, setPageIndex] = useState(0)
  const [repeatState, setRepeatState] = useState<RepeatState>('idle')
  const [showPhaseBanner, setShowPhaseBanner] = useState(false)
  const [sceneKey, setSceneKey] = useState(0)

  const load = useCallback(() => {
    if (!bookId) return
    setIsLoading(true)
    setError(null)
    const lessonId = `${bookId}-lesson-${selectedBook?.currentLesson ?? 1}`
    fetchLesson(bookId, lessonId)
      .then((l) => {
        if (!l) setError('레슨을 찾을 수 없어요.')
        else setLesson(l)
      })
      .catch(() => setError('레슨을 불러오지 못했어요.'))
      .finally(() => setIsLoading(false))
  }, [bookId, selectedBook])

  useEffect(() => { load() }, [load])

  const totalPages = lesson?.pages.length ?? 0
  const currentPage = lesson?.pages[pageIndex]

  const progress =
    phase === 'reading'
      ? (pageIndex / totalPages) * 0.5
      : 0.5 + ((pageIndex + (repeatState === 'done' ? 1 : 0)) / totalPages) * 0.5

  const goToNextScene = useCallback(() => {
    if (pageIndex < totalPages - 1) {
      setPageIndex((i) => i + 1)
      setRepeatState('idle')
      setSceneKey((k) => k + 1)
    } else {
      if (phase === 'reading') {
        setShowPhaseBanner(true)
        setTimeout(() => {
          setShowPhaseBanner(false)
          setPhase('repeat')
          setPageIndex(0)
          setRepeatState('idle')
          setSceneKey((k) => k + 1)
        }, 2000)
      } else {
        if (bookId && lesson) postProgress(bookId, lesson.id)
        navigate('/', { replace: true })
      }
    }
  }, [pageIndex, totalPages, phase, navigate, bookId, lesson])

  const handleMicTap = useCallback(() => {
    if (repeatState === 'idle') {
      setRepeatState('recording')
      postSpeechRecognize(new Blob(), currentPage?.text ?? '')
        .then(() => setRepeatState('done'))
        .catch(() => setRepeatState('idle'))
    } else if (repeatState === 'done') {
      goToNextScene()
    }
  }, [repeatState, goToNextScene, currentPage])

  const lessonTitle = selectedBook
    ? `${selectedBook.title} - lesson ${selectedBook.currentLesson}`
    : lesson?.title ?? ''

  if (isLoading || error) {
    return (
      <div className={styles.page}>
        <LessonHeader title={lessonTitle} progress={0} onBack={() => navigate(-1)} />
        <StatusScreen isLoading={isLoading} error={error} onRetry={load} />
      </div>
    )
  }

  if (!lesson || !currentPage) return null

  return (
    <div className={styles.page}>

      <LessonHeader title={lessonTitle} progress={progress} onBack={() => navigate(-1)} />

      <div key={sceneKey} className={styles.sceneEnter} style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>

        <div
          className={styles.illustration}
          style={{ background: currentPage.imageColor }}
          aria-label="동화 일러스트"
        >
          {currentPage.imageUrl
            ? <img src={currentPage.imageUrl} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            : <span>📖</span>
          }
        </div>

        <div className={styles.textArea}>
          <p className={`${styles.sentence} ${
            phase === 'reading'        ? styles.reading    :
            repeatState === 'done'     ? styles.repeatDone :
                                         styles.repeatIdle
          }`}>
            {currentPage.text}
          </p>
        </div>

      </div>

      <div className={styles.bottomArea}>
        {phase === 'reading' || repeatState === 'done' ? (
          <button className={styles.imgBtn} onClick={goToNextScene} aria-label="다음">
            <img src={IMAGES.nextBtnActive} alt="다음" className={styles.nextBtnImg} />
          </button>
        ) : (
          <button
            className={styles.imgBtn}
            onClick={handleMicTap}
            aria-label={repeatState === 'recording' ? '녹음 중...' : '탭하여 말하기'}
          >
            <img
              src={repeatState === 'recording' ? IMAGES.recordBtnActive : IMAGES.recordBtnInactive}
              alt={repeatState === 'recording' ? '녹음 중' : '탭하여 말하기'}
              className={`${styles.recordBtnImg} ${repeatState === 'recording' ? styles.recording : ''}`}
            />
          </button>
        )}
      </div>

      {showPhaseBanner && (
        <div className={styles.phaseBanner}>
          <div className={styles.phaseBannerCard}>
            <span className={styles.phaseBannerIcon}>🎤</span>
            <span className={styles.phaseBannerTitle}>이제 따라 말해봐요!</span>
            <span className={styles.phaseBannerSub}>들은 문장을 따라 말하면 돼요</span>
          </div>
        </div>
      )}

    </div>
  )
}
