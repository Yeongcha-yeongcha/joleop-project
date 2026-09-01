import { useMemo, useState } from 'react'
import styles from './ReviewPage.module.css'

type ReviewKind = 'pick' | 'keyword' | 'match' | 'order' | 'picture'

interface ReviewItem {
  id: string
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

const reviewQueue: ReviewItem[] = [
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
}

const gameMix = [
  { label: 'Pick', icon: 'Aa' },
  { label: 'Cards', icon: 'Pic' },
  { label: 'Match', icon: 'Link' },
  { label: 'Build', icon: 'ABC' },
  { label: 'Tap', icon: 'Tap' },
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

export default function ReviewPage() {
  const [started, setStarted] = useState(false)
  const [index, setIndex] = useState(0)
  const [results, setResults] = useState<Record<string, boolean>>({})
  const [selected, setSelected] = useState('')
  const [builtWords, setBuiltWords] = useState<string[]>([])
  const [matchLeft, setMatchLeft] = useState('')
  const [matches, setMatches] = useState<Record<string, string>>({})
  const [feedback, setFeedback] = useState<'correct' | 'wrong' | ''>('')

  const current = reviewQueue[index]
  const doneCount = Object.keys(results).length
  const isFinished = started && doneCount >= reviewQueue.length
  const averageMemory = Math.round(
    reviewQueue.reduce((sum, item) => sum + item.memory, 0) / reviewQueue.length,
  )
  const chapterNumbers = useMemo(
    () => Array.from(new Set(reviewQueue.map((item) => item.chapterNumber))).sort((a, b) => a - b),
    [],
  )
  const resultScore = useMemo(() => {
    const values = Object.values(results)
    if (!values.length) return 0
    return Math.round((values.filter(Boolean).length / values.length) * 100)
  }, [results])
  const rightOptions = useMemo(() => shuffle(current.pairs?.map((pair) => pair.right) ?? []), [current])

  const moveNext = (isCorrect: boolean) => {
    setResults((prev) => ({ ...prev, [current.id]: isCorrect }))
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
      moveNext(next.join(' ') === current.answer)
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
          <p>Play 5 tiny quizzes today.</p>
        </div>
      </header>

      {!started ? (
        <>
          <section className={styles.missionPanel}>
            <span className={styles.missionBadge}>Today&apos;s Quest</span>
            <div className={styles.missionBody}>
              <img src="/images/onboarding/lion-headphones.png" alt="" />
              <div>
                <h2>Ready for {reviewQueue.length} games?</h2>
                <p>Play with words from chapters you finished.</p>
              </div>
            </div>
          </section>

          <section className={styles.questGrid} aria-label="Today review summary">
            <article>
              <span>Cards</span>
              <strong>{reviewQueue.length}</strong>
            </article>
            <article>
              <span>Stars</span>
              <strong>0-3</strong>
            </article>
            <article>
              <span>Memory</span>
              <strong>{averageMemory}%</strong>
            </article>
          </section>

          <section className={styles.memoryCard}>
            <div>
              <span>Memory Power</span>
              <strong>{averageMemory}%</strong>
            </div>
            <b><i style={{ width: `${averageMemory}%` }} /></b>
            <p>Hard cards come back sooner. Easy cards wait longer.</p>
          </section>

          <section className={styles.sourceTrail} aria-label="Review chapters">
            <span>Story Map</span>
            <div>
              {chapterNumbers.map((chapterNumber) => (
                <b key={chapterNumber}>Ch {chapterNumber}</b>
              ))}
            </div>
          </section>

          <section className={styles.gameMix} aria-label="Game mix">
            {gameMix.map((game) => (
              <article key={game.label}>
                <span>{game.icon}</span>
                <strong>{game.label}</strong>
              </article>
            ))}
          </section>

          <button className={styles.startButton} onClick={() => setStarted(true)}>
            Start Review
          </button>
        </>
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
