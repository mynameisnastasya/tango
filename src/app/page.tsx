'use client'

import { FormEvent, useEffect, useMemo, useState } from 'react'
import {
  AlertCircle, ArrowRight, BadgeCheck, Check, ChevronDown, CircleDollarSign, Crown,
  Diamond, Globe2, HeartHandshake, Instagram, Languages, Menu, MessageCircle,
  ShieldCheck, Sparkles, Star, Target, Users, X, Zap
} from 'lucide-react'

type Lang = 'en' | 'ru'
type Settings = {
  welcome_bonus: string
  milestone_title: string
  milestone_reward: string
  telegram_url: string
  whatsapp_url: string
  instagram_url: string
  email: string
  faq_en?: string[][]
  faq_ru?: string[][]
}
const initialSettings: Settings = {
  welcome_bonus: '$15 joining bonus',
  milestone_title: '100,000 Diamond Milestone',
  milestone_reward: 'Additional broadcaster reward may be available.',
  telegram_url: '',
  whatsapp_url: '',
  instagram_url: '',
  email: '',
}

const copy = {
  en: {
    nav: ['How It Works', 'Benefits', 'Bonuses', 'FAQ', 'Apply'],
    join: 'Join the Agency',
    eyebrow: 'International creator management • 18+',
    h1a: 'Start Your Live',
    h1b: 'Streaming Journey',
    h1c: 'with ABHIGREEN',
    sub: 'Join ABHIGREEN, learn live streaming from zero, get personal support and build your audience with clear monetization guidance.',
    joinNow: 'Join Now',
    learn: 'Learn How It Works',
    realOnly: 'Real broadcasters only',
    noFake: 'No prerecorded or fake broadcasts',
    tangoCodeTitle: 'Connect to ABHIGREEN on Tango',
    tangoCodeSub: 'Android: use the referral link. iPhone: create your account on tango.me, then open Tango → Settings → Join an Agency and enter the agency code within the first 5 hours.',
    tangoCodeLabel: 'Tango Agency Code',
    copyCode: 'Copy Code',
    copied: 'Copied',
    journey: 'A clear path from application to confident live streaming',
    journeySub: 'You do not need to figure everything out alone. Our team guides new broadcasters during onboarding.',
    offer: 'What We Offer',
    offerSub: 'Support that stays useful after your first stream.',
    bonuses: 'Bonuses & Milestones',
    bonusesSub: 'Campaigns are editable and may change. Final conditions are always confirmed by your manager.',
    welcome: 'Welcome Bonus',
    welcomeText: 'Eligible new creators can receive',
    milestone: 'Milestone',
    bonusNote: 'Bonuses, coin amounts, eligibility requirements and campaigns may change. Final conditions are confirmed individually by the agency manager before participation.',
    growthTitle: 'Growth support',
    growth: 'We help you improve your profile, live format, audience engagement and monetization strategy as you grow.',
    looking: 'Who We Are Looking For',
    lookingSub: 'Women 18+ who want to communicate, grow and broadcast consistently.',
    warning: 'Prerecorded streams, fake broadcasters, impersonation, or attempts to bypass platform rules are not accepted.',
    longTitle: 'Your manager from day one.',
    longSub: 'Your agency for the long run.',
    community: 'ABHIGREEN Creator Community',
    communitySub: 'Accepted broadcasters get access to onboarding information, training materials, announcements, challenges, contests, bonus news and manager support.',
    telegram: 'Open Telegram',
    faq: 'Frequently Asked Questions',
    applyTitle: 'Join ABHIGREEN',
    applySub: 'Tell us a little about yourself. A manager will review your application and contact you.',
    submit: 'Send Application',
    sending: 'Sending...',
    success: 'Thank you! Your application has been received. Our manager will contact you soon.',
    consent: 'I agree to the policies below and confirm that the information I provide is accurate.',
    form: {
      name:'Name', country:'Country', languages:'Languages', telegram:'Telegram username',
      whatsapp:'WhatsApp', instagram:'Instagram username', platform:'Current streaming platform',
      experience:'Previous live-streaming experience', username:'Current Tango / SuperLive / Bigo / etc. username',
      hours:'How many hours per week can you stream?', message:'Short message / introduction'
    },
    age: 'I am 18 years or older',
    footer: 'Premium talent management for real live broadcasters.',
  },
  ru: {
    nav: ['Как это работает', 'Преимущества', 'Бонусы', 'FAQ', 'Заявка'],
    join: 'Вступить в агентство',
    eyebrow: 'Международное агентство для стримеров • 18+',
    h1a: 'Начни карьеру',
    h1b: 'в прямых эфирах',
    h1c: 'вместе с ABHIGREEN',
    sub: 'Освой прямые эфиры с нуля, развивай аудиторию и монетизацию, а личный менеджер ABHIGREEN поможет на каждом этапе.',
    joinNow: 'Присоединиться',
    learn: 'Как это работает',
    realOnly: 'Только реальные стримеры',
    noFake: 'Без записей и фейковых трансляций',
    tangoCodeTitle: 'Подключись к ABHIGREEN в Tango',
    tangoCodeSub: 'Android: используй реферальную ссылку. iPhone: создай аккаунт на tango.me, затем в Tango открой Settings → Join an Agency и введи код агентства в первые 5 часов.',
    tangoCodeLabel: 'Код агентства в Tango',
    copyCode: 'Скопировать код',
    copied: 'Скопировано',
    journey: 'Понятный путь от заявки до уверенных эфиров',
    journeySub: 'Не нужно разбираться во всём самостоятельно. Команда поможет с подключением, подготовкой и первыми эфирами.',
    offer: 'Что даёт ABHIGREEN',
    offerSub: 'Практическая поддержка до старта и после первого эфира.',
    bonuses: 'Бонусы и достижения',
    bonusesSub: 'Условия кампаний могут меняться. Актуальные суммы и требования всегда подтверждает менеджер до участия.',
    welcome: 'Бонус за подключение',
    welcomeText: 'Для подходящих новых стримеров доступен',
    milestone: 'Достижение',
    bonusNote: 'Размеры бонусов, требования и условия кампаний могут меняться. Менеджер подтверждает актуальные условия индивидуально до участия.',
    growthTitle: 'Поддержка роста',
    growth: 'Помогаем улучшать профиль, формат эфиров, общение с аудиторией и стратегию монетизации по мере роста.',
    looking: 'Кого мы ищем',
    lookingSub: 'Девушек 18+, которым комфортно общаться, развиваться и регулярно выходить в эфир.',
    warning: 'Записанные трансляции, фейковые аккаунты, выдача себя за другого человека и обход правил платформы не допускаются.',
    longTitle: 'Твой менеджер с первого дня.',
    longSub: 'Твоё агентство на долгий путь.',
    community: 'ABHIGREEN Creator Community',
    communitySub: 'Принятые стримеры получают материалы для старта, обучение, объявления агентства, челленджи, конкурсы, новости о бонусах и поддержку менеджеров.',
    telegram: 'Открыть Telegram',
    faq: 'Частые вопросы',
    applyTitle: 'Присоединиться к ABHIGREEN',
    applySub: 'Расскажи немного о себе. Менеджер рассмотрит заявку и свяжется с тобой.',
    submit: 'Отправить заявку',
    sending: 'Отправляем...',
    success: 'Спасибо! Заявка получена. Наш менеджер скоро свяжется с тобой.',
    consent: 'Я соглашаюсь с указанными ниже документами и подтверждаю, что предоставляю достоверную информацию.',
    form: {
      name:'Имя', country:'Страна', languages:'Языки', telegram:'Telegram username',
      whatsapp:'WhatsApp', instagram:'Instagram username', platform:'Текущая стриминг-платформа',
      experience:'Опыт прямых эфиров', username:'Ник в Tango / SuperLive / Bigo / другой платформе',
      hours:'Сколько часов в неделю можешь выходить в эфир?', message:'Коротко о себе'
    },
    age: 'Мне 18 лет или больше',
    footer: 'Помогаем девушкам 18+ уверенно развиваться в прямых эфирах.',
  }
}

