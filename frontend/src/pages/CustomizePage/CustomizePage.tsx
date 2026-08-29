import { useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAppStore } from '../../store/useAppStore'
import styles from './CustomizePage.module.css'

type Tab = 'character' | 'room'

interface ShopItem {
  id: string
  name: string
  category: Tab
  kind: 'characterItem' | 'rug' | 'lamp' | 'roomItem'
  cost: number
}

interface CustomizationState {
  characterItem?: string
  rug?: string
  lamp?: string
  roomItem?: string
}

const CUSTOMIZATION_KEY = 'yeongcha:customization'
const UNLOCKS_KEY = 'yeongcha:customization-unlocks'
const SPENT_KEY = 'yeongcha:customization-points-spent'

const items: ShopItem[] = [
  { id: 'hat', name: '보라 모자', category: 'character', kind: 'characterItem', cost: 25 },
  { id: 'sunglasses', name: '선글라스', category: 'character', kind: 'characterItem', cost: 35 },
  { id: 'necklace', name: '별 목걸이', category: 'character', kind: 'characterItem', cost: 30 },
  { id: 'earrings', name: '핑크 귀걸이', category: 'character', kind: 'characterItem', cost: 30 },
  { id: 'blue', name: '하늘 러그', category: 'room', kind: 'rug', cost: 20 },
  { id: 'mint', name: '민트 러그', category: 'room', kind: 'rug', cost: 25 },
  { id: 'pink', name: '핑크 러그', category: 'room', kind: 'rug', cost: 25 },
  { id: 'star', name: '별빛 조명', category: 'room', kind: 'lamp', cost: 35 },
  { id: 'moon', name: '달빛 조명', category: 'room', kind: 'lamp', cost: 35 },
  { id: 'bookcase', name: '책장', category: 'room', kind: 'roomItem', cost: 50 },
  { id: 'mirror', name: '동그란 거울', category: 'room', kind: 'roomItem', cost: 45 },
  { id: 'plant', name: '초록 화분', category: 'room', kind: 'roomItem', cost: 30 },
  { id: 'puppy', name: '작은 강아지', category: 'room', kind: 'roomItem', cost: 60 },
]

function readJson<T>(key: string, fallback: T): T {
  try {
    return JSON.parse(window.localStorage.getItem(key) || '') as T
  } catch {
    return fallback
  }
}

function itemClass(item: ShopItem): string {
  return styles[`preview_${item.kind}_${item.id}`] ?? ''
}

