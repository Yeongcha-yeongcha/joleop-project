import { SOUNDS } from '../constants/assets'

/** 주어진 시간만큼 기다린다. 연출 순서를 잇는 데 쓴다. */
export function wait(ms: number) {
  return new Promise<void>((resolve) => {
    window.setTimeout(resolve, ms)
  })
}

/**
 * 재생만 시작하고 바로 반환한다. 간격은 호출하는 쪽에서 잡는다.
 * 연타해도 끊기지 않도록 매번 새 Audio 를 만든다(효과음 파일이 수 KB 로 작다).
 * 자동재생이 막힌 경우는 조용히 무시한다.
 */
export function playEffect(src: string, volume = 1) {
  const audio = new Audio(src)
  audio.volume = volume
  audio.play().catch(() => undefined)
}

/** 클릭/터치 기본 사운드. */
export function playButtonSound() {
  playEffect(SOUNDS.button, 0.5)
}

/**
 * 반복 재생 배경음악을 시작하고, 멈추는 함수를 돌려준다.
 * 자동재생이 막히면 첫 상호작용에서 한 번 더 시도한다.
 */
export function startBackgroundMusic(src: string, volume: number) {
  const audio = new Audio(src)
  audio.loop = true
  audio.volume = volume

  const tryPlay = () => {
    audio.play().catch(() => undefined)
  }
  tryPlay()
  window.addEventListener('pointerdown', tryPlay, { once: true })

  return () => {
    window.removeEventListener('pointerdown', tryPlay)
    audio.pause()
    audio.currentTime = 0
  }
}
