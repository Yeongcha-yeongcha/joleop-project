import { type CSSProperties, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
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
import styles from './CustomizePage.module.css'

type Tab = 'background' | 'popo'

interface PopoItem {
  id: string
  name: string
  kind: 'hat' | 'glasses' | 'necklace' | 'outfit'
  price: number
}

interface PopoCustomization {
  hat?: string
  glasses?: string
  necklace?: string
  outfit?: string
}

const HOME_THEME_KEY = 'yeongcha:home-background-theme'
const THEME_UNLOCKS_KEY = 'yeongcha:home-background-theme-unlocks'
const THEME_SPENT_KEY = 'yeongcha:home-background-theme-points-spent'
const POPO_CUSTOMIZATION_KEY = 'yeongcha:popo-customization'
const POPO_UNLOCKS_KEY = 'yeongcha:popo-customization-unlocks'
const POPO_SPENT_KEY = 'yeongcha:popo-customization-points-spent'

const popoItems: PopoItem[] = [
  { id: 'sun-cap', name: 'Sun Hat', kind: 'hat', price: 80 },
  { id: 'star-cap', name: 'Star Hat', kind: 'hat', price: 120 },
  { id: 'round-glasses', name: 'Round Glasses', kind: 'glasses', price: 90 },
  { id: 'cool-glasses', name: 'Cool Glasses', kind: 'glasses', price: 130 },
  { id: 'star-necklace', name: 'Star Necklace', kind: 'necklace', price: 90 },
  { id: 'heart-necklace', name: 'Heart Necklace', kind: 'necklace', price: 110 },
  { id: 'blue-hoodie', name: 'Blue Hoodie', kind: 'outfit', price: 150 },
  { id: 'orange-vest', name: 'Orange Vest', kind: 'outfit', price: 150 },
]

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
  const navigate = useNavigate()
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

  const points = customization?.availableStars ?? Math.max(0, userStats.hearts - themeSpent - popoSpent)
  const previewTheme = useMemo(() => (
    HOME_BACKGROUND_THEMES.find((theme) => theme.id === previewThemeId) ?? HOME_BACKGROUND_THEMES[0]
  ), [previewThemeId])
  const unlockedThemeIds = useMemo(() => (
    new Set([DEFAULT_HOME_BACKGROUND_THEME_ID, ...themeUnlocks])
  ), [themeUnlocks])
  const isThemeOwned = (theme: HomeBackgroundTheme) => theme.owned || unlockedThemeIds.has(theme.id)
  const isPopoOwned = (item: PopoItem) => popoUnlocks.includes(item.id)
  const previewItems = popoItems.filter((item) => previewPopo[item.kind] === item.id)
  const previewCost = previewItems.reduce((sum, item) => sum + (isPopoOwned(item) ? 0 : item.price), 0)

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

  const choosePopoItem = (item: PopoItem) => {
    const isPreviewed = previewPopo[item.kind] === item.id
    const nextPreview = { ...previewPopo }
    if (isPreviewed) {
      delete nextPreview[item.kind]
      setPreviewPopo(nextPreview)
      setMessage(`${item.name} is off in preview.`)
      return
    }

    nextPreview[item.kind] = item.id
    setPreviewPopo(nextPreview)
    setMessage(isPopoOwned(item)
      ? `${item.name} is in preview. Tap Save Look to wear it at home.`
      : `${item.name} is preview only. Buy it with Save Look to wear it at home.`)
  }

  const savePopoLook = async () => {
    if (previewCost > points) {
      setMessage(`You need ${previewCost} stars to save this look.`)
      return
    }
    if (usesBackendApi()) {
      try {
        applyCustomization(await savePopoCustomization(previewPopo))
        setMessage(previewCost > 0 ? `Bought for ${previewCost} stars. Popo will wear this at home!` : 'Popo will wear this at home!')
      } catch {
        setMessage('Could not save Popo look.')
      }
      return
    }
    const nextUnlocks = Array.from(new Set([...popoUnlocks, ...previewItems.map((item) => item.id)]))
    const nextSpent = popoSpent + previewCost
    setPopoUnlocks(nextUnlocks)
    setPopoSpent(nextSpent)
    window.localStorage.setItem(POPO_UNLOCKS_KEY, JSON.stringify(nextUnlocks))
    window.localStorage.setItem(POPO_SPENT_KEY, String(nextSpent))
    setPopoCustomization(previewPopo)
    window.localStorage.setItem(POPO_CUSTOMIZATION_KEY, JSON.stringify(previewPopo))
    setMessage(previewCost > 0 ? `Bought for ${previewCost} stars. Popo will wear this at home!` : 'Popo will wear this at home!')
  }

  const resetPopoPreview = () => {
    setPreviewPopo(popoCustomization)
    setMessage('Preview is back to saved look.')
  }

  const clearPopoKind = (kind: PopoItem['kind']) => {
    const next = { ...previewPopo }
    delete next[kind]
    setPreviewPopo(next)
    setMessage('Popo item is off in preview.')
  }

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <button className={styles.backButton} onClick={() => navigate('/home')} aria-label="Go home">
          ←
        </button>
        <div className={styles.titleGroup}>
          <h1>Style</h1>
          <p>Make the room and Popo fun</p>
        </div>
        <div className={styles.points} aria-label={`${points} stars`}>
          <span>★</span>
          <strong>{points}</strong>
        </div>
      </header>

      <section
        className={`${styles.preview} ${styles[`theme_${previewTheme.id}`] ?? ''}`}
        style={{ '--preview-background': `url("${previewTheme.background}")` } as CSSProperties}
      >
        <div className={styles.previewBackdrop} aria-hidden="true" />
        <div className={styles.popoStage}>
          <img src="/images/HomeBearHands.png" alt="" className={styles.previewPopo} />
          {previewPopo.outfit && <span className={`${styles.popoOutfit} ${styles[`outfit_${previewPopo.outfit}`]}`} />}
          {previewPopo.hat && <span className={`${styles.popoHat} ${styles[`hat_${previewPopo.hat}`]}`} />}
          {previewPopo.glasses && <span className={`${styles.popoGlasses} ${styles[`glasses_${previewPopo.glasses}`]}`} />}
          {previewPopo.necklace && <span className={`${styles.popoNecklace} ${styles[`necklace_${previewPopo.necklace}`]}`} />}
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
                className={`${styles.themeCard} ${styles[`theme_${theme.id}`] ?? ''} ${selected ? styles.selected : ''}`}
              >
                <button
                  className={styles.themeButton}
                  onClick={() => chooseTheme(theme)}
                  aria-pressed={selected}
                >
                  <span
                    className={styles.thumbnail}
                    style={{ '--theme-thumbnail': `url("${theme.thumbnail}")` } as CSSProperties}
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
                        <span>★</span>
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
            {popoItems.map((item) => {
              const owned = isPopoOwned(item)
              const previewed = previewPopo[item.kind] === item.id
              const equipped = popoCustomization[item.kind] === item.id
              return (
                <article key={item.id} className={`${styles.popoCard} ${previewed ? styles.selected : ''}`}>
                  <button className={styles.popoButton} onClick={() => choosePopoItem(item)}>
                    <span className={`${styles.itemPreview} ${styles[`item_${item.id}`]}`} />
                    <strong>{item.name}</strong>
                    <em>{previewed ? 'Preview Off' : equipped ? 'Wearing' : owned ? 'Preview' : `★ ${item.price}`}</em>
                  </button>
                </article>
              )
            })}
          </section>
          <div className={styles.clearActions}>
            <button onClick={() => clearPopoKind('hat')}>No Hat</button>
            <button onClick={() => clearPopoKind('glasses')}>No Glasses</button>
            <button onClick={() => clearPopoKind('necklace')}>No Necklace</button>
            <button onClick={() => clearPopoKind('outfit')}>No Clothes</button>
          </div>
          <div className={styles.saveActions}>
            <button onClick={resetPopoPreview}>Reset Preview</button>
            <button onClick={savePopoLook}>{previewCost > 0 ? `Buy & Save ★ ${previewCost}` : 'Save Look'}</button>
          </div>
        </>
      )}

      <p className={styles.message}>{message}</p>
    </main>
  )
}
