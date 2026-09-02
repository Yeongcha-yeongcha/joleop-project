import { useEffect, useMemo, useState } from 'react'
import {
  fetchDueReviews,
  fetchStoryTalk,
  sendStoryTalkMessage,
  submitReviewAttempt,
  usesBackendApi,
  type ReviewCardData,
  type ReviewMode,
  type StoryTalkData,
} from '../../services/api'
import styles from './ReviewPage.module.css'

type ReviewKind = 'pick' | 'keyword' | 'match' | 'order' | 'picture' | 'chat'

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
  pairs?: Array<{ left: string; right: string }>
}

const fallbackReviewQueue: ReviewItem[] = [
  {
    id: 'chirping-pick',
    kind: 'pick',
    bookTitle: 'Popo Meadow Story',
    chapterNumber: 1,
    prompt: 'Pick the missing word.',
    sentence: 'They heard a faint ____ sound coming from a nearby bush.',
    answer: 'chirping',
    options: ['chirping', 'jumping', 'sleeping', 'painting'],
    memory: 42,
  },
  {
    id: 'bird-picture',
    kind: 'picture',
    bookTitle: 'Popo Meadow Story',
    chapterNumber: 1,
    prompt: 'Which card matches the story?',
    sentence: 'They saw a tiny bird trapped inside.',
    answer: 'tiny bird',
    options: ['tiny bird', 'big moon', 'red cake', 'blue boat'],
    memory: 51,
  },
  {
    id: 'kind-match',
    kind: 'match',
    bookTitle: 'Popo Meadow Story',
    chapterNumber: 2,
    prompt: 'Connect each word to its friend.',
    sentence: 'Match the story words.',
    answer: 'all',
    options: [],
    memory: 36,
    pairs: [
      { left: 'bird', right: 'wings' },
      { left: 'bush', right: 'leaves' },
      { left: 'song', right: 'music' },
    ],
  },
  {
    id: 'team-order',
    kind: 'order',
    bookTitle: 'Popo Meadow Story',
    chapterNumber: 3,
    prompt: 'Build the sentence.',
    sentence: 'We make a great team',
    answer: 'We make a great team',
    options: ['team', 'We', 'great', 'make', 'a'],
    memory: 64,
  },
  {
    id: 'thinking-keyword',
    kind: 'keyword',
    bookTitle: 'Popo Meadow Story',
    chapterNumber: 4,
    prompt: 'Tap the important word.',
    sentence: 'Toto used quick thinking to help Popo.',
    answer: 'thinking',
    options: ['Toto', 'used', 'quick', 'thinking', 'help', 'Popo'],
    memory: 58,
  },
]

const icons: Record<string, string> = {
  'tiny bird': '🐤',
  'big moon': '🌕',
  'red cake': '🍰',
  'blue boat': '⛵',
  bush: '🌿',
  song: '🎵',
  friend: '🤝',
  meadow: '🌻',
  help: '👐',
  team: '⭐',
}

const wordPlaygroundQueue: ReviewItem[] = [
  {
    id: 'word-spell-bird',
    kind: 'order',
    bookTitle: 'Popo Meadow Story',
    chapterNumber: 1,
    prompt: 'Spell the story word.',
    sentence: 'A tiny bird was in the bush.',
    answer: 'bird',
    options: ['r', 'b', 'd', 'i'],
    memory: 42,
  },
  {
    id: 'word-picture-bush',
    kind: 'picture',
    bookTitle: 'Popo Meadow Story',
    chapterNumber: 1,
    prompt: 'Pick the picture word.',
    sentence: 'They walked toward the bush.',
    answer: 'bush',
    options: ['bush', 'song', 'friend', 'team'],
    memory: 46,
  },
  {
    id: 'word-match-story',
    kind: 'match',
    bookTitle: 'Popo Meadow Story',
    chapterNumber: 2,
    prompt: 'Connect each word to its clue.',
    sentence: 'Match the story words.',
    answer: 'all',
    options: [],
    memory: 38,
    pairs: [
      { left: 'bird', right: 'small animal with wings' },
      { left: 'bush', right: 'green leaves' },
      { left: 'song', right: 'sweet sound' },
    ],
  },
  {
    id: 'word-tap-help',
    kind: 'keyword',
    bookTitle: 'Popo Meadow Story',
    chapterNumber: 2,
    prompt: 'Tap the important word.',
    sentence: 'Popo gently helped the tiny bird.',
    answer: 'helped',
    options: ['Popo', 'gently', 'helped', 'tiny', 'bird'],
    memory: 55,
  },
  {
    id: 'word-pick-team',
    kind: 'pick',
    bookTitle: 'Popo Meadow Story',
    chapterNumber: 3,
    prompt: 'Pick the missing word.',
    sentence: 'We make a great ____.',
    answer: 'team',
    options: ['team', 'moon', 'cake', 'boat'],
    memory: 61,
  },
]

