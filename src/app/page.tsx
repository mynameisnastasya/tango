'use client'

import { useState } from 'react'
import { ArrowRight, Menu, X } from 'lucide-react'

const navLinks = [
  { label: 'Главная', href: '#home' },
  { label: 'Кейсы', href: '#cases' },
  { label: 'Подход', href: '#approach' },
  { label: 'Связаться', href: '#contact' },
]

const videoUrl = 'https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260622_204221_5339e40b-e73d-4ab0-9c65-79c18c66fd50.mp4'

export default function Home() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <main className="landing-root" id="home">
      <span id="cases" className="anchor-point" aria-hidden="true" />
      <span id="approach" className="anchor-point" aria-hidden="true" />
      <span id="contact" className="anchor-point" aria-hidden="true" />

      <video
        autoPlay
        muted
        loop
        playsInline
        className="background-video"
        src={videoUrl}
      />
      <div className="video-overlay" />

      <nav className="navbar" aria-label="Основная навигация">
        <div className="navbar-left">
          <a href="#home" className="logo-text" onClick={() => setMobileMenuOpen(false)}>
            Настасья
          </a>
          <div className="desktop-links">
            {navLinks.map((link) => (
              <a key={link.label} href={link.href}>
                {link.label}
              </a>
            ))}
          </div>
        </div>

        <a className="desktop-cta" href="#contact">
          Обсудить сайт
        </a>

        <button
          className="mobile-toggle"
          type="button"
          aria-label={mobileMenuOpen ? 'Закрыть меню' : 'Открыть меню'}
          aria-expanded={mobileMenuOpen}
          onClick={() => setMobileMenuOpen((open) => !open)}
        >
          <Menu className={`toggle-icon menu-icon ${mobileMenuOpen ? 'hidden-icon' : 'visible-icon'}`} size={22} />
          <X className={`toggle-icon x-icon ${mobileMenuOpen ? 'visible-icon' : 'hidden-icon'}`} size={22} />
        </button>
      </nav>

      <div className={`mobile-menu ${mobileMenuOpen ? 'menu-open' : 'menu-closed'}`}>
        <div className={`mobile-menu-inner ${mobileMenuOpen ? 'inner-open' : 'inner-closed'}`}>
          {navLinks.map((link) => (
            <a key={link.label} href={link.href} onClick={() => setMobileMenuOpen(false)}>
              {link.label}
            </a>
          ))}
          <a className="mobile-cta" href="#contact" onClick={() => setMobileMenuOpen(false)}>
            Обсудить проект
          </a>
        </div>
      </div>

      <section className="hero-content">
        <div className="hero-top">
          <p className="hero-badge">Маркетинг • Дизайн • Сайты</p>
          <h1>
            Создаю сайты,<br />
            которые выглядят дорого<br />
            и приводят клиентов.
          </h1>
        </div>

        <div className="hero-bottom">
          <p>
            Соединяю маркетинг, визуальную эстетику и продуманную структуру, чтобы сайт не просто красиво выглядел, а продавал, объяснял ценность и усиливал доверие к бренду.
          </p>
          <a className="hero-button" href="#cases">
            Смотреть кейсы
            <ArrowRight size={16} />
          </a>
        </div>
      </section>

      <div className="desktop-corner-label">
        Websites / Strategy / Visual Identity
      </div>
    </main>
  )
}
