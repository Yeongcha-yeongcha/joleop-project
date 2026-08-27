import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import styles from './ProfileSetupPage.module.css'

export default function ProfileSetupPage() {
  const navigate = useNavigate()
  const [pin, setPin] = useState('')

  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (pin.length !== 4) return
    window.localStorage.setItem('yeongcha:pending-profile', JSON.stringify({
      profilePassword: pin,
      profileImageId: Math.floor(Math.random() * 6) + 1,
    }))
    navigate('/onboarding')
  }

  return (
    <main className={styles.page}>
      <img src="/images/onboarding/lion-flag.png" alt="" className={styles.lion} />
      <h1>새 유저 만들기</h1>
      <p>먼저 네 자리 PIN을 정해주세요.</p>
      <form onSubmit={submit} className={styles.form}>
        <input
          value={pin}
          onChange={(event) => setPin(event.target.value.replace(/\D/g, '').slice(0, 4))}
          inputMode="numeric"
          type="password"
          placeholder="네 자리 숫자"
        />
        <button disabled={pin.length !== 4}>온보딩 시작</button>
      </form>
    </main>
  )
}
