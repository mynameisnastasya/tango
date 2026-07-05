'use client'

import { useState } from 'react'
import { ArrowRight, Menu, Sparkles, X } from 'lucide-react'

const navLinks = [
  { label: 'Главная', href: '#home' },
  { label: 'Кейсы', href: '#cases' },
  { label: 'Подход', href: '#approach' },
  { label: 'Услуги', href: '#services' },
  { label: 'Контакт', href: '#contact' },
]

const videoUrl = 'https://cdn.pixabay.com/video/2016/11/15/6400-191716659_large.mp4'

export default function Home() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <main className="landing-root" id="home">
      <span id="cases" className="anchor-point" aria-hidden="true" />
      <span id="approach" className="anchor-point" aria-hidden="true" />
      <span id="services" className="anchor-point" aria-hidden="true" />
      <span id="contact" className="anchor-point" aria-hidden="true" />

      <video
        className="background-video"
        src={videoUrl}
        autoPlay
        muted
        loop
        playsInline
      />
      <div className="overlay-dark" />
      <div className="overlay-gradient" />
      <div className="overlay-radial" />
      <div className="video-grain" />

      <nav className="navbar" aria-label="Основная навигация">
        <div className="navbar-left">
          <a href="#home" className="logo-group" onClick={() => setMobileMenuOpen(false)}>
            <span className="logo-text">Настасья</span>
            <span className="logo-descriptor">web / marketing / visual</span>
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
          Обсудить проект
          <ArrowRight size={15} />
        </a>

        <button
          className="mobile-toggle"
          type="button"
          aria-label={mobileMenuOpen ? 'Закрыть меню' : 'Открыть меню'}
          aria-expanded={mobileMenuOpen}
          onClick={() => setMobileMenuOpen((open) => !open)}
        >
          <Menu className={`toggle-icon menu-icon ${mobileMenuOpen ? 'hidden-icon' : 'visible-icon'}`} size={20} />
          <X className={`toggle-icon x-icon ${mobileMenuOpen ? 'visible-icon' : 'hidden-icon'}`} size={20} />
        </button>
      </nav>

      <div className={`mobile-menu ${mobileMenuOpen ? 'menu-open' : 'menu-closed'}`}>
        <div className={`mobile-menu-inner ${mobileMenuOpen ? 'inner-open' : 'inner-closed'}`}>
          <div className="mobile-links">
            {navLinks.map((link) => (
              <a key={link.label} href={link.href} onClick={() => setMobileMenuOpen(false)}>
                {link.label}
              </a>
            ))}
          </div>

          <a className="mobile-cta" href="#contact" onClick={() => setMobileMenuOpen(false)}>
            Обсудить сайт
            <ArrowRight size={16} />
          </a>
        </div>
      </div>

      <section className="hero-content">
        <div className="hero-top">
          <p className="hero-badge">
            <Sparkles size={14} />
            Маркетинг • сайты • визуальная упаковка
          </p>

          <h1>
            Сайты, которые<br />
            выглядят дорого<br />
            и продают без крика.
          </h1>

          <p className="hero-subheading">
            Для экспертов и брендов, которым нужен не просто красивый экран, а сильная упаковка, понятный оффер и сайт, после которого хочется доверять.
          </p>
        </div>

        <div className="hero-bottom-wrap">
          <div className="thin-line" />

          <div className="hero-bottom">
            <div className="bottom-left">
              <p>
                Я соединяю стратегию, визуал и структуру, чтобы сайт не просто “был”, а работал: объяснял ценность, усиливал бренд и превращал внимание в заявки.
              </p>

              <div className="availability-chip">
                <span />
                доступна для 2 проектов в месяц
              </div>
            </div>

            <div className="cta-group">
              <a className="hero-button primary" href="#cases">
                Смотреть кейсы
                <ArrowRight size={16} />
              </a>
              <a className="hero-button secondary" href="#approach">
                Узнать подход
              </a>
            </div>

            <div className="micro-label" aria-hidden="true">
              <span>01 / HERO</span>
              <span>STRATEGY FIRST</span>
              <span>DESIGN THAT SELLS</span>
            </div>
          </div>
        </div>
      </section>
    </main>
  )
}
