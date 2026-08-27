import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { updateProfile, type ChildProfile } from '../../services/api'
import BottomNav from '../../components/BottomNav/BottomNav'
import styles from './MyPage.module.css'

const avatars = [
  '/images/onboarding/lion-wave.png',
  '/images/onboarding/lion-thinking.png',
  '/images/onboarding/lion-backpack.png',
  '/images/onboarding/lion-flag.png',
  '/images/onboarding/lion-reading.png',
  '/images/onboarding/lion-headphones.png',
]

export default function MyPage() {
  const navigate = useNavigate()
  const initialProfile = useMemo(() => (
    JSON.parse(window.localStorage.getItem('yeongcha:active-profile') || 'null') as ChildProfile | null
  ), [])
  const [profile, setProfile] = useState(initialProfile)

  const changeAvatar = async (index: number) => {
    if (!profile) return
    const updated = await updateProfile(profile.profileId, { profileImageId: index + 1 })
    const nextProfile = { ...profile, profileImageUrl: updated.profileImageUrl ?? avatars[index] }
    setProfile(nextProfile)
    window.localStorage.setItem('yeongcha:active-profile', JSON.stringify(nextProfile))
  }

  return (
    <main className={styles.page}>
      <button className={styles.backButton} onClick={() => navigate('/home')}>←</button>
      <h1>My Page</h1>
      <p>{profile?.nickname ?? '친구'}의 프로필</p>

      <div className={styles.currentAvatar}>
        <img src={profile?.profileImageUrl ?? avatars[0]} alt="" />
      </div>

      <section className={styles.avatarGrid}>
        {avatars.map((avatar, index) => (
          <button key={avatar} onClick={() => changeAvatar(index)}>
            <img src={avatar} alt="" />
          </button>
        ))}
      </section>
      <BottomNav />
    </main>
  )
}
