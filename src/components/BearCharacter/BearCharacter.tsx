import type { Book } from '../../types'
import styles from './BearCharacter.module.css'

// TODO: 피그마에서 에셋 추출 후 아래 경로로 교체
// import bearEmpty from '../../assets/bear-empty.png'
// import bearWithBook from '../../assets/bear-with-book.png'

interface Props {
  selectedBook: Book | null
  onTap: () => void
}

export default function BearCharacter({ selectedBook, onTap }: Props) {
  return (
    <div className={styles.wrapper}>
      <button
        className={styles.bearContainer}
        onClick={onTap}
        aria-label={selectedBook ? '책 바꾸기' : '책 선택하기'}
      >
        {selectedBook ? (
          // 책을 들고 있는 곰돌이
          <BearWithBook book={selectedBook} />
        ) : (
          // 빈 곰돌이
          <BearEmpty />
        )}
        <div className={styles.shadow} />
      </button>
    </div>
  )
}

function BearEmpty() {
  return (
    <div style={{ position: 'relative' }}>
      {/* 피그마 에셋으로 교체: <img src={bearEmpty} className={styles.bearImg} alt="곰돌이" /> */}
      <BearSVGPlaceholder hasBook={false} />
    </div>
  )
}

function BearWithBook({ book }: { book: Book }) {
  return (
    <div style={{ position: 'relative' }}>
      {/* 피그마 에셋으로 교체: <img src={bearWithBook} className={styles.bearWithBookImg} alt="곰돌이" /> */}
      <BearSVGPlaceholder hasBook coverColor={book.coverColor} />
    </div>
  )
}

// 피그마 에셋 교체 전까지 쓰는 SVG 플레이스홀더
function BearSVGPlaceholder({ hasBook, coverColor }: { hasBook: boolean; coverColor?: string }) {
  return (
    <svg
      width={hasBook ? 220 : 200}
      height={hasBook ? 220 : 200}
      viewBox="0 0 200 200"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* 몸통 */}
      <circle cx="100" cy="115" r="55" fill="#F5B942" />
      {/* 머리 */}
      <circle cx="100" cy="75" r="45" fill="#F5B942" />
      {/* 귀 */}
      <circle cx="64" cy="40" r="16" fill="#F5B942" />
      <circle cx="136" cy="40" r="16" fill="#F5B942" />
      <circle cx="64" cy="40" r="10" fill="#E8A030" />
      <circle cx="136" cy="40" r="10" fill="#E8A030" />
      {/* 눈 */}
      <circle cx="86" cy="72" r="9" fill="#1A1A2E" />
      <circle cx="114" cy="72" r="9" fill="#1A1A2E" />
      <circle cx="89" cy="70" r="3" fill="white" />
      <circle cx="117" cy="70" r="3" fill="white" />
      {/* 코 */}
      <ellipse cx="100" cy="87" rx="6" ry="4" fill="#1A1A2E" />
      {/* 볼 */}
      <circle cx="78" cy="84" r="7" fill="#F0907A" opacity="0.6" />
      <circle cx="122" cy="84" r="7" fill="#F0907A" opacity="0.6" />
      {/* 입 */}
      <path d="M93 93 Q100 100 107 93" stroke="#1A1A2E" strokeWidth="2" fill="none" strokeLinecap="round" />
      {/* 배 */}
      <ellipse cx="100" cy="118" rx="28" ry="24" fill="#EDA535" />
      {/* 팔 왼쪽 */}
      <ellipse cx="54" cy="118" rx="14" ry="24" fill="#F5B942" transform="rotate(-10 54 118)" />
      {/* 팔 오른쪽 */}
      <ellipse cx="146" cy="118" rx="14" ry="24" fill="#F5B942" transform="rotate(10 146 118)" />
      {/* 다리 */}
      <ellipse cx="82" cy="162" rx="16" ry="12" fill="#F5B942" />
      <ellipse cx="118" cy="162" rx="16" ry="12" fill="#F5B942" />

      {/* 책 (선택된 경우) */}
      {hasBook && coverColor && (
        <g>
          <rect x="68" y="108" width="64" height="52" rx="4" fill={coverColor} />
          <rect x="68" y="108" width="8" height="52" rx="2" fill="rgba(0,0,0,0.2)" />
          <rect x="72" y="120" width="48" height="3" rx="1.5" fill="rgba(255,255,255,0.4)" />
          <rect x="72" y="128" width="36" height="3" rx="1.5" fill="rgba(255,255,255,0.3)" />
        </g>
      )}
    </svg>
  )
}
