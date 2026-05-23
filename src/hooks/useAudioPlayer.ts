import { useCallback, useRef } from 'react'

export function useAudioPlayer() {
  const audioRef = useRef<HTMLAudioElement | null>(null)

  const play = useCallback((url: string): Promise<void> => {
    audioRef.current?.pause()
    const audio = new Audio(url)
    audioRef.current = audio
    return audio.play().catch(() => {})
  }, [])

  const stop = useCallback(() => {
    audioRef.current?.pause()
    audioRef.current = null
  }, [])

  return { play, stop }
}
