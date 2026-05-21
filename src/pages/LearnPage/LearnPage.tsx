import { useState, useEffect, useCallback } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAppStore } from '../../store/useAppStore'
import { fetchLesson, postProgress, postSpeechRecognize } from '../../services/api'
import { IMAGES } from '../../constants/assets'
import LessonHeader from '../../components/LessonHeader/LessonHeader'
import StatusScreen from '../../components/StatusScreen/StatusScreen'
import QuizScreen from '../../components/QuizScreen/QuizScreen'
import RoleplayScreen from '../../components/RoleplayScreen/RoleplayScreen'
import type { Lesson } from '../../types'
import styles from './LearnPage.module.css'

type Phase = 'reading' | 'repeat' | 'quiz' | 'roleplay'
type RepeatState = 'idle' | 'recording' | 'done'

/** Must match the phaseExit animation duration in LearnPage.module.css */
const PHASE_EXIT_MS = 230

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
  const [roleplayProgress, setRoleplayProgress] = useState(0.70)
  const [isExiting, setIsExiting] = useState(false)

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

  // Progress: reading 0–30%, repeat 30–60%, quiz 65%, roleplay 70–100%
  const lessonProgress =
    phase === 'reading' ? (pageIndex / totalPages) * 0.3
    : phase === 'repeat' ? 0.3 + ((pageIndex + (repeatState === 'done' ? 1 : 0)) / totalPages) * 0.3
    : 0.65
  const headerProgress = phase === 'roleplay' ? roleplayProgress : lessonProgress

  // Slide out current phase, then switch — keeps LessonHeader inside the
  // animated wrapper so position:fixed overlays (e.g. completion) cover it too.
  const goToPhase = useCallback((next: Phase, onSwitch?: () => void) => {
    setIsExiting(true)
    setTimeout(() => {
      setPhase(next)
      onSwitch?.()
      setIsExiting(false)
    }, PHASE_EXIT_MS)
  }, [])

  const goToNextScene = useCallback(() => {
    if (pageIndex < totalPages - 1) {
      setPageIndex((i) => i + 1)
      setRepeatState('idle')
      return
    }
    if (phase === 'reading') {
      goToPhase('repeat', () => { setPageIndex(0); setRepeatState('idle') })
    } else if (phase === 'repeat') {
      if (lesson?.quiz) {
        goToPhase('quiz')
      } else {
        if (bookId && lesson) postProgress(bookId, lesson.id)
        navigate('/', { replace: true })
      }
    }
  }, [pageIndex, totalPages, phase, navigate, bookId, lesson, goToPhase])

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

  const showNextBtn = phase === 'reading' || repeatState === 'done'

  return (
    <div className={styles.page}>
      <div
        key={phase}
        className={isExiting ? styles.phaseExit : styles.phaseEnter}
      >
        <LessonHeader title={lessonTitle} progress={headerProgress} onBack={() => navigate(-1)} />

        {phase === 'roleplay' && lesson.roleplay && (
          <RoleplayScreen
            roleplay={lesson.roleplay}
            onProgressChange={setRoleplayProgress}
            onFinish={() => {
              if (bookId) postProgress(bookId, lesson.id)
              navigate('/', { replace: true })
            }}
          />
        )}

        {phase === 'quiz' && lesson.quiz && (
          <QuizScreen
            quiz={lesson.quiz}
            onNext={() => {
              if (lesson.roleplay) goToPhase('roleplay')
              else {
                if (bookId) postProgress(bookId, lesson.id)
                navigate('/', { replace: true })
              }
            }}
          />
        )}

        {(phase === 'reading' || phase === 'repeat') && (
          <>
            <div className={styles.sceneContent}>
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
                  phase === 'reading'    ? styles.reading    :
                  repeatState === 'done' ? styles.repeatDone :
                                           styles.repeatIdle
                }`}>
                  {currentPage.text}
                </p>
              </div>
            </div>

            <div className={styles.bottomArea}>
              {showNextBtn ? (
                <button className={styles.imgBtn} onClick={goToNextScene} aria-label="다음">
                  <img src={IMAGES.nextBtnActive} alt="다음" className={styles.btnImg} />
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
                    className={`${styles.btnImg} ${repeatState === 'recording' ? styles.recording : ''}`}
                  />
                </button>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
