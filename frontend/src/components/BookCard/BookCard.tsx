/**
 * BookCard — My Library 그리드의 책 카드
 *
 * 잠금 여부에 따라 두 가지 형태로 렌더링됩니다.
 *   locked  : Book_locked 이미지 + 설명 카드 (클릭 불가)
 *   unlocked: 책 커버 이미지(클릭 가능) + 설명 카드(클릭 불가)
 *
 * 구조:
 *   [coverWrap]  ← 책 커버 이미지 (unlocked만 클릭 이벤트)
 *   [descCard]   ← 제목 + 상태 칩
 */

import type { Book } from '../../types'
import { IMAGES } from '../../constants/assets'
import styles from './BookCard.module.css'

interface Props {
  book: Book
  onSelect: (book: Book) => void
}

export default function BookCard({ book, onSelect }: Props) {
  const isLocked = book.status === 'locked'

  if (isLocked) {
    return (
      <div className={`${styles.card} ${styles.locked}`} aria-label="잠긴 책">
        <div className={styles.coverWrap}>
          <img src={IMAGES.bookLocked} className={styles.coverImage} alt="잠긴 책" />
        </div>
        <div className={styles.descCard}>
          <span className={styles.descTitle}>{book.title}</span>
          <span className={`${styles.chip} ${styles.chipLocked}`}>Locked</span>
        </div>
      </div>
    )
  }

  return (
    <div className={styles.card}>
      {/* 커버 이미지 — 클릭 시 책 선택 */}
      <div
        className={styles.coverWrap}
        onClick={() => onSelect(book)}
        role="button"
        aria-label={`${book.title} 선택`}
        style={{ cursor: 'pointer' }}
      >
        <img src={book.coverImage} className={styles.coverImage} alt={book.title} />
      </div>

      {/* 설명 카드 — 클릭 불가 */}
      <div className={styles.descCard}>
        <span className={styles.descTitle}>{book.title}</span>
        <div className={styles.chipRow}>
          <span className={`${styles.chip} ${styles.chipLv}`}>Lv. {book.level}</span>
          {book.status === 'reading' && (
            <span className={`${styles.chip} ${styles.chipReading}`}>읽는 중</span>
          )}
          {book.status === 'done' && (
            <span className={`${styles.chip} ${styles.chipDone}`}>DONE !</span>
          )}
        </div>
      </div>
    </div>
  )
}
