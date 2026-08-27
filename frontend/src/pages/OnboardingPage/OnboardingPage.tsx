import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createProfile, loginProfile, postOnboarding, type OnboardingAnswer } from '../../services/api'
import styles from './OnboardingPage.module.css'

type Step = 0 | 1 | 2 | 3 | 4 | 5 | 6
type SpeechRecognitionConstructor = new () => {
  lang: string
  interimResults: boolean
  maxAlternatives: number
  onresult: ((event: { results: { 0: { 0: { transcript: string } } } }) => void) | null
  onerror: (() => void) | null
  onend: (() => void) | null
  start: () => void
}

declare global {
  interface Window {
    SpeechRecognition?: SpeechRecognitionConstructor
    webkitSpeechRecognition?: SpeechRecognitionConstructor
  }
}

const fruitCards = [
  { id: 'apple', image: '/images/onboarding/apple.png', label: '사과', answer: 'Apple' },
  { id: 'banana', image: '/images/onboarding/banana.png', label: '바나나', answer: 'Banana' },
  { id: 'peach', image: '/images/onboarding/peach.png', label: '복숭아', answer: 'Peach' },
]

const weatherCards = [
  { id: 'rain', emoji: '🌧️', label: '비', answer: 'Rain' },
  { id: 'wind', emoji: '💨', label: '바람', answer: 'Wind' },
  { id: 'sun', emoji: '☀️', label: '맑음', answer: 'Sunny' },
]

function upsertAnswer(answers: OnboardingAnswer[], questionId: number, answer: string): OnboardingAnswer[] {
  return [
    ...answers.filter((item) => item.questionId !== questionId),
    { questionId, answer },
  ]
}

