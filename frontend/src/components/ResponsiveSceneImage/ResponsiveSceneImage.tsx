import { useEffect, useMemo, useState } from 'react'

interface Props {
  src: string
  alt?: string
  className?: string
}

const TABLET_QUERY = '(min-width: 700px)'

function getTabletImageUrl(src: string): string {
  const queryIndex = src.indexOf('?')
  const hashIndex = src.indexOf('#')
  const splitIndex = [queryIndex, hashIndex].filter((index) => index >= 0).sort((a, b) => a - b)[0]
  const path = splitIndex === undefined ? src : src.slice(0, splitIndex)
  const suffix = splitIndex === undefined ? '' : src.slice(splitIndex)
  const dotIndex = path.lastIndexOf('.')

  if (path.includes('-tablet')) return src
  if (dotIndex <= path.lastIndexOf('/')) return `${path}-tablet${suffix}`

  return `${path.slice(0, dotIndex)}-tablet${path.slice(dotIndex)}${suffix}`
}

function useTabletImagePreference() {
  const [prefersTablet, setPrefersTablet] = useState(() => {
    if (typeof window === 'undefined') return false
    return window.matchMedia(TABLET_QUERY).matches
  })

  useEffect(() => {
    const media = window.matchMedia(TABLET_QUERY)
    const update = () => setPrefersTablet(media.matches)
    update()
    media.addEventListener('change', update)
    return () => media.removeEventListener('change', update)
  }, [])

  return prefersTablet
}

export default function ResponsiveSceneImage({ src, alt = '', className }: Props) {
  const prefersTablet = useTabletImagePreference()
  const tabletSrc = useMemo(() => getTabletImageUrl(src), [src])
  const preferredSrc = prefersTablet ? tabletSrc : src
  const [failedSources, setFailedSources] = useState<Set<string>>(() => new Set())

  useEffect(() => {
    setFailedSources(new Set())
  }, [src])

  const currentSrc = failedSources.has(preferredSrc) ? src : preferredSrc

  return (
    <img
      src={currentSrc}
      alt={alt}
      className={className}
      onError={() => {
        setFailedSources((prev) => {
          const next = new Set(prev)
          next.add(currentSrc)
          return next
        })
      }}
    />
  )
}
