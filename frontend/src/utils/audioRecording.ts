import { isAppleMobileDevice } from './appleDevice'

const AUDIO_RECORDER_OPTIONS = [
  'audio/webm;codecs=opus',
  'audio/webm',
  'audio/mp4',
  'audio/ogg;codecs=opus',
]

const APPLE_AUDIO_RECORDER_OPTIONS = [
  'audio/mp4',
  'audio/webm;codecs=opus',
  'audio/webm',
]

export function supportedAudioRecorderOptions(): MediaRecorderOptions | undefined {
  const candidates = isAppleMobileDevice()
    ? APPLE_AUDIO_RECORDER_OPTIONS
    : AUDIO_RECORDER_OPTIONS
  const mimeType = candidates.find((type) => MediaRecorder.isTypeSupported(type))
  return mimeType ? { mimeType } : undefined
}
