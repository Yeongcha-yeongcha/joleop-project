import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchProfiles, logoutParent, type ChildProfile } from '../../services/api'
import { getProfileColor, getProfileImage } from '../../utils/profileAvatar'
import styles from './ProfileSelectPage.module.css'

function SettingsIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Z" />
      <path d="M19 13.5v-3l-2.1-.4a6.7 6.7 0 0 0-.8-1.9l1.2-1.8-2.1-2.1-1.8 1.2c-.6-.3-1.2-.6-1.9-.8L11 2.6H8l-.4 2.1c-.7.2-1.3.5-1.9.8L3.9 4.3 1.8 6.4 3 8.2c-.3.6-.6 1.2-.8 1.9L.1 10.5v3l2.1.4c.2.7.5 1.3.8 1.9l-1.2 1.8 2.1 2.1 1.8-1.2c.6.3 1.2.6 1.9.8L8 21.4h3l.4-2.1c.7-.2 1.3-.5 1.9-.8l1.8 1.2 2.1-2.1-1.2-1.8c.3-.6.6-1.2.8-1.9l2.2-.4Z" />
    </svg>
  )
}

export default function ProfileSelectPage() {
  const navigate = useNavigate()
  const [profiles, setProfiles] = useState<ChildProfile[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const parent = JSON.parse(window.localStorage.getItem('yeongcha:mock-parent') || 'null') as {
    username?: string
    nickname?: string
  } | null

  useEffect(() => {
    fetchProfiles()
      .then((data) => setProfiles(data.profiles))
      .finally(() => setIsLoading(false))
  }, [])

  const changeParentPassword = () => {
    const nextPassword = window.prompt('Type a new account password.')
    if (!nextPassword) return
    const raw = window.localStorage.getItem('yeongcha:mock-parent')
    if (raw) {
      window.localStorage.setItem('yeongcha:mock-parent', JSON.stringify({ ...JSON.parse(raw), password: nextPassword }))
    }
    window.alert('Your password changed.')
  }

  const handleLogout = async () => {
    await logoutParent()
    navigate('/start')
  }

  const handleWithdrawal = () => {
    window.alert('Account delete will work when the backend API is ready.')
  }

  return (
    <main className={styles.page}>
      <button className={styles.settingsButton} onClick={() => setSettingsOpen(true)} aria-label="Parent settings">
        <SettingsIcon />
      </button>
      <header className={styles.header}>
        <h1>Who will learn?</h1>
        <p>Pick your profile.</p>
      </header>

      <section className={styles.grid}>
        {isLoading && <p className={styles.loading}>Loading...</p>}
        {profiles.map((profile) => (
          <button key={profile.profileId} className={styles.profile} onClick={() => navigate(`/profiles/${profile.profileId}/pin`)}>
            <span
              className={styles.avatar}
              style={{ background: getProfileColor(profile) }}
            >
              {getProfileImage(profile) ? <img src={getProfileImage(profile) as string} alt="" /> : null}
            </span>
            <span>{profile.nickname}</span>
          </button>
        ))}
        <button className={styles.addProfile} onClick={() => navigate('/profiles/new')} aria-label="Add user">
          <span>+</span>
          <strong>Add User</strong>
        </button>
      </section>

      {settingsOpen && (
        <div className={styles.settingsBackdrop}>
          <section className={styles.settingsPanel} role="dialog" aria-modal="true" aria-label="Parent settings">
            <button className={styles.closeButton} onClick={() => setSettingsOpen(false)} aria-label="Close">×</button>
            <h2>Parent Settings</h2>
            <div className={styles.settingCard}>
              <strong>Basic Info</strong>
              <span>ID: {parent?.username ?? 'parent'}</span>
              <span>Name: {parent?.nickname ?? 'Parent'}</span>
            </div>
            <div className={styles.settingCard}>
              <strong>Account</strong>
              <button onClick={changeParentPassword}>Change Password</button>
              <button onClick={() => window.alert('Kakao link will work when the backend is ready.')}>
                Kakao Login
              </button>
              <button onClick={handleLogout}>Log Out</button>
              <button className={styles.dangerButton} onClick={handleWithdrawal}>Delete Account</button>
            </div>
          </section>
        </div>
      )}
    </main>
  )
}
