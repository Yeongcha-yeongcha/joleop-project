import styles from './LessonHeader.module.css'

interface Props {
  title: string
  progress: number // 0~1
  onBack: () => void
  onSkip?: () => void
  skipLabel?: string
  skipDisabled?: boolean
}

export default function LessonHeader({ title, progress, onBack, onSkip, skipLabel = 'Skip', skipDisabled = false }: Props) {
  return (
    <div className={styles.header}>
      <div className={styles.top}>
        <button className={styles.backBtn} onClick={onBack} aria-label="Go back">
          ‹
        </button>
        <span className={styles.title}>{title}</span>
        {onSkip && (
          <button
            className={styles.skipBtn}
            onClick={onSkip}
            disabled={skipDisabled}
            aria-label={skipLabel}
            title={skipLabel}
          >
            <span className={styles.skipIcon} aria-hidden="true">
              <span />
              <span />
            </span>
          </button>
        )}
      </div>
      <div className={styles.progressTrack}>
        <div className={styles.progressFill} style={{ width: `${progress * 100}%` }}>
          <div className={styles.progressHighlight} />
        </div>
      </div>
    </div>
  )
}
