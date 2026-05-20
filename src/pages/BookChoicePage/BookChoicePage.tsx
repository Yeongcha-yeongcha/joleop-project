/**
 * BookChoicePage — My Library 화면 (/books)
 *
 * 레이아웃:
 *   [WhiteHeader]   ← "My Library" 타이틀
 *   [BookGrid]      ← 3열 그리드, 내부 스크롤
 *
 * 동작:
 *   - 잠금 해제된 책 커버 클릭 → 전역 상태에 저장 후 홈으로 복귀
 *   - 잠긴 책은 클릭 불가
 *
 * TODO: BOOKS 데이터를 GET /books API 응답으로 교체
 */

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
    navigate(-1)
  }

  return (
    <div className={styles.page}>

      {/* 상단 흰 헤더 */}
      <div className={styles.whiteHeader}>
        <h1 className={styles.title}>My Library</h1>
      </div>

      {/* 책 그리드 (내부 스크롤) */}
      <div className={styles.grid}>
        {BOOKS.map((book) => (
          <BookCard key={book.id} book={book} onSelect={handleSelectBook} />
        ))}
      </div>

    </div>
  )
}
