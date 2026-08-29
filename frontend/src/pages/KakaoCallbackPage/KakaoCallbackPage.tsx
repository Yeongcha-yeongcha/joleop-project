import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { ApiError, completeKakaoLogin } from '../../services/api'
import styles from './KakaoCallbackPage.module.css'

const processingCodes = new Set<string>()

export default function KakaoCallbackPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [message, setMessage] = useState('카카오 로그인 중...')

  useEffect(() => {
    const code = searchParams.get('code')
    const state = searchParams.get('state')
    const error = searchParams.get('error')

    if (error) {
      setMessage('카카오 로그인이 취소되었어요.')
      window.setTimeout(() => navigate('/start'), 900)
      return
    }

    if (!code) {
      setMessage('카카오 인증 코드를 찾을 수 없어요.')
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
      setMessage('새 카카오 로그인으로 다시 시도해주세요.')
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
          setMessage('카카오 로그인에 실패했어요.')
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
