import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppStore } from '../../store/useAppStore'
import { fetchBooks } from '../../services/api'
import type { Book } from '../../types'
import BookCard from '../../components/BookCard/BookCard'
import StatusScreen from '../../components/StatusScreen/StatusScreen'
import styles from './BookChoicePage.module.css'

export default function BookChoicePage() {
  const navigate = useNavigate()
  const { selectBook } = useAppStore()
  const [books, setBooks] = useState<Book[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(() => {
    setIsLoading(true)
    setError(null)
    fetchBooks()
      .then(setBooks)
      .catch(() => setError('책 목록을 불러오지 못했어요.'))
      .finally(() => setIsLoading(false))
  }, [])

  useEffect(() => { load() }, [load])

  const handleSelectBook = (book: Book) => {
    selectBook(book)
    navigate(-1)
  }

  return (
    <div className={styles.page}>

      <div className={styles.whiteHeader}>
        <h1 className={styles.title}>My Library</h1>
      </div>

      {isLoading || error ? (
        <StatusScreen isLoading={isLoading} error={error} onRetry={load} />
      ) : (
        <div className={styles.grid}>
          {books.map((book) => (
            <BookCard key={book.id} book={book} onSelect={handleSelectBook} />
          ))}
        </div>
      )}

    </div>
  )
}