const sentenceQuestQueue: ReviewItem[] = [
  {
    id: 'sentence-pick-chirping',
    kind: 'pick',
    bookTitle: 'Popo Meadow Story',
    chapterNumber: 1,
    prompt: 'Pick the missing word.',
    sentence: 'They heard a faint ____ sound.',
    answer: 'chirping',
    options: ['chirping', 'sleeping', 'painting', 'jumping'],
    memory: 43,
  },
  {
    id: 'sentence-order-friends',
    kind: 'order',
    bookTitle: 'Popo Meadow Story',
    chapterNumber: 1,
    prompt: 'Put the words in order.',
    sentence: 'They all walked together',
    answer: 'They all walked together',
    options: ['walked', 'together', 'They', 'all'],
    memory: 50,
  },
  {
    id: 'sentence-pick-careful',
    kind: 'pick',
    bookTitle: 'Popo Meadow Story',
    chapterNumber: 2,
    prompt: 'Pick the missing word.',
    sentence: 'Popo was ____ with the little bird.',
    answer: 'careful',
    options: ['careful', 'angry', 'sleepy', 'noisy'],
    memory: 57,
  },
  {
    id: 'sentence-order-help',
    kind: 'order',
    bookTitle: 'Popo Meadow Story',
    chapterNumber: 3,
    prompt: 'Build the sentence.',
    sentence: 'I can help you',
    answer: 'I can help you',
    options: ['help', 'I', 'you', 'can'],
    memory: 62,
  },
  {
    id: 'sentence-keyword-kind',
    kind: 'keyword',
    bookTitle: 'Popo Meadow Story',
    chapterNumber: 4,
    prompt: 'Tap the kind action.',
    sentence: 'The friends cheered and hugged each other.',
    answer: 'hugged',
    options: ['friends', 'cheered', 'hugged', 'other'],
    memory: 66,
  },
]

const storyTalkQueue: ReviewItem[] = [
  {
    id: 'story-talk-bird',
    kind: 'chat',
    bookTitle: 'Popo Meadow Story',
    chapterNumber: 1,
    prompt: 'Talk about the story.',
    sentence: 'Popo and friends found a tiny bird.',
    answer: 'bird',
    options: [],
    memory: 48,
  },
]

const fallbackStoryTalk: StoryTalkData = {
  mode: 'STORY_TALK',
  topic: {
    title: 'Story Talk',
    opening: 'Popo found a tiny bird. What would you say to help?',
    targetWords: ['bird', 'help', 'bush', 'friend'],
    starterQuestions: [
      'I can help you!',
      'Where is the bird?',
      'Let us be careful.',
    ],
  },
  cards: [],
}

const modeCards: Array<{ mode: ReviewMode; title: string; description: string }> = [
  { mode: 'WORD_PLAYGROUND', title: 'Word Playground', description: 'Spelling, match, find' },
  { mode: 'SENTENCE_QUEST', title: 'Sentence Quest', description: 'Fill in blanks, order' },
  { mode: 'STORY_TALK', title: 'Story Talk', description: 'Short AI chat' },
]

const modeIcons: Record<ReviewMode, string> = {
  SMART_MIX: '▶',
  WORD_PLAYGROUND: 'ABC',
  SENTENCE_QUEST: '☰',
  STORY_TALK: 'AI',
}

const weekDays = [
  { label: 'Mon', state: 'done' },
  { label: 'Tue', state: 'done' },
  { label: 'Wed', state: 'done' },
  { label: 'Thu', state: 'today' },
  { label: 'Fri', state: 'next' },
  { label: 'Sat', state: 'next' },
  { label: 'Sun', state: 'next' },
]

