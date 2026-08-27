import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom'
import SplashPage from './pages/SplashPage/SplashPage'
import AuthPage from './pages/AuthPage/AuthPage'
import KakaoCallbackPage from './pages/KakaoCallbackPage/KakaoCallbackPage'
import ProfileSelectPage from './pages/ProfileSelectPage/ProfileSelectPage'
import ProfilePinPage from './pages/ProfilePinPage/ProfilePinPage'
import ProfileSetupPage from './pages/ProfileSetupPage/ProfileSetupPage'
import OnboardingPage from './pages/OnboardingPage/OnboardingPage'
import HomePage from './pages/HomePage/HomePage'
import MyPage from './pages/MyPage/MyPage'
import ReviewPage from './pages/ReviewPage/ReviewPage'
import BookChoicePage from './pages/BookChoicePage/BookChoicePage'
import LearnPage from './pages/LearnPage/LearnPage'
import './App.css'

function AnimatedRoutes() {
  const location = useLocation()

  return (
    <div className="app-shell">
      <Routes location={location} key={location.pathname}>
        <Route path="/" element={<PageWrapper><SplashPage /></PageWrapper>} />
        <Route path="/start" element={<PageWrapper><AuthPage /></PageWrapper>} />
        <Route path="/oauth/kakao/callback" element={<PageWrapper><KakaoCallbackPage /></PageWrapper>} />
        <Route path="/profiles" element={<PageWrapper><ProfileSelectPage /></PageWrapper>} />
        <Route path="/profiles/:profileId/pin" element={<PageWrapper><ProfilePinPage /></PageWrapper>} />
        <Route path="/profiles/new" element={<PageWrapper><ProfileSetupPage /></PageWrapper>} />
        <Route path="/onboarding" element={<PageWrapper><OnboardingPage /></PageWrapper>} />
        <Route path="/home" element={<PageWrapper><HomePage /></PageWrapper>} />
        <Route path="/review" element={<PageWrapper><ReviewPage /></PageWrapper>} />
        <Route path="/mypage" element={<PageWrapper slideUp><MyPage /></PageWrapper>} />
        <Route path="/books" element={<PageWrapper slideUp><BookChoicePage /></PageWrapper>} />
        <Route path="/learn/:bookId" element={<PageWrapper slideUp><LearnPage /></PageWrapper>} />
      </Routes>
    </div>
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
