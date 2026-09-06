import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  deleteProfile,
  fetchCustomization,
  fetchParentReport,
  fetchUserStats,
  loginProfile,
  logoutProfile,
  saveAvatarCustomization,
  updateProfile,
  updateProfilePassword,
  usesBackendApi,
  type ChildProfile,
  type CustomizationData,
  type ParentReportData,
  type ParentReportDay,
} from '../../services/api'
import type { UserStats } from '../../types'
import {
  getProfileColor,
  getProfileImage,
  saveProfileColor,
  saveProfileImageOverride,
} from '../../utils/profileAvatar'
import styles from './MyPage.module.css'

const avatars = [
  '/images/HomeBearHands.png',
  '/images/onboarding/lion-wave.png',
  '/images/onboarding/lion-thinking.png',
  '/images/onboarding/lion-backpack.png',
  '/images/onboarding/lion-flag.png',
  '/images/onboarding/lion-reading.png',
  '/images/onboarding/lion-headphones.png',
]

const AVATAR_COST = 50
const AVATAR_UNLOCKS_KEY = 'yeongcha:avatar-unlocks'
const POINT_SPENT_KEY = 'yeongcha:avatar-points-spent'

function readNumberSet(key: string): Set<number> {
  const raw = window.localStorage.getItem(key)
  if (!raw) return new Set()
  try {
    return new Set(JSON.parse(raw) as number[])
  } catch {
    return new Set()
  }
}

function LineIcon({ type }: { type: 'profile' | 'star' | 'lock' }) {
  if (type === 'profile') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z" />
        <path d="M4.5 21a7.5 7.5 0 0 1 15 0" />
      </svg>
    )
  }
  if (type === 'star') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="m12 3 2.7 5.5 6.1.9-4.4 4.3 1 6.1L12 16.9l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9L12 3Z" />
      </svg>
    )
  }
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M7 10V8a5 5 0 0 1 10 0v2" />
      <path d="M6 10h12v10H6z" />
      <path d="M12 14v2" />
    </svg>
  )
}

function profileLevelLabel(difficulty?: ChildProfile['difficulty'] | null) {
  if (difficulty === 'INTERMEDIATE') return 'Level 2'
  if (difficulty === 'ADVANCED') return 'Level 3'
  return 'Level 1'
}

function localDateIso(date = new Date()) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function buildReportWeekDays(attendanceDates: string[] = []) {
  const today = new Date()
  const todayIso = localDateIso(today)
  const mondayOffset = (today.getDay() + 6) % 7
  const monday = new Date(today)
  monday.setDate(today.getDate() - mondayOffset)
  const attended = new Set(attendanceDates)

  return ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((label, index) => {
    const day = new Date(monday)
    day.setDate(monday.getDate() + index)
    const iso = localDateIso(day)
    return {
      date: iso,
      label,
      state: attended.has(iso) ? 'done' : iso === todayIso ? 'today' : 'next',
    }
  })
}

function emptyReportDay(date: string): ParentReportDay {
  return {
    date,
    sessionCount: 0,
    averageScore: null,
    learnedWords: [],
    learnedExpressions: [],
    strengths: [],
    needsPractice: ['Try 5 review cards or one story chapter.'],
    comment: 'No finished lesson yet.',
  }
}

