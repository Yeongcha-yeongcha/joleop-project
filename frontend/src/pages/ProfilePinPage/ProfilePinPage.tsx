import { useState, type FormEvent } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { loginProfile } from '../../services/api'
import styles from './ProfilePinPage.module.css'

export default function ProfilePinPage() {
  const navigate = useNavigate()
  const { profileId } = useParams()
  const [pin, setPin] = useState('')
  const [error, setError] = useState('')

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    if (!profileId || pin.length !== 4) return
    try {
      await loginProfile(Number(profileId), pin)
      navigate('/home')
    } catch {
      setError('PIN 번호를 다시 확인해 주세요.')
      setPin('')
    }
  }

  return (
    <main className={styles.page}>
      <img src="/images/onboarding/lion-magnifier.png" alt="" className={styles.lion} />
      <h1>PIN을 입력해요</h1>
      <form onSubmit={submit} className={styles.form}>
        <input
          value={pin}
          onChange={(event) => setPin(event.target.value.replace(/\D/g, '').slice(0, 4))}
          inputMode="numeric"
          type="password"
          placeholder="0000"
          autoFocus
        />
        <div className={styles.dots}>
          {[0, 1, 2, 3].map((index) => <span key={index} className={index < pin.length ? styles.filled : ''} />)}
        </div>
        {error && <p>{error}</p>}
        <button disabled={pin.length !== 4}>들어가기</button>
      </form>
    </main>
  )
}
