import { useEffect, useRef } from 'react'
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom'
import SplashPage from './pages/SplashPage/SplashPage'
import AuthPage from './pages/AuthPage/AuthPage'
import KakaoCallbackPage from './pages/KakaoCallbackPage/KakaoCallbackPage'
import ServiceIntroPage from './pages/ServiceIntroPage/ServiceIntroPage'
import ProfileSelectPage from './pages/ProfileSelectPage/ProfileSelectPage'
import ProfilePinPage from './pages/ProfilePinPage/ProfilePinPage'
import ProfileSetupPage from './pages/ProfileSetupPage/ProfileSetupPage'
import OnboardingPage from './pages/OnboardingPage/OnboardingPage'
import HomePage from './pages/HomePage/HomePage'
import CustomizePage from './pages/CustomizePage/CustomizePage'
import MyPage from './pages/MyPage/MyPage'
import ReviewPage from './pages/ReviewPage/ReviewPage'
import BookChoicePage from './pages/BookChoicePage/BookChoicePage'
import ChapterSelectPage from './pages/ChapterSelectPage/ChapterSelectPage'
import LearnPage from './pages/LearnPage/LearnPage'
import OnboardingTour from './components/OnboardingTour/OnboardingTour'
import { playButtonSound } from './utils/sound'
import './App.css'

function AnimatedRoutes() {
  const location = useLocation()

  return (
    <div className="app-shell">
      <Routes location={location} key={location.pathname}>
        <Route path="/" element={<PageWrapper><SplashPage /></PageWrapper>} />
        <Route path="/start" element={<PageWrapper><AuthPage /></PageWrapper>} />
        <Route path="/oauth/kakao/callback" element={<PageWrapper><KakaoCallbackPage /></PageWrapper>} />
        <Route path="/intro" element={<PageWrapper><ServiceIntroPage /></PageWrapper>} />
        <Route path="/profiles" element={<PageWrapper><ProfileSelectPage /></PageWrapper>} />
        <Route path="/profiles/:profileId/pin" element={<PageWrapper><ProfilePinPage /></PageWrapper>} />
        <Route path="/profiles/new" element={<PageWrapper><ProfileSetupPage /></PageWrapper>} />
        <Route path="/onboarding" element={<PageWrapper><OnboardingPage /></PageWrapper>} />
        <Route path="/home" element={<PageWrapper><HomePage /></PageWrapper>} />
        <Route path="/customize" element={<PageWrapper slideUp><CustomizePage /></PageWrapper>} />
        <Route path="/review" element={<PageWrapper><ReviewPage /></PageWrapper>} />
        <Route path="/mypage" element={<PageWrapper slideUp><MyPage /></PageWrapper>} />
        <Route path="/books" element={<PageWrapper slideUp><BookChoicePage /></PageWrapper>} />
        <Route path="/books/:bookId/chapters" element={<PageWrapper slideUp><ChapterSelectPage /></PageWrapper>} />
        <Route path="/learn/:bookId" element={<PageWrapper slideUp><LearnPage /></PageWrapper>} />
      </Routes>
      <OnboardingTour />
      <ButtonSound />
    </div>
  )
}

/**
 * 학습 코스는 낭독·녹음 음성과 겹치므로 버튼 사운드를 끈다.
 * `/review` 도 시작하면 같은 학습 화면(QuizScreen, RoleplayScreen)을 띄운다.
 */
const SILENT_ROUTE_PREFIXES = ['/learn/', '/review']

/** 앱 전역 클릭/터치 기본 사운드. */
function ButtonSound() {
  const location = useLocation()
  const mutedRef = useRef(false)

  useEffect(() => {
    mutedRef.current = SILENT_ROUTE_PREFIXES.some((prefix) => location.pathname.startsWith(prefix))
  }, [location.pathname])

  useEffect(() => {
    const handlePointerDown = (event: PointerEvent) => {
      if (mutedRef.current) return
      const target = event.target
      if (!(target instanceof Element)) return
      const hit = target.closest('button, [role="button"]')
      if (!hit) return
      if (hit instanceof HTMLButtonElement && hit.disabled) return
      playButtonSound()
    }
    // 캡처 단계로 붙여 stopPropagation 을 쓰는 핸들러에도 영향받지 않게 한다.
    document.addEventListener('pointerdown', handlePointerDown, true)
    return () => document.removeEventListener('pointerdown', handlePointerDown, true)
  }, [])

  return null
}

function PageWrapper({
  children,
  slideUp,
}: {
  children: React.ReactNode
  slideUp?: boolean
}) {
  return (
    <div className={`page-enter ${slideUp ? 'page-enter-up' : 'page-enter-down'}`}>
      {children}
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AnimatedRoutes />
    </BrowserRouter>
  )
}
