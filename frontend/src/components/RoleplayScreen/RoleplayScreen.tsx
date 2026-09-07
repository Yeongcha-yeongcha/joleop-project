import { useState, useRef, useEffect } from 'react'
import lottie from 'lottie-web'
import type { RoleplayMission } from '../../types'
import type { ChapterResult } from '../../utils/chapterProgress'
import { IMAGES } from '../../constants/assets'
import styles from './RoleplayScreen.module.css'

function TrophyAnimation({ className, onComplete }: { className?: string; onComplete?: () => void }) {
  const ref = useRef<HTMLDivElement>(null)
  const onCompleteRef = useRef(onComplete)

  useEffect(() => {
    onCompleteRef.current = onComplete
  }, [onComplete])

  useEffect(() => {
    if (!ref.current) return
    const anim = lottie.loadAnimation({
      container: ref.current,
      renderer: 'svg',
      loop: false,
      autoplay: true,
      path: '/animations/Trophy.json',
    })
    anim.addEventListener('complete', () => onCompleteRef.current?.())
    return () => anim.destroy()
  }, [])
  return <div ref={ref} className={className} />
}

// Progress range: intro starts at 70%, chat fills the remaining 30% as turns complete
const PROGRESS_INTRO = 0.70
const PROGRESS_CHAT_RANGE = 0.30

const ROLEPLAY_MAX_RECORD_MS = 5200
const ROLEPLAY_SILENCE_MS = 750
const COMPLETION_TEXT_MS = 500    // delay before final result fades in

type RoleplayView = 'intro' | 'chat'
type RecordState = 'idle' | 'recording'

interface Props {
  roleplay: RoleplayMission
  onProgressChange: (v: number) => void
  onFinish: () => Promise<ChapterResult | null> | ChapterResult | null
  onExit: () => void
  onSpeakText?: (text: string) => Promise<void> | void
  onRecord: (audio: Blob, transcript?: string) => Promise<{
    userTranscript: string
    characterText: string
    missionCompleted: boolean
    score?: number
  }>
  variant?: 'lesson' | 'review'
}

function recordRoleplaySpeech(durationMs = ROLEPLAY_MAX_RECORD_MS): Promise<{ audio: Blob; transcript: string }> {
  return new Promise(async (resolve, reject) => {
    let stream: MediaStream
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    } catch {
      reject(new Error('Microphone permission is needed.'))
      return
    }

    const chunks: Blob[] = []
    const mediaRecorder = new MediaRecorder(stream)
    const Recognition = window.SpeechRecognition ?? window.webkitSpeechRecognition
    const recognition = Recognition ? new Recognition() : null
    const finalParts: string[] = []
    let interimTranscript = ''
    let settled = false
    let maxTimer: number | null = null
    let silenceTimer: number | null = null
    const deadline = Date.now() + durationMs

    const currentTranscript = () => [...finalParts, interimTranscript].join(' ').trim()

    const cleanup = () => {
      if (maxTimer !== null) window.clearTimeout(maxTimer)
      if (silenceTimer !== null) window.clearTimeout(silenceTimer)
      try {
        recognition?.abort()
      } catch {
        // Recognition may already be stopped.
      }
      stream.getTracks().forEach((track) => track.stop())
    }

    const finish = () => {
      if (settled) return
      settled = true
      if (mediaRecorder.state !== 'inactive') mediaRecorder.stop()
    }

    const restartSilenceTimer = () => {
      if (silenceTimer !== null) window.clearTimeout(silenceTimer)
      if (!currentTranscript()) return
      silenceTimer = window.setTimeout(finish, ROLEPLAY_SILENCE_MS)
    }

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) chunks.push(event.data)
    }
    mediaRecorder.onerror = () => {
      cleanup()
      reject(new Error('Recording failed.'))
    }
    mediaRecorder.onstop = () => {
      const transcript = currentTranscript()
      cleanup()
      resolve({
        audio: new Blob(chunks, { type: 'audio/webm' }),
        transcript,
      })
    }

    mediaRecorder.start()
    maxTimer = window.setTimeout(finish, durationMs)

    if (!recognition) return

    const restartIfNoSpeechYet = () => {
      if (settled || currentTranscript() || Date.now() >= deadline) {
        if (Date.now() >= deadline) finish()
        return
      }
      try {
        recognition.start()
      } catch {
        window.setTimeout(restartIfNoSpeechYet, 120)
      }
    }

    recognition.lang = 'en-US'
    recognition.interimResults = true
    recognition.continuous = false
    recognition.onresult = (event) => {
      interimTranscript = ''
      for (let index = event.resultIndex; index < event.results.length; index += 1) {
        const transcript = event.results[index][0]?.transcript ?? ''
        if (event.results[index].isFinal) finalParts.push(transcript)
        else interimTranscript = `${interimTranscript} ${transcript}`.trim()
      }
      restartSilenceTimer()
    }
    recognition.onerror = () => {
      if (currentTranscript()) {
        finish()
        return
      }
      restartIfNoSpeechYet()
    }
    recognition.onend = restartIfNoSpeechYet

    try {
      recognition.start()
    } catch {
      restartIfNoSpeechYet()
    }
  })
}

