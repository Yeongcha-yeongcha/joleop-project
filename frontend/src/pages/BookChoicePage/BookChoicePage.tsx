import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppStore } from '../../store/useAppStore'
import { ApiError, clearProfileSession, fetchBooks } from '../../services/api'
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
      .catch((err: unknown) => {
        if (err instanceof ApiError && err.status === 401) {
          clearProfileSession()
          navigate('/profiles', { replace: true })
          return
        }
        if (err instanceof TypeError) {
          setError('Start the backend server on port 8000.')
          return
        }
        setError(err instanceof Error ? err.message : 'Could not load books.')
      })
      .finally(() => setIsLoading(false))
  }, [navigate])

  useEffect(() => { load() }, [load])

  const handleSelectBook = (book: Book) => {
    selectBook(book)
    navigate(-1)
  }

  return (
    <div className={styles.page}>
      <div className={styles.whiteHeader}>
        <button
          className={styles.closeButton}
          onClick={() => navigate('/home')}
          aria-label="Close book picker"
        >
          ×
        </button>
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
