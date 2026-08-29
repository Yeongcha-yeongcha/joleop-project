import type { UserStats } from '../../types'
import styles from './StatsBar.module.css'

interface Props {
  stats: UserStats
  onCustomize?: () => void
}

function StatIcon({ type }: { type: 'streak' | 'points' | 'energy' }) {
  if (type === 'streak') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path className={styles.iconFill} d="M12 3.2c2 2 2.4 3.8 1.2 5.4 1.8-.2 4.1 1.3 4.8 3.8 1 3.6-1.6 7.1-6 7.1s-7-3.5-6-7.1c.5-1.9 1.9-3.4 3.7-4 .1-1.8.8-3.6 2.3-5.2Z" />
        <path className={styles.iconShine} d="M12 14.3c1 1 .9 2.4 0 3.3-.9-.9-1-2.3 0-3.3Z" />
      </svg>
    )
  }
  if (type === 'points') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path className={styles.iconFill} d="m12 2.9 2.8 5.6 6.2.9-4.5 4.4 1.1 6.2-5.6-2.9L6.4 20l1.1-6.2L3 9.4l6.2-.9L12 2.9Z" />
        <path className={styles.iconShine} d="m10 9.1 2-3 2 3" />
      </svg>
    )
  }
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path className={styles.iconFill} d="M12 20.4S4.6 16 3 11.6C1.8 8.2 4 5.1 7.5 5.1c1.9 0 3.5 1 4.5 2.4 1-1.4 2.6-2.4 4.5-2.4 3.5 0 5.7 3.1 4.5 6.5-1.6 4.4-9 8.8-9 8.8Z" />
      <path className={styles.iconShine} d="M8 8.2c.9-.5 2-.4 2.8.3" />
    </svg>
  )
}

export default function StatsBar({ stats, onCustomize }: Props) {
  return (
    <div className={styles.bar}>
      <div className={`${styles.stat} ${styles.streak}`}>
        <span className={styles.icon}><StatIcon type="streak" /></span>
        <span className={styles.meta}>
          <strong>{stats.streak}</strong>
          <em>연속</em>
        </span>
      </div>
      <div className={`${styles.stat} ${styles.rewards}`}>
        <span className={styles.icon}><StatIcon type="points" /></span>
        <span className={styles.meta}>
          <strong>{stats.hearts}</strong>
          <em>포인트</em>
        </span>
      </div>
      <div className={`${styles.stat} ${styles.energy}`}>
        <span className={styles.icon}><StatIcon type="energy" /></span>
        <span className={styles.meta}>
          <strong>{Math.round(stats.xpPercent * 5)}/5</strong>
          <em>에너지</em>
        </span>
      </div>
      {onCustomize && (
        <button className={styles.customizeButton} onClick={onCustomize}>
          꾸미기
        </button>
      )}
    </div>
  )
}