function initialUserAnswers(roleplay: RoleplayMission) {
  return roleplay.history?.map((turn) => turn.user).filter(Boolean) ?? []
}

function initialNpcReplies(roleplay: RoleplayMission) {
  const replies = roleplay.turns.map((turn) => turn.npc)
  roleplay.history?.forEach((turn, index) => {
    replies[index + 1] = turn.npc
  })
  return replies
}

export default function RoleplayScreen({
  roleplay,
  onProgressChange,
  onFinish,
  onExit,
  onSpeakText,
  onRecord,
  variant = 'lesson',
}: Props) {
  const [view, setView] = useState<RoleplayView>(() => roleplay.history?.length ? 'chat' : 'intro')
  const [userAnswers, setUserAnswers] = useState<string[]>(() => initialUserAnswers(roleplay))
  const [npcReplies, setNpcReplies] = useState<string[]>(() => initialNpcReplies(roleplay))
  const [recordState, setRecordState] = useState<RecordState>('idle')
  const [showFinalNpc, setShowFinalNpc] = useState(false)
  const [showCompletion, setShowCompletion] = useState(false)
  const [showText, setShowText] = useState(false)
  const [finalResult, setFinalResult] = useState<ChapterResult | null>(null)
  const [isFinalizing, setIsFinalizing] = useState(false)
  const [speechError, setSpeechError] = useState('')
  const [finishError, setFinishError] = useState('')
  const chatBottomRef = useRef<HTMLDivElement>(null)
  const roleplayKey = [
    roleplay.mission,
    roleplay.missionSummary,
    roleplay.turns.length,
    roleplay.history?.map((turn) => `${turn.user}=>${turn.npc}`).join('|') ?? '',
  ].join('::')

  useEffect(() => {
    setView(roleplay.history?.length ? 'chat' : 'intro')
    setUserAnswers(initialUserAnswers(roleplay))
    setNpcReplies(initialNpcReplies(roleplay))
    setRecordState('idle')
    setShowFinalNpc(Boolean(roleplay.history?.length && roleplay.history.length >= roleplay.turns.length))
    setShowCompletion(false)
    setShowText(false)
    setFinalResult(null)
    setSpeechError('')
    setFinishError('')
  }, [roleplayKey])

  useEffect(() => {
    const progress = view === 'intro'
      ? PROGRESS_INTRO
      : PROGRESS_INTRO + (userAnswers.length / roleplay.turns.length) * PROGRESS_CHAT_RANGE
    onProgressChange(progress)
  }, [view, userAnswers, roleplay.turns.length, onProgressChange])

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [userAnswers])

  const isDone = userAnswers.length >= roleplay.turns.length

  const handleRecord = async () => {
    if (recordState !== 'idle' || isDone) return
    const currentIdx = userAnswers.length
    setRecordState('recording')
    setSpeechError('')
    try {
      const { audio: blob, transcript } = await recordRoleplaySpeech()
      const cleanTranscript = transcript.trim()
      if (!cleanTranscript) {
        setSpeechError('I could not hear you. Please try again.')
        setRecordState('idle')
        return
      }
      const result = await onRecord(blob, cleanTranscript)
      setUserAnswers(prev => [...prev, result.userTranscript])
      setNpcReplies(prev => {
        const next = [...prev]
        next[currentIdx + 1] = result.characterText
        return next
      })
      void onSpeakText?.(result.characterText)
      if (currentIdx + 1 >= roleplay.turns.length) {
        setShowFinalNpc(true)
      }
      setRecordState('idle')
    } catch {
      setRecordState('idle')
    }
  }

  const handleCompleteLesson = async () => {
    if (isFinalizing) return
    setIsFinalizing(true)
    setFinishError('')
    try {
      const result = await Promise.resolve(onFinish())
      if (result) {
        setFinalResult(result)
        setShowCompletion(true)
        setTimeout(() => setShowText(true), COMPLETION_TEXT_MS)
      }
    } catch {
      setFinishError('Could not complete the lesson. Please try again.')
    } finally {
      setIsFinalizing(false)
    }
  }

  if (view === 'intro') {
    return (
      <div className={`${styles.introPage} ${variant === 'review' ? styles.reviewIntroPage : ''}`}>
        <div className={styles.introContent}>
          <div
            className={styles.thumbnail}
            style={{ background: roleplay.thumbnailColor }}
          >
            {roleplay.thumbnailUrl
              ? <img src={roleplay.thumbnailUrl} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
              : <span>🎭</span>
            }
          </div>
          <div className={styles.missionCard}>
            <div className={styles.missionBadge}>Mission</div>
            <p className={styles.missionText}>{roleplay.mission}</p>
          </div>
        </div>
        <div className={styles.introBottom}>
          <button
            className={styles.imgBtn}
            onClick={() => {
              setView('chat')
              void onSpeakText?.(roleplay.turns[0]?.npc ?? '')
            }}
            aria-label="Start"
          >
            <img src={IMAGES.nextBtnActive} alt="Start" className={styles.btnImg} />
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className={`${styles.chatPage} ${variant === 'review' ? styles.reviewChatPage : ''}`}>

      <div className={styles.chatHeader}>
        <div className={styles.missionSummaryCard}>
          <span className={styles.missionSummaryLabel}>Situation</span>
          <span className={styles.missionSummaryText}>{roleplay.missionSummary}</span>
        </div>
      </div>

      <div className={styles.chatArea}>
        {roleplay.turns.map((turn, i) => (
          <div key={i} className={styles.turnGroup}>
            {userAnswers.length >= i && (
              <div className={styles.npcBubble}>{npcReplies[i] ?? turn.npc}</div>
            )}
            {userAnswers.length > i && (
              <div className={styles.userBubble}>{userAnswers[i]}</div>
            )}
          </div>
        ))}
        {showFinalNpc && (
          <div className={styles.npcBubble}>{npcReplies[userAnswers.length] ?? roleplay.finalNpc}</div>
        )}
        <div ref={chatBottomRef} />
      </div>

      <div className={styles.chatBottom}>
        {speechError && <p className={styles.speechError}>{speechError}</p>}
        {!isDone && (
          <button
            className={styles.imgBtn}
            onClick={handleRecord}
            disabled={recordState === 'recording'}
            aria-label={recordState === 'recording' ? 'Recording...' : 'Tap to speak'}
          >
            <img
              src={recordState === 'recording' ? IMAGES.recordBtnActive : IMAGES.recordBtnInactive}
              alt={recordState === 'recording' ? 'Recording' : 'Tap to speak'}
              className={`${styles.btnImg} ${recordState === 'recording' ? styles.recording : ''}`}
            />
          </button>
        )}
        {isDone && (
          <section className={styles.finishPanel}>
            <div>
              <strong>Roleplay finished!</strong>
              <p>Check your chat, then complete the lesson.</p>
            </div>
            {finishError && <p className={styles.finishError}>{finishError}</p>}
            <button
              className={styles.finishButton}
              onClick={handleCompleteLesson}
              disabled={isFinalizing}
            >
              {isFinalizing ? 'Saving...' : 'Complete Lesson'}
            </button>
          </section>
        )}
      </div>

      {showCompletion && finalResult && (
        <div className={styles.completionOverlay}>
          <>
            <div className={styles.trophyWrapper}>
              <TrophyAnimation className={styles.trophyAnim} />
            </div>
            <section className={`${styles.completionResult} ${showText ? styles.completionVisible : ''}`}>
              <span className={styles.completionBadge}>
                Chapter {finalResult.chapterNumber}
              </span>
              <h1>{finalResult.message}</h1>
              <div className={styles.starFan} aria-label={`${finalResult.stars} stars`}>
                {[0, 1, 2].map((index) => (
                  <span key={index} className={index < finalResult.stars ? styles.starOn : styles.starOff}>
                    ★
                  </span>
                ))}
              </div>
              <strong>{`${finalResult.totalScore} points`}</strong>
              <p>
                {finalResult.totalScore >= 80
                  ? 'You spoke clearly and used the story words well.'
                  : 'Good effort. Try one more chapter to make the sentences smoother.'}
              </p>
            </section>
            <button
              className={`${styles.imgBtn} ${styles.completionBtn} ${showText ? styles.completionVisible : ''}`}
              onClick={onExit}
              aria-label="Back to chapters"
            >
              <img src={IMAGES.nextBtnActive} alt="Back to chapters" className={styles.btnImg} />
            </button>
          </>
        </div>
      )}

    </div>
  )
}
