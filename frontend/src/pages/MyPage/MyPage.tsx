import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  deleteProfile,
  fetchUserStats,
  loginProfile,
  logoutProfile,
  updateProfile,
  updateProfilePassword,
  type ChildProfile,
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
  const currentAvatarIndex = Math.max(0, avatars.indexOf(getProfileImage(initialProfile) ?? avatars[0]))
  const [unlockedAvatars, setUnlockedAvatars] = useState(() => {
    const saved = readNumberSet(AVATAR_UNLOCKS_KEY)
    saved.add(currentAvatarIndex)
    return saved
  })
  const [points, setPoints] = useState(0)
  const [stats, setStats] = useState<UserStats>({ streak: 0, hearts: 0, xpPercent: 0 })
  const [avatarPreview, setAvatarPreview] = useState(() => getProfileImage(initialProfile))
  const [avatarColor, setAvatarColor] = useState(() => getProfileColor(initialProfile))

  useEffect(() => {
    fetchUserStats().then((stats) => {
      const spent = Number(window.localStorage.getItem(POINT_SPENT_KEY) || '0')
      setStats(stats)
      setPoints(Math.max(0, stats.hearts - spent))
    })
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

  const verifyProfilePin = async (label: string): Promise<boolean> => {
    if (!profile) return false
    const pin = window.prompt(`Enter your PIN to ${label}.`)
    if (!pin) return false
    try {
      await loginProfile(profile.profileId, pin)
      return true
    } catch {
      setMessage('That PIN is not right.')
      return false
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

  const useSolidAvatar = () => {
    if (!profile) return
    const color = getProfileColor(profile)
    saveProfileColor(profile.profileId, color)
    saveProfileImageOverride(profile.profileId, '')
    setAvatarPreview(null)
    setAvatarColor(color)
    syncProfile({ ...profile, profileImageUrl: null })
    setMessage('Simple color is on!')
  }

  const uploadSelfie = (file: File | null) => {
    if (!profile || !file) return
    const reader = new FileReader()
    reader.onload = () => {
      const imageUrl = String(reader.result || '')
      if (!imageUrl) return
      saveProfileImageOverride(profile.profileId, imageUrl)
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
    const verified = await verifyProfilePin('open parent settings')
    if (!verified) return
    setIsGuardianUnlocked(true)
    setMessage('')
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
        <div className={styles.guardianSummary}>
          <div>
            <span>My Level</span>
            <strong>{profileLevelLabel(profile?.difficulty)}</strong>
          </div>
          <div>
            <span>Report</span>
            <strong>{Math.round(stats.xpPercent * 100)}%</strong>
          </div>
        </div>
        <div className={styles.reportGrid}>
          <div>
            <span>Days</span>
            <strong>{stats.streak}</strong>
          </div>
          <div>
            <span>Stars</span>
            <strong>{points}P</strong>
          </div>
        </div>
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
    </main>
  )
}
