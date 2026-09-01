import { useState, useEffect, useCallback, useMemo } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
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
import {
  type ChapterResult,
  messageForScore,
  saveChapterResult,
  starsForScore,
} from '../../utils/chapterProgress'
import styles from './LearnPage.module.css'

type Phase = 'reading' | 'repeat' | 'quiz' | 'roleplay'
type RepeatState = 'idle' | 'recording' | 'done'
type ScoreBreakdown = ChapterResult['breakdown']
type SpeechRate = 0.95 | 0.55

interface ReadToken {
  text: string
  start: number
  end: number
  isWord: boolean
  wordIndex: number | null
}

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

function getReadTokens(text: string): ReadToken[] {
  const matches = text.matchAll(/\S+|\s+/g)
  let wordIndex = -1
  return Array.from(matches, (match) => {
    const token = match[0]
    const start = match.index ?? 0
    const isWord = /\S/.test(token)
    if (isWord) wordIndex += 1
    return {
      text: token,
      start,
      end: start + token.length,
      isWord,
      wordIndex: isWord ? wordIndex : null,
    }
  })
}

function wordIndexFromChar(tokens: ReadToken[], charIndex: number): number | null {
  const token = tokens.find((item) => item.isWord && charIndex >= item.start && charIndex < item.end)
  if (token?.wordIndex !== null && token?.wordIndex !== undefined) return token.wordIndex
  return tokens.find((item) => item.isWord && charIndex < item.end)?.wordIndex ?? null
}

function pickKidFriendlyVoice(voices: SpeechSynthesisVoice[]): SpeechSynthesisVoice | null {
  const englishVoices = voices.filter((voice) => voice.lang.toLowerCase().startsWith('en'))
  const preferredNames = [
    'child',
    'kid',
    'junior',
    'jenny',
    'aria',
    'samantha',
    'google us english',
    'zira',
    'karen',
    'tessa',
  ]
  return englishVoices.find((voice) => {
    const label = `${voice.name} ${voice.voiceURI}`.toLowerCase()
    return preferredNames.some((name) => label.includes(name))
  }) ?? englishVoices[0] ?? null
}

