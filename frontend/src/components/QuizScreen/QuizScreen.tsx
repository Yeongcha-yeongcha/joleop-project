import { useState } from 'react'
import type { QuizQuestion } from '../../types'
import { IMAGES } from '../../constants/assets'
import styles from './QuizScreen.module.css'

const MOCK_RECORD_MS = 2000  // simulated recording duration (replace with real STT)

type QuizState = 'idle' | 'recording' | 'done'

interface Props {
  quiz: QuizQuestion
  onNext: () => void
}

export default function QuizScreen({ quiz, onNext }: Props) {
  const [state, setState] = useState<QuizState>('idle')

  const handleMicTap = () => {
    if (state === 'idle') {
      setState('recording')
      setTimeout(() => setState('done'), MOCK_RECORD_MS)
    } else if (state === 'done') {
      onNext()
    }
  }

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>

      <div className={styles.illustrationWrapper}>
        <div
          className={styles.illustration}
          style={{ background: quiz.imageColor }}
          aria-label="퀴즈 일러스트"
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
          <button className={styles.imgBtn} onClick={onNext} aria-label="다음">
            <img src={IMAGES.nextBtnActive} alt="다음" className={styles.btnImg} />
          </button>
        ) : (
          <button
            className={styles.imgBtn}
            onClick={handleMicTap}
            aria-label={state === 'recording' ? '녹음 중...' : '탭하여 말하기'}
          >
            <img
              src={state === 'recording' ? IMAGES.recordBtnActive : IMAGES.recordBtnInactive}
              alt={state === 'recording' ? '녹음 중' : '탭하여 말하기'}
              className={`${styles.btnImg} ${state === 'recording' ? styles.recording : ''}`}
            />
          </button>
        )}
      </div>

    </div>
  )
}
