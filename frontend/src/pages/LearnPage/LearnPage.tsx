import { useState, useEffect, useCallback } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAppStore } from '../../store/useAppStore'
import {
  completeLearningSession,
  createDescriptionAttempt,
  createRepeatAttempt,
  createRoleplayMessage,
  fetchDescriptionCourse,
  fetchLesson,
  fetchReadingCourse,
  fetchRepeatCourse,
  fetchRoleplayCourse,
  postProgress,
  postSpeechRecognize,
  startOrResumeLearningSession,
  updateDescriptionCourse,
  updateReadingCourse,
  updateRepeatCourse,
  usesBackendApi,
} from '../../services/api'
import type {
  DescriptionData,
  LearningSessionData,
  ReadingData,
  RepeatData,
  RoleplayData,
  SpeechResult,
} from '../../services/api'
import { useAudioRecorder } from '../../hooks/useAudioRecorder'
import { useAudioPlayer } from '../../hooks/useAudioPlayer'
import { IMAGES } from '../../constants/assets'
import LessonHeader from '../../components/LessonHeader/LessonHeader'
import StatusScreen from '../../components/StatusScreen/StatusScreen'
import QuizScreen from '../../components/QuizScreen/QuizScreen'
import RoleplayScreen from '../../components/RoleplayScreen/RoleplayScreen'
import type { Lesson, LessonPage, QuizQuestion, RoleplayMission } from '../../types'
import styles from './LearnPage.module.css'

type Phase = 'reading' | 'repeat' | 'quiz' | 'roleplay'
type RepeatState = 'idle' | 'recording' | 'done'

/** Must match the phaseExit animation duration in LearnPage.module.css */
const PHASE_EXIT_MS = 230

