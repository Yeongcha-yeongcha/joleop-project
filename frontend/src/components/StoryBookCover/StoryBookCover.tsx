import type { Book } from '../../types'
import { IMAGES } from '../../constants/assets'
import { resolveBookCover, resolveBookSceneFallbacks, resolveBookSceneImage } from '../../utils/bookAssets'
import styles from './StoryBookCover.module.css'

interface Props {
  book?: Book | null
  className?: string
  variant?: 'library' | 'held' | 'current'
}

export default function StoryBookCover({ book, className = '', variant = 'library' }: Props) {
  if (!book) {
    return <img src={IMAGES.bookBtnUnselected} alt="" className={className} />
  }

  const fallbacks = resolveBookSceneFallbacks(book)

  return (
    <span className={[styles.cover, styles[variant], className].filter(Boolean).join(' ')}>
      <img src={resolveBookCover(book)} className={styles.base} alt="" />
      <span className={styles.sceneFrame}>
        <img
          src={resolveBookSceneImage(book)}
          className={styles.scene}
          alt=""
          onError={(event) => {
            const nextIndex = Number(event.currentTarget.dataset.fallbackIndex ?? '0')
            const nextSrc = fallbacks[nextIndex]
            if (nextSrc) {
              event.currentTarget.dataset.fallbackIndex = String(nextIndex + 1)
              event.currentTarget.src = nextSrc
              return
            }
            event.currentTarget.hidden = true
          }}
        />
      </span>
    </span>
  )
}
