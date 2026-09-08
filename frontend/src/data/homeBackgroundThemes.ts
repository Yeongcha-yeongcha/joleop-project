export interface HomeBackgroundTheme {
  id: string
  name: string
  description: string
  price: number
  /** `background-image` 에 그대로 넣는 CSS 값. */
  background: string
  /** `background-size`. 패턴 타일 크기이며 단색/그라디언트는 `cover`. */
  backgroundSize: string
  /** `background-position`. 엇갈린 무늬를 만들 때 쓴다. */
  backgroundPosition: string
  /** 캐릭터가 서는 발판 색. 벽지와 같은 계열이되 채도를 올린 톤. */
  floor: string
  /** 발판 아래쪽 음영(inset box-shadow) 색. */
  floorShade: string
  owned: boolean
  isDefault: boolean
}

export const DEFAULT_HOME_BACKGROUND_THEME_ID = 'cream-gradient'

/**
 * 방 배경 테마.
 *
 * 이전에는 `/images/home-themes/*.png` 를 참조했는데 그 파일들이 저장소에
 * 없어서(루트 .gitignore 의 `*.png` 규칙) 전부 깨진 상태였다. 그래서 이미지
 * 대신 CSS 그라디언트로 정의한다 — 파일 의존이 없고 해상도에 상관없이 선명하다.
 *
 * 색은 흰기가 많은 아주 밝은 톤으로만 쓰고, 한 테마는 한 계열 안에서
 * 바탕색·무늬색·발판색을 나눈다(바탕이 가장 밝고, 무늬가 한 톤, 발판이 가장 진한 쪽).
 */
export const HOME_BACKGROUND_THEMES: HomeBackgroundTheme[] = [
  {
    id: 'cream-gradient',
    name: 'Cream Wall',
    description: 'Warm cream gradient',
    price: 0,
    // 변경 전 홈 화면의 기본 배경(HomePage 의 --theme-fallback)을 그대로 쓴다.
    background: [
      'radial-gradient(circle at 78% 36%, rgba(255, 201, 88, 0.28), transparent 24%)',
      'linear-gradient(180deg, #fff2c3 0%, #fff8df 56%, #fffdf4 100%)',
    ].join(', '),
    backgroundSize: 'cover, cover',
    backgroundPosition: 'center, center',
    // 기본 테마는 기존 파란 발판을 그대로 유지한다.
    floor: '#8dd4ff',
    floorShade: 'rgba(27, 99, 150, 0.12)',
    owned: true,
    isDefault: true,
  },
  {
    id: 'pink-stripe',
    name: 'Pink Stripe',
    description: 'Soft pink stripes',
    price: 180,
    // 세로 줄무늬. 바탕 #fff7f9 위에 한 톤 진한 #ffe9ee.
    background: 'repeating-linear-gradient(90deg, #ffe9ee 0 15px, #fff7f9 15px 34px)',
    backgroundSize: 'auto',
    backgroundPosition: 'center',
    floor: '#ffb7c8',
    floorShade: 'rgba(163, 58, 84, 0.12)',
    owned: false,
    isDefault: false,
  },
  {
    id: 'mint-dot',
    name: 'Mint Dots',
    description: 'Soft mint polka dots',
    price: 180,
    // 엇갈린 땡땡이. 두 겹을 반 타일씩 밀어 배치한다.
    background: [
      'radial-gradient(circle, #dcf3e7 0 5.5px, transparent 6px)',
      'radial-gradient(circle, #dcf3e7 0 5.5px, transparent 6px)',
      'linear-gradient(#f4fcf8, #f4fcf8)',
    ].join(', '),
    backgroundSize: '40px 40px, 40px 40px, cover',
    backgroundPosition: '0 0, 20px 20px, center',
    floor: '#93dfbb',
    floorShade: 'rgba(26, 116, 82, 0.12)',
    owned: false,
    isDefault: false,
  },
  {
    id: 'lavender-wave',
    name: 'Lavender Wave',
    description: 'Soft lavender waves',
    price: 180,
    // 물결. 위로 볼록한 호를 타일로 반복해 물결선을 만든다.
    background: [
      'radial-gradient(circle at 50% 0, transparent 0 10px, #ebe6ff 10px 13px, transparent 13.5px)',
      'linear-gradient(#f8f6ff, #f8f6ff)',
    ].join(', '),
    backgroundSize: '26px 15px, cover',
    backgroundPosition: 'center, center',
    floor: '#c2b5f4',
    floorShade: 'rgba(76, 55, 150, 0.12)',
    owned: false,
    isDefault: false,
  },
]

/** 방 배경을 CSS 변수로 넘길 때 쓰는 값 묶음. */
export type RoomBackgroundStyle = Pick<
  HomeBackgroundTheme,
  'background' | 'backgroundSize' | 'backgroundPosition' | 'floor' | 'floorShade'
>

/** 책 표지 배경처럼 실제 이미지 URL 을 쓸 때의 값. 발판은 기본 테마를 따른다. */
export function imageBackground(url: string): RoomBackgroundStyle {
  const base = HOME_BACKGROUND_THEMES[0]
  return {
    background: `url("${url}")`,
    backgroundSize: 'cover',
    backgroundPosition: 'center',
    floor: base.floor,
    floorShade: base.floorShade,
  }
}

export function findHomeBackgroundTheme(id: string | undefined): HomeBackgroundTheme {
  return (
    HOME_BACKGROUND_THEMES.find((theme) => theme.id === id) ?? HOME_BACKGROUND_THEMES[0]
  )
}