const steps = {
  en: [
    ['01','Submit your application'], ['02','Receive Tango connection instructions and the agency code'],
    ['03','Create or connect your broadcaster account'], ['04','Complete onboarding and start streaming'],
    ['05','Grow your audience and monetize your live content'],
  ],
  ru: [
    ['01','Отправь заявку'], ['02','Получи инструкцию и код для подключения к агентству в Tango'],
    ['03','Создай или подключи аккаунт стримера'], ['04','Пройди вводное обучение и начни эфиры'],
    ['05','Развивай аудиторию и монетизируй контент'],
  ],
}

const benefits = {
  en: [
    ['Personal onboarding', HeartHandshake], ['Russian & English support', Languages],
    ['Platform rules explained', ShieldCheck], ['Streaming tips', Sparkles],
    ['Creator community', Users], ['Performance bonuses', CircleDollarSign],
    ['Events, challenges & battles', Zap], ['Growth & monetization support', Target],
    ['Long-term support', Crown],
  ],
  ru: [
    ['Персональный старт', HeartHandshake], ['Поддержка RU / EN', Languages],
    ['Помощь с правилами платформ', ShieldCheck], ['Советы по эфирам', Sparkles],
    ['Сообщество стримеров', Users], ['Бонусы за результаты', CircleDollarSign],
    ['События, челленджи и батлы', Zap], ['Поддержка роста и монетизации', Target],
    ['Долгосрочная поддержка', Crown],
  ],
}