function getWordHighlights(expected: string, recognized: string) {
  const normalize = (s: string) => s.toLowerCase().replace(/[.,!?'"]/g, '').trim()
  const expWords = expected.trim().split(/\s+/)
  const recWords = recognized.trim().split(/\s+/)
  return expWords.map((word, i) => ({
    word,
    correct: normalize(word) === normalize(recWords[i] ?? ''),
  }))
}

function blankedDescriptionSentence(description: DescriptionData): string {
  const { sentence, sourceText, blankWord } = description.content
  if (sentence) return sentence
  if (sourceText && blankWord) {
    const pattern = new RegExp(`\\b${blankWord.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'i')
    return sourceText.replace(pattern, '____')
  }
  return sourceText ?? ''
}

export default function LearnPage() {
  const navigate = useNavigate()
  const { bookId } = useParams<{ bookId: string }>()
  const { selectedBook } = useAppStore()

  const [lesson, setLesson] = useState<Lesson | null>(null)
  const [backendSession, setBackendSession] = useState<LearningSessionData | null>(null)
  const [reading, setReading] = useState<ReadingData | null>(null)
  const [repeat, setRepeat] = useState<RepeatData | null>(null)
  const [description, setDescription] = useState<DescriptionData | null>(null)
  const [roleplay, setRoleplay] = useState<RoleplayData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [phase, setPhase] = useState<Phase>('reading')
  const [pageIndex, setPageIndex] = useState(0)
  const [repeatState, setRepeatState] = useState<RepeatState>('idle')
  const [sttResult, setSttResult] = useState<SpeechResult | null>(null)
  const [roleplayProgress, setRoleplayProgress] = useState(0.70)
  const [isExiting, setIsExiting] = useState(false)

  const recorder = useAudioRecorder()
  const { play: playAudio, stop: stopAudio } = useAudioPlayer()
  const isBackendMode = usesBackendApi()

  const loadBackendCourse = useCallback(async (session: LearningSessionData) => {
    setBackendSession(session)
    setReading(null)
    setRepeat(null)
    setDescription(null)
    setRoleplay(null)

    if (session.currentCourse === 'READING') {
      const data = await fetchReadingCourse(session.sessionId)
      setReading(data)
      setPhase('reading')
      setPageIndex(data.currentStep - 1)
      return
    }
    if (session.currentCourse === 'REPEAT') {
      const data = await fetchRepeatCourse(session.sessionId)
      setRepeat(data)
      setPhase('repeat')
      setPageIndex(data.currentStep - 1)
      setRepeatState('idle')
      return
    }
    if (session.currentCourse === 'DESCRIPTION') {
      const data = await fetchDescriptionCourse(session.sessionId)
      setDescription(data)
      setPhase('quiz')
      return
    }
    const data = await fetchRoleplayCourse(session.sessionId)
    setRoleplay(data)
    setPhase('roleplay')
    setRoleplayProgress(0.70)
  }, [])

  const load = useCallback(() => {
    if (!bookId) return
    setIsLoading(true)
    setError(null)
    if (isBackendMode) {
      startOrResumeLearningSession(bookId)
        .then(loadBackendCourse)
        .catch(() => setError('학습 세션을 불러오지 못했어요.'))
        .finally(() => setIsLoading(false))
      return
    }
    const lessonId = `${bookId}-lesson-${selectedBook?.currentLesson ?? 1}`
    fetchLesson(bookId, lessonId)
      .then((l) => {
        if (!l) setError('레슨을 찾을 수 없어요.')
        else setLesson(l)
      })
      .catch(() => setError('레슨을 불러오지 못했어요.'))
      .finally(() => setIsLoading(false))
  }, [bookId, selectedBook, isBackendMode, loadBackendCourse])

  useEffect(() => {
    void Promise.resolve().then(load)
  }, [load])

  const backendReadingPage: LessonPage | undefined = reading ? {
    id: String(reading.content.chunkId),
    text: reading.content.text,
    imageColor: '#B8D4E8',
    imageUrl: reading.content.imageUrl ?? undefined,
  } : undefined
  const backendRepeatPage: LessonPage | undefined = repeat ? {
    id: String(repeat.content.questionId),
    text: repeat.content.targetText,
    imageColor: '#B8D4E8',
    imageUrl: repeat.content.imageUrl ?? undefined,
  } : undefined
  const totalPages = isBackendMode
    ? phase === 'reading' ? reading?.totalSteps ?? 0 : repeat?.totalSteps ?? 0
    : lesson?.pages.length ?? 0
  const currentPage = isBackendMode
    ? phase === 'reading' ? backendReadingPage : backendRepeatPage
    : lesson?.pages[pageIndex]
  const backendQuiz: QuizQuestion | undefined = description ? {
    question: description.content.guideHint ?? description.content.instruction,
    sentence: blankedDescriptionSentence(description),
    answer: description.content.blankWord ?? description.content.answerSentence ?? '',
    imageColor: '#D4B8E8',
    imageUrl: description.content.imageUrl ?? undefined,
  } : undefined
  const backendRoleplay: RoleplayMission | undefined = roleplay ? {
    thumbnailColor: '#C4D4B8',
    thumbnailUrl: roleplay.character.imageUrl ?? undefined,
    mission: roleplay.mission.playerGoal ?? roleplay.mission.description,
    missionSummary: roleplay.mission.title,
    turns: Array.from(
      { length: Math.max(1, roleplay.mission.requiredTurns ?? 3) },
      (_, index) => ({
        npc: index === 0 ? roleplay.openingMessage.text : roleplay.mission.hints?.[index - 1] ?? '',
        user: '',
      }),
    ),
    finalNpc: 'Great job!',
  } : undefined

  // 읽기/따라말하기 단계에서 페이지 바뀔 때 오디오 자동 재생
  useEffect(() => {
    if ((phase === 'reading' || phase === 'repeat') && currentPage?.audioUrl) {
      playAudio(currentPage.audioUrl)
    }
    return () => { stopAudio() }
  }, [phase, pageIndex, currentPage?.audioUrl, playAudio, stopAudio])

  // Progress: reading 0–30%, repeat 30–60%, quiz 65%, roleplay 70–100%
  const lessonProgress =
    phase === 'reading' ? (totalPages ? pageIndex / totalPages : 0) * 0.3
    : phase === 'repeat' ? 0.3 + ((pageIndex + (repeatState === 'done' ? 1 : 0)) / Math.max(totalPages, 1)) * 0.3
    : 0.65
  const headerProgress = phase === 'roleplay' ? roleplayProgress : lessonProgress

  const goToPhase = useCallback((next: Phase, onSwitch?: () => void) => {
    setIsExiting(true)
    setTimeout(() => {
      setPhase(next)
      setSttResult(null)
      onSwitch?.()
      setIsExiting(false)
    }, PHASE_EXIT_MS)
  }, [])

  const goToNextScene = useCallback(async () => {
    if (isBackendMode && backendSession) {
      try {
        if (phase === 'reading' && reading) {
          const result = await updateReadingCourse(backendSession.sessionId, reading.currentStep)
          if (result.courseCompleted) {
            goToPhase('repeat', async () => {
              const next = await fetchRepeatCourse(backendSession.sessionId)
              setRepeat(next)
              setReading(null)
              setPageIndex(next.currentStep - 1)
              setRepeatState('idle')
            })
          } else if (result.content && result.currentStep && result.totalSteps) {
            setReading({
              ...reading,
              currentStep: result.currentStep,
              totalSteps: result.totalSteps,
              courseProgress: result.courseProgress,
              totalProgress: result.totalProgress,
              content: result.content,
            })
            setPageIndex(result.currentStep - 1)
          }
          setSttResult(null)
          return
        }
        if (phase === 'repeat' && repeat) {
          const result = await updateRepeatCourse(backendSession.sessionId, repeat.content.questionId)
          setSttResult(null)
          setRepeatState('idle')
          if (result.courseCompleted) {
            goToPhase('quiz', async () => {
              const next = await fetchDescriptionCourse(backendSession.sessionId)
              setDescription(next)
              setRepeat(null)
            })
          } else {
            const next = await fetchRepeatCourse(backendSession.sessionId)
            setRepeat(next)
            setPageIndex(next.currentStep - 1)
          }
          return
        }
      } catch {
        setError('진도를 저장하지 못했어요.')
      }
      return
    }
    if (pageIndex < totalPages - 1) {
      setPageIndex((i) => i + 1)
      setRepeatState('idle')
      setSttResult(null)
      return
    }
    if (phase === 'reading') {
      goToPhase('repeat', () => { setPageIndex(0); setRepeatState('idle') })
    } else if (phase === 'repeat') {
      setSttResult(null)
      if (lesson?.quiz) {
        goToPhase('quiz')
      } else {
        if (bookId && lesson) postProgress(bookId, lesson.id)
        navigate('/', { replace: true })
      }
    }
  }, [isBackendMode, backendSession, phase, reading, repeat, pageIndex, totalPages, navigate, bookId, lesson, goToPhase])

  const handleMicTap = useCallback(async () => {
    if (repeatState !== 'idle') return
    setSttResult(null)
    setRepeatState('recording')
    try {
      const blob = await recorder.record()
      const result = isBackendMode && backendSession && repeat
        ? await createRepeatAttempt(backendSession.sessionId, repeat.content.questionId, blob).then((attempt) => ({
            recognized: attempt.transcript,
            correct: attempt.passed,
            score: attempt.score / 100,
          }))
        : await postSpeechRecognize(blob, currentPage?.text ?? '')
      setSttResult(result)
      setRepeatState('done')
    } catch {
      setRepeatState('idle')
    }
  }, [repeatState, currentPage, recorder, isBackendMode, backendSession, repeat])

  const handleDescriptionRecord = useCallback(async (audio: Blob) => {
    if (!backendSession || !description) return
    await createDescriptionAttempt(
      backendSession.sessionId,
      description.content.questionId,
      audio,
    )
  }, [backendSession, description])

  const handleDescriptionNext = useCallback(async () => {
    if (!isBackendMode || !backendSession || !description) {
      if (lesson?.roleplay) goToPhase('roleplay')
      else {
        if (bookId && lesson) postProgress(bookId, lesson.id)
        navigate('/', { replace: true })
      }
      return
    }
    try {
      const result = await updateDescriptionCourse(
        backendSession.sessionId,
        description.content.questionId,
      )
      if (result.courseCompleted) {
        goToPhase('roleplay', async () => {
          const next = await fetchRoleplayCourse(backendSession.sessionId)
          setRoleplay(next)
          setDescription(null)
        })
      } else {
        const next = await fetchDescriptionCourse(backendSession.sessionId)
        setDescription(next)
      }
    } catch {
      setError('묘사 학습 진도를 저장하지 못했어요.')
    }
  }, [isBackendMode, backendSession, description, lesson, bookId, navigate, goToPhase])

  const handleRoleplayRecord = useCallback(async (audio: Blob) => {
    if (!backendSession || !roleplay) {
      return { userTranscript: '', characterText: '', missionCompleted: false }
    }
    const result = await createRoleplayMessage(
      backendSession.sessionId,
      roleplay.mission.missionId,
      audio,
    )
    setRoleplayProgress(0.70 + (result.courseProgress / 100) * 0.30)
    return {
      userTranscript: result.user.transcript,
      characterText: result.character.text,
      missionCompleted: result.missionCompleted,
    }
  }, [backendSession, roleplay])

  const finishBackendSession = useCallback(async () => {
    if (!backendSession) return
    await completeLearningSession(backendSession.sessionId)
    navigate('/', { replace: true })
  }, [backendSession, navigate])

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

  if ((!isBackendMode && !lesson) || ((phase === 'reading' || phase === 'repeat') && !currentPage)) return null

  const showNextBtn = phase === 'reading' || repeatState === 'done'
  const activeQuiz = isBackendMode ? backendQuiz : lesson?.quiz
  const activeRoleplay = isBackendMode ? backendRoleplay : lesson?.roleplay
  const displayPage = currentPage as LessonPage | undefined

  return (
    <div className={styles.page}>
      <div
        key={phase}
        className={isExiting ? styles.phaseExit : styles.phaseEnter}
      >
        <LessonHeader title={lessonTitle} progress={headerProgress} onBack={() => navigate(-1)} />

        {phase === 'roleplay' && activeRoleplay && (
          <RoleplayScreen
            roleplay={activeRoleplay}
            onProgressChange={setRoleplayProgress}
            onRecord={isBackendMode ? handleRoleplayRecord : undefined}
            onFinish={() => {
              if (isBackendMode) {
                finishBackendSession()
                return
              }
              if (bookId && lesson) postProgress(bookId, lesson.id)
              navigate('/', { replace: true })
            }}
          />
        )}

        {phase === 'quiz' && activeQuiz && (
          <QuizScreen
            quiz={activeQuiz}
            onRecord={isBackendMode ? handleDescriptionRecord : undefined}
            onNext={handleDescriptionNext}
          />
        )}

        {(phase === 'reading' || phase === 'repeat') && (
          <>
            <div className={styles.sceneContent}>
              <div
                className={styles.illustration}
                style={{ background: displayPage?.imageColor }}
                aria-label="동화 일러스트"
              >
                {displayPage?.imageUrl
                  ? <img src={displayPage.imageUrl} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                  : <span>📖</span>
                }
              </div>

              <div className={styles.textArea}>
                {phase === 'repeat' && sttResult ? (
                  <p className={styles.sentence}>
                    {getWordHighlights(displayPage?.text ?? '', sttResult.recognized).map(({ word, correct }, i: number) => (
                      <span key={i} className={correct ? styles.wordCorrect : styles.wordWrong}>
                        {word}{' '}
                      </span>
                    ))}
                  </p>
                ) : (
                  <p className={`${styles.sentence} ${
                    phase === 'reading'    ? styles.reading    :
                    repeatState === 'done' ? styles.repeatDone :
                                             styles.repeatIdle
                  }`}>
                    {displayPage?.text}
                  </p>
                )}
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
                  disabled={repeatState === 'recording'}
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