export default function CustomizePage() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const initialTab = searchParams.get('tab') === 'room' ? 'room' : 'character'
  const [tab, setTab] = useState<Tab>(initialTab)
  const { userStats } = useAppStore()
  const [customization, setCustomization] = useState<CustomizationState>(() => readJson(CUSTOMIZATION_KEY, {}))
  const [previewCustomization, setPreviewCustomization] = useState<CustomizationState>(() => readJson(CUSTOMIZATION_KEY, {}))
  const [unlocks, setUnlocks] = useState<string[]>(() => readJson(UNLOCKS_KEY, []))
  const [spent, setSpent] = useState(() => Number(window.localStorage.getItem(SPENT_KEY) || '0'))
  const [selectedItem, setSelectedItem] = useState<ShopItem | null>(null)
  const [pendingPurchase, setPendingPurchase] = useState<ShopItem | null>(null)
  const [message, setMessage] = useState('')

  const points = Math.max(0, userStats.hearts - spent)
  const visibleItems = useMemo(() => items.filter((item) => item.category === tab), [tab])

  const selectTab = (nextTab: Tab) => {
    setTab(nextTab)
    setSearchParams({ tab: nextTab })
    setMessage('')
  }

  const isUnlocked = (item: ShopItem) => unlocks.includes(item.id) || item.cost === 0
  const isEquipped = (item: ShopItem) => previewCustomization[item.kind] === item.id

  const persist = (nextCustomization: CustomizationState, nextUnlocks = unlocks, nextSpent = spent) => {
    setCustomization(nextCustomization)
    setPreviewCustomization(nextCustomization)
    setUnlocks(nextUnlocks)
    setSpent(nextSpent)
    window.localStorage.setItem(CUSTOMIZATION_KEY, JSON.stringify(nextCustomization))
    window.localStorage.setItem(UNLOCKS_KEY, JSON.stringify(nextUnlocks))
    window.localStorage.setItem(SPENT_KEY, String(nextSpent))
  }

  const previewItem = (item: ShopItem) => {
    const nextPreview = { ...previewCustomization, [item.kind]: item.id }
    setPreviewCustomization(nextPreview)
    setSelectedItem(item)
    if (isUnlocked(item)) {
      persist({ ...customization, [item.kind]: item.id })
      setMessage(`${item.name}을 장착했어요.`)
      return
    }
    setMessage(`${item.name}을 미리 입혀봤어요.`)
  }

  const openPurchase = (item: ShopItem) => {
    setSelectedItem(item)
    setPreviewCustomization({ ...previewCustomization, [item.kind]: item.id })
    if (points < item.cost) {
      setMessage(`${item.name}은 포인트 ${item.cost}개가 필요해요.`)
      return
    }
    setPendingPurchase(item)
  }

  const confirmPurchase = () => {
    if (!pendingPurchase) return
    if (points < pendingPurchase.cost) {
      setMessage(`${pendingPurchase.name}은 포인트 ${pendingPurchase.cost}개가 필요해요.`)
      setPendingPurchase(null)
      return
    }
    const nextUnlocks = unlocks.includes(pendingPurchase.id) ? unlocks : [...unlocks, pendingPurchase.id]
    const nextSpent = spent + pendingPurchase.cost
    const nextCustomization = { ...customization, [pendingPurchase.kind]: pendingPurchase.id }
    persist(nextCustomization, nextUnlocks, nextSpent)
    setMessage(`${pendingPurchase.name}을 구매하고 장착했어요.`)
    setPendingPurchase(null)
  }

  const clearSlot = (kind: ShopItem['kind']) => {
    const nextCustomization = { ...customization }
    delete nextCustomization[kind]
    persist(nextCustomization)
    setMessage('장착을 해제했어요.')
  }

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <button className={styles.backButton} onClick={() => navigate('/home')} aria-label="홈으로">←</button>
        <div>
          <h1>꾸미기</h1>
          <p>모은 포인트로 내 친구와 방을 꾸며요</p>
        </div>
        <div className={styles.points}>
          <span />
          <strong>{points}</strong>
        </div>
      </header>

      <div className={styles.tabs}>
        <button className={tab === 'character' ? styles.activeTab : ''} onClick={() => selectTab('character')}>
          캐릭터
        </button>
        <button className={tab === 'room' ? styles.activeTab : ''} onClick={() => selectTab('room')}>
          방
        </button>
      </div>

      <section className={styles.preview}>
        <div className={styles.previewRoom}>
          <div className={`${styles.previewRug} ${previewCustomization.rug ? styles[`preview_rug_${previewCustomization.rug}`] : ''}`} />
          <img src="/images/HomeBearHands.png" alt="" />
          {previewCustomization.characterItem && <span className={`${styles.equippedCharacter} ${styles[`preview_characterItem_${previewCustomization.characterItem}`]}`} />}
          {previewCustomization.lamp && <span className={`${styles.equippedLamp} ${styles[`preview_lamp_${previewCustomization.lamp}`]}`} />}
          {previewCustomization.roomItem && <span className={`${styles.equippedRoomItem} ${styles[`preview_roomItem_${previewCustomization.roomItem}`]}`} />}
        </div>
      </section>

      <section className={styles.grid}>
        {visibleItems.map((item) => {
          const unlocked = isUnlocked(item)
          const equipped = isEquipped(item)
          return (
            <article
              key={`${item.kind}-${item.id}`}
              className={`${styles.item} ${equipped ? styles.equipped : ''} ${selectedItem?.id === item.id ? styles.selected : ''}`}
            >
              <button className={styles.itemSelect} onClick={() => previewItem(item)}>
                <span className={`${styles.itemPreview} ${itemClass(item)}`} />
                <strong>{item.name}</strong>
                <em>{equipped ? '장착 중' : unlocked ? '장착하기' : '미리보기'}</em>
              </button>
              {!unlocked && (
                <button className={styles.buyButton} onClick={() => openPurchase(item)}>
                  구매 {item.cost}
                </button>
              )}
            </article>
          )
        })}
      </section>

      <div className={styles.clearActions}>
        {tab === 'character' ? (
          <button onClick={() => clearSlot('characterItem')}>소품 빼기</button>
        ) : (
          <>
            <button onClick={() => clearSlot('rug')}>러그 빼기</button>
            <button onClick={() => clearSlot('lamp')}>조명 빼기</button>
            <button onClick={() => clearSlot('roomItem')}>장식 빼기</button>
          </>
        )}
      </div>

      <p className={styles.message}>{message}</p>

      {pendingPurchase && (
        <div className={styles.modalBackdrop} role="presentation">
          <section className={styles.modal} role="dialog" aria-modal="true" aria-labelledby="purchase-title">
            <h2 id="purchase-title">구매하시겠습니까?</h2>
            <p>{pendingPurchase.name}을 포인트 {pendingPurchase.cost}개로 구매해요.</p>
            <div className={styles.modalActions}>
              <button onClick={() => setPendingPurchase(null)}>취소</button>
              <button onClick={confirmPurchase}>구매</button>
            </div>
          </section>
        </div>
      )}
    </main>
  )
}
