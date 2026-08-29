import { useState, useRef, useEffect } from 'react'
import lottie from 'lottie-web'
import type { RoleplayMission } from '../../types'
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
  }, []) // deps 비움 — 애니메이션은 마운트 시 1회만 생성
  return <div ref={ref} className={className} />
}

// Progress range: intro starts at 70%, chat fills the remaining 30% as turns complete
const PROGRESS_INTRO = 0.70
const PROGRESS_CHAT_RANGE = 0.30

const MOCK_RECORD_MS = 2000       // simulated recording duration (replace with real STT)
const FINAL_NPC_DELAY_MS = 3000   // pause after last user turn before showing completion
const COMPLETION_TEXT_MS = 700    // delay before "Very nice!" fades in
const COMPLETION_BTN_MS = 1400    // delay before next button fades in

type RoleplayView = 'intro' | 'chat'
type RecordState = 'idle' | 'recording'

interface Props {
  roleplay: RoleplayMission
  onProgressChange: (v: number) => void
  onFinish: () => void
  onRecord?: (audio: Blob) => Promise<{
    userTranscript: string
    characterText: string
    missionCompleted: boolean
  }>
}

export default function RoleplayScreen({ roleplay, onProgressChange, onFinish, onRecord }: Props) {
  const [view, setView] = useState<RoleplayView>('intro')
  const [userAnswers, setUserAnswers] = useState<string[]>([])
  const [npcReplies, setNpcReplies] = useState<string[]>(roleplay.turns.map((turn) => turn.npc))
  const [recordState, setRecordState] = useState<RecordState>('idle')
  const [showFinalNpc, setShowFinalNpc] = useState(false)
  const [showCompletion, setShowCompletion] = useState(false)
  const [showText, setShowText] = useState(false)
  const [showButton, setShowButton] = useState(false)
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
            <div className={styles.missionBadge}>미션</div>
            <p className={styles.missionText}>{roleplay.mission}</p>
          </div>
        </div>
        <div className={styles.introBottom}>
          <button className={styles.imgBtn} onClick={() => setView('chat')} aria-label="시작">
            <img src={IMAGES.nextBtnActive} alt="시작" className={styles.btnImg} />
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
            aria-label={recordState === 'recording' ? '녹음 중...' : '탭하여 말하기'}
          >
            <img
              src={recordState === 'recording' ? IMAGES.recordBtnActive : IMAGES.recordBtnInactive}
              alt={recordState === 'recording' ? '녹음 중' : '탭하여 말하기'}
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
                setTimeout(() => setShowButton(true), COMPLETION_BTN_MS)
              }}
            />
          </div>
          <span className={`${styles.completionText} ${showText ? styles.completionVisible : ''}`}>
            Very nice!
          </span>
          <button
            className={`${styles.imgBtn} ${styles.completionBtn} ${showButton ? styles.completionVisible : ''}`}
            onClick={onFinish}
            aria-label="홈으로"
            disabled={!showButton}
          >
            <img src={IMAGES.nextBtnActive} alt="홈으로" className={styles.btnImg} />
          </button>
        </div>
      )}

    </div>
  )
}
