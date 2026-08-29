import BottomNav from '../../components/BottomNav/BottomNav'
import styles from './ReviewPage.module.css'

const reviewItems = [
  { type: '단어', text: 'cave', source: 'The Dragon Story', due: '오늘', interval: '1일', strength: 38 },
  { type: '문장', text: 'Take a deep breath.', source: 'The Dragon Story', due: '오늘', interval: '1일', strength: 52 },
  { type: '표현', text: 'Yes, please.', source: 'Fresh Lemonade!', due: '내일', interval: '3일', strength: 66 },
  { type: '단어', text: 'clouds', source: 'The Snack Museum', due: '3일 뒤', interval: '7일', strength: 78 },
]

const reviewCycles = [
  { label: '처음 학습', caption: '바로 오늘 복습' },
  { label: '1일 뒤', caption: '짧게 다시 확인' },
  { label: '3일 뒤', caption: '헷갈린 표현 고정' },
  { label: '7일 뒤', caption: '오래 기억하기' },
]

export default function ReviewPage() {
  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <img src="/images/onboarding/lion-headphones.png" alt="" />
        <div>
          <h1>복습</h1>
          <p>학습한 표현을 기억이 흐려지기 전에 다시 만나요.</p>
        </div>
      </header>

      <section className={styles.summary}>
        <span>오늘 할 복습</span>
        <strong>2개</strong>
        <p>틀리면 오늘 다시, 맞히면 다음 주기로 넘어가요.</p>
      </section>

      <section className={styles.cycles} aria-label="복습 주기">
        {reviewCycles.map((cycle, index) => (
          <article key={cycle.label}>
            <span>{index + 1}</span>
            <strong>{cycle.label}</strong>
            <em>{cycle.caption}</em>
          </article>
        ))}
      </section>

      <section className={styles.list}>
        {reviewItems.map((item) => (
          <article key={`${item.type}-${item.text}`} className={styles.card}>
            <div>
              <span>{item.type}</span>
              <strong>{item.text}</strong>
              <small>{item.source} · 다음 성공 시 {item.interval} 주기</small>
              <b><i style={{ width: `${item.strength}%` }} /></b>
            </div>
            <em>{item.due}</em>
          </article>
        ))}
      </section>

      <button className={styles.startButton}>복습 시작</button>
      <BottomNav />
    </main>
  )
}
