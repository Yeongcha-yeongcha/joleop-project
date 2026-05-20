import { useState, useEffect, useCallback } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAppStore } from '../../store/useAppStore'
import { fetchLesson, postProgress, postSpeechRecognize } from '../../services/api'
import { IMAGES } from '../../constants/assets'
import LessonHeader from '../../components/LessonHeader/LessonHeader'
import type { Lesson } from '../../types'
import styles from './LearnPage.module.css'

type Phase = 'reading' | 'repeat'
type RepeatState = 'idle' | 'recording' | 'done'

export default function LearnPage() {
  const navigate = useNavigate()
  const { bookId } = useParams<{ bookId: string }>()
  const { selectedBook } = useAppStore()

  const [lesson, setLesson] = useState<Lesson | null>(null)
  const [phase, setPhase] = useState<Phase>('reading')
  const [pageIndex, setPageIndex] = useState(0)
  const [repeatState, setRepeatState] = useState<RepeatState>('idle')
  const [showPhaseBanner, setShowPhaseBanner] = useState(false)
  const [sceneKey, setSceneKey] = useState(0)

  useEffect(() => {
    if (!bookId) return
    const lessonId = `${bookId}-lesson-${selectedBook?.currentLesson ?? 1}`
    fetchLesson(bookId, lessonId).then((l) => setLesson(l ?? null))
  }, [bookId, selectedBook])

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
        // TODO: postProgress 호출 후 navigate
        if (bookId && lesson) postProgress(bookId, lesson.id)
        navigate('/', { replace: true })
      }
    }
  }, [pageIndex, totalPages, phase, navigate, bookId, lesson])

  const handleMicTap = useCallback(() => {
    if (repeatState === 'idle') {
      setRepeatState('recording')
      // TODO: 실제 녹음 blob을 전달하도록 교체
      postSpeechRecognize(new Blob(), currentPage?.text ?? '').then(() => {
        setRepeatState('done')
      })
    } else if (repeatState === 'done') {
      goToNextScene()
    }
  }, [repeatState, goToNextScene, currentPage])

  if (!lesson || !currentPage) {
    return (
      <div className={styles.page} style={{ alignItems: 'center', justifyContent: 'center' }}>
        <p style={{ color: '#888' }}>레슨을 찾을 수 없습니다.</p>
      </div>
    )
  }

  const lessonTitle = selectedBook
    ? `${selectedBook.title} - lesson ${selectedBook.currentLesson}`
    : lesson.title

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
