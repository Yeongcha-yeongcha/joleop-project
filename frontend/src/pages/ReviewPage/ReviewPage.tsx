import { useEffect, useMemo, useState } from 'react'
import { useLocation } from 'react-router-dom'
import {
  fetchDueReviews,
  fetchUserStats,
  fetchStoryTalk,
  sendReviewRoleplayMessage,
  synthesizeSpeech,
  submitReviewAttempt,
  usesBackendApi,
  type ReviewCardData,
  type ReviewMode,
} from '../../services/api'
import RoleplayScreen from '../../components/RoleplayScreen/RoleplayScreen'
import type { RoleplayHistoryTurn, RoleplayMission } from '../../types'
import type { ChapterResult } from '../../utils/chapterProgress'
import styles from './ReviewPage.module.css'

type ReviewKind = 'word' | 'sentenceOrder' | 'sentenceRepeat' | 'chat'

interface ReviewItem {
  id: string
  cardId?: number
  kind: ReviewKind
  bookTitle: string
  chapterNumber: number
  prompt: string
  sentence: string
  answer: string
  options: string[]
  memory: number
  roleplay?: RoleplayMission
}

const modeCards: Array<{ mode: ReviewMode; title: string; description: string }> = [
  { mode: 'WORD_PLAYGROUND', title: 'Word Playground', description: 'See a word, then find it in the choices.' },
  { mode: 'SENTENCE_QUEST', title: 'Sentence Quest', description: 'Build 3 sentences, then say 2 sentences.' },
  { mode: 'STORY_TALK', title: 'Story Talk', description: 'Replay finished roleplays at the right time.' },
]

const modeIcons: Record<ReviewMode, string> = {
  SMART_MIX: '▶',
  WORD_PLAYGROUND: 'ABC',
  SENTENCE_QUEST: '☰',
  STORY_TALK: '🎭',
}

const MAX_ORDER_WORDS = 6
const MIN_ORDER_WORDS = 3

const smartFlowCards = [
  { label: 'Word', icon: 'A', tone: 'word' },
  { label: 'Sentence', icon: '', tone: 'sentence' },
  { label: 'Word', icon: 'B', tone: 'word' },
  { label: 'Sentence', icon: '', tone: 'sentence' },
  { label: 'Roleplay', icon: '🎭', tone: 'chat' },
]

function activeProfileKey() {
  try {
    const profile = JSON.parse(window.localStorage.getItem('yeongcha:active-profile') || 'null') as {
      profileId?: number | string
    } | null
    return String(profile?.profileId ?? 'guest')
  } catch {
    return 'guest'
  }
}

function reviewAttendanceKey() {
  return `yeongcha:review-attendance:${activeProfileKey()}`
}

function localDateIso(date = new Date()) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function readReviewAttendanceDates() {
  try {
    return JSON.parse(window.localStorage.getItem(reviewAttendanceKey()) || '[]') as string[]
  } catch {
    return []
  }
}

function saveReviewAttendanceDate(date = localDateIso()) {
  const dates = Array.from(new Set([...readReviewAttendanceDates(), date]))
  window.localStorage.setItem(reviewAttendanceKey(), JSON.stringify(dates))
  return dates
}

function buildWeekDays(attendanceDates: string[] = []) {
  const today = new Date()
  const todayIso = localDateIso(today)
  const mondayOffset = (today.getDay() + 6) % 7
  const monday = new Date(today)
  monday.setDate(today.getDate() - mondayOffset)
  const attended = new Set(attendanceDates)

  return ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((label, index) => {
    const day = new Date(monday)
    day.setDate(monday.getDate() + index)
    const iso = localDateIso(day)
    return {
      label,
      state: attended.has(iso) ? 'done' : iso === todayIso ? 'today' : 'next',
    }
  })
}

function starsForScore(score: number) {
  if (score >= 90) return 3
  if (score >= 70) return 2
  if (score >= 45) return 1
  return 0
}

function shuffle<T>(items: T[]): T[] {
  return [...items].sort((a, b) => {
    const left = String(a)
    const right = String(b)
    return left.length === right.length ? left.localeCompare(right) : left.length - right.length
  })
}

