import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { ApiError, loginParent, signupParent, startKakaoLogin } from '../../services/api'
import styles from './AuthPage.module.css'

export default function AuthPage() {
  const navigate = useNavigate()
  const [mode, setMode] = useState<'login' | 'signup'>('login')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [nickname, setNickname] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setError('')
    setIsLoading(true)
    try {
      if (mode === 'signup') {
        await signupParent(username, password, nickname || undefined)
      } else {
        await loginParent(username, password)
      }
      navigate('/profiles')
    } catch (error) {
      if (error instanceof ApiError) {
        setError(error.message)
      } else {
        setError(mode === 'signup' ? 'Please check your sign up info.' : 'Please check your ID or password.')
      }
    } finally {
      setIsLoading(false)
    }
  }

  const handleKakao = async () => {
    setError('')
    try {
      startKakaoLogin()
    } catch {
      setError('Please set the Kakao REST API key in .env.local.')
    }
  }

  return (
    <main className={styles.page}>
      <div className={styles.backgroundLion} aria-hidden="true">
        <img src="/images/onboarding/lion-wave.png" alt="" />
      </div>

      <section className={styles.card}>
        <header className={styles.header}>
          <img src="/images/onboarding/lion-headphones.png" alt="" />
          <h1>{mode === 'signup' ? 'Join Lion!' : 'Hello Again!'}</h1>
          <p>{mode === 'signup' ? 'Create a parent account.' : 'Welcome back, parent.'}</p>
        </header>

        <form className={styles.form} onSubmit={submit}>
          {mode === 'signup' && (
            <label htmlFor="parent-nickname">
              <span>Parent name</span>
              <input
                id="parent-nickname"
                name="nickname"
                value={nickname}
                onChange={(event) => setNickname(event.target.value)}
                placeholder="Mom or Dad"
                autoComplete="name"
              />
            </label>
          )}
          <label htmlFor="parent-username">
            <span>ID</span>
            <input
              id="parent-username"
              name="username"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              placeholder="lion_parent"
              autoCapitalize="none"
              autoComplete="username"
            />
          </label>
          <label htmlFor="parent-password">
            <span>Password</span>
            <input
              id="parent-password"
              name="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              type="password"
              placeholder="6+ characters"
              autoComplete={mode === 'signup' ? 'new-password' : 'current-password'}
            />
          </label>
          {error && <p className={styles.error}>{error}</p>}
          <button className={styles.primaryButton} disabled={isLoading || !username || !password}>
            {isLoading ? 'Loading...' : mode === 'signup' ? 'Register Now' : 'Sign In'}
          </button>
        </form>

        <button className={styles.kakaoButton} onClick={handleKakao}>
          Kakao Login
        </button>

        <button
          className={styles.switchButton}
          onClick={() => setMode(mode === 'login' ? 'signup' : 'login')}
        >
          {mode === 'login' ? 'Not a member? Register Now' : 'Already joined? Sign In'}
        </button>
      </section>
    </main>
  )
}