export default function MyPage() {
  const navigate = useNavigate()
  const initialProfile = useMemo(() => (
    JSON.parse(window.localStorage.getItem('yeongcha:active-profile') || 'null') as ChildProfile | null
  ), [])
  const [profile, setProfile] = useState(initialProfile)
  const [nickname, setNickname] = useState(initialProfile?.nickname ?? '')
  const [isSaving, setIsSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [isGuardianUnlocked, setIsGuardianUnlocked] = useState(false)
  const [isPinModalOpen, setIsPinModalOpen] = useState(false)
  const [pinInput, setPinInput] = useState('')
  const [pinError, setPinError] = useState('')
  const [parentReport, setParentReport] = useState<ParentReportData | null>(null)
  const [isReportLoading, setIsReportLoading] = useState(false)
  const [selectedReportDate, setSelectedReportDate] = useState(localDateIso())
  const currentAvatarIndex = Math.max(0, avatars.indexOf(getProfileImage(initialProfile) ?? avatars[0]))
  const [unlockedAvatars, setUnlockedAvatars] = useState(() => {
    const saved = readNumberSet(AVATAR_UNLOCKS_KEY)
    saved.add(currentAvatarIndex)
    return saved
  })
  const [points, setPoints] = useState(0)
  const [stats, setStats] = useState<UserStats>({ streak: 0, hearts: 0, xpPercent: 0 })
  const [, setCustomization] = useState<CustomizationData | null>(null)
  const [avatarPreview, setAvatarPreview] = useState(() => getProfileImage(initialProfile))
  const [avatarColor, setAvatarColor] = useState(() => getProfileColor(initialProfile))
  const reportWeekDays = useMemo(
    () => buildReportWeekDays(parentReport?.attendanceDates ?? stats.attendanceDates),
    [parentReport?.attendanceDates, stats.attendanceDates],
  )
  const selectedReportDay = reportWeekDays.find((day) => day.date === selectedReportDate) ?? reportWeekDays[0]
  const selectedReport = parentReport?.days.find((day) => day.date === selectedReportDate)
    ?? emptyReportDay(selectedReportDay?.date ?? selectedReportDate)

  useEffect(() => {
    fetchUserStats().then((stats) => {
      const spent = Number(window.localStorage.getItem(POINT_SPENT_KEY) || '0')
      setStats(stats)
      setPoints(Math.max(0, stats.hearts - spent))
    })
    if (usesBackendApi()) {
      fetchCustomization()
        .then((data) => {
          setCustomization(data)
          setUnlockedAvatars(new Set(data.unlockedAvatarIndices))
          setPoints(data.availableStars)
          if (data.profileImageUrl !== undefined) {
            setAvatarPreview(data.profileImageUrl)
          }
          if (data.profileColor) {
            setAvatarColor(data.profileColor)
          }
        })
        .catch(() => undefined)
    }
  }, [])

  const syncProfile = (nextProfile: ChildProfile) => {
    setProfile(nextProfile)
    setNickname(nextProfile.nickname)
    setAvatarPreview(getProfileImage(nextProfile))
    setAvatarColor(getProfileColor(nextProfile))
    window.localStorage.setItem('yeongcha:active-profile', JSON.stringify(nextProfile))
  }

  const saveUnlockedAvatars = (nextUnlocked: Set<number>) => {
    setUnlockedAvatars(nextUnlocked)
    window.localStorage.setItem(AVATAR_UNLOCKS_KEY, JSON.stringify([...nextUnlocked]))
  }

  const spendPoints = (amount: number) => {
    const spent = Number(window.localStorage.getItem(POINT_SPENT_KEY) || '0') + amount
    window.localStorage.setItem(POINT_SPENT_KEY, String(spent))
    setPoints((current) => Math.max(0, current - amount))
  }

  const verifyProfilePin = async (pin: string): Promise<boolean> => {
    if (!profile) return false
    try {
      await loginProfile(profile.profileId, pin)
      return true
    } catch {
      return false
    }
  }

  const openPinModal = () => {
    if (!profile) return
    setPinInput('')
    setPinError('')
    setIsPinModalOpen(true)
  }

  const closePinModal = () => {
    setIsPinModalOpen(false)
    setPinInput('')
    setPinError('')
  }

  const submitPin = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const pin = pinInput.trim()
    if (!pin) return
    setPinError('')
    const verified = await verifyProfilePin(pin)
    if (!verified) {
      setPinError('That PIN is not right.')
      return
    }
    setIsGuardianUnlocked(true)
    setMessage('')
    closePinModal()
    if (profile) {
      setIsReportLoading(true)
      fetchParentReport(profile.profileId)
        .then((report) => {
          setParentReport(report)
          setSelectedReportDate(report.range.to)
        })
        .catch(() => setMessage('Could not load the parent report.'))
        .finally(() => setIsReportLoading(false))
    }
  }

  const changeAvatar = async (index: number) => {
    if (!profile) return
    const isUnlocked = unlockedAvatars.has(index)
    if (!isUnlocked && points < AVATAR_COST) {
      setMessage(`You need ${AVATAR_COST} stars.`)
      return
    }
    setIsSaving(true)
    setMessage('')
    try {
      if (usesBackendApi()) {
        const data = await saveAvatarCustomization({ avatarIndex: index, profileImageUrl: avatars[index] })
        setCustomization(data)
        setUnlockedAvatars(new Set(data.unlockedAvatarIndices))
        setPoints(data.availableStars)
        syncProfile({ ...profile, profileImageUrl: data.profileImageUrl ?? avatars[index] })
        setMessage(isUnlocked ? 'Your picture changed!' : 'New picture unlocked!')
        return
      }
      if (!isUnlocked) {
        const nextUnlocked = new Set(unlockedAvatars)
        nextUnlocked.add(index)
        saveUnlockedAvatars(nextUnlocked)
        spendPoints(AVATAR_COST)
      }
      const updated = await updateProfile(profile.profileId, { profileImageId: index + 1 })
      const nextProfile = { ...profile, ...updated, profileImageUrl: avatars[index] }
      saveProfileImageOverride(profile.profileId, avatars[index])
      syncProfile(nextProfile)
      setMessage(isUnlocked ? 'Your picture changed!' : 'New picture unlocked!')
    } finally {
      setIsSaving(false)
    }
  }

  const useSolidAvatar = async () => {
    if (!profile) return
    const color = getProfileColor(profile)
    if (usesBackendApi()) {
      const data = await saveAvatarCustomization({ profileImageUrl: null, profileColor: color })
      setCustomization(data)
      setPoints(data.availableStars)
    } else {
      saveProfileColor(profile.profileId, color)
      saveProfileImageOverride(profile.profileId, '')
    }
    setAvatarPreview(null)
    syncProfile({ ...profile, profileImageUrl: null })
    setAvatarColor(color)
    setMessage('Simple color is on!')
  }

  const uploadSelfie = (file: File | null) => {
    if (!profile || !file) return
    const reader = new FileReader()
    reader.onload = async () => {
      const imageUrl = String(reader.result || '')
      if (!imageUrl) return
      if (usesBackendApi()) {
        const data = await saveAvatarCustomization({ profileImageUrl: imageUrl })
        setCustomization(data)
        setPoints(data.availableStars)
      } else {
        saveProfileImageOverride(profile.profileId, imageUrl)
      }
      setAvatarPreview(imageUrl)
      syncProfile({ ...profile, profileImageUrl: imageUrl })
      setMessage('Your selfie is on!')
    }
    reader.readAsDataURL(file)
  }

  const saveNickname = async () => {
    const nextNickname = nickname.trim()
    if (!profile || !nextNickname || nextNickname === profile.nickname) return
    setIsSaving(true)
    setMessage('')
    try {
      const updated = await updateProfile(profile.profileId, { nickname: nextNickname })
      syncProfile({ ...profile, ...updated, nickname: updated.nickname ?? nextNickname })
      setMessage('Your name changed!')
    } finally {
      setIsSaving(false)
    }
  }

  const changePassword = async () => {
    if (!profile) return
    const nextPassword = window.prompt('Enter a new PIN.')
    if (!nextPassword) return
    setIsSaving(true)
    setMessage('')
    try {
      await updateProfilePassword(profile.profileId, nextPassword)
      syncProfile({ ...profile, passwordEnabled: true })
      setMessage('Your PIN changed!')
    } finally {
      setIsSaving(false)
    }
  }

  const leaveProfile = async () => {
    await logoutProfile()
    navigate('/profiles')
  }

  const removeProfile = async () => {
    if (!profile) return
    const confirmed = window.confirm(`Delete ${profile.nickname}?`)
    if (!confirmed) return
    setIsSaving(true)
    try {
      await deleteProfile(profile.profileId)
      navigate('/profiles')
    } finally {
      setIsSaving(false)
    }
  }

  const unlockGuardianPanel = async () => {
    openPinModal()
  }

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <div className={styles.currentAvatar} style={{ background: avatarColor }}>
          {avatarPreview ? <img src={avatarPreview} alt="" /> : null}
        </div>
        <div>
          <h1>My Page</h1>
          <p>{profile?.nickname ?? 'Friend'}'s profile</p>
        </div>
      </header>

      <section className={styles.card}>
        <div className={styles.sectionTitle}>
          <span><LineIcon type="profile" /></span>
          <strong>Profile</strong>
        </div>
        <label htmlFor="profile-nickname" className={styles.fieldLabel}>Name</label>
        <div className={styles.inputRow}>
          <input
            id="profile-nickname"
            value={nickname}
            onChange={(event) => setNickname(event.target.value)}
            maxLength={30}
            disabled={!profile || isSaving}
          />
          <button onClick={saveNickname} disabled={!profile || isSaving || !nickname.trim()}>
            Save
          </button>
        </div>
      </section>

      <section className={styles.card}>
        <div className={styles.sectionTitle}>
          <span><LineIcon type="star" /></span>
          <strong>Picture Shop</strong>
          <em>{points}P</em>
        </div>
        <div className={styles.avatarTools}>
          <button onClick={useSolidAvatar} disabled={!profile || isSaving}>
            Color
          </button>
          <label>
            Selfie
            <input
              type="file"
              accept="image/*"
              onChange={(event) => uploadSelfie(event.target.files?.[0] ?? null)}
              disabled={!profile || isSaving}
            />
          </label>
        </div>
        <section className={styles.avatarGrid}>
          {avatars.map((avatar, index) => {
            const isSelected = avatarPreview === avatar
            const isUnlocked = unlockedAvatars.has(index)
            return (
              <button
                key={avatar}
                onClick={() => changeAvatar(index)}
                disabled={!profile || isSaving}
                className={isSelected ? styles.selectedAvatar : ''}
              >
                <img src={avatar} alt="" />
                <span>{isUnlocked ? isSelected ? 'On' : 'Use' : `${AVATAR_COST}P`}</span>
              </button>
            )
          })}
        </section>
      </section>

      {message && <p className={styles.message}>{message}</p>}

      <section className={`${styles.card} ${styles.safePanel}`}>
        <div className={styles.sectionTitle}>
          <span><LineIcon type="lock" /></span>
          <strong>Parent Settings</strong>
        </div>
        <div className={styles.childLevelCard}>
          <span>{profile?.nickname ?? 'Friend'}'s Level</span>
          <strong>{profileLevelLabel(profile?.difficulty)}</strong>
        </div>
        <section className={styles.parentReport}>
          {isReportLoading && <p className={styles.reportLoading}>Loading report...</p>}
          {parentReport?.summary.comment && (
            <div className={styles.reportComment}>
              {parentReport.summary.comment}
            </div>
          )}
          <div className={styles.reportBlock}>
            <strong>Did Well</strong>
            <ul>
              {selectedReport.strengths.map((item) => <li key={item}>{item}</li>)}
            </ul>
          </div>
          <div className={styles.reportBlock}>
            <strong>Needs Practice</strong>
            <ul>
              {selectedReport.needsPractice.map((item) => <li key={item}>{item}</li>)}
            </ul>
          </div>
          <div className={styles.weekReport} aria-label="Weekly learning report">
            <strong>This Week</strong>
            <div>
              {reportWeekDays.map((day) => (
                <button
                  key={day.date}
                  className={`${styles.weekDay} ${styles[`weekDay_${day.state}`]} ${selectedReportDay?.date === day.date ? styles.selectedWeekDay : ''}`}
                  onClick={() => setSelectedReportDate(day.date)}
                  type="button"
                >
                  <span>{day.state === 'done' ? '✓' : ''}</span>
                  <b>{day.label}</b>
                </button>
              ))}
            </div>
          </div>
          <article className={styles.dailyFeedback}>
            <span>
              {selectedReportDay?.label ?? 'Today'} · {selectedReport.sessionCount > 0 ? `${selectedReport.sessionCount} lesson` : 'No session'}
            </span>
            <div>
              <strong>New Words</strong>
              <p>{selectedReport.learnedWords.length ? selectedReport.learnedWords.join(', ') : 'No new words saved.'}</p>
            </div>
            <div>
              <strong>Expressions</strong>
              <p>{selectedReport.learnedExpressions.length ? selectedReport.learnedExpressions.join(' / ') : 'No expression practice yet.'}</p>
            </div>
            {selectedReport.breakdown && (
              <div>
                <strong>Scores</strong>
                <p>
                  Repeat {selectedReport.breakdown.repeat ?? '-'} · Quiz {selectedReport.breakdown.description ?? '-'} · Roleplay {selectedReport.breakdown.roleplay ?? '-'}
                </p>
              </div>
            )}
            <em>{selectedReport.comment}</em>
          </article>
        </section>
        <button onClick={changePassword} disabled={!profile || isSaving}>
          Change PIN
        </button>
        <button onClick={leaveProfile} disabled={isSaving}>
          Switch User
        </button>
        <button className={styles.dangerButton} onClick={removeProfile} disabled={!profile || isSaving}>
          Delete User
        </button>
        {!isGuardianUnlocked && (
          <button className={styles.guardianOverlay} onClick={unlockGuardianPanel}>
            <span><LineIcon type="lock" /></span>
            <strong>Parent Area</strong>
            <em>Enter PIN</em>
          </button>
        )}
      </section>
      {isPinModalOpen && (
        <div className={styles.modalBackdrop} role="presentation">
          <form className={styles.pinModal} onSubmit={submitPin} role="dialog" aria-modal="true" aria-labelledby="parent-pin-title">
            <div className={styles.sectionTitle}>
              <span><LineIcon type="lock" /></span>
              <strong id="parent-pin-title">Parent Area</strong>
            </div>
            <label htmlFor="parent-pin">Enter PIN</label>
            <input
              id="parent-pin"
              autoFocus
              inputMode="numeric"
              maxLength={12}
              type="password"
              value={pinInput}
              onChange={(event) => setPinInput(event.target.value)}
            />
            {pinError && <p>{pinError}</p>}
            <div className={styles.modalActions}>
              <button type="button" onClick={closePinModal}>Cancel</button>
              <button type="submit" disabled={!pinInput.trim()}>Open</button>
            </div>
          </form>
        </div>
      )}
    </main>
  )
}
