import { useState, type FormEvent } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { loginProfile } from '../../services/api'
import styles from './ProfilePinPage.module.css'

const keypad = ['1', '2', '3', '4', '5', '6', '7', '8', '9', 'backspace', '0', 'clear']

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

  const enterDigit = (digit: string) => {
    setError('')
    setPin((current) => (current + digit).slice(0, 4))
  }

  const pressKeypad = (key: string) => {
    if (key === 'backspace') {
      setError('')
      setPin((current) => current.slice(0, -1))
      return
    }
    if (key === 'clear') {
      setError('')
      setPin('')
      return
    }
    enterDigit(key)
  }

  return (
    <main className={styles.page}>
      <img src="/images/onboarding/lion-magnifier.png" alt="" className={styles.lion} />
      <h1>PIN을 입력해요</h1>
      <form onSubmit={submit} className={styles.form}>
        <input
          value={pin}
          onChange={(event) => {
            setError('')
            setPin(event.target.value.replace(/\D/g, '').slice(0, 4))
          }}
          inputMode="numeric"
          type="password"
          placeholder="0000"
          autoFocus
        />
        <div className={styles.dots}>
          {[0, 1, 2, 3].map((index) => <span key={index} className={index < pin.length ? styles.filled : ''} />)}
        </div>
        <div className={styles.keypad} aria-label="PIN 키패드">
          {keypad.map((key) => (
            <button
              key={key}
              type="button"
              className={key === 'clear' ? styles.utilityKey : ''}
              onClick={() => pressKeypad(key)}
              aria-label={key === 'backspace' ? '한 자리 지우기' : key === 'clear' ? '전체 지우기' : `${key} 입력`}
            >
              {key === 'backspace' ? '⌫' : key === 'clear' ? 'C' : key}
            </button>
          ))}
        </div>
        {error && <p>{error}</p>}
        <button disabled={pin.length !== 4}>들어가기</button>
      </form>
    </main>
  )
}
