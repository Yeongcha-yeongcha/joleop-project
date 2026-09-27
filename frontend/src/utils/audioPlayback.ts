const SILENT_WAV_DATA_URL = 'data:audio/wav;base64,UklGRigAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQQAAACAgICA'

let sharedAudio: HTMLAudioElement | null = null
let unlockInFlight = false
let unlocked = false

export function getSharedAudioElement() {
  if (!sharedAudio) {
    sharedAudio = new Audio()
    sharedAudio.preload = 'auto'
    sharedAudio.setAttribute('playsinline', '')
  }
  return sharedAudio
}

export function unlockAudioPlayback() {
  if (unlocked || unlockInFlight) return
  const audio = getSharedAudioElement()
  if (!audio.paused) return

  unlockInFlight = true
  audio.src = SILENT_WAV_DATA_URL
  const playPromise = audio.play()
  if (!playPromise) {
    unlocked = true
    unlockInFlight = false
    return
  }

  void playPromise
    .then(() => {
      unlocked = true
      if (audio.src === SILENT_WAV_DATA_URL) {
        audio.pause()
        audio.currentTime = 0
      }
    })
    .catch(() => undefined)
    .finally(() => {
      unlockInFlight = false
    })
}
