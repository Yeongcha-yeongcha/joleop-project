const AUDIO_RECORDER_OPTIONS = [
  'audio/webm;codecs=opus',
  'audio/webm',
  'audio/mp4',
  'audio/ogg;codecs=opus',
]

export function supportedAudioRecorderOptions(): MediaRecorderOptions | undefined {
  const mimeType = AUDIO_RECORDER_OPTIONS.find((type) => MediaRecorder.isTypeSupported(type))
  return mimeType ? { mimeType } : undefined
}
