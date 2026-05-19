import { useState, useCallback } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAppStore } from '../../store/useAppStore'
import { getLessonByBookId } from '../../data/lessons'
import LessonHeader from '../../components/LessonHeader/LessonHeader'
import styles from './LearnPage.module.css'

type Phase = 'reading' | 'repeat'
type RepeatState = 'idle' | 'recording' | 'done'

export default function LearnPage() {
  const navigate = useNavigate()
  const { bookId } = useParams<{ bookId: string }>()
  const { selectedBook } = useAppStore()

  const lesson = getLessonByBookId(bookId ?? '')

  const [phase, setPhase] = useState<Phase>('reading')
  const [pageIndex, setPageIndex] = useState(0)
  const [repeatState, setRepeatState] = useState<RepeatState>('idle')
  const [showPhaseBanner, setShowPhaseBanner] = useState(false)
  const [sceneKey, setSceneKey] = useState(0) // 씬 전환 애니메이션용

  const totalPages = lesson?.pages.length ?? 0
  const currentPage = lesson?.pages[pageIndex]

  // 전체 진도: reading(0~50%) + repeat(50~100%)
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
      // 마지막 씬 → 페이즈 전환 또는 완료
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
        // 모두 완료 → 홈으로
        navigate('/', { replace: true })
      }
    }
  }, [pageIndex, totalPages, phase, navigate])

  const handleMicTap = useCallback(() => {
    if (repeatState === 'idle') {
      // 녹음 시작 (실제 녹음 API 연결 자리)
      setRepeatState('recording')
      // 2초 후 완료 시뮬레이션 (실제는 음성 인식 결과로 전환)
      setTimeout(() => setRepeatState('done'), 2000)
    } else if (repeatState === 'done') {
      goToNextScene()
    }
  }, [repeatState, goToNextScene])

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
      {/* Status bar */}
      <div className={styles.statusBar}>
        <span className={styles.time}>9:41</span>
      </div>

      {/* 헤더 */}
      <LessonHeader
        title={lessonTitle}
        progress={progress}
        onBack={() => navigate(-1)}
      />

      {/* 일러스트 + 문장 — 씬 전환 시 key로 애니메이션 */}
      <div key={sceneKey} className={styles.sceneEnter} style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {/* 일러스트 영역 */}
        <div
          className={styles.illustration}
          style={{ background: currentPage.imageColor }}
          aria-label="동화 일러스트"
        >
          {/* TODO: 실제 이미지로 교체 */}
          {currentPage.imageUrl ? (
            <img src={currentPage.imageUrl} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
          ) : (
            <span>📖</span>
          )}
        </div>

        {/* 문장 */}
        <div className={styles.textArea}>
          <p
            className={`${styles.sentence} ${
              phase === 'reading'
                ? styles.reading
                : repeatState === 'done'
                ? styles.repeatDone
                : styles.repeatIdle
            }`}
          >
            {currentPage.text}
          </p>
        </div>
      </div>

      {/* 하단 버튼 */}
      <div className={styles.bottomArea}>
        {phase === 'reading' ? (
          <button className={styles.nextBtn} onClick={goToNextScene} aria-label="다음">
            →
          </button>
        ) : repeatState === 'done' ? (
          <button className={styles.nextBtn} onClick={goToNextScene} aria-label="다음">
            →
          </button>
        ) : (
          <button
            className={`${styles.micBtn} ${repeatState === 'recording' ? styles.recording : ''}`}
            onClick={handleMicTap}
            aria-label={repeatState === 'recording' ? '녹음 중...' : '탭하여 말하기'}
          >
            <span>🎤</span>
            <span>{repeatState === 'recording' ? '녹음 중...' : '탭하여 말하기'}</span>
          </button>
        )}
      </div>

      {/* 페이즈 전환 배너 */}
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
