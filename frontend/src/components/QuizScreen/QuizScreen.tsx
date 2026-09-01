import { useState } from 'react'
import type { QuizQuestion } from '../../types'
import { useAudioRecorder } from '../../hooks/useAudioRecorder'
import { IMAGES } from '../../constants/assets'
import styles from './QuizScreen.module.css'

const MOCK_RECORD_MS = 2000  // simulated recording duration (replace with real STT)

type QuizState = 'idle' | 'recording' | 'done'

interface Props {
  quiz: QuizQuestion
  onNext: () => void
  onRecord?: (audio: Blob) => Promise<void | number>
}

export default function QuizScreen({ quiz, onNext, onRecord }: Props) {
  const [state, setState] = useState<QuizState>('idle')
  const recorder = useAudioRecorder()

  const handleMicTap = async () => {
    if (state === 'done') {
      onNext()
      return
    }
    if (state === 'idle') {
      setState('recording')
      try {
        if (onRecord) {
          const blob = await recorder.record()
          await onRecord(blob)
        } else {
          await new Promise((resolve) => setTimeout(resolve, MOCK_RECORD_MS))
        }
        setState('done')
      } catch {
        setState('idle')
      }
    }
  }

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>

      <div className={styles.illustrationWrapper}>
        <div
          className={styles.illustration}
          style={{ background: quiz.imageColor }}
          aria-label="Quiz picture"
        >
          {quiz.imageUrl
            ? <img src={quiz.imageUrl} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            : <span>📖</span>
          }
        </div>
        <div className={styles.quizCard}>
          <span className={styles.quizCardText}>{quiz.question}</span>
        </div>
      </div>

      <div className={styles.sentenceBoxWrapper}>
        <div className={styles.sentenceBox}>
          <p className={`${styles.sentence} ${state === 'done' ? styles.sentenceDone : ''}`}>
            {quiz.sentence}{' '}
            <span className={`${styles.blank} ${state === 'done' ? styles.blankFilled : ''}`}>
              {state === 'done' ? quiz.answer : ''}
            </span>
          </p>
        </div>
      </div>

      <div className={styles.bottomArea}>
        {state === 'done' ? (
          <button className={styles.imgBtn} onClick={onNext} aria-label="Next">
            <img src={IMAGES.nextBtnActive} alt="Next" className={styles.btnImg} />
          </button>
        ) : (
          <button
            className={styles.imgBtn}
            onClick={handleMicTap}
            aria-label={state === 'recording' ? 'Recording...' : 'Tap to speak'}
          >
            <img
              src={state === 'recording' ? IMAGES.recordBtnActive : IMAGES.recordBtnInactive}
              alt={state === 'recording' ? 'Recording' : 'Tap to speak'}
              className={`${styles.btnImg} ${state === 'recording' ? styles.recording : ''}`}
            />
          </button>
        )}
      </div>

    </div>
  )
}
