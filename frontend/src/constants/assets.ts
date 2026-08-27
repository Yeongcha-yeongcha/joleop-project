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
  bookSamples: {
    A: '/images/BookSample_A.png',
    B: '/images/BookSample_B.png',
    C: '/images/BookSample_C.png',
  },

  // 학습 화면 버튼
  nextBtnActive: '/images/NextBtn_active.png',
  recordBtnActive: '/images/RecordBtn_active.png',
  recordBtnInactive: '/images/RecordBtn_inactive.png',

  // 롤플레잉
  roleplayBg: '/images/Roleplaying_Background.png',
} as const
