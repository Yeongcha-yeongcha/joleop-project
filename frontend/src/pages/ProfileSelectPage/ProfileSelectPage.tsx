import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchProfiles, logoutParent, type ChildProfile } from '../../services/api'
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
    const nextPassword = window.prompt('새 계정 비밀번호를 입력해 주세요.')
    if (!nextPassword) return
    const raw = window.localStorage.getItem('yeongcha:mock-parent')
    if (raw) {
      window.localStorage.setItem('yeongcha:mock-parent', JSON.stringify({ ...JSON.parse(raw), password: nextPassword }))
    }
    window.alert('비밀번호가 변경되었어요.')
  }

  const handleLogout = async () => {
    await logoutParent()
    navigate('/start')
  }

  const handleWithdrawal = () => {
    window.alert('회원 탈퇴는 백엔드 계정 삭제 API가 연결되면 사용할 수 있어요.')
  }

  return (
    <main className={styles.page}>
      <button className={styles.settingsButton} onClick={() => setSettingsOpen(true)} aria-label="보호자 설정">
        <SettingsIcon />
      </button>
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
          </button>
        ))}
        <button className={styles.addProfile} onClick={() => navigate('/profiles/new')} aria-label="유저 추가">
          <span>+</span>
          <strong>유저 추가</strong>
        </button>
      </section>

      {settingsOpen && (
        <div className={styles.settingsBackdrop}>
          <section className={styles.settingsPanel} role="dialog" aria-modal="true" aria-label="보호자 설정">
            <button className={styles.closeButton} onClick={() => setSettingsOpen(false)} aria-label="닫기">×</button>
            <h2>보호자 설정</h2>
            <div className={styles.settingCard}>
              <strong>기본 정보</strong>
              <span>아이디: {parent?.username ?? 'parent'}</span>
              <span>이름: {parent?.nickname ?? '보호자'}</span>
            </div>
            <div className={styles.settingCard}>
              <strong>계정 관리</strong>
              <button onClick={changeParentPassword}>비밀번호 변경</button>
              <button onClick={() => window.alert('카카오 연동 관리는 백엔드 연동 상태에 맞춰 연결하면 됩니다.')}>
                카카오 연동 로그인
              </button>
              <button onClick={handleLogout}>로그아웃</button>
              <button className={styles.dangerButton} onClick={handleWithdrawal}>회원 탈퇴</button>
            </div>
          </section>
        </div>
      )}
    </main>
  )
}