export default function OnboardingPage() {
  const navigate = useNavigate()
  const [step, setStep] = useState<Step>(0)
  const [name, setName] = useState('')
  const [age, setAge] = useState('')
  const [answers, setAnswers] = useState<OnboardingAnswer[]>([])
  const [placementLevel, setPlacementLevel] = useState<1 | 2 | 3>(3)
  const [isListening, setIsListening] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const isTreeScene = step <= 1
  const isCastleScene = step === 6

  const lionImage = useMemo(() => {
    if (step === 0) return '/images/onboarding/lion-wave.png'
    if (step === 1) return '/images/onboarding/lion-thinking.png'
    if (step === 2) return '/images/onboarding/lion-backpack.png'
    if (step === 4) return '/images/onboarding/lion-side.png'
    if (step === 5) return '/images/onboarding/lion-flag.png'
    if (step === 6) return '/images/onboarding/lion-reading.png'
    return null
  }, [step])

  const addAnswer = (questionId: number, answer: string) => {
    setAnswers((current) => upsertAnswer(current, questionId, answer))
  }

  const next = () => setStep((current) => Math.min(current + 1, 6) as Step)

  const handleSpeechFallback = (field: 'name' | 'age') => {
    const fallback = field === 'name' ? '별명' : '7'
    const value = window.prompt(field === 'name' ? '내 별명을 입력해줘' : '내 나이를 입력해줘', fallback)
    if (!value) return
    completeSpeechInput(field, value)
  }

  const completeSpeechInput = (field: 'name' | 'age', value: string) => {
    if (field === 'name') {
      setName(value)
      addAnswer(1, value)
    } else {
      setAge(value)
      addAnswer(2, value)
    }
    next()
  }

  const handleSpeechInput = (field: 'name' | 'age') => {
    if (isListening) return
    const SpeechRecognition = window.SpeechRecognition ?? window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      handleSpeechFallback(field)
      return
    }

    const recognition = new SpeechRecognition()
    recognition.lang = 'ko-KR'
    recognition.interimResults = false
    recognition.maxAlternatives = 1
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript.trim()
      if (transcript) completeSpeechInput(field, transcript)
    }
    recognition.onerror = () => {
      setIsListening(false)
      handleSpeechFallback(field)
    }
    recognition.onend = () => setIsListening(false)
    setIsListening(true)
    recognition.start()
  }

  const submitOnboarding = async () => {
    if (isSubmitting) return
    setIsSubmitting(true)
    const pendingProfile = JSON.parse(window.localStorage.getItem('yeongcha:pending-profile') || 'null') as {
      profilePassword?: string
      profileImageId?: number
    } | null
    const payload = answers.length
      ? answers
      : [
          { questionId: 1, answer: name || '별명' },
          { questionId: 2, answer: age || '7' },
          { questionId: 3, answer: 'Apple' },
        ]
    try {
      if (pendingProfile?.profilePassword) {
        const profile = await createProfile({
          nickname: name || '새 친구',
          age: Number.parseInt(age, 10) || 7,
          profilePassword: pendingProfile.profilePassword,
          profileImageId: pendingProfile.profileImageId,
        })
        await loginProfile(profile.profileId, pendingProfile.profilePassword)
      }
      await postOnboarding(payload)
    } catch {
      // 인증이 붙기 전에도 온보딩 화면 흐름은 완료 처리합니다.
    } finally {
      window.localStorage.setItem('yeongcha:onboarding-completed', 'true')
      window.localStorage.setItem('yeongcha:placement-level', String(placementLevel))
      window.localStorage.removeItem('yeongcha:pending-profile')
      navigate('/home')
    }
  }

  return (
    <main
      className={[
        styles.page,
        isTreeScene ? styles.treeScene : styles.meadowScene,
        isCastleScene ? styles.castleScene : '',
        styles[`step${step}`],
      ].join(' ')}
    >
      {(step === 2 || step === 3) && (
        <img src="/images/onboarding/adventure-bag.png" alt="" className={styles.bag} />
      )}

      {lionImage && <img src={lionImage} alt="포포" className={styles.lion} />}

      {step === 3 && (
        <div className={styles.cardRow} aria-label="과일 선택">
          {fruitCards.map((card) => (
            <button
              key={card.id}
              className={styles.choiceCard}
              onClick={() => {
                const nextAnswers = upsertAnswer(answers, 3, card.answer)
                setAnswers(nextAnswers)
                if (card.answer === 'Apple') {
                  setStep(4)
                } else {
                  setPlacementLevel(1)
                  setStep(6)
                }
              }}
            >
              <img src={card.image} alt="" className={styles.choiceImage} />
              <span>{card.label}</span>
            </button>
          ))}
        </div>
      )}

      {step === 4 && (
        <div className={styles.cardRow} aria-label="날씨 선택">
          {weatherCards.map((card) => (
            <button
              key={card.id}
              className={styles.choiceCard}
              onClick={() => {
                const nextAnswers = upsertAnswer(answers, 4, card.answer)
                setAnswers(nextAnswers)
                if (card.answer === 'Rain') {
                  setPlacementLevel(3)
                  setStep(5)
                } else {
                  setPlacementLevel(2)
                  setStep(6)
                }
              }}
            >
              <span className={styles.choiceEmoji}>{card.emoji}</span>
              <span>{card.label}</span>
            </button>
          ))}
        </div>
      )}

      <section className={styles.bottomPanel}>
        {step !== 3 && (
          <div className={styles.speechBox}>
          {step === 0 && (
            <>
              Hi! I’m Popo.
              <br />
              I’m your story guide.
              <br />
              What is your name?
            </>
          )}
          {step === 1 && (
            <>
              Nice name!
              <br />
              How old are you?
              <br />
              Tell me your age.
            </>
          )}
          {step === 2 && (
            <>
              Great!
              <br />
              Let’s pack your bag.
              <br />
              Can you find “Apple”?
            </>
          )}
          {step === 4 && (
            <>
              Good job!
              <br />
              Can you find
              <br />
              “It is raining”?
              <br />
              Pick the weather card.
            </>
          )}
          {step === 5 && (
            <>
              All set!
              <br />
              Say it with me.
              <br />
              Let’s go!
            </>
          )}
          {step === 6 && (
            <>
              Great!
              <br />
              Level {placementLevel} is ready for {name || 'you'}.
              <br />
              Let’s start your story!
            </>
          )}
          </div>
        )}

        {step <= 1 && (
          <button className={styles.primaryButton} onClick={() => handleSpeechInput(step === 0 ? 'name' : 'age')}>
            <span className={styles.micIcon}>●</span>
            {isListening ? 'Listening...' : 'Tap to speak'}
          </button>
        )}

        {step === 2 && (
          <button className={styles.primaryButton} onClick={next} aria-label="다음">
            →
          </button>
        )}

        {step === 3 && (
          <button
            className={styles.primaryButton}
            onClick={() => {
              addAnswer(3, 'Apple')
              setStep(4)
            }}
            aria-label="다음"
          >
            →
          </button>
        )}

        {step === 4 && (
          <button
            className={styles.primaryButton}
            onClick={() => {
              addAnswer(4, 'Rain')
              setPlacementLevel(3)
              next()
            }}
            aria-label="다음"
          >
            →
          </button>
        )}

        {step === 5 && (
          <button
            className={styles.primaryButton}
            onClick={() => {
              addAnswer(5, "Let's go")
              next()
            }}
          >
            <span className={styles.micIcon}>●</span>
            Tap to speak
          </button>
        )}

        {step === 6 && (
          <button className={styles.primaryButton} onClick={submitOnboarding} disabled={isSubmitting}>
            {isSubmitting ? 'Loading...' : 'Start Adventure'}
          </button>
        )}
      </section>
    </main>
  )
}
