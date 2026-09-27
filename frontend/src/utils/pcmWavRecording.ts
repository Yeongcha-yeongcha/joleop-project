export interface PcmWavCapture {
  stop: () => Blob
}

interface AudioSessionNavigator extends Navigator {
  audioSession?: { type: string }
}

export function prepareAppleAudioCapture() {
  const audioSession = (navigator as AudioSessionNavigator).audioSession
  if (!audioSession) return
  try {
    audioSession.type = 'auto'
  } catch {
    // Older WebKit versions do not expose a writable audio session.
  }
}

export async function startPcmWavCapture(
  stream: MediaStream,
  onLevel?: (rms: number) => void,
): Promise<PcmWavCapture> {
  const AudioContextConstructor = window.AudioContext ?? window.webkitAudioContext
  if (!AudioContextConstructor) throw new Error('Audio recording is not supported.')

  const context = new AudioContextConstructor()
  const audioSession = (navigator as AudioSessionNavigator).audioSession
  if (audioSession) {
    try {
      audioSession.type = 'play-and-record'
    } catch {
      // Microphone capture still works on versions without this session mode.
    }
  }
  const source = context.createMediaStreamSource(stream)
  // ScriptProcessor is deprecated, but it is still the most broadly supported
  // way to capture raw microphone samples across current iPad WebKit versions.
  const processor = context.createScriptProcessor(4096, 1, 1)
  const chunks: Float32Array[] = []
  let stopped = false

  processor.onaudioprocess = (event) => {
    if (stopped) return
    const input = event.inputBuffer.getChannelData(0)
    const copy = new Float32Array(input)
    chunks.push(copy)
    if (onLevel) {
      let sumOfSquares = 0
      for (const sample of copy) sumOfSquares += sample * sample
      onLevel(Math.sqrt(sumOfSquares / copy.length))
    }
  }

  source.connect(processor)
  processor.connect(context.destination)
  if (context.state === 'suspended') void context.resume().catch(() => undefined)

  return {
    stop: () => {
      if (!stopped) {
        stopped = true
        processor.onaudioprocess = null
        source.disconnect()
        processor.disconnect()
        void context.close().catch(() => undefined)
        if (audioSession) {
          try {
            audioSession.type = 'playback'
            audioSession.type = 'auto'
          } catch {
            // Ignore audio-session reset failures after the recording is complete.
          }
        }
      }
      return encodePcmWav(chunks, context.sampleRate)
    },
  }
}

function encodePcmWav(chunks: Float32Array[], sampleRate: number) {
  const sampleCount = chunks.reduce((total, chunk) => total + chunk.length, 0)
  const buffer = new ArrayBuffer(44 + sampleCount * 2)
  const view = new DataView(buffer)

  writeAscii(view, 0, 'RIFF')
  view.setUint32(4, 36 + sampleCount * 2, true)
  writeAscii(view, 8, 'WAVE')
  writeAscii(view, 12, 'fmt ')
  view.setUint32(16, 16, true)
  view.setUint16(20, 1, true)
  view.setUint16(22, 1, true)
  view.setUint32(24, sampleRate, true)
  view.setUint32(28, sampleRate * 2, true)
  view.setUint16(32, 2, true)
  view.setUint16(34, 16, true)
  writeAscii(view, 36, 'data')
  view.setUint32(40, sampleCount * 2, true)

  let offset = 44
  for (const chunk of chunks) {
    for (const sample of chunk) {
      const clamped = Math.max(-1, Math.min(1, sample))
      view.setInt16(offset, clamped < 0 ? clamped * 0x8000 : clamped * 0x7fff, true)
      offset += 2
    }
  }
  return new Blob([buffer], { type: 'audio/wav' })
}

function writeAscii(view: DataView, offset: number, value: string) {
  for (let index = 0; index < value.length; index += 1) {
    view.setUint8(offset + index, value.charCodeAt(index))
  }
}
