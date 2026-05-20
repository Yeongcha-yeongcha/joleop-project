/**
 * HomePage — 앱 진입 화면 (/)
 *
 * 레이아웃:
 *   [StatsBar]           ← 🔥 💜 ⚡ 학습 통계
 *   [LionArea]           ← StartLion 이미지 + 책 버튼 오버레이
 *   [BookInfoCard?]      ← 책 선택 시에만 표시 (제목 / Lesson / 진도바)
 *   [StartButton]        ← 책 미선택: 비활성 / 선택: 활성
 *
 * 상태 흐름:
 *   책 미선택 → BookBtn 클릭 → /books → 책 선택 → 홈 복귀
 *   책 선택됨 → 시작하기 클릭 → /learn/:bookId
 */

import { useNavigate } from 'react-router-dom'
import { useAppStore } from '../../store/useAppStore'
import { IMAGES } from '../../constants/assets'
import StatsBar from '../../components/StatsBar/StatsBar'
import styles from './HomePage.module.css'

export default function HomePage() {
  const navigate = useNavigate()
  const { selectedBook, userStats } = useAppStore()

  const handleStart = () => {
    if (!selectedBook) return
    navigate(`/learn/${selectedBook.id}`)
  }

  return (
    <div className={styles.page}>

      {/* 학습 통계 바 */}
      <StatsBar stats={userStats} />

      {/* 캐릭터 + 책 버튼 */}
      <div className={styles.bearArea}>
        <div className={styles.lionContainer}>
          <img src={IMAGES.startLion} alt="캐릭터" className={styles.lionImg} />

          {/* 책 선택 버튼 — 선택 후엔 해당 책 커버로 교체 */}
          <button
            className={styles.bookBtn}
            onClick={() => navigate('/books')}
            aria-label={selectedBook ? '책 바꾸기' : '책 선택하기'}
          >
            <img
              src={selectedBook?.coverImage ?? IMAGES.bookBtnUnselected}
              alt={selectedBook ? selectedBook.title : '책 선택'}
              className={styles.bookBtnImg}
            />
            {/* 모서리 장식 타원 */}
            <span className={`${styles.corner} ${styles.cornerTL}`} />
            <span className={`${styles.corner} ${styles.cornerTR}`} />
            <span className={`${styles.corner} ${styles.cornerBL}`} />
            <span className={`${styles.corner} ${styles.cornerBR}`} />
          </button>
        </div>
      </div>

      {/* 하단 영역 */}
      <div className={styles.bottomArea}>

        {/* 책 정보 카드 — 책 선택 시에만 노출 */}
        {selectedBook && (
          <div className={styles.bookInfoCard}>
            <div className={styles.bookMeta}>
              <span className={styles.bookTitle}>{selectedBook.title}</span>
              <span className={styles.bookSubtitle}>Lesson {selectedBook.currentLesson}</span>
              <span className={styles.bookSubtitle}>{selectedBook.currentText}</span>
              <div className={styles.progressTrack}>
                <div
                  className={styles.progressFill}
                  style={{ width: `${selectedBook.progress * 100}%` }}
                >
                  <div className={styles.progressHighlight} />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 시작하기 버튼 */}
        <button
          className={styles.startBtn}
          onClick={handleStart}
          disabled={!selectedBook}
          aria-label={selectedBook ? '학습 시작하기' : '책을 먼저 선택해주세요'}
        >
          <img
            src={selectedBook ? IMAGES.startBtnActive : IMAGES.startBtnInactive}
            alt="시작하기"
            className={styles.startBtnImg}
          />
        </button>

      </div>
    </div>
  )
}
