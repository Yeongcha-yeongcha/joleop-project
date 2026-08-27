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
import BottomNav from '../../components/BottomNav/BottomNav'
import type { UserStats } from '../../types'
import styles from './MyPage.module.css'

const avatars = [
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
  if (difficulty === 'INTERMEDIATE') return '2단계'
  if (difficulty === 'ADVANCED') return '3단계'
  return '1단계'
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
  const currentAvatarIndex = Math.max(0, avatars.indexOf(initialProfile?.profileImageUrl ?? avatars[0]))
  const [unlockedAvatars, setUnlockedAvatars] = useState(() => {
    const saved = readNumberSet(AVATAR_UNLOCKS_KEY)
    saved.add(currentAvatarIndex)
    return saved
  })
  const [points, setPoints] = useState(0)
  const [stats, setStats] = useState<UserStats>({ streak: 0, hearts: 0, xpPercent: 0 })

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
    const pin = window.prompt(`${label}하려면 현재 유저 PIN을 입력해 주세요.`)
    if (!pin) return false
    try {
      await loginProfile(profile.profileId, pin)
      return true
    } catch {
      setMessage('PIN이 맞지 않아요.')
      return false
    }
  }

  const changeAvatar = async (index: number) => {
    if (!profile) return
    const isUnlocked = unlockedAvatars.has(index)
    if (!isUnlocked && points < AVATAR_COST) {
      setMessage(`포인트 ${AVATAR_COST}개가 필요해요.`)
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
      syncProfile({ ...profile, ...updated, profileImageUrl: avatars[index] })
      setMessage(isUnlocked ? '프로필 사진이 변경되었어요.' : '새 프로필 사진을 열었어요!')
    } finally {
      setIsSaving(false)
    }
  }

  const saveNickname = async () => {
    const nextNickname = nickname.trim()
    if (!profile || !nextNickname || nextNickname === profile.nickname) return
    setIsSaving(true)
    setMessage('')
    try {
      const updated = await updateProfile(profile.profileId, { nickname: nextNickname })
      syncProfile({ ...profile, ...updated, nickname: updated.nickname ?? nextNickname })
      setMessage('별명이 변경되었어요.')
    } finally {
      setIsSaving(false)
    }
  }

  const changePassword = async () => {
    if (!profile) return
    const nextPassword = window.prompt('새 프로필 비밀번호를 입력해 주세요.')
    if (!nextPassword) return
    setIsSaving(true)
    setMessage('')
    try {
      await updateProfilePassword(profile.profileId, nextPassword)
      syncProfile({ ...profile, passwordEnabled: true })
      setMessage('비밀번호가 변경되었어요.')
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
    const confirmed = window.confirm(`${profile.nickname} 유저를 삭제할까요?`)
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
    const verified = await verifyProfilePin('보호자 설정을 확인')
    if (!verified) return
    setIsGuardianUnlocked(true)
    setMessage('')
  }

  return (
    <main className={styles.page}>
      <button className={styles.backButton} onClick={() => navigate('/home')}>←</button>
      <header className={styles.header}>
        <div className={styles.currentAvatar}>
          <img src={profile?.profileImageUrl ?? avatars[0]} alt="" />
        </div>
        <div>
          <h1>My Page</h1>
          <p>{profile?.nickname ?? '친구'}의 프로필</p>
        </div>
      </header>

      <section className={styles.card}>
        <div className={styles.sectionTitle}>
          <span><LineIcon type="profile" /></span>
          <strong>프로필 설정</strong>
        </div>
        <label htmlFor="profile-nickname" className={styles.fieldLabel}>별명</label>
        <div className={styles.inputRow}>
          <input
            id="profile-nickname"
            value={nickname}
            onChange={(event) => setNickname(event.target.value)}
            maxLength={30}
            disabled={!profile || isSaving}
          />
          <button onClick={saveNickname} disabled={!profile || isSaving || !nickname.trim()}>
            저장
          </button>
        </div>
      </section>

      <section className={styles.card}>
        <div className={styles.sectionTitle}>
          <span><LineIcon type="star" /></span>
          <strong>프로필 사진 상점</strong>
          <em>{points}P</em>
        </div>
        <section className={styles.avatarGrid}>
          {avatars.map((avatar, index) => {
            const isSelected = profile?.profileImageUrl === avatar
            const isUnlocked = unlockedAvatars.has(index)
            return (
              <button
                key={avatar}
                onClick={() => changeAvatar(index)}
                disabled={!profile || isSaving}
                className={isSelected ? styles.selectedAvatar : ''}
              >
                <img src={avatar} alt="" />
                <span>{isUnlocked ? isSelected ? '사용중' : '변경' : `${AVATAR_COST}P`}</span>
              </button>
            )
          })}
        </section>
      </section>

      {message && <p className={styles.message}>{message}</p>}

      <section className={`${styles.card} ${styles.safePanel}`}>
        <div className={styles.sectionTitle}>
          <span><LineIcon type="lock" /></span>
          <strong>보호자 확인 설정</strong>
        </div>
        <div className={styles.guardianSummary}>
          <div>
            <span>아이 레벨</span>
            <strong>{profileLevelLabel(profile?.difficulty)}</strong>
          </div>
          <div>
            <span>학습 리포트</span>
            <strong>{Math.round(stats.xpPercent * 100)}%</strong>
          </div>
        </div>
        <div className={styles.reportGrid}>
          <div>
            <span>연속 학습</span>
            <strong>{stats.streak}일</strong>
          </div>
          <div>
            <span>보유 포인트</span>
            <strong>{points}P</strong>
          </div>
        </div>
        <button onClick={changePassword} disabled={!profile || isSaving}>
          비밀번호 변경
        </button>
        <button onClick={leaveProfile} disabled={isSaving}>
          유저 선택으로 이동
        </button>
        <button className={styles.dangerButton} onClick={removeProfile} disabled={!profile || isSaving}>
          유저 삭제
        </button>
        {!isGuardianUnlocked && (
          <button className={styles.guardianOverlay} onClick={unlockGuardianPanel}>
            <span><LineIcon type="lock" /></span>
            <strong>보호자 영역</strong>
            <em>PIN 입력 후 보기</em>
          </button>
        )}
      </section>
      <BottomNav />
    </main>
  )
}
