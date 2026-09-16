import { type CSSProperties, useEffect, useMemo, useState } from 'react'
import { useAppStore } from '../../store/useAppStore'
import {
  fetchCustomization,
  savePopoCustomization,
  selectCustomizationTheme,
  usesBackendApi,
  type CustomizationData,
} from '../../services/api'
import {
  DEFAULT_HOME_BACKGROUND_THEME_ID,
  HOME_BACKGROUND_THEMES,
  type HomeBackgroundTheme,
} from '../../data/homeBackgroundThemes'
import PageHeader from '../../components/PageHeader/PageHeader'
import { ICONS } from '../../constants/assets'
import {
  POPO_ITEMS,
  resolvePopoSpots,
  type PopoCustomization,
  type PopoItem,
} from '../../data/popoItems'
import styles from './CustomizePage.module.css'

type Tab = 'background' | 'popo'
type PendingPurchase =
  | { type: 'theme'; theme: HomeBackgroundTheme }
  | { type: 'popo'; item: PopoItem }

const HOME_THEME_KEY = 'yeongcha:home-background-theme'
const THEME_UNLOCKS_KEY = 'yeongcha:home-background-theme-unlocks'
const THEME_SPENT_KEY = 'yeongcha:home-background-theme-points-spent'
const POPO_CUSTOMIZATION_KEY = 'yeongcha:popo-customization'
const POPO_UNLOCKS_KEY = 'yeongcha:popo-customization-unlocks'
const POPO_SPENT_KEY = 'yeongcha:popo-customization-points-spent'

function readJson<T>(key: string, fallback: T): T {
  try {
    return JSON.parse(window.localStorage.getItem(key) || '') as T
  } catch {
    return fallback
  }
}

function readSelectedThemeId(): string {
  return window.localStorage.getItem(HOME_THEME_KEY) || DEFAULT_HOME_BACKGROUND_THEME_ID
}