const smartFlowCards = [
  { label: 'Word', icon: 'A', tone: 'word' },
  { label: 'Sentence', icon: '', tone: 'sentence' },
  { label: 'Word', icon: 'B', tone: 'word' },
  { label: 'Sentence', icon: '', tone: 'sentence' },
  { label: 'Chat', icon: '...', tone: 'chat' },
]

function starsForScore(score: number) {
  if (score >= 90) return 3
  if (score >= 70) return 2
  if (score >= 45) return 1
  return 0
}

function shuffle<T>(items: T[]): T[] {
  return [...items].sort((a, b) => String(a).localeCompare(String(b)))
}

function normalizeBuiltAnswer(value: string) {
  return value.replace(/\s+/g, '').toLowerCase()
}

function mockQueueForMode(mode: ReviewMode) {
  if (mode === 'WORD_PLAYGROUND') return wordPlaygroundQueue
  if (mode === 'SENTENCE_QUEST') return sentenceQuestQueue
  if (mode === 'STORY_TALK') return storyTalkQueue
  return fallbackReviewQueue
}

function cardKind(card: ReviewCardData, index: number): ReviewKind {
  if (card.cardType === 'SENTENCE') return index % 2 === 0 ? 'pick' : 'order'
  if (card.cardType === 'CHAT') return 'chat'
  return (['keyword', 'picture', 'match'] as ReviewKind[])[index % 3]
}

