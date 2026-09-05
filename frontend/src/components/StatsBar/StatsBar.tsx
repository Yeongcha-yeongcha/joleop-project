import { useEffect, useMemo, useState } from 'react'
import type { UserStats } from '../../types'
import styles from './StatsBar.module.css'

interface Props {
  stats: UserStats
  tone?: 'light' | 'dark'
  onCustomize?: () => void
}

function StatIcon({ type }: { type: 'streak' | 'points' | 'energy' }) {
  if (type === 'streak') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path className={styles.iconFill} d="M12 3.2c2 2 2.4 3.8 1.2 5.4 1.8-.2 4.1 1.3 4.8 3.8 1 3.6-1.6 7.1-6 7.1s-7-3.5-6-7.1c.5-1.9 1.9-3.4 3.7-4 .1-1.8.8-3.6 2.3-5.2Z" />
        <path className={styles.iconShine} d="M12 14.3c1 1 .9 2.4 0 3.3-.9-.9-1-2.3 0-3.3Z" />
      </svg>
    )
  }
  if (type === 'points') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path className={styles.iconFill} d="m12 2.9 2.8 5.6 6.2.9-4.5 4.4 1.1 6.2-5.6-2.9L6.4 20l1.1-6.2L3 9.4l6.2-.9L12 2.9Z" />
        <path className={styles.iconShine} d="m10 9.1 2-3 2 3" />
      </svg>
    )
  }
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path className={styles.iconFill} d="M12 20.4S4.6 16 3 11.6C1.8 8.2 4 5.1 7.5 5.1c1.9 0 3.5 1 4.5 2.4 1-1.4 2.6-2.4 4.5-2.4 3.5 0 5.7 3.1 4.5 6.5-1.6 4.4-9 8.8-9 8.8Z" />
      <path className={styles.iconShine} d="M8 8.2c.9-.5 2-.4 2.8.3" />
    </svg>
  )
}

function formatTimer(totalSeconds: number) {
  const seconds = Math.max(0, Math.floor(totalSeconds))
  const minutes = Math.floor(seconds / 60)
  const rest = seconds % 60
  return `${minutes}:${String(rest).padStart(2, '0')}`
}

function attendanceDays(streak: number) {
  const today = new Date()
  return Array.from({ length: Math.min(Math.max(streak, 0), 30) }, (_, index) => {
    const day = new Date(today)
    day.setDate(today.getDate() - index)
    return day.toISOString().slice(0, 10)
  }).reverse()
}

function localDateIso(date: Date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function addDays(date: Date, days: number) {
  const next = new Date(date)
  next.setDate(date.getDate() + days)
  return next
}

function buildCalendarDays(attendanceDates: string[]) {
  const today = new Date()
  const monthStart = new Date(today.getFullYear(), today.getMonth(), 1)
  const gridStart = addDays(monthStart, -monthStart.getDay())
  const attended = new Set(attendanceDates)
  const currentMonth = today.getMonth()

  return Array.from({ length: 42 }, (_, index) => {
    const date = addDays(gridStart, index)
    const iso = localDateIso(date)
    const isAttended = attended.has(iso)
    const previousAttended = attended.has(localDateIso(addDays(date, -1)))
    const nextAttended = attended.has(localDateIso(addDays(date, 1)))
    return {
      iso,
      day: date.getDate(),
      isToday: iso === localDateIso(today),
      isCurrentMonth: date.getMonth() === currentMonth,
      isAttended,
      isStreakStart: isAttended && !previousAttended,
      isStreakEnd: isAttended && !nextAttended,
    }
  })
}

export default function StatsBar({ stats, tone = 'light', onCustomize }: Props) {
  const [showAttendance, setShowAttendance] = useState(false)
  const [remainingSeconds, setRemainingSeconds] = useState(
    stats.nextEnergyInSeconds ?? (stats.energyRechargeMinutes ?? 15) * 60,
  )
  const energy = stats.energy ?? Math.round(stats.xpPercent * (stats.maxEnergy ?? 5))
  const maxEnergy = stats.maxEnergy ?? 5
  const days = useMemo(() => {
    if (stats.attendanceDates?.length) {
      return [...stats.attendanceDates].sort((a, b) => a.localeCompare(b))
    }
    return attendanceDays(stats.streak)
  }, [stats.attendanceDates, stats.streak])
  const calendarDays = useMemo(() => buildCalendarDays(days), [days])
  const monthLabel = useMemo(() => (
    new Date().toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
  ), [])

  useEffect(() => {
    setRemainingSeconds(stats.nextEnergyInSeconds ?? (stats.energyRechargeMinutes ?? 15) * 60)
  }, [stats.energyRechargeMinutes, stats.nextEnergyInSeconds])

  useEffect(() => {
    if (energy >= maxEnergy || remainingSeconds <= 0) return
    const timer = window.setInterval(() => {
      setRemainingSeconds((value) => Math.max(0, value - 1))
    }, 1000)
    return () => window.clearInterval(timer)
  }, [energy, maxEnergy, remainingSeconds])

  const energyLabel = energy >= maxEnergy
    ? 'Full'
    : `+1 in ${formatTimer(remainingSeconds)}`

  return (
    <div className={`${styles.bar} ${tone === 'dark' ? styles.dark : ''}`} data-tour="stats">
      <button className={`${styles.stat} ${styles.streak}`} onClick={() => setShowAttendance(true)} aria-label="Open attendance calendar">
        <span className={styles.icon}><StatIcon type="streak" /></span>
        <span className={styles.meta}>
          <strong>{stats.streak}</strong>
          <em>Days</em>
        </span>
      </button>
      <div className={`${styles.stat} ${styles.rewards}`}>
        <span className={styles.icon}><StatIcon type="points" /></span>
        <span className={styles.meta}>
          <strong>{stats.hearts}</strong>
          <em>Stars</em>
        </span>
      </div>
      <div className={`${styles.stat} ${styles.energy}`}>
        <span className={styles.icon}><StatIcon type="energy" /></span>
        <span className={styles.meta}>
          <strong>{energy}/{maxEnergy}</strong>
          <em>Energy</em>
          <small>{energyLabel}</small>
        </span>
      </div>
      {showAttendance && (
        <div className={styles.attendanceOverlay} role="dialog" aria-modal="true" aria-label="Attendance calendar">
          <section className={styles.attendancePanel}>
            <button className={styles.closeButton} onClick={() => setShowAttendance(false)} aria-label="Close attendance calendar">x</button>
            <span>Learning Days</span>
            <h2>{stats.streak} day streak</h2>
            <strong className={styles.monthLabel}>{monthLabel}</strong>
            <div className={styles.calendarGrid}>
              {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day) => (
                <small key={day} className={styles.weekday}>{day}</small>
              ))}
              {calendarDays.map((day) => (
                <b
                  key={day.iso}
                  className={[
                    day.isCurrentMonth ? '' : styles.mutedDay,
                    day.isToday ? styles.today : '',
                    day.isAttended ? styles.attendedDay : '',
                    day.isStreakStart ? styles.streakStart : '',
                    day.isStreakEnd ? styles.streakEnd : '',
                  ].join(' ')}
                >
                  <strong>{day.day}</strong>
                </b>
              ))}
            </div>
            <p>One finished lesson marks today as a learning day.</p>
          </section>
        </div>
      )}
      {onCustomize && (
        <button className={styles.customizeButton} data-tour="customize" onClick={onCustomize} aria-label="Dress up">
          <span>🎨</span>
          <strong>Style</strong>
        </button>
      )}
    </div>
  )
}
