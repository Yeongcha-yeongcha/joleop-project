import { useNavigate } from 'react-router-dom'
import { useAppStore } from '../../store/useAppStore'
import { BOOKS } from '../../data/books'
import type { Book } from '../../types'
import BookCard from '../../components/BookCard/BookCard'
import styles from './BookChoicePage.module.css'

export default function BookChoicePage() {
  const navigate = useNavigate()
  const { selectBook } = useAppStore()

  const handleSelectBook = (book: Book) => {
    selectBook(book)
    navigate(-1) // 홈으로 돌아가기
  }

  const handleBack = () => {
    navigate(-1)
  }

  return (
    <div className={styles.page}>
      {/* Status bar */}
      <div className={styles.statusBarPlaceholder}>
        <span className={styles.time}>9:41</span>
        <div className={styles.signals}>
          <span>📶</span>
          <span>🔋</span>
        </div>
      </div>

      {/* 헤더 */}
      <div className={styles.header}>
        <button className={styles.backBtn} onClick={handleBack} aria-label="뒤로가기">
          ‹
        </button>
        <h1 className={styles.title}>My Library</h1>
      </div>

      {/* 책 그리드 */}
      <div className={styles.grid}>
        {BOOKS.map((book) => (
          <BookCard key={book.id} book={book} onSelect={handleSelectBook} />
        ))}
      </div>
    </div>
  )
}