function cardToReviewItem(card: ReviewCardData, cards: ReviewCardData[], index: number): ReviewItem {
  const kind = cardKind(card, index)
  const otherWords = cards
    .map((item) => item.keyword)
    .filter((word) => word && word !== card.keyword)
    .slice(0, 3)
  const words = card.sourceSentence.split(/\s+/).map((word) => word.replace(/[.,!?;:'"]/g, '')).filter(Boolean)
  if (kind === 'order') {
    return {
      id: `review-${card.cardId}`,
      cardId: card.cardId,
      kind,
      bookTitle: card.bookTitle || 'Story',
      chapterNumber: card.chapterNumber,
      prompt: 'Build the sentence.',
      sentence: card.sourceSentence,
      answer: card.sourceSentence.replace(/[.!?]$/, ''),
      options: shuffle(words).slice(0, 8),
      memory: card.memoryScore,
    }
  }
  if (kind === 'match') {
    const pairCards = [card, ...cards.filter((item) => item.cardId !== card.cardId)].slice(0, 3)
    return {
      id: `review-${card.cardId}`,
      cardId: card.cardId,
      kind,
      bookTitle: card.bookTitle || 'Story',
      chapterNumber: card.chapterNumber,
      prompt: 'Connect each word to its story clue.',
      sentence: 'Match the story words.',
      answer: 'all',
      options: [],
      memory: card.memoryScore,
      pairs: pairCards.map((item) => ({ left: item.keyword, right: item.sourceSentence.split(/\s+/).slice(0, 4).join(' ') })),
    }
  }
  return {
    id: `review-${card.cardId}`,
    cardId: card.cardId,
    kind,
    bookTitle: card.bookTitle || 'Story',
    chapterNumber: card.chapterNumber,
    prompt: kind === 'chat' ? 'Talk about the story.' : kind === 'picture' ? 'Which word matches the story?' : 'Pick the missing word.',
    sentence: card.clozeSentence || card.sourceSentence,
    answer: card.keyword,
    options: shuffle([card.keyword, ...otherWords, 'story', 'friend']).slice(0, 4),
    memory: card.memoryScore,
  }
}

export default function ReviewPage() {
  const [started, setStarted] = useState(false)
  const [index, setIndex] = useState(0)
  const [results, setResults] = useState<Record<string, boolean>>({})
  const [selected, setSelected] = useState('')
  const [builtWords, setBuiltWords] = useState<string[]>([])
  const [matchLeft, setMatchLeft] = useState('')
  const [matches, setMatches] = useState<Record<string, string>>({})
  const [feedback, setFeedback] = useState<'correct' | 'wrong' | ''>('')
  const [showHelp, setShowHelp] = useState(false)
  const [reviewQueue, setReviewQueue] = useState<ReviewItem[]>(fallbackReviewQueue)
  const [selectedMode, setSelectedMode] = useState<ReviewMode>('SMART_MIX')
  const [storyTalk, setStoryTalk] = useState<StoryTalkData | null>(null)
  const [storyMessage, setStoryMessage] = useState('')
  const [storyReply, setStoryReply] = useState('')

  const current = reviewQueue[index]
  const doneCount = Object.keys(results).length
  const isFinished = started && doneCount >= reviewQueue.length
  const resultScore = useMemo(() => {
    const values = Object.values(results)
    if (!values.length) return 0
    return Math.round((values.filter(Boolean).length / values.length) * 100)
  }, [results])
  const rightOptions = useMemo(() => shuffle(current.pairs?.map((pair) => pair.right) ?? []), [current])

  useEffect(() => {
    if (!usesBackendApi()) return
    fetchDueReviews(5, 'SMART_MIX')
      .then((data) => {
        if (data.cards.length) {
          setReviewQueue(data.cards.map((card, cardIndex, cards) => cardToReviewItem(card, cards, cardIndex)))
        }
      })
      .catch(() => undefined)
  }, [])

  const loadMode = async (mode: ReviewMode) => {
    setSelectedMode(mode)
    setIndex(0)
    setResults({})
    setSelected('')
    setBuiltWords([])
    setMatchLeft('')
    setMatches({})
    setFeedback('')
    setStoryReply('')
    if (mode === 'STORY_TALK') {
      setStoryTalk(await fetchStoryTalk(5))
      setStarted(true)
      return
    }
    const data = await fetchDueReviews(5, mode)
    if (data.cards.length) {
      setReviewQueue(data.cards.map((card, cardIndex, cards) => cardToReviewItem(card, cards, cardIndex)))
    }
    setStarted(true)
  }

  const beginMode = (mode: ReviewMode) => {
    setSelectedMode(mode)
    setIndex(0)
    setResults({})
    setSelected('')
    setBuiltWords([])
    setMatchLeft('')
    setMatches({})
    setFeedback('')
    setStoryReply('')
    setStoryMessage('')
    if (!usesBackendApi()) {
      setReviewQueue(mockQueueForMode(mode))
      setStoryTalk(mode === 'STORY_TALK' ? fallbackStoryTalk : null)
      setStarted(true)
      return
    }
    void loadMode(mode).catch(() => {
      setReviewQueue(mockQueueForMode(mode))
      setStoryTalk(mode === 'STORY_TALK' ? fallbackStoryTalk : null)
      setStarted(true)
    })
  }

  const moveNext = (isCorrect: boolean) => {
    setResults((prev) => ({ ...prev, [current.id]: isCorrect }))
    if (current.cardId && usesBackendApi()) {
      void submitReviewAttempt(current.cardId, isCorrect ? 'GOOD' : 'AGAIN', isCorrect, isCorrect ? 100 : 40)
    }
    setFeedback(isCorrect ? 'correct' : 'wrong')
    window.setTimeout(() => {
      setIndex((value) => Math.min(value + 1, reviewQueue.length - 1))
      setSelected('')
      setBuiltWords([])
      setMatchLeft('')
      setMatches({})
      setFeedback('')
    }, 620)
  }

  const chooseOption = (option: string) => {
    if (feedback) return
    setSelected(option)
    moveNext(option === current.answer)
  }

  const addWord = (word: string) => {
    if (feedback || builtWords.includes(word)) return
    const next = [...builtWords, word]
    setBuiltWords(next)
    if (next.length === current.options.length) {
      moveNext(normalizeBuiltAnswer(next.join(' ')) === normalizeBuiltAnswer(current.answer))
    }
  }

  const chooseMatchRight = (right: string) => {
    if (!matchLeft || feedback) return
    const pair = current.pairs?.find((item) => item.left === matchLeft)
    const next = { ...matches, [matchLeft]: right }
    setMatches(next)
    setMatchLeft('')
    if (pair?.right !== right) {
      moveNext(false)
      return
    }
    if (Object.keys(next).length === current.pairs?.length) {
      moveNext(true)
    }
  }

  const restart = () => {
    setStarted(false)
    setIndex(0)
    setResults({})
    setSelected('')
    setBuiltWords([])
    setMatchLeft('')
    setMatches({})
    setFeedback('')
    setStoryTalk(null)
    setStoryMessage('')
    setStoryReply('')
  }

  const sendStoryMessage = async () => {
    if (!storyMessage.trim()) return
    const message = storyMessage.trim()
    setStoryMessage('')
    if (!usesBackendApi()) {
      setStoryReply(`Nice idea! You used story words. Can you say one more thing about ${current?.answer ?? 'the story'}?`)
      if (current?.kind === 'chat') {
        window.setTimeout(() => moveNext(true), 900)
      }
      return
    }
    if (current?.kind === 'chat' && current.cardId && usesBackendApi()) {
      const result = await sendStoryTalkMessage([current.cardId], message)
      setStoryReply(result.reply)
      window.setTimeout(() => moveNext(true), 900)
      return
    }
    if (storyTalk) {
      const result = await sendStoryTalkMessage(storyTalk.cards.map((card) => card.cardId), message)
      setStoryReply(result.reply)
    }
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
                <p>Words and sentences come from chapters you finished.</p>
                <p>You play 5 quick cards at a time.</p>
                <p>Hard cards come back sooner. Easy cards wait longer.</p>
                <p>Word games help you remember meaning. Sentence quests help you use the words.</p>
                <p>Your stars and answers are saved for your learning report.</p>
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
                <p>5 mixed review cards from saved chapter words, sentences, and story talk.</p>
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
            {current.kind === 'picture' ? (
              <p>Find <strong>{current.answer}</strong></p>
            ) : current.kind === 'match' ? (
              <p>Connect story words.</p>
            ) : (
              <p>{current.sentence}</p>
            )}
          </article>

          {current.kind === 'order' && (
            <>
              <div className={styles.spellSlots}>
                {current.answer.split('').map((_, letterIndex) => (
                  <span key={`${current.id}-slot-${letterIndex}`}>{builtWords[letterIndex] ?? ''}</span>
                ))}
              </div>
              <div className={styles.letterTiles}>
                {current.options.map((word) => (
                  <button key={word} disabled={builtWords.includes(word)} onClick={() => addWord(word)}>
                    {word}
                  </button>
                ))}
              </div>
            </>
          )}

          {current.kind === 'picture' && (
            <div className={styles.wordPictureGrid}>
              {current.options.map((option) => (
                <button key={option} className={selected === option ? styles.picked : ''} onClick={() => chooseOption(option)}>
                  <span>{icons[option] ?? '⭐'}</span>
                  <strong>{option}</strong>
                </button>
              ))}
            </div>
          )}

          {current.kind === 'match' && current.pairs && (
            <div className={styles.matchGame}>
              <svg viewBox="0 0 100 200" aria-hidden="true">
                {current.pairs.map((pair, pairIndex) => {
                  const rightIndex = rightOptions.indexOf(matches[pair.left])
                  if (rightIndex < 0) return null
                  return <line key={pair.left} x1="28" y1={32 + pairIndex * 58} x2="72" y2={32 + rightIndex * 58} />
                })}
              </svg>
              <div className={styles.matchColumn}>
                {current.pairs.map((pair) => (
                  <button
                    key={pair.left}
                    className={matchLeft === pair.left || matches[pair.left] ? styles.picked : ''}
                    disabled={Boolean(matches[pair.left])}
                    onClick={() => setMatchLeft(pair.left)}
                  >
                    {pair.left}
                  </button>
                ))}
              </div>
              <div className={styles.matchColumn}>
                {rightOptions.map((right) => (
                  <button key={right} disabled={Object.values(matches).includes(right)} onClick={() => chooseMatchRight(right)}>
                    {right}
                  </button>
                ))}
              </div>
            </div>
          )}

          {(current.kind === 'pick' || current.kind === 'keyword') && (
            <div className={styles.wordTokenGrid}>
              {current.options.map((option) => (
                <button key={option} className={selected === option ? styles.picked : ''} onClick={() => chooseOption(option)}>
                  {option}
                </button>
              ))}
            </div>
          )}

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

          {current.kind === 'order' ? (
            <>
              <div className={styles.sentenceTray}>
                {builtWords.length ? builtWords.map((word) => <span key={word}>{word}</span>) : <em>Build the sentence</em>}
              </div>
              <div className={styles.sentenceTiles}>
                {current.options.map((word) => (
                  <button key={word} disabled={builtWords.includes(word)} onClick={() => addWord(word)}>
                    {word}
                  </button>
                ))}
              </div>
            </>
          ) : (
            <div className={styles.sentenceChoices}>
              {current.options.map((option) => (
                <button key={option} className={selected === option ? styles.picked : ''} onClick={() => chooseOption(option)}>
                  {option}
                </button>
              ))}
            </div>
          )}

          {feedback && <div className={styles.feedback}>{feedback === 'correct' ? 'Great!' : `Oops! ${current.answer}`}</div>}
        </section>
      ) : selectedMode === 'STORY_TALK' ? (
        <section className={styles.storyTalk}>
          <span>Story Talk</span>
          <h2>{storyTalk?.topic.title ?? 'Story Talk'}</h2>
          <p>{storyReply || storyTalk?.topic.opening || 'Tell me one thing you remember.'}</p>
          <div className={styles.wordChips}>
            {(storyTalk?.topic.targetWords ?? []).map((word) => <b key={word}>{word}</b>)}
          </div>
          <div className={styles.starterQuestions}>
            {(storyTalk?.topic.starterQuestions ?? []).map((question) => (
              <button key={question} onClick={() => setStoryMessage(question)}>{question}</button>
            ))}
          </div>
          <div className={styles.storyInput}>
            <input value={storyMessage} onChange={(event) => setStoryMessage(event.target.value)} placeholder="Type your idea" />
            <button onClick={sendStoryMessage}>Send</button>
          </div>
          <button className={styles.startButton} onClick={restart}>Back</button>
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

          {(current.kind === 'pick' || current.kind === 'keyword') && (
            <div className={current.kind === 'keyword' ? styles.wordCloud : styles.choiceGrid}>
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

          {current.kind === 'picture' && (
            <div className={styles.pictureGrid}>
              {current.options.map((option) => (
                <button
                  key={option}
                  className={selected === option ? styles.picked : ''}
                  onClick={() => chooseOption(option)}
                >
                  <span>{icons[option] ?? '⭐'}</span>
                  <strong>{option}</strong>
                </button>
              ))}
            </div>
          )}

          {current.kind === 'order' && (
            <>
              <div className={styles.buildTray}>
                {builtWords.length ? builtWords.map((word) => <span key={word}>{word}</span>) : <em>Tap words in order</em>}
              </div>
              <div className={styles.wordCloud}>
                {current.options.map((word) => (
                  <button
                    key={word}
                    disabled={builtWords.includes(word)}
                    onClick={() => addWord(word)}
                  >
                    {word}
                  </button>
                ))}
              </div>
            </>
          )}

          {current.kind === 'match' && current.pairs && (
            <div className={styles.matchGame}>
              <svg viewBox="0 0 100 200" aria-hidden="true">
                {current.pairs.map((pair, pairIndex) => {
                  const rightIndex = rightOptions.indexOf(matches[pair.left])
                  if (rightIndex < 0) return null
                  return (
                    <line
                      key={pair.left}
                      x1="28"
                      y1={32 + pairIndex * 58}
                      x2="72"
                      y2={32 + rightIndex * 58}
                    />
                  )
                })}
              </svg>
              <div className={styles.matchColumn}>
                {current.pairs.map((pair) => (
                  <button
                    key={pair.left}
                    className={matchLeft === pair.left || matches[pair.left] ? styles.picked : ''}
                    disabled={Boolean(matches[pair.left])}
                    onClick={() => setMatchLeft(pair.left)}
                  >
                    {pair.left}
                  </button>
                ))}
              </div>
              <div className={styles.matchColumn}>
                {rightOptions.map((right) => (
                  <button
                    key={right}
                    disabled={Object.values(matches).includes(right)}
                    onClick={() => chooseMatchRight(right)}
                  >
                    {right}
                  </button>
                ))}
              </div>
            </div>
          )}

          {current.kind === 'chat' && (
            <div className={styles.chatCard}>
              <span>Use this word</span>
              <strong>{current.answer}</strong>
              <p>{storyReply || 'Tell Popo one thing you remember from this story moment.'}</p>
              <div className={styles.storyInput}>
                <input value={storyMessage} onChange={(event) => setStoryMessage(event.target.value)} placeholder="Type a short answer" />
                <button onClick={sendStoryMessage}>Send</button>
              </div>
              {!usesBackendApi() && (
                <button className={styles.chatSkip} onClick={() => moveNext(true)}>Done</button>
              )}
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