export default function CustomizePage() {
  const { userStats } = useAppStore()
  const [tab, setTab] = useState<Tab>('background')
  const [selectedThemeId, setSelectedThemeId] = useState(readSelectedThemeId)
  const [previewThemeId, setPreviewThemeId] = useState(readSelectedThemeId)
  const [themeUnlocks, setThemeUnlocks] = useState<string[]>(() => (
    readJson(THEME_UNLOCKS_KEY, [DEFAULT_HOME_BACKGROUND_THEME_ID])
  ))
  const [themeSpent, setThemeSpent] = useState(() => Number(window.localStorage.getItem(THEME_SPENT_KEY) || '0'))
  const [popoCustomization, setPopoCustomization] = useState<PopoCustomization>(() => readJson(POPO_CUSTOMIZATION_KEY, {}))
  const [previewPopo, setPreviewPopo] = useState<PopoCustomization>(() => readJson(POPO_CUSTOMIZATION_KEY, {}))
  const [popoUnlocks, setPopoUnlocks] = useState<string[]>(() => readJson(POPO_UNLOCKS_KEY, []))
  const [popoSpent, setPopoSpent] = useState(() => Number(window.localStorage.getItem(POPO_SPENT_KEY) || '0'))
  const [customization, setCustomization] = useState<CustomizationData | null>(null)
  const [message, setMessage] = useState('')
  const [pendingPurchase, setPendingPurchase] = useState<PendingPurchase | null>(null)

  const points = customization?.availableStars ?? Math.max(0, userStats.hearts - themeSpent - popoSpent)
  const previewTheme = useMemo(() => (
    HOME_BACKGROUND_THEMES.find((theme) => theme.id === previewThemeId) ?? HOME_BACKGROUND_THEMES[0]
  ), [previewThemeId])
  const unlockedThemeIds = useMemo(() => (
    new Set([DEFAULT_HOME_BACKGROUND_THEME_ID, ...themeUnlocks])
  ), [themeUnlocks])
  const isThemeOwned = (theme: HomeBackgroundTheme) => theme.owned || unlockedThemeIds.has(theme.id)
  const isPopoOwned = (item: PopoItem) => popoUnlocks.includes(item.id)

  useEffect(() => {
    if (!usesBackendApi()) return
    fetchCustomization()
      .then((data) => {
        setCustomization(data)
        setSelectedThemeId(data.selectedThemeId)
        setPreviewThemeId(data.selectedThemeId)
        setThemeUnlocks(data.unlockedThemeIds)
        setPopoCustomization(data.selectedPopo)
        setPreviewPopo(data.selectedPopo)
        setPopoUnlocks(data.unlockedPopoItemIds)
      })
      .catch(() => setMessage('Could not load style.'))
  }, [])

  const persistTheme = (theme: HomeBackgroundTheme, nextUnlocks = themeUnlocks, nextSpent = themeSpent) => {
    setSelectedThemeId(theme.id)
    setPreviewThemeId(theme.id)
    setThemeUnlocks(nextUnlocks)
    setThemeSpent(nextSpent)
    window.localStorage.setItem(HOME_THEME_KEY, theme.id)
    window.localStorage.setItem(THEME_UNLOCKS_KEY, JSON.stringify(nextUnlocks))
    window.localStorage.setItem(THEME_SPENT_KEY, String(nextSpent))
  }

  const applyCustomization = (data: CustomizationData) => {
    setCustomization(data)
    setSelectedThemeId(data.selectedThemeId)
    setPreviewThemeId(data.selectedThemeId)
    setThemeUnlocks(data.unlockedThemeIds)
    setPopoCustomization(data.selectedPopo)
    setPreviewPopo(data.selectedPopo)
    setPopoUnlocks(data.unlockedPopoItemIds)
    useAppStore.setState((state) => ({
      userStats: { ...state.userStats, hearts: data.availableStars },
    }))
  }

  const chooseTheme = async (theme: HomeBackgroundTheme) => {
    setPreviewThemeId(theme.id)
    if (isThemeOwned(theme)) {
      if (usesBackendApi()) {
        try {
          applyCustomization(await selectCustomizationTheme(theme.id))
        } catch {
          setMessage('Could not save this room.')
          return
        }
      } else {
        persistTheme(theme)
      }
      setMessage(`${theme.name} is on!`)
      return
    }
    if (points < theme.price) {
      setMessage(`You need ${theme.price} stars for ${theme.name}.`)
      return
    }
    setPendingPurchase({ type: 'theme', theme })
  }

  const buyTheme = async (theme: HomeBackgroundTheme) => {
    if (usesBackendApi()) {
      try {
        applyCustomization(await selectCustomizationTheme(theme.id))
        setMessage(`${theme.name} is yours!`)
      } catch {
        setMessage('Could not buy this room.')
      }
      return
    }
    const nextUnlocks = themeUnlocks.includes(theme.id) ? themeUnlocks : [...themeUnlocks, theme.id]
    persistTheme(theme, nextUnlocks, themeSpent + theme.price)
    setMessage(`${theme.name} is yours!`)
  }

  const applyPopoLook = async (nextPopo: PopoCustomization, successMessage: string) => {
    if (usesBackendApi()) {
      try {
        applyCustomization(await savePopoCustomization(nextPopo))
        setMessage(successMessage)
      } catch {
        setMessage('Could not save Popo look.')
      }
      return
    }
    setPopoCustomization(nextPopo)
    setPreviewPopo(nextPopo)
    window.localStorage.setItem(POPO_CUSTOMIZATION_KEY, JSON.stringify(nextPopo))
    setMessage(successMessage)
  }

  const choosePopoItem = async (item: PopoItem) => {
    if (!isPopoOwned(item)) {
      if (points < item.price) {
        setMessage(`You need ${item.price} stars for ${item.name}.`)
        return
      }
      setPendingPurchase({ type: 'popo', item })
      return
    }
    const isPreviewed = previewPopo[item.kind] === item.id
    const nextPreview = { ...previewPopo }
    if (isPreviewed) {
      delete nextPreview[item.kind]
      await applyPopoLook(nextPreview, `${item.name} is off.`)
      return
    }

    nextPreview[item.kind] = item.id
    await applyPopoLook(nextPreview, `${item.name} is on!`)
  }

  const buyPopoItem = async (item: PopoItem) => {
    const nextPopo = { ...previewPopo, [item.kind]: item.id }
    if (usesBackendApi()) {
      try {
        applyCustomization(await savePopoCustomization(nextPopo))
        setMessage(`${item.name} is yours!`)
      } catch {
        setMessage('Could not buy this item.')
      }
      return
    }
    const nextUnlocks = popoUnlocks.includes(item.id) ? popoUnlocks : [...popoUnlocks, item.id]
    const nextSpent = popoSpent + item.price
    setPopoUnlocks(nextUnlocks)
    setPopoSpent(nextSpent)
    setPopoCustomization(nextPopo)
    setPreviewPopo(nextPopo)
    window.localStorage.setItem(POPO_UNLOCKS_KEY, JSON.stringify(nextUnlocks))
    window.localStorage.setItem(POPO_SPENT_KEY, String(nextSpent))
    window.localStorage.setItem(POPO_CUSTOMIZATION_KEY, JSON.stringify(nextPopo))
    setMessage(`${item.name} is yours!`)
  }

  const confirmPurchase = async () => {
    const purchase = pendingPurchase
    if (!purchase) return
    setPendingPurchase(null)
    if (purchase.type === 'theme') {
      await buyTheme(purchase.theme)
      return
    }
    await buyPopoItem(purchase.item)
  }

  return (
    <main className={styles.page}>
      <PageHeader
        title="Style"
        backLabel="Go home"
        trailing={
          <div className={styles.points} aria-label={`${points} stars`}>
            <img src={ICONS.star} alt="" className={styles.pointsIcon} aria-hidden="true" />
            <strong>{points}</strong>
          </div>
        }
      />

      <div className={styles.body}>

      <section
        className={styles.preview}
        style={{
          '--preview-background': previewTheme.background,
          '--preview-background-size': previewTheme.backgroundSize,
          '--preview-background-position': previewTheme.backgroundPosition,
          '--room-floor': previewTheme.floor,
          '--room-floor-shade': previewTheme.floorShade,
        } as CSSProperties}
      >
        <div className={styles.previewBackdrop} aria-hidden="true" />
        <div className={styles.popoStage}>
          <img src="/images/HomePopo.webp" alt="" className={styles.previewPopo} />
          {previewPopo.hat && <span className={`${styles.popoHat} ${styles[`hat_${previewPopo.hat}`]}`} />}
          {resolvePopoSpots(previewPopo).map((item) => (
            <img key={item.id} src={item.spot} alt="" className={styles.popoSpot} aria-hidden="true" />
          ))}
        </div>
      </section>

      <div className={styles.tabs}>
        <button className={tab === 'background' ? styles.activeTab : ''} onClick={() => setTab('background')}>
          Room
        </button>
        <button className={tab === 'popo' ? styles.activeTab : ''} onClick={() => setTab('popo')}>
          Popo
        </button>
      </div>

      {tab === 'background' ? (
        <section className={styles.themeGrid} aria-label="Room themes">
          {HOME_BACKGROUND_THEMES.map((theme, index) => {
            const owned = isThemeOwned(theme)
            const selected = selectedThemeId === theme.id
            return (
              <article
                key={theme.id}
                className={`${styles.themeCard} ${selected ? styles.selected : ''}`}
              >
                <button
                  className={styles.themeButton}
                  onClick={() => chooseTheme(theme)}
                  aria-pressed={selected}
                >
                  <span
                    className={styles.thumbnail}
                    style={{
                      '--theme-thumbnail': theme.background,
                      '--theme-thumbnail-size': theme.backgroundSize,
                      '--theme-thumbnail-position': theme.backgroundPosition,
                      '--room-floor': theme.floor,
                      '--room-floor-shade': theme.floorShade,
                    } as CSSProperties}
                  >
                    {selected && <span className={styles.checkMark}>✓</span>}
                  </span>
                  <span className={styles.themeCopy}>
                    <strong>{index + 1}. {theme.name}</strong>
                    <em>{theme.description}</em>
                  </span>
                  <span className={owned ? styles.ownedBadge : styles.priceBadge}>
                    {owned ? 'Use' : (
                      <>
                        <img src={ICONS.star} alt="" className={styles.badgeIcon} aria-hidden="true" />
                        {theme.price}
                      </>
                    )}
                  </span>
                </button>
              </article>
            )
          })}
        </section>
      ) : (
        <>
          <section className={styles.popoGrid} aria-label="Popo items">
            {POPO_ITEMS.map((item) => {
              const owned = isPopoOwned(item)
              const previewed = previewPopo[item.kind] === item.id
              const equipped = popoCustomization[item.kind] === item.id
              return (
                <article key={item.id} className={`${styles.popoCard} ${previewed ? styles.selected : ''}`}>
                  <button className={styles.popoButton} onClick={() => { void choosePopoItem(item) }}>
                    {item.thumbnail ? (
                      <span className={styles.itemPreview}>
                        <img src={item.thumbnail} alt="" className={styles.itemThumb} />
                      </span>
                    ) : (
                      <span className={`${styles.itemPreview} ${styles[`item_${item.id}`]}`} />
                    )}
                    <strong>{item.name}</strong>
                    <em>
                      {previewed ? 'Off' : equipped ? 'Wearing' : owned ? 'Use' : (
                        <>
                          <img src={ICONS.star} alt="" className={styles.badgeIcon} aria-hidden="true" />
                          {item.price}
                        </>
                      )}
                    </em>
                  </button>
                </article>
              )
            })}
          </section>
        </>
      )}

      <p className={styles.message}>{message}</p>
      </div>
      {pendingPurchase && (
        <div className={styles.modalBackdrop} role="presentation">
          <section className={styles.purchaseModal} role="dialog" aria-modal="true" aria-label="Confirm purchase">
            <strong>Buy this style?</strong>
            <p>
              {pendingPurchase.type === 'theme'
                ? pendingPurchase.theme.name
                : pendingPurchase.item.name}
            </p>
            <span>
              <img src={ICONS.star} alt="" className={styles.badgeIcon} aria-hidden="true" />
              {pendingPurchase.type === 'theme'
                ? pendingPurchase.theme.price
                : pendingPurchase.item.price}
            </span>
            <div>
              <button onClick={() => setPendingPurchase(null)}>Cancel</button>
              <button onClick={() => { void confirmPurchase() }}>Buy</button>
            </div>
          </section>
        </div>
      )}
    </main>
  )
}
