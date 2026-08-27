import { useLocation, useNavigate } from 'react-router-dom'
import styles from './BottomNav.module.css'

const items = [
  { path: '/review', label: '복습', icon: 'review' },
  { path: '/home', label: '홈', icon: 'home' },
  { path: '/mypage', label: '마이', icon: 'my' },
]

function NavIcon({ type }: { type: string }) {
  if (type === 'review') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M5 12a7 7 0 0 1 14 0" />
        <path d="M5 12v4a2 2 0 0 0 2 2h1v-6H7a2 2 0 0 0-2 2" />
        <path d="M19 12v4a2 2 0 0 1-2 2h-1v-6h1a2 2 0 0 1 2 2" />
      </svg>
    )
  }
  if (type === 'home') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="m4 11 8-7 8 7" />
        <path d="M6.5 10.5V20h11v-9.5" />
        <path d="M10 20v-5h4v5" />
      </svg>
    )
  }
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M8 9V7a4 4 0 0 1 8 0v2" />
      <path d="M7 10h10l1 9H6l1-9Z" />
      <path d="M9.5 14h.1" />
      <path d="M14.5 14h.1" />
    </svg>
  )
}

export default function BottomNav() {
  const navigate = useNavigate()
  const location = useLocation()

  return (
    <nav className={styles.nav} aria-label="주요 메뉴">
      {items.map((item) => {
        const isActive = location.pathname === item.path
        return (
          <button
            key={item.path}
            className={`${styles.item} ${isActive ? styles.active : ''} ${item.path === '/home' ? styles.home : ''}`}
            onClick={() => navigate(item.path)}
            aria-current={isActive ? 'page' : undefined}
          >
            <span className={styles.icon}><NavIcon type={item.icon} /></span>
            <strong>{item.label}</strong>
          </button>
        )
      })}
    </nav>
  )
}
