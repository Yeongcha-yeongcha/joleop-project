import BottomNav from '../../components/BottomNav/BottomNav'
import styles from './ReviewPage.module.css'

const reviewItems = [
  { type: 'Word', text: 'apple', due: 'Today', level: 1 },
  { type: 'Sentence', text: 'It is raining.', due: 'Today', level: 2 },
  { type: 'Word', text: 'sunny', due: 'Tomorrow', level: 1 },
]

export default function ReviewPage() {
  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <img src="/images/onboarding/lion-headphones.png" alt="" />
        <div>
          <h1>Review</h1>
          <p>Practice words and sentences at the right time.</p>
        </div>
      </header>

      <section className={styles.summary}>
        <span>Due Today</span>
        <strong>2 cards</strong>
      </section>

      <section className={styles.list}>
        {reviewItems.map((item) => (
          <article key={`${item.type}-${item.text}`} className={styles.card}>
            <div>
              <span>{item.type}</span>
              <strong>{item.text}</strong>
            </div>
            <em>{item.due}</em>
          </article>
        ))}
      </section>

      <button className={styles.startButton}>Start Review</button>
      <BottomNav />
    </main>
  )
}
