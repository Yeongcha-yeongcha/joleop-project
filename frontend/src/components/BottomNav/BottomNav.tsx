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
        <path d="M12 6.8c-1.7-1-3.7-1.5-6-1.5v12.2c2.3 0 4.3.5 6 1.5" />
        <path d="M12 6.8c1.7-1 3.7-1.5 6-1.5v12.2c-2.3 0-4.3.5-6 1.5" />
        <path d="M12 6.8V19" />
        <path d="M7.8 9.2c1.1.1 2 .3 2.8.7" />
        <path d="M16.2 9.2c-1.1.1-2 .3-2.8.7" />
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
