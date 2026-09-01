import { useLocation, useNavigate } from 'react-router-dom'
import styles from './BottomNav.module.css'

const items = [
  { path: '/review', label: 'Review', icon: 'review', tourId: 'nav-review' },
  { path: '/home', label: 'Home', icon: 'home', tourId: 'nav-home' },
  { path: '/mypage', label: 'Me', icon: 'my', tourId: 'nav-my' },
]

function NavIcon({ type }: { type: string }) {
  if (type === 'review') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M5.5 5.5h9.2a3.8 3.8 0 0 1 0 7.6H7" />
        <path d="m9 9.7-3.5 3.4L9 16.5" />
        <path d="M8 19h10" />
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
      <path d="M12 12.2a4.2 4.2 0 1 0 0-8.4 4.2 4.2 0 0 0 0 8.4Z" />
      <path d="M5 20.2a7 7 0 0 1 14 0" />
    </svg>
  )
}

export default function BottomNav() {
  const navigate = useNavigate()
  const location = useLocation()

  return (
    <nav className={styles.nav} aria-label="Main menu">
      {items.map((item) => {
        const isActive = location.pathname === item.path
        return (
          <button
            key={item.path}
            className={`${styles.item} ${isActive ? styles.active : ''} ${item.path === '/home' ? styles.home : ''}`}
            data-tour={item.tourId}
            onClick={() => navigate(item.path)}
            aria-current={isActive ? 'page' : undefined}
            aria-label={item.label}
            title={item.label}
          >
            <span className={styles.icon}><NavIcon type={item.icon} /></span>
          </button>
        )
      })}
    </nav>
  )
}
