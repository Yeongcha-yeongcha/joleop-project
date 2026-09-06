import { BrowserRouter, Routes, Route, useLocation, useNavigate } from 'react-router-dom'
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
import BottomNav from './components/BottomNav/BottomNav'
import OnboardingTour from './components/OnboardingTour/OnboardingTour'
import './App.css'

function AnimatedRoutes() {
  const location = useLocation()

  return (
    <div className="app-shell">
      <AppNavButton />
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
      <AppBottomNav />
      <OnboardingTour />
    </div>
  )
}

function AppBottomNav() {
  const location = useLocation()
  const visibleRoutes = ['/home', '/review', '/mypage']
  if (!visibleRoutes.includes(location.pathname)) return null
  return <BottomNav />
}

function AppNavButton() {
  const location = useLocation()
  const navigate = useNavigate()
  const path = location.pathname
  const activeProfile = window.localStorage.getItem('yeongcha:active-profile')
  const hasParentToken = window.localStorage.getItem('yeongcha:parent-access-token')

  const hiddenRoutes = ['/', '/onboarding']
  const routesWithOwnNav = ['/home', '/customize', '/review', '/mypage', '/books']
  if (
    hiddenRoutes.includes(path) ||
    routesWithOwnNav.includes(path) ||
    path.startsWith('/books/') ||
    path.startsWith('/learn/')
  ) {
    return null
  }

  const shouldGoHome = Boolean(activeProfile) && !path.startsWith('/profiles') && path !== '/start'
  const label = shouldGoHome ? 'Go home' : 'Go back'
  const text = shouldGoHome ? '⌂' : '←'

  const fallbackPath = (() => {
    if (path === '/profiles') return '/start'
    if (path.startsWith('/profiles/')) return '/profiles'
    if (path === '/intro') return '/profiles/new'
    if (path === '/onboarding') return hasParentToken ? '/profiles' : '/start'
    return '/start'
  })()

  const handleClick = () => {
    if (shouldGoHome) {
      navigate('/home')
      return
    }
    if (window.history.length > 1) {
      navigate(-1)
      return
    }
    navigate(fallbackPath, { replace: true })
  }

  return (
    <button className="app-nav-button" onClick={handleClick} aria-label={label}>
      {text}
    </button>
  )
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
