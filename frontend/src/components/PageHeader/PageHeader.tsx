import type { ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import styles from './PageHeader.module.css'

interface Props {
  title: string
  /** 뒤로가기 목적지. 홈이 허브라 기본값은 '/home'. */
  backTo?: string
  backLabel?: string
  /** 우측 슬롯. 도움말 버튼, 별 개수처럼 페이지 고유 요소를 넣는다. */
  trailing?: ReactNode
}

/**
 * Books(My Library)의 .whiteHeader 와 같은 스타일의 공용 상단바.
 * 좌측 뒤로가기 / 중앙 타이틀 / 우측 슬롯.
 */
export default function PageHeader({
  title,
  backTo = '/home',
  backLabel = 'Go back',
  trailing,
}: Props) {
  const navigate = useNavigate()

  return (
    <header className={styles.bar}>
      <button className={styles.backButton} onClick={() => navigate(backTo)} aria-label={backLabel}>
        ←
      </button>
      <h1 className={styles.title}>{title}</h1>
      <div className={styles.trailing}>{trailing}</div>
    </header>
  )
}
