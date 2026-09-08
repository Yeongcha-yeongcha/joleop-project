import { ICONS } from '../../constants/assets'
import styles from './StarRow.module.css'

interface Props {
  /** 켜진 별 개수. */
  lit: number
  /** 전체 별 개수. */
  total?: number
  /** 별 한 개의 크기(px). */
  size?: number
  /** 별 사이 간격(px). */
  gap?: number
  /** 켜진 별에 팝 애니메이션을 넣는다(결과 화면처럼 하나씩 켜질 때). */
  animateLit?: boolean
  className?: string
  /** 없으면 `N of M stars` 로 붙는다. */
  label?: string
}

/**
 * 받은 별을 1행으로 보여준다.
 * 아직 받지 못한 별은 같은 이미지의 채도 0(`grayscale(1)`)으로 그린다.
 * 챕터 목록과 레슨 결과 화면이 같은 표현을 쓰도록 한곳에 모았다.
 */
export default function StarRow({
  lit,
  total = 3,
  size = 22,
  gap = 3,
  animateLit = false,
  className,
  label,
}: Props) {
  return (
    <span
      className={[styles.row, className].filter(Boolean).join(' ')}
      style={{ '--star-size': `${size}px`, '--star-gap': `${gap}px` } as React.CSSProperties}
      aria-label={label ?? `${lit} of ${total} stars`}
    >
      {Array.from({ length: total }, (_, index) => (
        <img
          key={index}
          src={ICONS.star}
          alt=""
          aria-hidden="true"
          className={[
            styles.star,
            index < lit ? styles.on : styles.off,
            index < lit && animateLit ? styles.pop : '',
          ].filter(Boolean).join(' ')}
        />
      ))}
    </span>
  )
}
