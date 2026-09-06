import { type CSSProperties, useEffect, useMemo, useState } from 'react'
import { useLocation } from 'react-router-dom'
import styles from './OnboardingTour.module.css'

const TOUR_PENDING_KEY = 'yeongcha:home-tour-pending'
const TOUR_DONE_PREFIX = 'yeongcha:home-tour-done:'

interface TourStep {
  selector: string
  title: string
  description: string
}

interface Rect {
  top: number
  left: number
  width: number
  height: number
}

const steps: TourStep[] = [
  {
    selector: '[data-tour="stats"]',
    title: 'Your Power',
    description: 'See your days, stars, and energy here.',
  },
  {
    selector: '[data-tour="customize"]',
    title: 'Style Popo',
    description: 'Use stars to change the room and dress up Popo.',
  },
  {
    selector: '[data-tour="book"]',
    title: 'Pick a Book',
    description: 'Tap the book card to choose a story for your level.',
  },
  {
    selector: '[data-tour="start-learning"]',
    title: 'Start',
    description: 'Read, speak, answer, and play a role in the story.',
  },
  {
    selector: '[data-tour="nav-review"]',
    title: 'Review',
    description: 'Practice words again so you remember them.',
  },
  {
    selector: '[data-tour="nav-my"]',
    title: 'Me',
    description: 'Change your profile and check your stars here.',
  },
]

function getActiveProfileKey() {
  try {
    const profile = JSON.parse(window.localStorage.getItem('yeongcha:active-profile') || 'null') as {
      profileId?: number | string
    } | null
    return String(profile?.profileId ?? 'guest')
  } catch {
    return 'guest'
  }
}

function getTargetRect(selector: string): Rect | null {
  const element = document.querySelector<HTMLElement>(selector)
  if (!element) return null
  const rect = element.getBoundingClientRect()
  return {
    top: rect.top,
    left: rect.left,
    width: rect.width,
    height: rect.height,
  }
}

export default function OnboardingTour() {
  const location = useLocation()
  const [isVisible, setIsVisible] = useState(false)
  const [stepIndex, setStepIndex] = useState(0)
  const [targetRect, setTargetRect] = useState<Rect | null>(null)
  const profileKey = useMemo(getActiveProfileKey, [location.pathname])
  const doneKey = `${TOUR_DONE_PREFIX}${profileKey}`
  const step = steps[stepIndex]

  useEffect(() => {
    if (location.pathname !== '/home') {
      setIsVisible(false)
      return
    }
    const shouldShow =
      window.localStorage.getItem(TOUR_PENDING_KEY) === 'true' &&
      window.localStorage.getItem(doneKey) !== 'true'
    setIsVisible(shouldShow)
    setStepIndex(0)
  }, [doneKey, location.pathname])

  useEffect(() => {
    if (!isVisible || !step) return

    const updateRect = () => {
      window.requestAnimationFrame(() => setTargetRect(getTargetRect(step.selector)))
    }

    updateRect()
    window.addEventListener('resize', updateRect)
    window.addEventListener('scroll', updateRect, true)
    return () => {
      window.removeEventListener('resize', updateRect)
      window.removeEventListener('scroll', updateRect, true)
    }
  }, [isVisible, step])

  if (!isVisible || !step) return null

  const finish = () => {
    window.localStorage.setItem(doneKey, 'true')
    window.localStorage.removeItem(TOUR_PENDING_KEY)
    setIsVisible(false)
  }

  const next = () => {
    if (stepIndex >= steps.length - 1) {
      finish()
      return
    }
    setStepIndex((current) => current + 1)
  }

  const safeGap = 12
  const pad = targetRect && targetRect.width > window.innerWidth - 56 ? 4 : 10
  const spotlightStyle: CSSProperties = targetRect
    ? (() => {
        const left = Math.max(safeGap, targetRect.left - pad)
        const top = Math.max(safeGap, targetRect.top - pad)
        return {
          top,
          left,
          width: Math.min(targetRect.width + pad * 2, window.innerWidth - left - safeGap),
          height: Math.min(targetRect.height + pad * 2, window.innerHeight - top - safeGap),
        }
      })()
    : {}

  const tooltipAbove = targetRect ? targetRect.top > window.innerHeight * 0.52 : false
  const tooltipStyle: CSSProperties = targetRect
    ? (() => {
        const tooltipWidth = Math.min(window.innerWidth - 32, 304)
        const maxLeft = Math.max(16, window.innerWidth - tooltipWidth - 16)
        return {
          left: Math.min(Math.max(16, targetRect.left + targetRect.width / 2 - tooltipWidth / 2), maxLeft),
        top: tooltipAbove
          ? Math.max(16, targetRect.top - 178)
          : Math.min(window.innerHeight - 186, targetRect.top + targetRect.height + 24),
        }
      })()
    : {}

  return (
    <div className={styles.tour} role="dialog" aria-modal="true" aria-labelledby="home-tour-title">
      <div className={styles.spotlight} style={spotlightStyle} />
      <section className={styles.tooltip} style={tooltipStyle}>
        <span className={styles.count}>{stepIndex + 1}/{steps.length}</span>
        <h2 id="home-tour-title">{step.title}</h2>
        <p>{step.description}</p>
        <div className={styles.actions}>
          <button className={styles.skipButton} onClick={finish}>Skip</button>
          <button className={styles.nextButton} onClick={next}>
            {stepIndex === steps.length - 1 ? 'Done' : 'Next'}
          </button>
        </div>
      </section>
    </div>
  )
}
