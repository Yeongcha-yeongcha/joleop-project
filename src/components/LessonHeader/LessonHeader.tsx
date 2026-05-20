import styles from './LessonHeader.module.css'

interface Props {
  title: string
  progress: number // 0~1
  onBack: () => void
}

export default function LessonHeader({ title, progress, onBack }: Props) {
  return (
    <div className={styles.header}>
      <div className={styles.top}>
        <button className={styles.backBtn} onClick={onBack} aria-label="뒤로가기">
          ‹
        </button>
        <span className={styles.title}>{title}</span>
      </div>
      <div className={styles.progressTrack}>
        <div className={styles.progressFill} style={{ width: `${progress * 100}%` }}>
          <div className={styles.progressHighlight} />
        </div>
      </div>
    </div>
  )
}
