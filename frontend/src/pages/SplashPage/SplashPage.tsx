import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import styles from './SplashPage.module.css'

export default function SplashPage() {
  const navigate = useNavigate()

  useEffect(() => {
    const timer = window.setTimeout(() => navigate('/start'), 1400)
    return () => window.clearTimeout(timer)
  }, [navigate])

  return (
    <main className={styles.page}>
      <div className={styles.logoMark}>
        <img src="/images/onboarding/lion-reading.png" alt="Lion" />
      </div>
      <h1>Lion</h1>
      <p>AI English Stories</p>
    </main>
  )
}
