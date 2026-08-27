import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchProfiles, type ChildProfile } from '../../services/api'
import styles from './ProfileSelectPage.module.css'

export default function ProfileSelectPage() {
  const navigate = useNavigate()
  const [profiles, setProfiles] = useState<ChildProfile[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    fetchProfiles()
      .then((data) => setProfiles(data.profiles))
      .finally(() => setIsLoading(false))
  }, [])

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <h1>누가 배울까요?</h1>
        <p>프로필을 선택해 주세요</p>
      </header>

      <section className={styles.grid}>
        {isLoading && <p className={styles.loading}>불러오는 중...</p>}
        {profiles.map((profile) => (
          <button key={profile.profileId} className={styles.profile} onClick={() => navigate(`/profiles/${profile.profileId}/pin`)}>
            <span className={styles.avatar}>
              <img src={profile.profileImageUrl ?? '/images/onboarding/lion-wave.png'} alt="" />
            </span>
            <span>{profile.nickname}</span>
            {profile.difficulty && <small>Level {profile.difficulty === 'BEGINNER' ? 1 : profile.difficulty === 'INTERMEDIATE' ? 2 : 3}</small>}
          </button>
        ))}
        <button className={styles.addProfile} onClick={() => navigate('/profiles/new')} aria-label="유저 추가">
          <span>+</span>
          <strong>유저 추가</strong>
        </button>
      </section>
    </main>
  )
}
