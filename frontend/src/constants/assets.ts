/**
 * 앱에서 사용하는 정적 에셋 경로 상수
 * 경로 변경 시 이 파일만 수정하면 됩니다.
 */

export const IMAGES = {
  // 홈 화면
  startLion: '/images/onboarding/lion-flag.png',
  homeBg: '/images/onboarding/bg-meadow-house.png',
  libraryBg: '/images/onboarding/bg-castle-path.png',
  lionReading: '/images/onboarding/lion-reading.png',
  lionWave: '/images/onboarding/lion-wave.png',
  bookBtnUnselected: '/images/BookBtn_unselected.png',
  startBtnActive: '/images/StartBtn_active.png',
  startBtnInactive: '/images/StartBtn_Inactive.png',

  // My Library
  myLibraryBg: '/images/MyLibrary_Background.png',
  bookLocked: '/images/Book_locked.png',
  bookBackgrounds: {
    dragon: '/images/home-themes/cream-book-room.png',
    lemonade: '/images/home-themes/sunset-lounge.png',
    snack: '/images/home-themes/sky-dream-room.png',
    ocean: '/images/home-themes/ocean-blue-room.png',
    forest: '/images/home-themes/forest-cozy-room.png',
    space: '/images/home-themes/space-adventure-room.png',
  },

  // 학습 화면 버튼
  nextBtnActive: '/images/NextBtn_active.png',
  recordBtnActive: '/images/RecordBtn_active.png',
  recordBtnInactive: '/images/RecordBtn_inactive.png',

  // 롤플레잉
  roleplayBg: '/images/Roleplaying_Background.png',

  // 음성 녹음
  voiceRecord: '/images/voice-record.png',
} as const

/**
 * HUD / 내비게이션 아이콘.
 * 외곽선 없는 두툼한 플랫 스타일(파스텔 2~3톤 셰이딩) 512x512 PNG 세트.
 */
export const ICONS = {
  fire: '/images/icons/fire.png',
  star: '/images/icons/star.png',
  heart: '/images/icons/heart.png',
  book: '/images/icons/book.png',
  bookmark: '/images/icons/bookmark.png',
  brain: '/images/icons/brain.png',
  pencil: '/images/icons/pencil.png',
  plant: '/images/icons/plant.png',
  bed: '/images/icons/bed.png',
  armchair: '/images/icons/armchair.png',
  goal: '/images/icons/goal.png',
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
