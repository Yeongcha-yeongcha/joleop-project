import { useEffect, useState } from 'react'
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
  currentStep?: number
  totalSteps?: number
}

export default function QuizScreen({ quiz, onNext, onRecord, currentStep, totalSteps }: Props) {
  const [state, setState] = useState<QuizState>('idle')
  const [error, setError] = useState('')
  const recorder = useAudioRecorder()

  useEffect(() => {
    setState('idle')
    setError('')
  }, [quiz.question, quiz.sentence, quiz.answer])

  const handleMicTap = async () => {
    if (state === 'done') {
      onNext()
      return
    }
    if (state === 'idle') {
      setState('recording')
      setError('')
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
        setError('Could not hear that. Please try again.')
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
          {currentStep && totalSteps && (
            <b className={styles.quizStep}>
              {currentStep}/{totalSteps}
            </b>
          )}
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
        {error && <p className={styles.errorText}>{error}</p>}
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
