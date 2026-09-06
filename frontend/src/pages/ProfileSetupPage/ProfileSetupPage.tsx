import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { randomProfileColor } from '../../utils/profileAvatar'
import styles from './ProfileSetupPage.module.css'

export default function ProfileSetupPage() {
  const navigate = useNavigate()
  const [pin, setPin] = useState('')

  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (pin.length !== 4) return
    window.localStorage.setItem('yeongcha:pending-profile', JSON.stringify({
      profilePassword: pin,
      profileColor: randomProfileColor(),
    }))
    window.localStorage.removeItem('yeongcha:service-intro-completed')
    navigate('/intro')
  }

  return (
    <main className={styles.page}>
      <img src="/images/onboarding/lion-flag.png" alt="" className={styles.lion} />
      <h1>Make a New User</h1>
      <p>First, choose a 4-number PIN.</p>
      <form onSubmit={submit} className={styles.form}>
        <input
          value={pin}
          onChange={(event) => setPin(event.target.value.replace(/\D/g, '').slice(0, 4))}
          inputMode="numeric"
          type="password"
          placeholder="4 numbers"
        />
        <button disabled={pin.length !== 4}>Start</button>
      </form>
    </main>
  )
}
