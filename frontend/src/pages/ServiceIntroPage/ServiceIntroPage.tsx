import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import styles from './ServiceIntroPage.module.css'

const slides = [
  {
    image: '/images/onboarding/lion-reading.png',
    title: 'Start with Stories',
    text: 'Read short scenes. Meet new words with pictures.',
  },
  {
    image: '/images/onboarding/lion-headphones.png',
    title: 'Listen and Say',
    text: 'Hear a sentence. Say it out loud.',
  },
  {
    image: '/images/onboarding/lion-magnifier.png',
    title: 'Look and Answer',
    text: 'Look at the picture. Say a word or a short sentence.',
  },
  {
    image: '/images/onboarding/lion-wave.png',
    title: 'Talk with Friends',
    text: 'Use what you learned in a small role play.',
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
        {isLast ? 'Start' : 'Next'}
      </button>
    </main>
  )
}
