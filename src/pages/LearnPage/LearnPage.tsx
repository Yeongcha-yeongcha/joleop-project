/**
 * LearnPage — 학습 화면 (/learn/:bookId)
 *
 * 2단계 페이즈로 구성됩니다.
 *
 * [Phase 1: reading]
 *   - 일러스트 + 문장 표시 (굵은 검정)
 *   - NextBtn → 다음 씬으로 이동
 *   - 마지막 씬 도달 시 2초 배너 → Phase 2로 전환
 *
 * [Phase 2: repeat]
 *   idle  : 문장(회색) + RecordBtn_inactive → 클릭 시 recording
 *   recording: 문장(회색) + RecordBtn_active → 2초 후 done (실제 음성인식 연동 예정)
 *   done  : 문장(주황) + NextBtn → 다음 씬으로 이동
 *   마지막 씬 done → 홈으로 복귀
 *
 * 진도율 계산:
 *   reading  0%~50%  (pageIndex / totalPages * 0.5)
 *   repeat  50%~100% (0.5 + pageIndex / totalPages * 0.5)
 *
 * TODO: recording 상태에서 실제 음성인식 API 연동
 * TODO: 학습 완료 시 POST /users/me/progress 호출
 */

import { useState, useCallback } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAppStore } from '../../store/useAppStore'
import { getLessonByBookId } from '../../data/lessons'
import { IMAGES } from '../../constants/assets'
import LessonHeader from '../../components/LessonHeader/LessonHeader'
import styles from './LearnPage.module.css'

type Phase = 'reading' | 'repeat'
type RepeatState = 'idle' | 'recording' | 'done'

export default function LearnPage() {
  const navigate = useNavigate()
  const { bookId } = useParams<{ bookId: string }>()
  const { selectedBook } = useAppStore()

  const lesson = getLessonByBookId(bookId ?? '')
  const totalPages = lesson?.pages.length ?? 0

  const [phase, setPhase] = useState<Phase>('reading')
  const [pageIndex, setPageIndex] = useState(0)
  const [repeatState, setRepeatState] = useState<RepeatState>('idle')
  const [showPhaseBanner, setShowPhaseBanner] = useState(false)
  const [sceneKey, setSceneKey] = useState(0) // 씬 전환 fade 애니메이션용

  const currentPage = lesson?.pages[pageIndex]

  // 전체 진도율 (reading: 0~50%, repeat: 50~100%)
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
        // reading 완료 → 2초 배너 후 repeat 페이즈 시작
        setShowPhaseBanner(true)
        setTimeout(() => {
          setShowPhaseBanner(false)
          setPhase('repeat')
          setPageIndex(0)
          setRepeatState('idle')
          setSceneKey((k) => k + 1)
        }, 2000)
      } else {
        // repeat 완료 → 홈으로
        // TODO: POST /users/me/progress 호출
        navigate('/', { replace: true })
      }
    }
  }, [pageIndex, totalPages, phase, navigate])

  const handleMicTap = useCallback(() => {
    if (repeatState === 'idle') {
      setRepeatState('recording')
      // TODO: 실제 음성인식 API로 교체 (현재 2초 시뮬레이션)
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

      {/* 레슨 헤더: 뒤로가기 + 제목 + 진도바 */}
      <LessonHeader title={lessonTitle} progress={progress} onBack={() => navigate(-1)} />

      {/* 씬 영역 — key 변경으로 fade 애니메이션 트리거 */}
      <div key={sceneKey} className={styles.sceneEnter} style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>

        {/* 일러스트 */}
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

        {/* 문장 — 페이즈/상태에 따라 색상 변경 */}
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

      {/* 하단 버튼 */}
      <div className={styles.bottomArea}>
        {phase === 'reading' || repeatState === 'done' ? (
          // 다음 버튼
          <button className={styles.imgBtn} onClick={goToNextScene} aria-label="다음">
            <img src={IMAGES.nextBtnActive} alt="다음" className={styles.nextBtnImg} />
          </button>
        ) : (
          // 녹음 버튼 (idle / recording)
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

      {/* 페이즈 전환 배너 (reading → repeat) */}
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