const criteria = {
  en: ['Be 18+', 'Be comfortable appearing live on camera', 'Use your real identity and content', 'Be willing to communicate with viewers', 'Follow streaming platform rules', 'Be interested in regular live broadcasting'],
  ru: ['Быть 18+', 'Комфортно чувствовать себя в кадре', 'Использовать свою реальную личность и контент', 'Быть готовой общаться со зрителями', 'Соблюдать правила платформы', 'Быть заинтересованной в регулярных эфирах'],
}

const faqs = {
  en: [
    ['Is joining the agency free?', 'Yes. ABHIGREEN does not charge an application or joining fee. Platform and campaign rules may differ.'],
    ['Do I need previous experience?', 'No. Beginners can apply and receive onboarding support.'],
    ['Can beginners join?', 'Yes, if you are 18+ and willing to learn and follow platform rules.'],
    ['What is the Tango Agency Code?', 'KCu4ZY is the ABHIGREEN code used inside Tango when connecting your broadcaster account to our agency. Detailed step-by-step instructions will be added separately.'],
    ['Are bonuses guaranteed?', 'No. Bonuses and campaigns can change and are confirmed by your manager before participation.'],
    ['Which countries can join?', 'We work internationally. Eligibility can depend on the current platform and campaign.'],
    ['Can I work with other agencies?', 'This depends on the platform and your existing agency agreement. Ask your manager before joining another agency.'],
    ['What if my account belongs to another agency?', 'Tell us before onboarding. We will explain the available options under the platform rules.'],
    ['Do I need to stream every day?', 'Not necessarily. Consistency matters, but the recommended schedule depends on your goals and platform conditions.'],
    ['Are prerecorded streams allowed?', 'No. ABHIGREEN accepts real live broadcasters only.'],
  ],
  ru: [
    ['Вступление в агентство бесплатное?', 'Да. ABHIGREEN не берёт плату за заявку или вступление. Правила платформ и кампаний могут отличаться.'],
    ['Нужен ли опыт?', 'Нет. Новички могут подать заявку и пройти вводное обучение.'], 
    ['Можно ли новичкам?', 'Да, если тебе 18+ и ты готова учиться и соблюдать правила платформы.'],
    ['Что такое Tango Agency Code?', 'KCu4ZY — код ABHIGREEN, который вводится внутри Tango при подключении аккаунта стримера к нашему агентству. Пошаговая инструкция есть выше на этой странице.'], 
    ['Бонусы гарантированы?', 'Нет. Условия и кампании могут меняться и подтверждаются менеджером до участия.'],
    ['Из каких стран можно?', 'Мы работаем международно. Доступность зависит от текущих правил платформы и условий кампании.'], 
    ['Можно работать с другими агентствами?', 'Это зависит от правил платформы и твоих действующих агентских условий. Лучше уточнить у менеджера.'],
    ['Что если аккаунт уже в другом агентстве?', 'Сообщи об этом до подключения. Мы объясним доступные варианты по правилам платформы.'], 
    ['Нужно стримить каждый день?', 'Не обязательно. Важна регулярность, а график зависит от целей и условий платформы.'],
    ['Записанные эфиры разрешены?', 'Нет. ABHIGREEN принимает только реальных live-стримеров.'],
  ],
}

