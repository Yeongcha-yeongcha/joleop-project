import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { ApiError, completeKakaoLogin } from '../../services/api'
import styles from './KakaoCallbackPage.module.css'

const processingCodes = new Set<string>()

export default function KakaoCallbackPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [message, setMessage] = useState('Kakao login is loading...')

  useEffect(() => {
    const code = searchParams.get('code')
    const state = searchParams.get('state')
    const error = searchParams.get('error')

    if (error) {
      setMessage('Kakao login was canceled.')
      window.setTimeout(() => navigate('/start'), 900)
      return
    }

    if (!code) {
      setMessage('We could not find the Kakao code.')
      window.setTimeout(() => navigate('/start'), 900)
      return
    }

    const processedKey = `yeongcha:kakao-code:${code}`
    const processedState = window.sessionStorage.getItem(processedKey)
    if (processingCodes.has(code)) {
      return
    }
    if (processedState === 'processing') {
      return
    }
    if (processedState === 'done') {
      navigate('/profiles')
      return
    }
    if (processedState === 'failed') {
      setMessage('Please try Kakao login again.')
      window.setTimeout(() => navigate('/start'), 900)
      return
    }
    processingCodes.add(code)
    window.sessionStorage.setItem(processedKey, 'processing')

    completeKakaoLogin(code, state)
      .then(() => {
        window.sessionStorage.setItem(processedKey, 'done')
        navigate('/profiles')
      })
      .catch((error: unknown) => {
        window.sessionStorage.setItem(processedKey, 'failed')
        if (error instanceof ApiError) {
          setMessage(`${error.message} (${error.code ?? error.status})`)
        } else {
          setMessage('Kakao login failed.')
        }
        window.setTimeout(() => navigate('/start'), 1800)
      })
  }, [navigate, searchParams])

  return (
    <main className={styles.page}>
      <img src="/images/onboarding/lion-headphones.png" alt="" />
      <p>{message}</p>
    </main>
  )
}
