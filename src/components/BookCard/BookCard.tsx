import type { Book } from '../../types'
import styles from './BookCard.module.css'

interface Props {
  book: Book
  onSelect: (book: Book) => void
}

export default function BookCard({ book, onSelect }: Props) {
  const isLocked = book.status === 'locked'

  return (
    <div
      className={`${styles.card} ${isLocked ? styles.locked : ''}`}
      onClick={() => !isLocked && onSelect(book)}
      role={isLocked ? 'img' : 'button'}
      aria-label={isLocked ? `잠긴 책: ${book.title}` : `${book.title} 선택`}
    >
      <div className={styles.coverWrap}>
        <div className={styles.cover} style={{ background: book.coverColor }}>
          {book.coverImage ? (
            <img src={book.coverImage} className={styles.coverImage} alt={book.title} />
          ) : null}
        </div>

        {isLocked && (
          <div className={styles.lockOverlay}>
            <span className={styles.lockIcon}>🔒</span>
          </div>
        )}
      </div>

      <div className={styles.info}>
        <span className={styles.title}>{book.title}</span>
        <div className={styles.badges}>
          <span className={`${styles.badge} ${styles.badgeLv}`}>Lv. {book.level}</span>
          {book.status === 'reading' && (
            <span className={`${styles.badge} ${styles.badgeReading}`}>읽는 중</span>
          )}
          {book.status === 'done' && (
            <span className={`${styles.badge} ${styles.badgeDone}`}>DONE !</span>
          )}
          {isLocked && (
            <span className={`${styles.badge} ${styles.badgeLessons}`}>
              {book.totalLessons} lessons
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
