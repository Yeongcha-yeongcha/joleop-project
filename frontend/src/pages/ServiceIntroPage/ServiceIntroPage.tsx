import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import styles from './ServiceIntroPage.module.css'

const slides = [
  {
    image: '/images/onboarding/lion-reading.png',
    title: '영어 동화로 시작해요',
    text: '짧은 장면을 넘기며 이야기를 읽고, 그림과 문장으로 오늘 배울 표현을 만나요.',
  },
  {
    image: '/images/onboarding/lion-headphones.png',
    title: '듣고 따라 말해요',
    text: '문장을 듣고 직접 말하면 발음과 자신감을 함께 연습할 수 있어요.',
  },
  {
    image: '/images/onboarding/lion-magnifier.png',
    title: '그림을 보고 답해요',
    text: '색깔, 사물, 상황을 말하면서 단어와 짧은 문장을 자연스럽게 익혀요.',
  },
  {
    image: '/images/onboarding/lion-wave.png',
    title: '캐릭터와 대화해요',
    text: '마지막에는 이야기 속 친구를 도와주는 역할놀이로 배운 표현을 써봐요.',
  },
]

export default function ServiceIntroPage() {
  const navigate = useNavigate()
  const [index, setIndex] = useState(0)
  const slide = slides[index]
  const isLast = index === slides.length - 1

  const next = () => {
    if (!isLast) {
      setIndex((current) => current + 1)
      return
    }
    window.localStorage.setItem('yeongcha:service-intro-completed', 'true')
    navigate('/onboarding')
  }

  return (
    <main className={styles.page}>
      <section className={styles.content}>
        <div className={styles.imageBubble}>
          <img src={slide.image} alt="" />
        </div>
        <div className={styles.copy}>
          <h1>{slide.title}</h1>
          <p>{slide.text}</p>
        </div>
        <div className={styles.dots} aria-label={`${index + 1} / ${slides.length}`}>
          {slides.map((item, dotIndex) => (
            <span
              key={item.title}
              className={dotIndex === index ? styles.dotActive : ''}
            />
          ))}
        </div>
      </section>
      <button className={styles.primaryButton} onClick={next}>
        {isLast ? '시작하기' : '다음'}
      </button>
    </main>
  )
}
