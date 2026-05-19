import { useNavigate } from 'react-router-dom'
import { useAppStore } from '../../store/useAppStore'
import StatsBar from '../../components/StatsBar/StatsBar'
import BearCharacter from '../../components/BearCharacter/BearCharacter'
import styles from './HomePage.module.css'

export default function HomePage() {
  const navigate = useNavigate()
  const { selectedBook, userStats } = useAppStore()

  const handleBearTap = () => {
    navigate('/books')
  }

  const handleStart = () => {
    if (!selectedBook) return
    navigate(`/learn/${selectedBook.id}`)
  }

  return (
    <div className={styles.page}>
      {/* 상단 status bar */}
      <div className={styles.statusBarPlaceholder}>
        <span className={styles.time}>9:41</span>
        <div className={styles.signals}>
          <span>📶</span>
          <span>🔋</span>
        </div>
      </div>

      {/* 스탯 바 */}
      <StatsBar stats={userStats} />

      {/* 곰돌이 영역 */}
      <div className={styles.bearArea}>
        <BearCharacter selectedBook={selectedBook} onTap={handleBearTap} />
      </div>

      {/* 하단 영역 */}
      <div className={styles.bottomArea}>
        {/* 책 정보 카드 (책 선택 후 표시) */}
        {selectedBook && (
          <div className={styles.bookInfoCard}>
            <div
              className={styles.bookThumb}
              style={{ background: selectedBook.coverColor }}
            >
              {selectedBook.coverImage && (
                <img
                  src={selectedBook.coverImage}
                  alt={selectedBook.title}
                  style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: 6 }}
                />
              )}
            </div>
            <div className={styles.bookMeta}>
              <span className={styles.bookTitle}>{selectedBook.title}</span>
              <span className={styles.bookSubtitle}>
                Lesson {selectedBook.currentLesson}
              </span>
              <span className={styles.bookSubtitle}>
                {selectedBook.currentText}
              </span>
              <div className={styles.progressTrack}>
                <div
                  className={styles.progressFill}
                  style={{ width: `${selectedBook.progress * 100}%` }}
                />
              </div>
            </div>
          </div>
        )}

        {/* 시작하기 버튼 */}
        <button
          className={`${styles.startBtn} ${
            selectedBook ? styles.startBtnActive : styles.startBtnDisabled
          }`}
          onClick={handleStart}
          disabled={!selectedBook}
          aria-label={selectedBook ? '학습 시작하기' : '책을 먼저 선택해주세요'}
        >
          시작하기
        </button>
      </div>
    </div>
  )
}
