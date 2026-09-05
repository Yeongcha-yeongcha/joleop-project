import { useState, useRef, useEffect } from 'react'
import lottie from 'lottie-web'
import type { RoleplayMission } from '../../types'
import type { ChapterResult } from '../../utils/chapterProgress'
import { useAudioRecorder } from '../../hooks/useAudioRecorder'
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

const MOCK_RECORD_MS = 2000       // simulated recording duration (replace with real STT)
const FINAL_NPC_DELAY_MS = 3000   // pause after last user turn before showing completion
const COMPLETION_TEXT_MS = 500    // delay before final result fades in

type RoleplayView = 'intro' | 'chat'
type RecordState = 'idle' | 'recording'

interface Props {
  roleplay: RoleplayMission
  onProgressChange: (v: number) => void
  onFinish: () => Promise<ChapterResult | null> | ChapterResult | null
  onExit: () => void
  onRecord?: (audio: Blob) => Promise<{
    userTranscript: string
    characterText: string
    missionCompleted: boolean
    score?: number
  }>
}

function scoreLabel(value: number | null) {
  return value === null ? '-' : `${value}%`
}

export default function RoleplayScreen({ roleplay, onProgressChange, onFinish, onExit, onRecord }: Props) {
  const [view, setView] = useState<RoleplayView>('intro')
  const [userAnswers, setUserAnswers] = useState<string[]>([])
  const [npcReplies, setNpcReplies] = useState<string[]>(roleplay.turns.map((turn) => turn.npc))
  const [recordState, setRecordState] = useState<RecordState>('idle')
  const [showFinalNpc, setShowFinalNpc] = useState(false)
  const [showCompletion, setShowCompletion] = useState(false)
  const [showText, setShowText] = useState(false)
  const [finalResult, setFinalResult] = useState<ChapterResult | null>(null)
  const [isFinalizing, setIsFinalizing] = useState(false)
  const chatBottomRef = useRef<HTMLDivElement>(null)
  const recorder = useAudioRecorder()

  useEffect(() => {
    const progress = view === 'intro'
      ? PROGRESS_INTRO
      : PROGRESS_INTRO + (userAnswers.length / roleplay.turns.length) * PROGRESS_CHAT_RANGE
    onProgressChange(progress)
  }, [view, userAnswers, roleplay.turns.length, onProgressChange])

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [userAnswers])

  useEffect(() => {
    if (!showCompletion || finalResult || isFinalizing) return
    setIsFinalizing(true)
    Promise.resolve(onFinish())
      .then((result) => {
        if (result) setFinalResult(result)
      })
      .finally(() => setIsFinalizing(false))
  }, [finalResult, isFinalizing, onFinish, showCompletion])

  const isDone = userAnswers.length >= roleplay.turns.length

  const handleRecord = async () => {
    if (recordState !== 'idle' || isDone) return
    const currentIdx = userAnswers.length
    setRecordState('recording')
    try {
      if (onRecord) {
        const blob = await recorder.record()
        const result = await onRecord(blob)
        setUserAnswers(prev => [...prev, result.userTranscript])
        setNpcReplies(prev => {
          const next = [...prev]
          next[currentIdx + 1] = result.characterText
          return next
        })
        if (result.missionCompleted || currentIdx + 1 >= roleplay.turns.length) {
          setShowFinalNpc(true)
          setTimeout(() => setShowCompletion(true), FINAL_NPC_DELAY_MS)
        }
      } else {
        await new Promise((resolve) => setTimeout(resolve, MOCK_RECORD_MS))
        setUserAnswers(prev => [...prev, roleplay.turns[currentIdx].user])
        if (currentIdx + 1 >= roleplay.turns.length) {
          setShowFinalNpc(true)
          setTimeout(() => setShowCompletion(true), FINAL_NPC_DELAY_MS)
        }
      }
      setRecordState('idle')
    } catch {
      setRecordState('idle')
    }
  }

  if (view === 'intro') {
    return (
      <div className={styles.introPage}>
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
          <button className={styles.imgBtn} onClick={() => setView('chat')} aria-label="Start">
            <img src={IMAGES.nextBtnActive} alt="Start" className={styles.btnImg} />
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className={styles.chatPage}>

      <div className={styles.chatHeader}>
        <div className={styles.missionSummaryCard}>
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
      </div>

      {showCompletion && (
        <div className={styles.completionOverlay}>
          <div className={styles.trophyWrapper}>
            <TrophyAnimation
              className={styles.trophyAnim}
              onComplete={() => {
                setTimeout(() => setShowText(true), COMPLETION_TEXT_MS)
              }}
            />
          </div>
          <section className={`${styles.completionResult} ${showText ? styles.completionVisible : ''}`}>
            <span className={styles.completionBadge}>
              Chapter {finalResult?.chapterNumber ?? 1}
            </span>
            <h1>{finalResult?.message ?? 'Great job!'}</h1>
            <div className={styles.starFan} aria-label={`${finalResult?.stars ?? 0} stars`}>
              {[0, 1, 2].map((index) => (
                <span key={index} className={index < (finalResult?.stars ?? 0) ? styles.starOn : styles.starOff}>
                  ★
                </span>
              ))}
            </div>
            <strong>{finalResult ? `${finalResult.totalScore} points` : 'Saving...'}</strong>
            {finalResult && (
              <div className={styles.scoreBreakdown}>
                <div>
                  <span>Repeat</span>
                  <b>{scoreLabel(finalResult.breakdown.repeat)}</b>
                </div>
                <div>
                  <span>Quiz</span>
                  <b>{scoreLabel(finalResult.breakdown.description)}</b>
                </div>
                <div>
                  <span>Roleplay</span>
                  <b>{scoreLabel(finalResult.breakdown.roleplay)}</b>
                </div>
              </div>
            )}
            <p>
              {finalResult && finalResult.totalScore >= 80
                ? 'You spoke clearly and used the story words well.'
                : 'Good effort. Try one more chapter to make the sentences smoother.'}
            </p>
          </section>
          <button
            className={`${styles.imgBtn} ${styles.completionBtn} ${finalResult ? styles.completionVisible : ''}`}
            onClick={onExit}
            aria-label="Back to chapters"
            disabled={!finalResult}
          >
            <img src={IMAGES.nextBtnActive} alt="Back to chapters" className={styles.btnImg} />
          </button>
        </div>
      )}

    </div>
  )
}
