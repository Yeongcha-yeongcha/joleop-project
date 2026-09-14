/**
 * 앱에서 사용하는 정적 에셋 경로 상수
 * 경로 변경 시 이 파일만 수정하면 됩니다.
 */

export const IMAGES = {
  // 홈 화면
  startLion: '/images/onboarding/lion-flag.webp',
  homeBg: '/images/onboarding/bg-meadow-house.webp',
  libraryBg: '/images/onboarding/bg-castle-path.webp',
  lionReading: '/images/onboarding/lion-reading.webp',
  lionWave: '/images/onboarding/lion-wave.webp',
  bookBtnUnselected: '/images/BookBtn_unselected.webp',
  startBtnActive: '/images/StartBtn_active.webp',
  startBtnInactive: '/images/StartBtn_Inactive.webp',

  // My Library
  myLibraryBg: '/images/MyLibrary_Background.webp',
  bookLocked: '/images/Book_locked.webp',
  bookBackgrounds: {
    dragon: '/images/home-themes/cream-book-room.webp',
    lemonade: '/images/home-themes/sunset-lounge.webp',
    snack: '/images/home-themes/sky-dream-room.webp',
    ocean: '/images/home-themes/ocean-blue-room.webp',
    forest: '/images/home-themes/forest-cozy-room.webp',
    space: '/images/home-themes/space-adventure-room.webp',
  },

  // 학습 화면 버튼
  nextBtnActive: '/images/NextBtn_active.webp',
  recordBtnActive: '/images/RecordBtn_active.webp',
  recordBtnInactive: '/images/RecordBtn_inactive.webp',

  // 롤플레잉
  roleplayBg: '/images/Roleplaying_Background.webp',

  // 음성 녹음
  voiceRecord: '/images/voice-record.webp',
} as const

/**
 * HUD / 내비게이션 아이콘.
 * 외곽선 없는 두툼한 플랫 스타일(파스텔 2~3톤 셰이딩) 512x512 PNG 세트.
 */
export const ICONS = {
  fire: '/images/icons/fire.webp',
  star: '/images/icons/star.webp',
  heart: '/images/icons/heart.webp',
  book: '/images/icons/book.webp',
  bookmark: '/images/icons/bookmark.webp',
  brain: '/images/icons/brain.webp',
  pencil: '/images/icons/pencil.webp',
  plant: '/images/icons/plant.webp',
  bed: '/images/icons/bed.webp',
  armchair: '/images/icons/armchair.webp',
  goal: '/images/icons/goal.webp',
} as const

/**
 * 효과음. 루트 .gitignore 가 `*.mp3` 를 무시하므로 이 파일들은 저장소에
 * 커밋되지 않는다(로컬/배포 시 별도 반영 필요).
 */
export const SOUNDS = {
  trophy: '/audio/trophy.mp3',
  star: '/audio/star.mp3',
  onboardingBgm: '/audio/onboarding-bgm.mp3',
  button: '/audio/button.mp3',
} as const
