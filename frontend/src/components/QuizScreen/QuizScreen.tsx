import { useEffect, useState } from 'react'
import type { QuizQuestion } from '../../types'
import { useAudioRecorder } from '../../hooks/useAudioRecorder'
import { IMAGES } from '../../constants/assets'
import styles from './QuizScreen.module.css'

const RECORD_MS = 4000

type QuizState = 'idle' | 'recording' | 'done'
type QuizFeedback = 'correct' | 'wrong' | ''

interface QuizRecordResult {
  transcript: string
  passed: boolean
}

interface Props {
  quiz: QuizQuestion
  onNext: () => void
  onRecord: (audio: Blob, transcript?: string) => Promise<void | number | boolean | QuizRecordResult>
  currentStep?: number
  totalSteps?: number
}

function recognizeSpeech(durationMs = RECORD_MS): Promise<string> {
  return new Promise((resolve) => {
    if (typeof window === 'undefined') {
      resolve('')
      return
    }

    const Recognition = window.SpeechRecognition ?? window.webkitSpeechRecognition
    if (!Recognition) {
      resolve('')
      return
    }

    const recognition = new Recognition()
    let transcript = ''
    let settled = false

    const finish = () => {
      if (settled) return
      settled = true
      try {
        recognition.stop()
      } catch {
        // The browser may already have stopped recognition.
      }
      resolve(transcript.trim())
    }

    recognition.lang = 'en-US'
    recognition.interimResults = true
    recognition.continuous = true
    recognition.onresult = (event) => {
      transcript = Array.from(event.results)
        .map((result) => result[0]?.transcript ?? '')
        .join(' ')
        .trim()
    }
    recognition.onerror = finish
    recognition.onend = finish

    try {
      recognition.start()
      window.setTimeout(finish, durationMs)
    } catch {
      resolve('')
    }
  })
}

export default function QuizScreen({ quiz, onNext, onRecord, currentStep, totalSteps }: Props) {
  const [state, setState] = useState<QuizState>('idle')
  const [error, setError] = useState('')
  const [feedback, setFeedback] = useState<QuizFeedback>('')
  const [spokenAnswer, setSpokenAnswer] = useState('')
  const recorder = useAudioRecorder()

  useEffect(() => {
    setState('idle')
    setError('')
    setFeedback('')
    setSpokenAnswer('')
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
        const [blob, transcript] = await Promise.all([
          recorder.record(RECORD_MS),
          recognizeSpeech(RECORD_MS),
        ])
        const result = await onRecord(blob, transcript)
        if (typeof result === 'boolean') {
          setFeedback(result ? 'correct' : 'wrong')
        } else if (typeof result === 'number') {
          setFeedback(result >= 70 ? 'correct' : 'wrong')
        } else if (result && typeof result === 'object') {
          setSpokenAnswer(result.transcript)
          setFeedback(result.passed ? 'correct' : 'wrong')
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
            <span className={[
              styles.blank,
              state === 'done' ? styles.blankFilled : '',
              feedback === 'correct' ? styles.blankCorrect : '',
              feedback === 'wrong' ? styles.blankWrong : '',
            ].join(' ')}>
              {state === 'done' ? spokenAnswer : ''}
            </span>
          </p>
        </div>
      </div>

      <div className={styles.bottomArea}>
        {error && <p className={styles.errorText}>{error}</p>}
        {feedback && (
          <p className={`${styles.feedbackText} ${styles[feedback]}`}>
            {feedback === 'correct' ? 'Correct!' : 'Wrong!'}
          </p>
        )}
        {feedback === 'wrong' && (
          <div className={styles.answerBox} aria-label="Correct answer">
            <span className={styles.answerLabel}>Answer</span>
            <strong className={styles.answerWord}>{quiz.answer}</strong>
          </div>
        )}
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
