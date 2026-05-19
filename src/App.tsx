import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom'
import HomePage from './pages/HomePage/HomePage'
import BookChoicePage from './pages/BookChoicePage/BookChoicePage'
import LearnPage from './pages/LearnPage/LearnPage'
import './App.css'

function AnimatedRoutes() {
  const location = useLocation()

  return (
    <div className="app-shell">
      <Routes location={location} key={location.pathname}>
        <Route path="/" element={<PageWrapper><HomePage /></PageWrapper>} />
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
