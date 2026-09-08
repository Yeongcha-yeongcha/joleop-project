export type PopoItemKind = 'hat' | 'glasses' | 'necklace'

export interface PopoItem {
  id: string
  name: string
  kind: PopoItemKind
  price: number
  /** 아이템 목록에 쓰는 썸네일. 없으면 CSS 로 그린다(모자). */
  thumbnail?: string
  /**
   * 캐릭터 위에 그대로 겹치면 위치가 맞는 오버레이.
   * 캐릭터(HomePopo.png 321x321)와 같은 정사각 캔버스(435x435)로 만들어져 있어
   * `inset: 0` + `object-fit: contain` 이면 좌표가 정확히 맞는다.
   */
  spot?: string
}

export type PopoCustomization = Partial<Record<PopoItemKind, string>>

const BASE = '/images/popo'

export const POPO_ITEMS: PopoItem[] = [
  // 모자는 기존 CSS 도형을 그대로 쓴다(썸네일/스팟 이미지 없음).
  { id: 'sun-cap', name: 'Sun Hat', kind: 'hat', price: 80 },
  { id: 'star-cap', name: 'Star Hat', kind: 'hat', price: 120 },
  {
    id: 'heart-sunglass',
    name: 'Heart Sunglasses',
    kind: 'glasses',
    price: 90,
    thumbnail: `${BASE}/heart_sunglass_thumbnail.png`,
    spot: `${BASE}/heart_sunglass_spot.png`,
  },
  {
    id: 'cool-sunglass',
    name: 'Cool Sunglasses',
    kind: 'glasses',
    price: 130,
    thumbnail: `${BASE}/cool_sunglass_thumbnail.png`,
    spot: `${BASE}/cool_sunglass_spot.png`,
  },
  {
    id: 'rainbow-necklace',
    name: 'Rainbow Necklace',
    kind: 'necklace',
    price: 90,
    thumbnail: `${BASE}/rainbow_necklace_thumbnail.png`,
    spot: `${BASE}/rainbow_necklace_spot.png`,
  },
  {
    id: 'pearl-necklace',
    name: 'Pearl Necklace',
    kind: 'necklace',
    price: 110,
    thumbnail: `${BASE}/pearl_necklace_thumbnail.png`,
    spot: `${BASE}/pearl_necklace_spot.png`,
  },
]

export const POPO_ITEM_KINDS: PopoItemKind[] = ['hat', 'glasses', 'necklace']

export function findPopoItem(kind: PopoItemKind, id: string | undefined): PopoItem | undefined {
  if (!id) return undefined
  return POPO_ITEMS.find((item) => item.kind === kind && item.id === id)
}

/**
 * 저장된 커스터마이징에서 스팟 이미지를 가진 항목만 뽑는다.
 * 목록에서 사라진 예전 아이템(의상 등)이 저장돼 있어도 자연히 무시된다.
 */
export function resolvePopoSpots(customization: PopoCustomization): PopoItem[] {
  return POPO_ITEM_KINDS
    .map((kind) => findPopoItem(kind, customization[kind]))
    .filter((item): item is PopoItem => Boolean(item?.spot))
}
