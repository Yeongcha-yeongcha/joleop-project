import type { UserStats } from '../../types'
import styles from './StatsBar.module.css'

interface Props {
  stats: UserStats
}

export default function StatsBar({ stats }: Props) {
  return (
    <div className={styles.bar}>
      <div className={`${styles.badge} ${styles.streak}`}>
        <span className={styles.meta}>
          <strong>{stats.streak}</strong>
          <em>Streak</em>
        </span>
      </div>
      <div className={`${styles.badge} ${styles.rewards}`}>
        <span className={styles.meta}>
          <strong>{stats.hearts}</strong>
          <em>Points</em>
        </span>
      </div>
      <div className={`${styles.badge} ${styles.energy}`}>
        <span className={styles.meta}>
          <strong>{Math.round(stats.xpPercent * 5)}/5</strong>
          <em>Energy</em>
        </span>
      </div>
    </div>
  )
}
