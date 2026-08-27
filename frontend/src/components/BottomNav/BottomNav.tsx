import { useLocation, useNavigate } from 'react-router-dom'
import styles from './BottomNav.module.css'

const items = [
  { path: '/review', label: 'Review' },
  { path: '/home', label: 'Home' },
  { path: '/mypage', label: 'My' },
]

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
            <strong>{item.label}</strong>
          </button>
        )
      })}
    </nav>
  )
}
