export interface HomeBackgroundTheme {
  id: string
  name: string
  description: string
  price: number
  thumbnail: string
  background: string
  owned: boolean
  isDefault: boolean
}

const HOME_THEME_ASSET_BASE = '/images/home-themes'

export const DEFAULT_HOME_BACKGROUND_THEME_ID = 'cream-book-room'

export const HOME_BACKGROUND_THEMES: HomeBackgroundTheme[] = [
  {
    id: 'cream-book-room',
    name: 'Cream Room',
    description: 'A warm and cozy room',
    price: 0,
    thumbnail: `${HOME_THEME_ASSET_BASE}/cream-book-room.png`,
    background: `${HOME_THEME_ASSET_BASE}/cream-book-room.png`,
    owned: true,
    isDefault: true,
  },
  {
    id: 'sky-dream-room',
    name: 'Sky Room',
    description: 'A bright room with clouds',
    price: 250,
    thumbnail: `${HOME_THEME_ASSET_BASE}/sky-dream-room.png`,
    background: `${HOME_THEME_ASSET_BASE}/sky-dream-room.png`,
    owned: false,
    isDefault: false,
  },
  {
    id: 'forest-cozy-room',
    name: 'Forest Room',
    description: 'A soft green forest room',
    price: 250,
    thumbnail: `${HOME_THEME_ASSET_BASE}/forest-cozy-room.png`,
    background: `${HOME_THEME_ASSET_BASE}/forest-cozy-room.png`,
    owned: false,
    isDefault: false,
  },
  {
    id: 'sunset-lounge',
    name: 'Sunset Room',
    description: 'A warm sunset room',
    price: 250,
    thumbnail: `${HOME_THEME_ASSET_BASE}/sunset-lounge.png`,
    background: `${HOME_THEME_ASSET_BASE}/sunset-lounge.png`,
    owned: false,
    isDefault: false,
  },
  {
    id: 'night-star-room',
    name: 'Star Room',
    description: 'A room with stars and moon',
    price: 250,
    thumbnail: `${HOME_THEME_ASSET_BASE}/night-star-room.png`,
    background: `${HOME_THEME_ASSET_BASE}/night-star-room.png`,
    owned: false,
    isDefault: false,
  },
  {
    id: 'ocean-blue-room',
    name: 'Ocean Room',
    description: 'A cool blue ocean room',
    price: 250,
    thumbnail: `${HOME_THEME_ASSET_BASE}/ocean-blue-room.png`,
    background: `${HOME_THEME_ASSET_BASE}/ocean-blue-room.png`,
    owned: false,
    isDefault: false,
  },
  {
    id: 'rainbow-room',
    name: 'Rainbow Room',
    description: 'A happy pastel room',
    price: 250,
    thumbnail: `${HOME_THEME_ASSET_BASE}/rainbow-room.png`,
    background: `${HOME_THEME_ASSET_BASE}/rainbow-room.png`,
    owned: false,
    isDefault: false,
  },
  {
    id: 'mint-garden-room',
    name: 'Mint Garden',
    description: 'A room with plants',
    price: 250,
    thumbnail: `${HOME_THEME_ASSET_BASE}/mint-garden-room.png`,
    background: `${HOME_THEME_ASSET_BASE}/mint-garden-room.png`,
    owned: false,
    isDefault: false,
  },
  {
    id: 'winter-snow-room',
    name: 'Snow Room',
    description: 'A soft winter room',
    price: 250,
    thumbnail: `${HOME_THEME_ASSET_BASE}/winter-snow-room.png`,
    background: `${HOME_THEME_ASSET_BASE}/winter-snow-room.png`,
    owned: false,
    isDefault: false,
  },
  {
    id: 'space-adventure-room',
    name: 'Space Room',
    description: 'A room for space dreams',
    price: 250,
    thumbnail: `${HOME_THEME_ASSET_BASE}/space-adventure-room.png`,
    background: `${HOME_THEME_ASSET_BASE}/space-adventure-room.png`,
    owned: false,
    isDefault: false,
  },
]
