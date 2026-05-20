import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppStore } from '../../store/useAppStore'
import { fetchBooks } from '../../services/api'
import type { Book } from '../../types'
import BookCard from '../../components/BookCard/BookCard'
import styles from './BookChoicePage.module.css'

export default function BookChoicePage() {
  const navigate = useNavigate()
  const { selectBook } = useAppStore()
  const [books, setBooks] = useState<Book[]>([])

  useEffect(() => {
    fetchBooks().then(setBooks)
  }, [])

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
        {books.map((book) => (
          <BookCard key={book.id} book={book} onSelect={handleSelectBook} />
        ))}
      </div>

    </div>
  )
}