function Logo() {
  return <a href="#top" className="brand"><span className="brand-mark">A</span><span><b>ABHIGREEN</b></span></a>
}

export default function Home() {
  const [lang, setLang] = useState<Lang>('en')
  const [menu, setMenu] = useState(false)
  const [settings, setSettings] = useState<Settings>(initialSettings)
  const [copiedCode, setCopiedCode] = useState(false)
  const [openFaq, setOpenFaq] = useState<number | null>(0)
  const [sending, setSending] = useState(false)
  const [sent, setSent] = useState(false)
  const [formError, setFormError] = useState('')
  const [referralCode, setReferralCode] = useState('')
  const t = copy[lang]
  const configuredFaq = lang === 'en' ? settings.faq_en : settings.faq_ru
  const faqItems = Array.isArray(configuredFaq) && configuredFaq.length ? configuredFaq : faqs[lang]

  useEffect(() => {
    const storedLang = window.localStorage.getItem('abhi_lang')
    if (storedLang === 'en' || storedLang === 'ru') setLang(storedLang)

    const params = new URLSearchParams(window.location.search)
    const ref = params.get('ref') || params.get('referral')
    if (ref) setReferralCode(ref.trim().slice(0, 80))

    fetch('/api/settings').then(r => r.ok ? r.json() : null).then(x => x && setSettings(x)).catch(() => {})
  }, [])

  useEffect(() => {
    document.documentElement.lang = lang
    window.localStorage.setItem('abhi_lang', lang)
    setMenu(false)
  }, [lang])

  async function copyTangoCode() {
    try {
      await navigator.clipboard.writeText('KCu4ZY')
      setCopiedCode(true)
      window.setTimeout(() => setCopiedCode(false), 1800)
    } catch {
      setCopiedCode(false)
    }
  }

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setFormError('')
    setSending(true)
    const form = e.currentTarget
    const fd = new FormData(form)
    const data = Object.fromEntries(fd.entries())
    const hasContact = ['telegram', 'whatsapp', 'instagram'].some(key => String(fd.get(key) || '').trim())

    if (!hasContact) {
      setFormError(lang === 'ru' ? 'Укажи хотя бы один способ связи: Telegram, WhatsApp или Instagram.' : 'Add at least one contact method: Telegram, WhatsApp or Instagram.')
      setSending(false)
      return
    }

    const payload = {
      ...data,
      age_confirmed: fd.get('age_confirmed') === 'on',
      consent: fd.get('consent') === 'on',
      referral_code: referralCode,
      source: window.location.href.split('#')[0],
    }

    try {
      const res = await fetch('/api/applications', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify(payload)
      })

      if (!res.ok) {
        const isLocalDemo = ['localhost', '127.0.0.1'].includes(window.location.hostname)
        if (isLocalDemo) {
          const saved = JSON.parse(localStorage.getItem('abhi_demo_applications') || '[]')
          saved.unshift({ id: crypto.randomUUID(), created_at:new Date().toISOString(), status:'New', ...payload })
          localStorage.setItem('abhi_demo_applications', JSON.stringify(saved))
        } else {
          throw new Error('SUBMISSION_FAILED')
        }
      }

      setSent(true)
      form.reset()
    } catch {
      setFormError(lang === 'ru'
        ? 'Не удалось отправить заявку. Проверь интернет и попробуй ещё раз. Если ошибка повторится, свяжись с менеджером напрямую.'
        : 'We could not send your application. Check your connection and try again. If the problem continues, contact your manager directly.')
    } finally {
      setSending(false)
    }
  }

  const socialLinks = useMemo(() => [
    ['Telegram', settings.telegram_url, MessageCircle],
    ['WhatsApp', settings.whatsapp_url, MessageCircle],
    ['Instagram', settings.instagram_url, Instagram],
    ['Email', settings.email ? 'mailto:' + settings.email : '', MessageCircle],
  ].filter((x) => Boolean(x[1])), [settings])

  return (
    <main id="top">
      <div className="top-note"><ShieldCheck size={14}/> {lang==='ru'?'18+ • Только реальные стримеры • Международная поддержка':'18+ • Real broadcasters only • International support'}</div>
      <header className="header">
        <Logo />
        <nav className="desktop-nav">
          {t.nav.map((x,i)=><a key={x} href={['#how','#benefits','#bonuses','#faq','#apply'][i]}>{x}</a>)}
        </nav>
        <div className="header-actions">
          <button className="lang-switch" type="button" aria-label={lang==='ru'?'Switch to English':'Переключить на русский'} onClick={()=>setLang(lang==='en'?'ru':'en')}><Globe2 size={15}/>{lang.toUpperCase()}</button>
          <a className="button small gold" href="#apply">{t.join}</a>
          <button className="menu-btn" type="button" aria-label={menu?(lang==='ru'?'Закрыть меню':'Close menu'):(lang==='ru'?'Открыть меню':'Open menu')} aria-expanded={menu} aria-controls="mobile-navigation" onClick={()=>setMenu(!menu)}>{menu?<X/>:<Menu/>}</button>
        </div>
      </header>

      {menu && <div className="mobile-nav" id="mobile-navigation">
        {t.nav.map((x,i)=><a key={x} onClick={()=>setMenu(false)} href={['#how','#benefits','#bonuses','#faq','#apply'][i]}>{x}</a>)}
        <a className="button gold" href="#apply" onClick={()=>setMenu(false)}>{t.join}</a>
      </div>}

      <section className="hero section">
        <div className="hero-copy">
          <div className="eyebrow"><Sparkles size={15}/>{t.eyebrow}</div>
          <h1>{t.h1a}<br/><span>{t.h1b}</span><br/>{t.h1c}</h1>
          <p className="hero-sub">{t.sub}</p>
          <div className="hero-actions">
            <a className="button gold" href="#apply">{t.joinNow}<ArrowRight size={17}/></a>
            <a className="button ghost" href="#how">{t.learn}</a>
          </div>
          <div className="trust-row">
            <span><BadgeCheck size={17}/>{t.realOnly}</span>
            <span><ShieldCheck size={17}/>{t.noFake}</span>
          </div>
        </div>

        <div className="creator-visual">
          <div className="visual-glow"/>
          <div className="streamer-proof">
            <img
              src="https://images.pexels.com/photos/7676397/pexels-photo-7676397.jpeg?auto=compress&cs=tinysrgb&w=1600"
              srcSet="https://images.pexels.com/photos/7676397/pexels-photo-7676397.jpeg?auto=compress&cs=tinysrgb&w=900 900w, https://images.pexels.com/photos/7676397/pexels-photo-7676397.jpeg?auto=compress&cs=tinysrgb&w=1600 1600w, https://images.pexels.com/photos/7676397/pexels-photo-7676397.jpeg?auto=compress&cs=tinysrgb&w=2200 2200w"
              sizes="(max-width: 1100px) 94vw, 470px"
              loading="eager"
              decoding="async"
              fetchPriority="high"
              referrerPolicy="no-referrer"
              alt={lang==='ru'?'Взрослая девушка готовится к прямому эфиру со смартфоном и кольцевой лампой':'Adult female content creator preparing a live stream with a smartphone and ring light'}
            />
            <div className="streamer-proof-badge"><span>● LIVE</span><b>ABHIGREEN CREATOR</b></div>
          </div>
          <div className="float-card card-one"><HeartHandshake/><span>{lang==='ru'?'Личный менеджер':'Personal manager'}<br/><b>{lang==='ru'?'с первого дня':'from day one'}</b></span></div>
          <div className="float-card card-two"><Globe2/><span>{lang==='ru'?'Международно':'International'}<br/><b>RU / EN</b></span></div>
        </div>
      </section>

      <section className="section referral-section">
        <div className="referral-card tango-code-card">
          <div>
            <div className="eyebrow gold-text"><Target size={15}/> {lang==='ru'?'TANGO • ПОДКЛЮЧЕНИЕ К АГЕНТСТВУ':'TANGO • AGENCY CONNECTION'}</div>
            <h2>{t.tangoCodeTitle}</h2>
            <p>{t.tangoCodeSub}</p>
          </div>
          <div className="tango-code-box">
            <div className="platform-join-grid">
              <div className="join-option">
                <small>ANDROID</small>
                <h3>{lang==='ru'?'Нажми здесь, чтобы присоединиться':'Click here to join now'}</h3>
                <p className="tango-code-help">{lang==='ru'?'Реферальная ссылка работает для Android.':'The referral link is for Android.'}</p>
                <a className="button gold tango-copy" href="https://tango.onelink.me/RCIH/cdw49a6s" target="_blank" rel="noopener noreferrer">
                  {lang==='ru'?'Открыть реферальную ссылку':'Open referral link'} <ArrowRight size={17}/>
                </a>
              </div>
              <div className="join-option">
                <small>IPHONE / IOS</small>
                <h3>{lang==='ru'?'Создай аккаунт через tango.me':'Create your account on tango.me'}</h3>
                <p className="tango-code-help">{lang==='ru'?'После регистрации открой Tango → Settings → Join an Agency и введи код ниже. Для нового аккаунта — в первые 5 часов.':'After signup open Tango → Settings → Join an Agency and enter the code below. For a new account, do this within the first 5 hours.'}</p>
                <a className="button gold tango-copy" href="https://www.tango.me/" target="_blank" rel="noopener noreferrer">
                  {lang==='ru'?'Открыть tango.me':'Open tango.me'} <ArrowRight size={17}/>
                </a>
              </div>
            </div>
            <small>{t.tangoCodeLabel}</small>
            <div className="tango-code">KCu4ZY</div>
            <button className="button gold tango-copy" onClick={copyTangoCode}>
              {copiedCode ? <Check size={17}/> : <Target size={17}/>}
              {copiedCode ? t.copied : t.copyCode}
            </button>
          </div>
        </div>
        <div className="join-guide-panel">
          <div className="join-guide-copy">
            <div className="eyebrow gold-text"><Target size={15}/> {lang==='ru'?'ПОШАГОВАЯ ИНСТРУКЦИЯ':'STEP-BY-STEP'}</div>
            <h3>{lang==='ru'?'Инструкция: как подключиться к ABHIGREEN':'How to join ABHIGREEN on Tango'}</h3>
            <p>{lang==='ru'?'Шаги теперь собраны прямо на странице — текст остаётся чётким на любом экране и не превращается в пиксели.':'The steps now live directly on the page, so the text stays sharp on every screen instead of turning into pixels.'}</p>
            <div className="guide-quality-note"><Sparkles size={16}/><span>{lang==='ru'?'Не скриншот: это живая веб-инструкция в высоком качестве.':'Not a screenshot: this is a live high-resolution web guide.'}</span></div>
          </div>
          <div className="guide-board" aria-label={lang==='ru'?'Пошаговая инструкция подключения ABHIGREEN в Tango':'ABHIGREEN Tango connection guide'}>
            <div className="guide-code">
              <small>TANGO AGENCY CODE</small>
              <strong>KCu4ZY</strong>
              <span>{lang==='ru'?'Код вводится внутри Tango, не на сайте.':'Enter the code inside Tango, not on this website.'}</span>
            </div>
            <div className="guide-columns">
              <section className="guide-lane guide-android">
                <div className="guide-lane-title"><span>🤖</span><b>ANDROID</b></div>
                <ol>
                  <li>{lang==='ru'?'Нажми на реферальную ссылку':'Open the referral link'}</li>
                  <li>{lang==='ru'?'Открой Tango и создай аккаунт':'Open Tango and create your account'}</li>
                  <li>{lang==='ru'?'Заверши подключение к агентству':'Finish connecting to the agency'}</li>
                </ol>
              </section>
              <section className="guide-lane guide-ios">
                <div className="guide-lane-title"><span>●</span><b>IPHONE / IOS</b></div>
                <ol>
                  <li>{lang==='ru'?'Открой tango.me':'Open tango.me'}</li>
                  <li>{lang==='ru'?'Создай новый аккаунт':'Create a new account'}</li>
                  <li>{lang==='ru'?'В Tango: Settings → Join an Agency':'In Tango: Settings → Join an Agency'}</li>
                  <li>{lang==='ru'?'Введи KCu4ZY в первые 5 часов':'Enter KCu4ZY within the first 5 hours'}</li>
                </ol>
              </section>
            </div>
            <div className="guide-bonus"><span>🎁</span><div><b>{lang==='ru'?'Бонус $15':'$15 bonus'}</b><small>{lang==='ru'?'Для подходящих новых стримеров • условия подтверждает менеджер':'For eligible new creators • conditions confirmed by your manager'}</small></div></div>
          </div>
        </div>
      </section>

      <section className="section" id="how">
        <div className="section-head">
          <div><span className="section-number">01</span><h2>{t.journey}</h2></div>
          <p>{t.journeySub}</p>
        </div>
        <div className="steps-grid">
          {steps[lang].map(([n,label],i)=><div className="step-card" key={n}>
            <span>{n}</span><div className="step-icon">{i===4?<CircleDollarSign/>:<ArrowRight/>}</div><h3>{label}</h3>
          </div>)}
        </div>
      </section>

      <section className="section alt" id="benefits">
        <div className="section-head">
          <div><span className="section-number">02</span><h2>{t.offer}</h2></div><p>{t.offerSub}</p>
        </div>
        <div className="benefits-grid">
          {benefits[lang].map(([label,Icon])=><div className="benefit-card" key={label as string}><Icon/><span>{label as string}</span></div>)}
        </div>
      </section>

      <section className="section" id="bonuses">
        <div className="section-head">
          <div><span className="section-number">03</span><h2>{t.bonuses}</h2></div><p>{t.bonusesSub}</p>
        </div>
        <div className="bonus-grid">
          <article className="bonus-card featured">
            <span className="bonus-icon"><Sparkles/></span><small>{t.welcome}</small>
            <h3>{settings.welcome_bonus}</h3><p>{t.welcomeText} {settings.welcome_bonus}.</p>
          </article>
          <article className="bonus-card">
            <span className="bonus-icon"><Diamond/></span><small>{t.milestone}</small>
            <h3>{settings.milestone_title}</h3><p>{settings.milestone_reward}</p>
          </article>
          <article className="bonus-card ftr-card">
            <span className="bonus-icon"><Target/></span><small>{lang==='ru'?'Обучение':'Education'}</small>
            <h3>{t.growthTitle}</h3><p>{t.growth}</p>
          </article>
        </div>
        <p className="fine-print">{t.bonusNote}</p>
      </section>

      <section className="section criteria-section">
        <div className="criteria-panel">
          <div className="criteria-copy"><span className="section-number">04</span><h2>{t.looking}</h2><p>{t.lookingSub}</p></div>
          <div className="criteria-list">
            {criteria[lang].map(x=><div key={x}><span><Check size={15}/></span>{x}</div>)}
          </div>
        </div>
        <div className="warning-card"><ShieldCheck/><p>{t.warning}</p></div>
      </section>

      <section className="manifesto">
        <div className="manifesto-inner">
          <small>ABHIGREEN</small>
          <h2>{t.longTitle}<br/><span>{t.longSub}</span></h2>
          <a href="#apply" className="button gold">{t.applyTitle}<ArrowRight size={17}/></a>
        </div>
      </section>

      <section className="section community-section">
        <div className="community-card">
          <div className="community-icon"><Users/></div>
          <div><small>{lang==='ru'?'ЗАКРЫТОЕ СООБЩЕСТВО СТРИМЕРОВ':'PRIVATE CREATOR SPACE'}</small><h2>{t.community}</h2><p>{t.communitySub}</p></div>
          {settings.telegram_url ? <a className="button ghost" target="_blank" rel="noopener noreferrer" href={settings.telegram_url}>{t.telegram}<ArrowRight size={16}/></a> : <a className="button ghost" href="#apply">{t.join}<ArrowRight size={16}/></a>}
        </div>
      </section>

      <section className="section faq-section" id="faq">
        <div className="section-head"><div><span className="section-number">05</span><h2>{t.faq}</h2></div></div>
        <div className="faq-list">
          {faqItems.map(([q,a],i)=><div className={'faq-item '+(openFaq===i?'open':'')} key={q}>
            <button type="button" aria-expanded={openFaq===i} aria-controls={`faq-answer-${i}`} onClick={()=>setOpenFaq(openFaq===i?null:i)}><span>{q}</span><ChevronDown/></button>
            <div className="faq-answer" id={`faq-answer-${i}`}><p>{a}</p></div>
          </div>)}
        </div>
      </section>

      <section className="section application-section" id="apply">
        <div className="application-shell">
          <div className="application-intro">
            <span className="section-number">06</span><h2>{t.applyTitle}</h2><p>{t.applySub}</p>
            <div className="mini-points"><span><Check/>18+</span><span><Check/>{lang==='ru'?'Реальные стримеры':'Real creators'}</span><span><Check/>{lang==='ru'?'Поддержка RU / EN':'RU / EN support'}</span></div>
          </div>
          {sent ? <div className="success-panel" role="status" aria-live="polite"><BadgeCheck size={44}/><h3>{t.success}</h3><button className="button ghost" type="button" onClick={()=>setSent(false)}>OK</button></div> :
          <form className="application-form" onSubmit={submit} noValidate={false}>
            <label className="hp-field" aria-hidden="true">Website<input name="website" tabIndex={-1} autoComplete="off"/></label>
            <div className="form-grid">
              <label>{t.form.name}<input name="name" required maxLength={120} autoComplete="name"/></label>
              <label>{t.form.country}<input name="country" required maxLength={100} autoComplete="country-name"/></label>
              <label>{t.form.languages}<input name="languages" maxLength={200}/></label>
              <label>{t.form.telegram}<input name="telegram" maxLength={150} autoComplete="off" placeholder="@username"/></label>
              <label>{t.form.whatsapp}<input name="whatsapp" maxLength={150} autoComplete="tel" inputMode="tel"/></label>
              <label>{t.form.instagram}<input name="instagram" maxLength={150} autoComplete="off" placeholder="@username"/></label>
              <label>{t.form.platform}<input name="platform" maxLength={100} placeholder="Tango, SuperLive, Bigo..."/></label>
              <label>{t.form.username}<input name="username" maxLength={150}/></label>
              <label className="full">{t.form.experience}<textarea name="experience" rows={3} maxLength={1000}/></label>
              <label>{t.form.hours}<input name="hours_per_week" maxLength={80} inputMode="numeric" placeholder="10, 20, 30..."/></label>
              <label className="full">{t.form.message}<textarea name="message" rows={4} maxLength={2000}/></label>
            </div>
            <label className="check-row"><input type="checkbox" name="age_confirmed" required/><span>{t.age}</span></label>
            <label className="check-row"><input type="checkbox" name="consent" required/><span>{t.consent} <a href="/privacy">{lang==='ru'?'Политика конфиденциальности':'Privacy Policy'}</a> / <a href="/terms">{lang==='ru'?'Условия':'Terms'}</a></span></label>
            {formError&&<div className="form-error" role="alert" aria-live="polite"><AlertCircle size={18}/><span>{formError}</span></div>}
            <button className="button gold submit-button" disabled={sending} aria-busy={sending}>{sending?t.sending:t.submit}<ArrowRight size={17}/></button>
          </form>}
        </div>
      </section>

      <footer className="footer">
        <div><Logo/><p>{t.footer}</p></div>
        <div className="footer-links"><a href="/privacy">{lang==='ru'?'Политика конфиденциальности':'Privacy Policy'}</a><a href="/terms">{lang==='ru'?'Условия использования':'Terms & Conditions'}</a></div>
        <div className="footer-socials">{socialLinks.map(([name,url,Icon])=><a key={name as string} href={url as string} target="_blank" rel="noopener noreferrer"><Icon size={17}/>{name as string}</a>)}</div>
        <small>© {new Date().getFullYear()} ABHIGREEN. 18+ only.</small>
      </footer>

      {socialLinks.length>0 && <div className="floating-socials">{socialLinks.slice(0,2).map(([name,url,Icon])=><a aria-label={name as string} key={name as string} href={url as string} target="_blank" rel="noopener noreferrer"><Icon/></a>)}</div>}
    </main>
  )
}
