export function isAppleMobileDevice(device: Navigator = navigator) {
  const userAgent = device.userAgent ?? ''
  const platform = device.platform ?? ''
  const isIOSBrowser = /iPad|iPhone|iPod|CriOS|FxiOS|EdgiOS|OPiOS/i.test(userAgent)
  const isDesktopModeIPad = device.maxTouchPoints > 1
    && /Macintosh|MacIntel|Mac OS X/i.test(`${platform} ${userAgent}`)
  return isIOSBrowser || isDesktopModeIPad
}