export default function LearnPage() {
  const navigate = useNavigate()
  const { bookId } = useParams<{ bookId: string }>()
  const [searchParams] = useSearchParams()
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
  const [repeatScores, setRepeatScores] = useState<number[]>([])
  const [descriptionScores, setDescriptionScores] = useState<number[]>([])
  const [roleplayScores, setRoleplayScores] = useState<number[]>([])
  const [completionResult, setCompletionResult] = useState<ChapterResult | null>(null)
  const [speechRate, setSpeechRate] = useState<SpeechRate>(0.95)
  const [speechVoices, setSpeechVoices] = useState<SpeechSynthesisVoice[]>([])
  const [speakingWordIndex, setSpeakingWordIndex] = useState<number | null>(null)

  const recorder = useAudioRecorder()
  const { play: playAudio, stop: stopAudio } = useAudioPlayer()
  const isBackendMode = usesBackendApi()
  const chapterNumber = Math.max(1, Number.parseInt(searchParams.get('chapter') || String(selectedBook?.currentLesson ?? 1), 10) || 1)
  const shouldRestart = searchParams.has('restart')

  const average = (scores: number[]) => scores.length
    ? Math.round(scores.reduce((sum, score) => sum + score, 0) / scores.length)
    : null

  const buildLocalResult = useCallback((fallbackScore = 85): ChapterResult | null => {
    if (!bookId) return null
    const breakdown: ScoreBreakdown = {
      repeat: average(repeatScores),
      description: average(descriptionScores),
      roleplay: average(roleplayScores),
    }
    const availableScores = Object.values(breakdown).filter((score): score is number => score !== null)
    const totalScore = availableScores.length
      ? Math.round(availableScores.reduce((sum, score) => sum + score, 0) / availableScores.length)
      : fallbackScore
    return {
      bookId,
      chapterNumber,
      stars: starsForScore(totalScore),
      totalScore,
      message: messageForScore(totalScore),
      completedAt: new Date().toISOString(),
      breakdown,
    }
  }, [bookId, chapterNumber, descriptionScores, repeatScores, roleplayScores])

  const showCompletion = useCallback((result: ChapterResult | null) => {
    if (!result) return
    saveChapterResult(result)
    setCompletionResult(result)
  }, [])

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
      startOrResumeLearningSession(bookId, chapterNumber, shouldRestart)
        .then(loadBackendCourse)
        .catch(() => setError('Could not load your lesson.'))
        .finally(() => setIsLoading(false))
      return
    }
    const lessonId = `${bookId}-lesson-${chapterNumber}`
    fetchLesson(bookId, lessonId)
      .then((l) => {
        if (!l) setError('Could not find this lesson.')
        else setLesson(l)
      })
      .catch(() => setError('Could not load this lesson.'))
      .finally(() => setIsLoading(false))
  }, [bookId, chapterNumber, shouldRestart, selectedBook, isBackendMode, loadBackendCourse])

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

  useEffect(() => {
    if (!('speechSynthesis' in window)) return
    const updateVoices = () => setSpeechVoices(window.speechSynthesis.getVoices())
    updateVoices()
    window.speechSynthesis.addEventListener('voiceschanged', updateVoices)
    return () => window.speechSynthesis.removeEventListener('voiceschanged', updateVoices)
  }, [])

  const speakCurrentPage = useCallback(() => {
    if (!currentPage?.text || !('speechSynthesis' in window)) return
    window.speechSynthesis.cancel()
    setSpeakingWordIndex(null)
    const utterance = new SpeechSynthesisUtterance(currentPage.text)
    const tokens = getReadTokens(currentPage.text)
    const voice = pickKidFriendlyVoice(speechVoices)
    utterance.lang = 'en-US'
    if (voice) utterance.voice = voice
    utterance.rate = speechRate
    utterance.pitch = 1.28
    utterance.volume = 1
    utterance.onboundary = (event) => {
      if (event.name === 'word' || event.charIndex >= 0) {
        setSpeakingWordIndex(wordIndexFromChar(tokens, event.charIndex))
      }
    }
    utterance.onend = () => setSpeakingWordIndex(null)
    utterance.onerror = () => setSpeakingWordIndex(null)
    window.speechSynthesis.speak(utterance)
  }, [currentPage?.text, speechRate, speechVoices])

  const goToFirstPage = useCallback(() => {
    if (isBackendMode && bookId) {
      navigate(`/learn/${bookId}?chapter=${chapterNumber}&restart=${Date.now()}`, { replace: true })
      return
    }
    setPageIndex(0)
    setRepeatState('idle')
    setSttResult(null)
    setSpeakingWordIndex(null)
  }, [bookId, chapterNumber, isBackendMode, navigate])

  // Auto-play audio when the reading or speaking page changes.
  useEffect(() => {
    if ((phase === 'reading' || phase === 'repeat') && currentPage?.audioUrl) {
      playAudio(currentPage.audioUrl)
    }
    if ((phase === 'reading' || phase === 'repeat') && currentPage?.text) {
      speakCurrentPage()
    }
    return () => {
      stopAudio()
      if ('speechSynthesis' in window) window.speechSynthesis.cancel()
      setSpeakingWordIndex(null)
    }
  }, [phase, pageIndex, currentPage?.audioUrl, currentPage?.text, playAudio, stopAudio, speakCurrentPage])

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
        setError('Could not save your progress.')
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
        showCompletion(buildLocalResult())
      }
    }
  }, [isBackendMode, backendSession, phase, reading, repeat, pageIndex, totalPages, bookId, lesson, goToPhase, buildLocalResult, showCompletion])

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
      setRepeatScores((scores) => [...scores, Math.round(result.score * 100)])
      setRepeatState('done')
    } catch {
      setRepeatState('idle')
    }
  }, [repeatState, currentPage, recorder, isBackendMode, backendSession, repeat])

  const handleDescriptionRecord = useCallback(async (audio: Blob) => {
    if (!backendSession || !description) return
    const attempt = await createDescriptionAttempt(
      backendSession.sessionId,
      description.content.questionId,
      audio,
    )
    setDescriptionScores((scores) => [...scores, attempt.score])
    return attempt.score
  }, [backendSession, description])

  const handleDescriptionNext = useCallback(async () => {
    if (!isBackendMode || !backendSession || !description) {
      if (lesson?.roleplay) goToPhase('roleplay')
      else {
        if (bookId && lesson) postProgress(bookId, lesson.id)
        showCompletion(buildLocalResult())
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
      setError('Could not save your quiz progress.')
    }
  }, [isBackendMode, backendSession, description, lesson, bookId, goToPhase, buildLocalResult, showCompletion])

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
    setRoleplayScores((scores) => [...scores, result.score])
    return {
      userTranscript: result.user.transcript,
      characterText: result.character.text,
      missionCompleted: result.missionCompleted,
      score: result.score,
    }
  }, [backendSession, roleplay])

  const finishBackendSession = useCallback(async () => {
    if (!backendSession) return
    const result = await completeLearningSession(backendSession.sessionId)
    if (!bookId) return
    showCompletion({
      bookId,
      chapterNumber,
      stars: result.stars,
      totalScore: result.totalScore,
      message: messageForScore(result.totalScore),
      completedAt: result.completedAt,
      breakdown: {
        repeat: average(repeatScores),
        description: average(descriptionScores),
        roleplay: average(roleplayScores),
      },
    })
  }, [backendSession, bookId, chapterNumber, descriptionScores, repeatScores, roleplayScores, showCompletion])

  const lessonTitle = selectedBook
    ? `${selectedBook.title} - Chapter ${chapterNumber}`
    : lesson?.title ?? ''
  const displayPage = currentPage as LessonPage | undefined
  const displayReadTokens = useMemo(() => getReadTokens(displayPage?.text ?? ''), [displayPage?.text])

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

  if (completionResult) {
    return (
      <div className={styles.page}>
        <section className={styles.resultOverlay}>
          <div className={styles.resultCard}>
            <span className={styles.resultBadge}>Chapter {completionResult.chapterNumber}</span>
            <h1>{completionResult.message}</h1>
            <div className={styles.resultStars} aria-label={`${completionResult.stars} stars`}>
              {[0, 1, 2].map((index) => (
                <span key={index} className={index < completionResult.stars ? styles.starOn : styles.starOff}>
                  ★
                </span>
              ))}
            </div>
            <strong>{completionResult.totalScore} points</strong>
            <p>Your result is saved for your parent report.</p>
            <button onClick={() => navigate(bookId ? `/books/${bookId}/chapters` : '/', { replace: true })}>
              Back to Chapters
            </button>
          </div>
        </section>
      </div>
    )
  }

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
              showCompletion(buildLocalResult())
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
              <div className={styles.audioControls} aria-label="Audio controls">
                <button onClick={goToFirstPage}>First</button>
                <div className={styles.rateToggle}>
                  <button className={speechRate === 0.95 ? styles.activeRate : ''} onClick={() => setSpeechRate(0.95)}>
                    Normal
                  </button>
                  <button className={speechRate === 0.55 ? styles.activeRate : ''} onClick={() => setSpeechRate(0.55)}>
                    Slow
                  </button>
                </div>
                <button onClick={speakCurrentPage}>Listen</button>
              </div>
              <div
                className={styles.illustration}
                style={{ background: displayPage?.imageColor }}
                aria-label="Story picture"
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
                    {displayReadTokens.map((token, tokenIndex) => (
                      <span
                        key={`${token.text}-${token.start}-${tokenIndex}`}
                        className={
                          token.isWord && speakingWordIndex !== null && token.wordIndex === speakingWordIndex
                            ? styles.spokenWord
                            : undefined
                        }
                      >
                        {token.text}
                      </span>
                    ))}
                  </p>
                )}
              </div>
            </div>

            <div className={styles.bottomArea}>
              {showNextBtn ? (
                <button className={styles.imgBtn} onClick={goToNextScene} aria-label="Next">
                  <img src={IMAGES.nextBtnActive} alt="Next" className={styles.btnImg} />
                </button>
              ) : (
                <button
                  className={styles.imgBtn}
                  onClick={handleMicTap}
                  disabled={repeatState === 'recording'}
                  aria-label={repeatState === 'recording' ? 'Recording...' : 'Tap to speak'}
                >
                  <img
                    src={repeatState === 'recording' ? IMAGES.recordBtnActive : IMAGES.recordBtnInactive}
                    alt={repeatState === 'recording' ? 'Recording' : 'Tap to speak'}
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
