import type { UserStats } from '../../types'
import styles from './StatsBar.module.css'

interface Props {
  stats: UserStats
}

export default function StatsBar({ stats }: Props) {
  return (
    <div className={styles.bar}>
      <div className={`${styles.badge} ${styles.streak}`}>
        <span className={styles.icon}>🔥</span>
        <span>+{stats.streak}</span>
      </div>
      <div className={`${styles.badge} ${styles.hearts}`}>
        <span className={styles.icon}>💜</span>
        <span>{stats.hearts}</span>
      </div>
      <div className={styles.xp}>
        <span className={styles.icon}>⚡</span>
        <div className={styles.xpTrack}>
          <div
            className={styles.xpFill}
            style={{ width: `${stats.xpPercent * 100}%` }}
          />
        </div>
      </div>
    </div>
  )
}
