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
  const [usernameTouched, setUsernameTouched] = useState(false)
  const [passwordTouched, setPasswordTouched] = useState(false)
  const isSignup = mode === 'signup'
  const usernameChecks = [
    { valid: username.length >= 6, message: '아이디는 6자리 이상이어야 해요.' },
    { valid: /^[A-Za-z0-9_]*$/.test(username), message: '아이디는 영문, 숫자, 밑줄(_)만 사용할 수 있어요.' },
  ]
  const passwordChecks = [
    { valid: password.length >= 6, message: '비밀번호는 6자리 이상이어야 해요.' },
    { valid: /[A-Za-z]/.test(password), message: '비밀번호에 영문자를 포함해 주세요.' },
    { valid: /\d/.test(password), message: '비밀번호에 숫자를 포함해 주세요.' },
    { valid: /[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?`~]/.test(password), message: '비밀번호에 특수문자를 포함해 주세요.' },
  ]
  const usernameValid = usernameChecks.every((check) => check.valid)
  const passwordValid = passwordChecks.every((check) => check.valid)
  const signupValid = usernameValid && passwordValid
  const showUsernameValidation = isSignup && usernameTouched && username.length > 0
  const showPasswordValidation = isSignup && passwordTouched && password.length > 0

  const validationMessage = (checks: Array<{ valid: boolean; message: string }>) => (
    checks.find((check) => !check.valid)?.message ?? '사용할 수 있어요.'
  )

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setError('')
    setIsLoading(true)
    try {
      if (isSignup) {
        if (!signupValid) {
          setError('아이디와 비밀번호 조건을 확인해 주세요.')
          return
        }
        await signupParent(username, password, nickname || undefined)
      } else {
        await loginParent(username, password)
      }
      navigate('/profiles')
    } catch (error) {
      if (error instanceof ApiError) {
        setError(error.message)
      } else {
        setError(isSignup ? 'Please check your sign up info.' : 'Please check your ID or password.')
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
          {isSignup && (
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
            <div className={styles.inputWrap}>
              <input
                id="parent-username"
                name="username"
                value={username}
                onChange={(event) => {
                  setUsername(event.target.value)
                  setUsernameTouched(true)
                }}
                placeholder="lion_parent"
                autoCapitalize="none"
                autoComplete="username"
                aria-invalid={isSignup ? !usernameValid : undefined}
              />
              {showUsernameValidation && (
                <b className={`${styles.validationIcon} ${usernameValid ? styles.valid : styles.invalid}`}>
                  {usernameValid ? 'O' : 'X'}
                </b>
              )}
            </div>
            {showUsernameValidation && (
              <em className={`${styles.validationText} ${usernameValid ? styles.valid : styles.invalid}`}>
                {validationMessage(usernameChecks)}
              </em>
            )}
          </label>
          <label htmlFor="parent-password">
            <span>Password</span>
            <div className={styles.inputWrap}>
              <input
                id="parent-password"
                name="password"
                value={password}
                onChange={(event) => {
                  setPassword(event.target.value)
                  setPasswordTouched(true)
                }}
                type="password"
                placeholder="6+ characters"
                autoComplete={isSignup ? 'new-password' : 'current-password'}
                aria-invalid={isSignup ? !passwordValid : undefined}
              />
              {showPasswordValidation && (
                <b className={`${styles.validationIcon} ${passwordValid ? styles.valid : styles.invalid}`}>
                  {passwordValid ? 'O' : 'X'}
                </b>
              )}
            </div>
            {showPasswordValidation && (
              <em className={`${styles.validationText} ${passwordValid ? styles.valid : styles.invalid}`}>
                {validationMessage(passwordChecks)}
              </em>
            )}
          </label>
          {error && <p className={styles.error}>{error}</p>}
          <button className={styles.primaryButton} disabled={isLoading || !username || !password || (isSignup && !signupValid)}>
            {isLoading ? 'Loading...' : isSignup ? 'Register Now' : 'Sign In'}
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