function normalizeBuiltAnswer(value: string) {
  return value.replace(/\s+/g, '').toLowerCase()
}

function normalizeSpokenSentence(value: string) {
  return value.replace(/[.,!?;:'"]/g, '').replace(/\s+/g, ' ').trim().toLowerCase()
}

function wordUseCount(words: string[], target: string) {
  return words.filter((word) => word === target).length
}

function recognizeSentence(): Promise<string> {
  return new Promise((resolve, reject) => {
    const Recognition = window.SpeechRecognition ?? window.webkitSpeechRecognition
    if (!Recognition) {
      reject(new Error('Speech recognition is not available.'))
      return
    }
    const recognition = new Recognition()
    let transcript = ''
    let settled = false
    const timer = window.setTimeout(() => {
      if (settled) return
      settled = true
      recognition.stop()
      resolve(transcript.trim())
    }, 5500)

    recognition.lang = 'en-US'
    recognition.interimResults = true
    recognition.continuous = false
    recognition.onresult = (event) => {
      transcript = ''
      for (let index = 0; index < event.results.length; index += 1) {
        transcript = `${transcript} ${event.results[index][0]?.transcript ?? ''}`.trim()
      }
      if (event.results[event.results.length - 1]?.isFinal && !settled) {
        settled = true
        window.clearTimeout(timer)
        recognition.stop()
        resolve(transcript.trim())
      }
    }
    recognition.onerror = () => {
      if (settled) return
      settled = true
      window.clearTimeout(timer)
      reject(new Error('Speech recognition failed.'))
    }
    recognition.onend = () => {
      if (settled) return
      settled = true
      window.clearTimeout(timer)
      resolve(transcript.trim())
    }
    recognition.start()
  })
}

function cleanSentenceWords(sentence: string) {
  return sentence
    .replace(/[“”]/g, '"')
    .split(/\s+/)
    .map((word) => word.replace(/[.,!?;:'"]/g, ''))
    .filter(Boolean)
}

function cardKind(card: ReviewCardData, index: number): ReviewKind {
  if (card.cardType === 'CHAT') return 'chat'
  if (card.cardType === 'SENTENCE') return index % 5 >= 3 ? 'sentenceRepeat' : 'sentenceOrder'
  return 'word'
}

function uniqueWords(cards: ReviewCardData[]) {
  return cards
    .map((item) => item.keyword.trim())
    .filter((word) => word && !word.startsWith('roleplay:'))
    .filter((word, index, words) => words.findIndex((candidate) => candidate.toLowerCase() === word.toLowerCase()) === index)
}

function wordOptions(card: ReviewCardData, cards: ReviewCardData[]) {
  const answer = card.keyword.trim()
  const distractors = uniqueWords(cards).filter((word) => word.toLowerCase() !== answer.toLowerCase()).slice(0, 3)
  return shuffle([answer, ...distractors]).slice(0, Math.max(1, Math.min(4, 1 + distractors.length)))
}

function sentenceForOrder(card: ReviewCardData) {
  const sentence = (card.sourceSentence || card.clozeSentence).trim()
  const words = cleanSentenceWords(sentence)
  if (words.length >= MIN_ORDER_WORDS && words.length <= MAX_ORDER_WORDS) {
    return words.join(' ')
  }
  const keywordIndex = words.findIndex((word) => word.toLowerCase() === card.keyword.toLowerCase())
  const start = keywordIndex >= 0
    ? Math.max(0, Math.min(keywordIndex - 2, words.length - MAX_ORDER_WORDS))
    : 0
  return words.slice(start, start + MAX_ORDER_WORDS).join(' ')
}

function roleplayCardToMission(card: ReviewCardData): RoleplayMission | undefined {
  if (!card.roleplay) return undefined
  const requiredTurns = Math.max(3, card.roleplay.requiredTurns || 3)
  return {
    thumbnailColor: '#C4D4B8',
    thumbnailUrl: card.roleplay.imageUrl ?? undefined,
    mission: card.roleplay.playerGoal || card.roleplay.description,
    missionSummary: card.roleplay.description,
    turns: Array.from({ length: requiredTurns }, (_, index) => ({
      npc: index === 0
        ? card.roleplay?.openingMessage ?? 'Hi! What should we do?'
        : card.roleplay?.hints?.[index - 1] ?? 'What else can you say?',
      user: '',
    })),
    history: [],
    finalNpc: 'Great job!',
  }
}

function cardToReviewItem(card: ReviewCardData, cards: ReviewCardData[], index: number): ReviewItem {
  const kind = cardKind(card, index)
  if (kind === 'sentenceOrder' || kind === 'sentenceRepeat') {
    const sentence = sentenceForOrder(card)
    return {
      id: `review-${card.cardId}`,
      cardId: card.cardId,
      kind,
      bookTitle: card.bookTitle || 'Story',
      chapterNumber: card.chapterNumber,
      prompt: kind === 'sentenceRepeat' ? 'Say the sentence.' : 'Build the sentence.',
      sentence,
      answer: sentence,
      options: kind === 'sentenceRepeat' ? [] : shuffle(cleanSentenceWords(sentence)),
      memory: card.memoryScore,
    }
  }
  return {
    id: `review-${card.cardId}`,
    cardId: card.cardId,
    kind,
    bookTitle: card.bookTitle || 'Story',
    chapterNumber: card.chapterNumber,
    prompt: kind === 'chat' ? 'Replay the roleplay.' : 'Find the word.',
    sentence: kind === 'chat' ? card.sourceSentence : card.keyword,
    answer: card.keyword,
    options: kind === 'chat' ? [] : wordOptions(card, cards),
    memory: card.memoryScore,
    roleplay: roleplayCardToMission(card),
  }
}

export default function ReviewPage() {
  const location = useLocation()
  const [started, setStarted] = useState(false)
  const [index, setIndex] = useState(0)
  const [results, setResults] = useState<Record<string, boolean>>({})
  const [selected, setSelected] = useState('')
  const [builtWords, setBuiltWords] = useState<string[]>([])
  const [feedback, setFeedback] = useState<'correct' | 'wrong' | ''>('')
  const [showHelp, setShowHelp] = useState(false)
  const [reviewQueue, setReviewQueue] = useState<ReviewItem[]>([])
  const [selectedMode, setSelectedMode] = useState<ReviewMode>('SMART_MIX')
  const [reviewRoleplayHistory, setReviewRoleplayHistory] = useState<RoleplayHistoryTurn[]>([])
  const [attendanceDates, setAttendanceDates] = useState<string[]>([])
  const [isListening, setIsListening] = useState(false)
  const [spokenTranscript, setSpokenTranscript] = useState('')

  const current = reviewQueue[index]
  const doneCount = Object.keys(results).length
  const isFinished = started && reviewQueue.length > 0 && doneCount >= reviewQueue.length
  const resultScore = useMemo(() => {
    const values = Object.values(results)
    if (!values.length) return 0
    return Math.round((values.filter(Boolean).length / values.length) * 100)
  }, [results])
  const weekDays = useMemo(() => buildWeekDays(attendanceDates), [attendanceDates])

  useEffect(() => {
    setStarted(false)
    setIndex(0)
    setResults({})
    setSelected('')
    setBuiltWords([])
    setFeedback('')
    setIsListening(false)
    setSpokenTranscript('')
    setSelectedMode('SMART_MIX')
    setReviewRoleplayHistory([])
    fetchUserStats()
      .then((stats) => {
        setAttendanceDates(Array.from(new Set([...(stats.attendanceDates ?? []), ...readReviewAttendanceDates()])))
      })
      .catch(() => setAttendanceDates(readReviewAttendanceDates()))
    if (!usesBackendApi()) return
    fetchDueReviews(5, 'SMART_MIX')
      .then((data) => {
        setReviewQueue(data.cards.map((card, cardIndex, cards) => cardToReviewItem(card, cards, cardIndex)))
      })
      .catch(() => undefined)
  }, [location.key])

  useEffect(() => {
    if (!isFinished) return
    const savedDates = saveReviewAttendanceDate()
    setAttendanceDates((currentDates) => Array.from(new Set([...currentDates, ...savedDates])))
  }, [isFinished])

  const loadMode = async (mode: ReviewMode) => {
    setSelectedMode(mode)
    setIndex(0)
    setResults({})
    setSelected('')
    setBuiltWords([])
    setFeedback('')
    setIsListening(false)
    setSpokenTranscript('')
    setReviewRoleplayHistory([])
    if (mode === 'STORY_TALK') {
      const data = await fetchStoryTalk(5)
      setReviewQueue(data.cards.map((card, cardIndex, cards) => cardToReviewItem(card, cards, cardIndex)))
      setStarted(true)
      return
    }
    const data = await fetchDueReviews(5, mode)
    setReviewQueue(data.cards.map((card, cardIndex, cards) => cardToReviewItem(card, cards, cardIndex)))
    setStarted(true)
  }

  const beginMode = (mode: ReviewMode) => {
    setSelectedMode(mode)
    setIndex(0)
    setResults({})
    setSelected('')
    setBuiltWords([])
    setFeedback('')
    setIsListening(false)
    setSpokenTranscript('')
    setReviewRoleplayHistory([])
    if (!usesBackendApi()) return
    void loadMode(mode).catch(() => {
      setReviewQueue([])
      setStarted(true)
    })
  }

  const moveNext = (isCorrect: boolean) => {
    if (!current) return
    setResults((prev) => ({ ...prev, [current.id]: isCorrect }))
    if (current.cardId && usesBackendApi()) {
      void submitReviewAttempt(current.cardId, isCorrect ? 'GOOD' : 'AGAIN', isCorrect, isCorrect ? 100 : 40)
    }
    setFeedback(isCorrect ? 'correct' : 'wrong')
    window.setTimeout(() => {
      setIndex((value) => Math.min(value + 1, reviewQueue.length - 1))
      setSelected('')
      setBuiltWords([])
      setFeedback('')
      setIsListening(false)
      setSpokenTranscript('')
    }, 620)
  }

  const chooseOption = (option: string) => {
    if (!current) return
    if (feedback) return
    setSelected(option)
    moveNext(option === current.answer)
  }

  const addWord = (word: string) => {
    if (!current) return
    if (feedback) return
    const next = [...builtWords, word]
    setBuiltWords(next)
    if (next.length === current.options.length) {
      moveNext(normalizeBuiltAnswer(next.join(' ')) === normalizeBuiltAnswer(current.answer))
    }
  }

  const removeBuiltWord = (wordIndex: number) => {
    if (feedback) return
    setBuiltWords((words) => words.filter((_, index) => index !== wordIndex))
  }

  const restart = () => {
    setStarted(false)
    setIndex(0)
    setResults({})
    setSelected('')
    setBuiltWords([])
    setFeedback('')
    setIsListening(false)
    setSpokenTranscript('')
    setReviewRoleplayHistory([])
  }

  const handleSentenceRepeat = async () => {
    if (!current || feedback || isListening) return
    setIsListening(true)
    setSpokenTranscript('')
    try {
      const transcript = await recognizeSentence()
      setSpokenTranscript(transcript)
      const expected = normalizeSpokenSentence(current.answer)
      const spoken = normalizeSpokenSentence(transcript)
      moveNext(Boolean(spoken) && spoken === expected)
    } catch {
      setSpokenTranscript('')
      moveNext(false)
    } finally {
      setIsListening(false)
    }
  }

  const speakReviewText = async (text: string) => {
    const trimmed = text.trim()
    if (!trimmed) return
    if ('speechSynthesis' in window) window.speechSynthesis.cancel()
    if (usesBackendApi()) {
      try {
        const audio = await synthesizeSpeech(trimmed, 'normal')
        const audioUrl = URL.createObjectURL(audio)
        const player = new Audio(audioUrl)
        player.onended = () => URL.revokeObjectURL(audioUrl)
        player.onerror = () => URL.revokeObjectURL(audioUrl)
        await player.play()
        return
      } catch (error) {
        console.warn('Review TTS failed. Falling back to browser speech.', error)
      }
    }
    if (!('speechSynthesis' in window)) return
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = 'en-US'
    utterance.rate = 0.9
    utterance.pitch = 1.25
    window.speechSynthesis.speak(utterance)
  }

  const recordReviewRoleplay = async (audio: Blob, transcript?: string) => {
    if (!current?.cardId) throw new Error('Missing review roleplay card.')
    const result = await sendReviewRoleplayMessage(current.cardId, audio, transcript, reviewRoleplayHistory)
    setReviewRoleplayHistory((prev) => [...prev, {
      user: result.userTranscript,
      npc: result.characterText,
    }])
    return result
  }

  const completeReviewRoleplay = async (): Promise<ChapterResult | null> => {
    if (!current?.cardId) return null
    await submitReviewAttempt(current.cardId, 'GOOD', true, 100)
    setResults((prev) => ({ ...prev, [current.id]: true }))
    return {
      bookId: String(current.bookTitle || current.cardId),
      chapterNumber: current.chapterNumber,
      message: 'Review Done!',
      stars: 3,
      totalScore: 100,
      completedAt: new Date().toISOString(),
      breakdown: {
        repeat: null,
        description: null,
        roleplay: 100,
      },
    }
  }

  const exitReviewRoleplay = () => {
    setReviewRoleplayHistory([])
    if (index < reviewQueue.length - 1) {
      setIndex((value) => value + 1)
      return
    }
    restart()
  }

  if (isFinished) {
    const stars = starsForScore(resultScore)
    return (
      <main className={styles.page}>
        <section className={styles.result}>
          <span>Review Done</span>
          <h1>{resultScore >= 80 ? 'Excellent!' : resultScore >= 60 ? 'Nice Work!' : 'Try Again!'}</h1>
          <div className={styles.stars} aria-label={`${stars} stars`}>
            {[0, 1, 2].map((starIndex) => (
              <b key={starIndex} className={starIndex < stars ? styles.starOn : styles.starOff}>★</b>
            ))}
          </div>
          <p>{resultScore}% remembered. Next cards will follow your memory.</p>
          <button onClick={restart}>Back to Review</button>
        </section>
      </main>
    )
  }

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <img src="/images/onboarding/lion-headphones.png" alt="" />
        <div>
          <h1>Review</h1>
          <p>Small practice makes big memory.</p>
        </div>
        <button className={styles.helpButton} onClick={() => setShowHelp(true)} aria-label="Review help">
          ?
        </button>
      </header>

      {!started ? (
        <>
          {showHelp && (
            <div className={styles.helpOverlay} role="dialog" aria-modal="true" aria-label="Review help">
              <section className={styles.helpPanel}>
                <button onClick={() => setShowHelp(false)} aria-label="Close help">x</button>
                <h2>How Review Works</h2>
                <div className={styles.memoryPath} aria-label="Memory schedule">
                  <span>Learn</span>
                  <i />
                  <span>Review</span>
                  <i />
                  <span>Grow</span>
                </div>
                <div className={styles.memoryCurve}>
                  <b>memory</b>
                  <i />
                  <strong>Review pops up before words fade.</strong>
                </div>
                <div className={styles.helpModes}>
                  <article>
                    <b>A</b>
                    <strong>Word Playground</strong>
                    <p>A word appears first. Find the same word among saved DB words.</p>
                  </article>
                  <article>
                    <b>□</b>
                    <strong>Sentence Quest</strong>
                    <p>First build 3 short sentences. Then say 2 sentences out loud.</p>
                  </article>
                  <article>
                    <b>🎭</b>
                    <strong>Story Talk</strong>
                    <p>Replay a finished roleplay when memory needs a boost.</p>
                  </article>
                </div>
                <p className={styles.helpNote}>Hard cards visit sooner. Easy cards sleep longer.</p>
              </section>
            </div>
          )}

          <section className={styles.weekCard} aria-label="This week">
            <h2>This Week</h2>
            <div>
              {weekDays.map((day) => (
                <article key={day.label} className={styles[`day_${day.state}`]}>
                  <span>{day.state === 'done' ? '✓' : ''}</span>
                  <b>{day.label}</b>
                </article>
              ))}
            </div>
          </section>

          <section className={styles.smartHero}>
            <span className={styles.heroBadge}>Today&apos;s Review</span>
            <div className={styles.smartTop}>
              <img src="/images/onboarding/lion-headphones.png" alt="" />
              <div>
                <h2>Start Smart Mix</h2>
                <p>5 mixed review cards from saved words, sentences, and finished roleplays.</p>
              </div>
            </div>

            <div className={styles.smartFlow} aria-label="Smart Mix cards">
              {smartFlowCards.map((item, itemIndex) => (
                <div className={styles.flowStep} key={`${item.label}-${itemIndex}`}>
                  <b className={styles[`flowIcon_${item.tone}`]}>{item.icon}</b>
                  <span className={styles.flowLabel}>{item.label}</span>
                  {itemIndex < smartFlowCards.length - 1 && <i aria-hidden="true">›</i>}
                </div>
              ))}
            </div>

            <button className={styles.smartButton} onClick={() => beginMode('SMART_MIX')}>
              Start Smart Mix
            </button>
            {!usesBackendApi() && <p className={styles.emptyHint}>Connect the backend to load saved review cards.</p>}
          </section>

          <section className={styles.modeArea} aria-label="Practice modes">
            <h2>More ways to review</h2>
            <div className={styles.modeGrid}>
              {modeCards.map((modeCard) => (
                <button key={modeCard.mode} onClick={() => beginMode(modeCard.mode)}>
                  <b className={styles[`modeIcon_${modeCard.mode.toLowerCase()}`]}>{modeIcons[modeCard.mode]}</b>
                  <strong>{modeCard.title}</strong>
                  <span>{modeCard.description}</span>
                </button>
              ))}
            </div>
          </section>
        </>
      ) : !current ? (
        <section className={styles.emptyReview}>
          <span>All Clear</span>
          <h2>{selectedMode === 'STORY_TALK' ? 'No roleplays ready.' : 'No review cards ready.'}</h2>
          <p>
            {selectedMode === 'STORY_TALK'
              ? 'Finish a main roleplay first. Then it will return here on the memory schedule.'
              : 'Finish a chapter first. Then words and sentences from the review DB will appear here at the right time.'}
          </p>
          <button onClick={restart}>Back to Review</button>
        </section>
      ) : current.roleplay ? (
        <section className={styles.reviewRoleplayShell}>
          <RoleplayScreen
            roleplay={{ ...current.roleplay, history: reviewRoleplayHistory }}
            onProgressChange={() => undefined}
            onFinish={completeReviewRoleplay}
            onExit={exitReviewRoleplay}
            onSpeakText={speakReviewText}
            onRecord={recordReviewRoleplay}
          />
        </section>
      ) : selectedMode === 'WORD_PLAYGROUND' ? (
        <section className={`${styles.playMode} ${styles.wordMode} ${feedback ? styles[feedback] : ''}`}>
          <div className={styles.modeHeader}>
            <button onClick={restart} aria-label="Back to review">‹</button>
            <div>
              <span>Word Playground</span>
              <h2>{current.prompt}</h2>
            </div>
            <b>{index + 1}/{reviewQueue.length}</b>
          </div>

          <article className={styles.wordStage}>
            <small>{current.bookTitle} · Chapter {current.chapterNumber}</small>
            <span className={styles.wordCueLabel}>Find this word</span>
            <p><strong>{current.answer}</strong></p>
          </article>

          <div className={styles.wordTokenGrid}>
            {current.options.map((option) => (
              <button key={option} className={selected === option ? styles.picked : ''} onClick={() => chooseOption(option)}>
                {option}
              </button>
            ))}
          </div>

          {feedback && <div className={styles.feedback}>{feedback === 'correct' ? 'Great!' : `Oops! ${current.answer}`}</div>}
        </section>
      ) : selectedMode === 'SENTENCE_QUEST' ? (
        <section className={`${styles.playMode} ${styles.sentenceMode} ${feedback ? styles[feedback] : ''}`}>
          <div className={styles.modeHeader}>
            <button onClick={restart} aria-label="Back to review">‹</button>
            <div>
              <span>Sentence Quest</span>
              <h2>{current.prompt}</h2>
            </div>
            <b>{index + 1}/{reviewQueue.length}</b>
          </div>

          <article className={styles.sentenceStage}>
            <small>{current.bookTitle} · Chapter {current.chapterNumber}</small>
            <p>{current.sentence}</p>
          </article>

          {current.kind === 'sentenceRepeat' ? (
            <div className={styles.repeatPanel}>
              <button disabled={isListening || Boolean(feedback)} onClick={handleSentenceRepeat}>
                {isListening ? 'Listening...' : 'Tap and say it'}
              </button>
              <span>{spokenTranscript || 'Your voice will appear here.'}</span>
            </div>
          ) : (
            <>
              <div className={styles.sentenceTray}>
                {builtWords.length ? builtWords.map((word, wordIndex) => (
                  <button
                    key={`${word}-${wordIndex}`}
                    type="button"
                    onClick={() => removeBuiltWord(wordIndex)}
                    aria-label={`Remove ${word}`}
                  >
                    {word}
                  </button>
                )) : <em>Build the sentence</em>}
              </div>
              <div className={styles.sentenceTiles}>
                {current.options.map((word, optionIndex) => {
                  const sameWordBefore = current.options.slice(0, optionIndex + 1).filter((option) => option === word).length
                  const isUsed = wordUseCount(builtWords, word) >= sameWordBefore
                  return (
                  <button key={`${word}-${optionIndex}`} disabled={isUsed} onClick={() => addWord(word)}>
                    {word}
                  </button>
                  )
                })}
              </div>
            </>
          )}

          {feedback && <div className={styles.feedback}>{feedback === 'correct' ? 'Great!' : `Oops! ${current.answer}`}</div>}
        </section>
      ) : selectedMode === 'STORY_TALK' ? (
        <section className={styles.emptyReview}>
          <span>Story Talk</span>
          <h2>No roleplay review ready.</h2>
          <p>Completed roleplays will appear here when the memory schedule says it is time to practice again.</p>
          <button onClick={restart}>Back to Review</button>
        </section>
      ) : (
        <section className={`${styles.quiz} ${feedback ? styles[feedback] : ''}`}>
          <div className={styles.progressRow}>
            <span>{index + 1} / {reviewQueue.length}</span>
            <b><i style={{ width: `${((index + 1) / reviewQueue.length) * 100}%` }} /></b>
          </div>

          <article className={styles.quizCard}>
            <span>{current.prompt}</span>
            <small>{current.bookTitle} · Chapter {current.chapterNumber}</small>
            <p>{current.sentence}</p>
          </article>

          {current.kind === 'word' && (
            <div className={styles.choiceGrid}>
              {current.options.map((option) => (
                <button
                  key={option}
                  className={selected === option ? styles.picked : ''}
                  onClick={() => chooseOption(option)}
                >
                  {option}
                </button>
              ))}
            </div>
          )}

          {current.kind === 'sentenceOrder' && (
            <>
              <div className={styles.buildTray}>
                {builtWords.length ? builtWords.map((word, wordIndex) => (
                  <button
                    key={`${word}-${wordIndex}`}
                    type="button"
                    onClick={() => removeBuiltWord(wordIndex)}
                    aria-label={`Remove ${word}`}
                  >
                    {word}
                  </button>
                )) : <em>Tap words in order</em>}
              </div>
              <div className={styles.wordCloud}>
                {current.options.map((word, optionIndex) => {
                  const sameWordBefore = current.options.slice(0, optionIndex + 1).filter((option) => option === word).length
                  const isUsed = wordUseCount(builtWords, word) >= sameWordBefore
                  return (
                  <button
                    key={`${word}-${optionIndex}`}
                    disabled={isUsed}
                    onClick={() => addWord(word)}
                  >
                    {word}
                  </button>
                  )
                })}
              </div>
            </>
          )}

          {current.kind === 'sentenceRepeat' && (
            <div className={styles.repeatPanel}>
              <button disabled={isListening || Boolean(feedback)} onClick={handleSentenceRepeat}>
                {isListening ? 'Listening...' : 'Tap and say it'}
              </button>
              <span>{spokenTranscript || 'Your voice will appear here.'}</span>
            </div>
          )}

          {feedback && (
            <div className={styles.feedback}>
              {feedback === 'correct' ? 'Great!' : `Oops! ${current.answer}`}
            </div>
          )}
        </section>
      )}
    </main>
  )
}
