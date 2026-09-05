import type { ChildProfile } from '../services/api'

const PROFILE_COLORS_KEY = 'yeongcha:profile-colors'
const PROFILE_IMAGE_OVERRIDES_KEY = 'yeongcha:profile-image-overrides'

export const profileColors = [
  '#ffcf6a',
  '#ff9ab1',
  '#9fe47c',
  '#8ed8ff',
  '#c6a7ff',
  '#ffb36d',
]

function readRecord(key: string): Record<string, string> {
  try {
    return JSON.parse(window.localStorage.getItem(key) || '{}')
  } catch {
    return {}
  }
}

function writeRecord(key: string, value: Record<string, string>) {
  window.localStorage.setItem(key, JSON.stringify(value))
}

export function randomProfileColor(): string {
  return profileColors[Math.floor(Math.random() * profileColors.length)]
}

export function saveProfileColor(profileId: number, color: string) {
  const colors = readRecord(PROFILE_COLORS_KEY)
  colors[String(profileId)] = color
  writeRecord(PROFILE_COLORS_KEY, colors)
}

export function getProfileColor(profile: Pick<ChildProfile, 'profileId' | 'nickname'> | null): string {
  if (!profile) return profileColors[0]
  const colors = readRecord(PROFILE_COLORS_KEY)
  const saved = colors[String(profile.profileId)]
  if (saved) return saved
  const seed = [...profile.nickname].reduce((sum, char) => sum + char.charCodeAt(0), profile.profileId)
  const color = profileColors[Math.abs(seed) % profileColors.length]
  saveProfileColor(profile.profileId, color)
  return color
}

export function saveProfileImageOverride(profileId: number, imageUrl: string) {
  const images = readRecord(PROFILE_IMAGE_OVERRIDES_KEY)
  images[String(profileId)] = imageUrl
  writeRecord(PROFILE_IMAGE_OVERRIDES_KEY, images)
}

export function getProfileImage(profile: ChildProfile | null): string | null {
  if (!profile) return null
  const images = readRecord(PROFILE_IMAGE_OVERRIDES_KEY)
  return images[String(profile.profileId)] ?? profile.profileImageUrl ?? null
}
