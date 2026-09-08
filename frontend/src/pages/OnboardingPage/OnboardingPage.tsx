import { useEffect, useMemo, useRef, useState, type FormEvent, type PointerEvent as ReactPointerEvent, type ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { createProfile, loginProfile, postOnboarding, type OnboardingAnswer } from '../../services/api'
import { saveProfileColor } from '../../utils/profileAvatar'
import { SOUNDS } from '../../constants/assets'
import { startBackgroundMusic } from '../../utils/sound'
import styles from './OnboardingPage.module.css'

type Step = 0 | 1 | 2 | 3 | 4 | 5 | 6

const SCENE_FADE_MS = 520   // 배경 크로스페이드 길이. CSS 의 sceneOut 과 맞춘다.
const fruitCards = [
  { id: 'apple', image: '/images/onboarding/apple.png', answer: 'Apple' },
  { id: 'banana', image: '/images/onboarding/banana.png', answer: 'Banana' },
  { id: 'peach', image: '/images/onboarding/peach.png', answer: 'Peach' },
]

const weatherCards = [
  { id: 'rain', emoji: '🌧️', answer: 'Rain' },
  { id: 'wind', emoji: '💨', answer: 'Wind' },
  { id: 'sun', emoji: '☀️', answer: 'Sunny' },
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
  const [manualInputField, setManualInputField] = useState<'name' | 'age' | null>(null)
  const [manualInputValue, setManualInputValue] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Popo 자기소개(step 0)부터 여행 마지막까지 배경음악을 작게 깐다.
  // 이 화면을 떠나면(=/home 으로 이동) 언마운트되며 멈춘다.
  useEffect(() => startBackgroundMusic(SOUNDS.onboardingBgm, 0.14), [])

  const [dragId, setDragId] = useState<string | null>(null)
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 })
  const [isOverBag, setIsOverBag] = useState(false)
  const bagRef = useRef<HTMLImageElement | null>(null)
  const dragOriginRef = useRef<{ x: number; y: number } | null>(null)

  const isTreeScene = step <= 1
  const isCastleScene = step === 6
  const scene = isTreeScene ? 'tree' : isCastleScene ? 'castle' : 'meadow'
  // 배경이 바뀔 때 이전 배경을 위에 얹어 서서히 지운다(크로스페이드).
  // 새 배경을 페이드 인 시키면 첫 진입에서 한 번 비어 보이므로 반대로 한다.
  const sceneRef = useRef(scene)
  const [leavingScene, setLeavingScene] = useState<string | null>(null)
  useEffect(() => {
    if (sceneRef.current === scene) return
    const previous = sceneRef.current
    sceneRef.current = scene
    setLeavingScene(previous)
    const timer = window.setTimeout(() => setLeavingScene(null), SCENE_FADE_MS)
    return () => window.clearTimeout(timer)
  }, [scene])

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

  const commitCard = (questionId: 3 | 4, answer: string) => {
    setAnswers((current) => upsertAnswer(current, questionId, answer))
    if (questionId === 3) {
      if (answer === 'Apple') {
        setStep(4)
      } else {
        setPlacementLevel(1)
        setStep(6)
      }
      return
    }
    if (answer === 'Rain') {
      setPlacementLevel(3)
      setStep(5)
    } else {
      setPlacementLevel(2)
      setStep(6)
    }
  }

  // 가방 판정 영역. 손가락이 카드에 가려 정확히 겨누기 어려우므로 여유를 둔다.
  const isOverBagAt = (x: number, y: number) => {
    const rect = bagRef.current?.getBoundingClientRect()
    if (!rect) return false
    const pad = 28
    return x >= rect.left - pad && x <= rect.right + pad && y >= rect.top - pad && y <= rect.bottom + pad
  }

  const resetDrag = () => {
    dragOriginRef.current = null
    setDragId(null)
    setDragOffset({ x: 0, y: 0 })
    setIsOverBag(false)
  }

  const startDrag = (event: ReactPointerEvent<HTMLButtonElement>, cardId: string) => {
    event.currentTarget.setPointerCapture(event.pointerId)
    dragOriginRef.current = { x: event.clientX, y: event.clientY }
    setDragId(cardId)
    setDragOffset({ x: 0, y: 0 })
    setIsOverBag(false)
  }

  const moveDrag = (event: ReactPointerEvent<HTMLButtonElement>) => {
    const origin = dragOriginRef.current
    if (!origin) return
    setDragOffset({ x: event.clientX - origin.x, y: event.clientY - origin.y })
    setIsOverBag(isOverBagAt(event.clientX, event.clientY))
  }

  const endDrag = (event: ReactPointerEvent<HTMLButtonElement>, questionId: 3 | 4, answer: string) => {
    const dropped = dragOriginRef.current !== null && isOverBagAt(event.clientX, event.clientY)
    resetDrag()
    if (dropped) commitCard(questionId, answer)
  }

  const renderChoiceCard = (
    questionId: 3 | 4,
    card: { id: string; answer: string },
    children: ReactNode,
  ) => (
    <button
      key={card.id}
      className={[styles.choiceCard, dragId === card.id ? styles.choiceCardDragging : ''].join(' ')}
      style={dragId === card.id ? { transform: `translate(${dragOffset.x}px, ${dragOffset.y}px)` } : undefined}
      aria-label={`${card.answer}. Drag it into the bag, or press Enter to choose it.`}
      onPointerDown={(event) => startDrag(event, card.id)}
      onPointerMove={moveDrag}
      onPointerUp={(event) => endDrag(event, questionId, card.answer)}
      onPointerCancel={resetDrag}
      onKeyDown={(event) => {
        if (event.key !== 'Enter' && event.key !== ' ') return
        event.preventDefault()
        commitCard(questionId, card.answer)
      }}
    >
      {children}
    </button>
  )

  const handleSpeechFallback = (field: 'name' | 'age') => {
    setManualInputField(field)
    setManualInputValue(field === 'name' ? name : age)
  }

  const completeSpeechInput = (field: 'name' | 'age', value: string) => {
    setManualInputField(null)
    setManualInputValue('')
    if (field === 'name') {
      setName(value)
      addAnswer(1, value)
    } else {
      setAge(value)
      addAnswer(2, value)
    }
    next()
  }

  const handleRepeatSpeech = () => {
    if (isListening) return
    const SpeechRecognition = window.SpeechRecognition ?? window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      addAnswer(5, "Let's go")
      next()
      return
    }

    const recognition = new SpeechRecognition()
    recognition.lang = 'en-US'
    recognition.interimResults = false
    recognition.maxAlternatives = 1
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript.trim()
      addAnswer(5, transcript || "Let's go")
      next()
    }
    recognition.onerror = (event) => {
      console.warn('Speech recognition error:', event.error)
      setIsListening(false)
      addAnswer(5, "Let's go")
      next()
    }
    recognition.onend = () => setIsListening(false)
    setIsListening(true)
    try {
      recognition.start()
    } catch {
      setIsListening(false)
      addAnswer(5, "Let's go")
      next()
    }
  }

  const handleSpeechInput = (field: 'name' | 'age') => {
    if (isListening) return
    setManualInputField(null)
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
    recognition.onerror = (event) => {
      console.warn('Speech recognition error:', event.error)
      setIsListening(false)
      handleSpeechFallback(field)
    }
    recognition.onend = () => setIsListening(false)
    setIsListening(true)
    try {
      recognition.start()
    } catch {
      setIsListening(false)
      handleSpeechFallback(field)
    }
  }

  const submitManualInput = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!manualInputField) return
    const trimmedValue = manualInputValue.trim()
    if (!trimmedValue) return
    completeSpeechInput(manualInputField, trimmedValue)
  }

  const submitOnboarding = async () => {
    if (isSubmitting) return
    setIsSubmitting(true)
    const pendingProfile = JSON.parse(window.localStorage.getItem('yeongcha:pending-profile') || 'null') as {
      profilePassword?: string
      profileColor?: string
    } | null
    const payload = answers.length
      ? answers
      : [
          { questionId: 1, answer: name || 'Friend' },
          { questionId: 2, answer: age || '7' },
          { questionId: 3, answer: 'Apple' },
        ]
    try {
      if (pendingProfile?.profilePassword) {
        const profile = await createProfile({
          nickname: name || 'New Friend',
          age: Number.parseInt(age, 10) || 7,
          profilePassword: pendingProfile.profilePassword,
        })
        if (pendingProfile.profileColor) {
          saveProfileColor(profile.profileId, pendingProfile.profileColor)
        }
        await loginProfile(profile.profileId, pendingProfile.profilePassword)
      }
      await postOnboarding(payload)
    } catch {
      // 인증이 붙기 전에도 온보딩 화면 흐름은 완료 처리합니다.
    } finally {
      window.localStorage.setItem('yeongcha:onboarding-completed', 'true')
      window.localStorage.setItem('yeongcha:placement-level', String(placementLevel))
      window.localStorage.setItem('yeongcha:home-tour-pending', 'true')
      window.localStorage.removeItem('yeongcha:pending-profile')
      navigate('/home')
    }
  }

  return (
    <main
      className={[
        styles.page,
        styles[`step${step}`],
        isOverBag ? styles.dropActive : '',
      ].join(' ')}
    >
      <div className={`${styles.sceneLayer} ${styles[`scene_${scene}`]}`} aria-hidden="true" />
      {leavingScene && (
        <div
          key={leavingScene}
          className={`${styles.sceneLayer} ${styles[`scene_${leavingScene}`]} ${styles.sceneLeaving}`}
          aria-hidden="true"
        />
      )}
      <div className={styles.progress} role="progressbar" aria-label="Onboarding progress"
        aria-valuemin={1} aria-valuemax={7} aria-valuenow={step + 1}>
        {[0, 1, 2, 3, 4, 5, 6].map((index) => (
          <span
            key={index}
            className={[
              styles.progressDot,
              index < step ? styles.progressDotDone : '',
              index === step ? styles.progressDotCurrent : '',
            ].join(' ')}
          />
        ))}
      </div>

      {(step === 2 || step === 3 || step === 4) && (
        <img
          ref={bagRef}
          src="/images/onboarding/adventure-bag.png"
          alt=""
          className={styles.bag}
        />
      )}

      {lionImage && <img key={lionImage} src={lionImage} alt="Popo" className={styles.lion} />}

      {step === 3 && (
        <div
          className={[styles.cardRow, dragId ? styles.cardRowDragging : ''].join(' ')}
          aria-label="Drag a fruit into the bag"
        >
          {fruitCards.map((card) =>
            renderChoiceCard(3, card, <img src={card.image} alt="" className={styles.choiceImage} />),
          )}
        </div>
      )}

      {step === 4 && (
        <div
          className={[styles.cardRow, dragId ? styles.cardRowDragging : ''].join(' ')}
          aria-label="Drag the weather card into the bag"
        >
          {weatherCards.map((card) =>
            renderChoiceCard(4, card, <span className={styles.choiceEmoji}>{card.emoji}</span>),
          )}
        </div>
      )}

      <section className={styles.bottomPanel}>
        <div className={styles.speechBox} lang="en">
          <span key={step} className={styles.speechText}>
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
          {step === 3 && (
            <>
              Which one is the “Apple”?
              <br />
              Drag it into the bag!
            </>
          )}
          {step === 4 && (
            <>
              Good job!
              <br />
              Which one is “It is raining”?
              <br />
              Drag it into the bag!
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
              Your story is ready for {name || 'you'}.
              <br />
              Let’s start your story!
            </>
          )}
          </span>
        </div>

        {step <= 1 && (
          manualInputField ? (
            <form className={styles.manualInputForm} onSubmit={submitManualInput}>
              <input
                className={styles.manualInput}
                inputMode={manualInputField === 'age' ? 'numeric' : 'text'}
                maxLength={manualInputField === 'age' ? 2 : 24}
                onChange={(event) => setManualInputValue(event.target.value)}
                placeholder={manualInputField === 'name' ? 'Type your name' : 'Type your age'}
                value={manualInputValue}
              />
              <button className={styles.confirmButton} type="submit" disabled={!manualInputValue.trim()}>
                OK
              </button>
            </form>
          ) : (
            <button
              className={styles.primaryButton}
              onClick={() => handleSpeechInput(step === 0 ? 'name' : 'age')}
              disabled={isListening}
            >
              <img src="/images/voice-record.png" alt="" className={styles.micIcon} />
              <span aria-live="polite">{isListening ? 'Listening...' : 'Tap to speak'}</span>
            </button>
          )
        )}

        {step === 2 && (
          <button className={styles.primaryButton} onClick={next}>
            Next
          </button>
        )}

        {step === 3 && (
          <button
            className={styles.primaryButton}
            onClick={() => {
              addAnswer(3, 'Apple')
              setStep(4)
            }}
            aria-label="Next"
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
            aria-label="Next"
          >
            →
          </button>
        )}

        {step === 5 && (
          <button
            className={styles.primaryButton}
            onClick={handleRepeatSpeech}
            disabled={isListening}
          >
            <img src="/images/voice-record.png" alt="" className={styles.micIcon} />
            <span aria-live="polite">{isListening ? 'Listening...' : 'Tap to speak'}</span>
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
