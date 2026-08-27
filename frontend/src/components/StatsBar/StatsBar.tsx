import type { UserStats } from '../../types'
import styles from './StatsBar.module.css'

interface Props {
  stats: UserStats
}

function StatIcon({ type }: { type: 'streak' | 'points' | 'energy' }) {
  if (type === 'streak') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M12 3c1.8 2 2.2 3.8 1.2 5.4 1.7-.4 3.8.7 4.8 2.8 1.7 3.7-.8 7.8-6 7.8s-7.7-4.1-6-7.8c.7-1.6 2-2.7 3.5-3.3.1-1.7.8-3.4 2.5-4.9Z" />
        <path d="M12 14.5c.8.8.8 2.2 0 3-.8-.8-.8-2.2 0-3Z" />
      </svg>
    )
  }
  if (type === 'points') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="m12 3 2.7 5.5 6.1.9-4.4 4.3 1 6.1L12 16.9l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9L12 3Z" />
      </svg>
    )
  }
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M12 20s-7-4.3-8.7-8.6C2 8 4.2 5 7.6 5c1.9 0 3.4 1 4.4 2.4C13 6 14.5 5 16.4 5 19.8 5 22 8 20.7 11.4 19 15.7 12 20 12 20Z" />
    </svg>
  )
}

export default function StatsBar({ stats }: Props) {
  return (
    <div className={styles.bar}>
      <div className={`${styles.badge} ${styles.streak}`}>
        <span className={styles.icon}><StatIcon type="streak" /></span>
        <span className={styles.meta}>
          <strong>{stats.streak}</strong>
          <em>연속</em>
        </span>
      </div>
      <div className={`${styles.badge} ${styles.rewards}`}>
        <span className={styles.icon}><StatIcon type="points" /></span>
        <span className={styles.meta}>
          <strong>{stats.hearts}</strong>
          <em>포인트</em>
        </span>
      </div>
      <div className={`${styles.badge} ${styles.energy}`}>
        <span className={styles.icon}><StatIcon type="energy" /></span>
        <span className={styles.meta}>
          <strong>{Math.round(stats.xpPercent * 5)}/5</strong>
          <em>에너지</em>
        </span>
      </div>
    </div>
  )
}
