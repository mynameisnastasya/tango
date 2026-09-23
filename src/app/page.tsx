'use client'

import { FormEvent, useEffect, useMemo, useState } from 'react'
import {
  ArrowRight, BadgeCheck, Check, ChevronDown, CircleDollarSign, Crown,
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
  welcome_bonus: '4,000–5,000 coins',
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
    h1c: 'with ABHI AGANCY',
    sub: 'Join an international agency, receive personal support, onboarding, bonuses and guidance from your first stream to your first withdrawal.',
    joinNow: 'Join Now',
    learn: 'Learn How It Works',
    realOnly: 'Real broadcasters only',
    noFake: 'No prerecorded or fake broadcasts',
    tangoCodeTitle: 'Connect to ABHI AGANCY on Tango',
    tangoCodeSub: 'Use this agency code inside the Tango app when connecting your broadcaster account to ABHI AGANCY. This code is entered in Tango — not on this website.',
    tangoCodeLabel: 'Tango Agency Code',
    copyCode: 'Copy Code',
    copied: 'Copied',
    journey: 'A clear path from application to first withdrawal',
    journeySub: 'You do not need to figure everything out alone. Our team guides new broadcasters during onboarding.',
    offer: 'What We Offer',
    offerSub: 'Support that stays useful after your first stream.',
    bonuses: 'Bonuses & Milestones',
    bonusesSub: 'Campaigns are editable and may change. Final conditions are always confirmed by your manager.',
    welcome: 'Welcome Bonus',
    welcomeText: 'New eligible broadcasters may receive approximately',
    milestone: 'Milestone',
    bonusNote: 'Bonuses, coin amounts, eligibility requirements and campaigns may change. Final conditions are confirmed individually by the agency manager before participation.',
    ftrTitle: 'What is FTR?',
    ftr: 'FTR means First Time Redeemer — a new broadcaster who reaches the required balance and successfully completes their first eligible withdrawal.',
    looking: 'Who We Are Looking For',
    lookingSub: 'Creators who want to communicate, grow and broadcast consistently.',
    warning: 'Prerecorded streams, fake broadcasters, impersonation, or attempts to bypass platform rules are not accepted.',
    longTitle: 'Your manager from day one.',
    longSub: 'Your agency for the long run.',
    community: 'ABHI Creator Community',
    communitySub: 'Accepted broadcasters get access to onboarding information, training materials, announcements, challenges, contests, bonus news and manager support.',
    telegram: 'Open Telegram',
    faq: 'Frequently Asked Questions',
    applyTitle: 'Become an ABHI Creator',
    applySub: 'Tell us a little about yourself. A manager will review your application and contact you.',
    submit: 'Send Application',
    sending: 'Sending...',
    success: 'Thank you! Your application has been received. Our manager will contact you soon.',
    consent: 'I confirm that I am 18 years or older and agree to the Privacy Policy and Terms.',
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
    eyebrow: 'Международное creator-агентство • 18+',
    h1a: 'Начни свой путь',
    h1b: 'в live-стриминге',
    h1c: 'с ABHI AGANCY',
    sub: 'Присоединяйся к международному агентству и получай персональное сопровождение, onboarding, бонусы и помощь от первого эфира до первого вывода.',
    joinNow: 'Присоединиться',
    learn: 'Как это работает',
    realOnly: 'Только реальные стримеры',
    noFake: 'Без записанных и фейковых трансляций',
    tangoCodeTitle: 'Подключись к ABHI AGANCY в Tango',
    tangoCodeSub: 'Этот код нужно ввести внутри приложения Tango при подключении своего аккаунта стримера к ABHI AGANCY. На этом сайте вводить его не нужно.',
    tangoCodeLabel: 'Код агентства в Tango',
    copyCode: 'Скопировать код',
    copied: 'Скопировано',
    journey: 'Понятный путь от заявки до первого вывода',
    journeySub: 'Не нужно разбираться во всём одной. Команда сопровождает новых стримеров во время onboarding.',
    offer: 'Что мы даём',
    offerSub: 'Поддержка, которая не заканчивается после первого эфира.',
    bonuses: 'Бонусы и Milestones',
    bonusesSub: 'Условия кампаний редактируются и могут меняться. Финальные условия всегда подтверждает менеджер.',
    welcome: 'Welcome Bonus',
    welcomeText: 'Подходящие новые стримеры могут получить примерно',
    milestone: 'Milestone',
    bonusNote: 'Размеры бонусов, coins, требования и кампании могут меняться. Финальные условия подтверждаются менеджером индивидуально до участия.',
    ftrTitle: 'Что такое FTR?',
    ftr: 'FTR = First Time Redeemer — новый стример, который выполнил условия платформы и впервые успешно вывел заработанные средства.',
    looking: 'Кого мы ищем',
    lookingSub: 'Девушек, которым комфортно общаться, развиваться и регулярно выходить в эфир.',
    warning: 'Записанные трансляции, фейковые стримеры, выдача себя за другого человека и обход правил платформы не принимаются.',
    longTitle: 'Твой менеджер с первого дня.',
    longSub: 'Твоё агентство на долгий путь.',
    community: 'ABHI Creator Community',
    communitySub: 'Принятые стримеры получают onboarding-материалы, обучение, объявления агентства, челленджи, конкурсы, новости о бонусах и поддержку менеджеров.',
    telegram: 'Открыть Telegram',
    faq: 'Частые вопросы',
    applyTitle: 'Стать стримером ABHI',
    applySub: 'Расскажи немного о себе. Менеджер рассмотрит заявку и свяжется с тобой.',
    submit: 'Отправить заявку',
    sending: 'Отправляем...',
    success: 'Спасибо! Заявка получена. Наш менеджер скоро свяжется с тобой.',
    consent: 'Мне 18 лет или больше, и я соглашаюсь с Privacy Policy и Terms.',
    form: {
      name:'Имя', country:'Страна', languages:'Языки', telegram:'Telegram username',
      whatsapp:'WhatsApp', instagram:'Instagram username', platform:'Текущая стриминг-платформа',
      experience:'Опыт live-стриминга', username:'Ник в Tango / SuperLive / Bigo / etc.',
      hours:'Сколько часов в неделю можешь стримить?', message:'Коротко о себе'
    },
    age: 'Мне 18 лет или больше',
    footer: 'Премиальное talent management агентство для реальных live-стримеров.',
  }
}

const steps = {
  en: [
    ['01','Submit your application'], ['02','Receive Tango connection instructions and the agency code'],
    ['03','Create or connect your broadcaster account'], ['04','Complete onboarding and start streaming'],
    ['05','Earn coins / diamonds and make your first withdrawal'],
  ],
  ru: [
    ['01','Отправь заявку'], ['02','Получи инструкцию для подключения в Tango и код агентства'],
    ['03','Создай или подключи broadcaster account'], ['04','Пройди onboarding и начни эфиры'],
    ['05','Зарабатывай coins / diamonds и сделай первый вывод'],
  ],
}

const benefits = {
  en: [
    ['Personal onboarding', HeartHandshake], ['Russian & English support', Languages],
    ['Platform rules explained', ShieldCheck], ['Streaming tips', Sparkles],
    ['Creator community', Users], ['Performance bonuses', CircleDollarSign],
    ['Events, challenges & battles', Zap], ['Help reaching FTR', Target],
    ['Long-term support', Crown],
  ],
  ru: [
    ['Персональный onboarding', HeartHandshake], ['Поддержка RU / EN', Languages],
    ['Помощь с правилами платформ', ShieldCheck], ['Советы по эфирам', Sparkles],
    ['Creator community', Users], ['Performance-бонусы', CircleDollarSign],
    ['Ивенты, челленджи и батлы', Zap], ['Помощь с достижением FTR', Target],
    ['Долгосрочная поддержка', Crown],
  ],
}

const criteria = {
  en: ['Be 18+', 'Be comfortable appearing live on camera', 'Use your real identity and content', 'Be willing to communicate with viewers', 'Follow streaming platform rules', 'Be interested in regular live broadcasting'],
  ru: ['Быть 18+', 'Комфортно чувствовать себя в кадре', 'Использовать свою реальную личность и контент', 'Быть готовой общаться со зрителями', 'Соблюдать правила платформы', 'Быть заинтересованной в регулярных эфирах'],
}

const faqs = {
  en: [
    ['Is joining the agency free?', 'Yes. ABHI AGANCY does not charge an application or joining fee. Platform and campaign rules may differ.'],
    ['Do I need previous experience?', 'No. Beginners can apply and receive onboarding support.'],
    ['Can beginners join?', 'Yes, if you are 18+ and willing to learn and follow platform rules.'],
    ['What is the Tango Agency Code?', 'KCu4ZY is the ABHI AGANCY code used inside Tango when connecting your broadcaster account to our agency. Detailed step-by-step instructions will be added separately.'],
    ['What is FTR?', 'First Time Redeemer: your first successful eligible withdrawal after reaching the required platform balance.'],
    ['When can I withdraw earnings?', 'Withdrawal timing depends on the platform rules, balance requirements and your account eligibility.'],
    ['Are bonuses guaranteed?', 'No. Bonuses and campaigns can change and are confirmed by your manager before participation.'],
    ['Which countries can join?', 'We work internationally. Eligibility can depend on the current platform and campaign.'],
    ['Can I work with other agencies?', 'This depends on the platform and your existing agency agreement. Ask your manager before joining another agency.'],
    ['What if my account belongs to another agency?', 'Tell us before onboarding. We will explain the available options under the platform rules.'],
    ['Do I need to stream every day?', 'Not necessarily. Consistency matters, but the recommended schedule depends on your goals and platform conditions.'],
    ['Are prerecorded streams allowed?', 'No. ABHI AGANCY accepts real live broadcasters only.'],
  ],
  ru: [
    ['Вступление в агентство бесплатное?', 'Да. ABHI AGANCY не берёт плату за заявку или вступление. Правила платформ и кампаний могут отличаться.'],
    ['Нужен ли опыт?', 'Нет. Новички могут подать заявку и пройти onboarding.'],
    ['Можно ли новичкам?', 'Да, если тебе 18+ и ты готова учиться и соблюдать правила платформы.'],
    ['Что такое Tango Agency Code?', 'KCu4ZY — код ABHI AGANCY, который вводится внутри Tango при подключении аккаунта стримера к нашему агентству. Пошаговую инструкцию мы добавим отдельно.'],
    ['Что такое FTR?', 'First Time Redeemer — первый успешный вывод после достижения необходимого баланса и выполнения условий платформы.'],
    ['Когда можно вывести деньги?', 'Сроки зависят от правил платформы, минимального баланса и eligibility аккаунта.'],
    ['Бонусы гарантированы?', 'Нет. Условия и кампании могут меняться и подтверждаются менеджером до участия.'],
    ['Из каких стран можно?', 'Мы работаем международно. Eligibility зависит от текущей платформы и кампании.'],
    ['Можно работать с другими агентствами?', 'Это зависит от правил платформы и твоих действующих агентских условий. Лучше уточнить у менеджера.'],
    ['Что если аккаунт уже в другом агентстве?', 'Скажи об этом до onboarding. Мы объясним доступные варианты по правилам платформы.'],
    ['Нужно стримить каждый день?', 'Не обязательно. Важна регулярность, а график зависит от целей и условий платформы.'],
    ['Записанные эфиры разрешены?', 'Нет. ABHI AGANCY принимает только реальных live-стримеров.'],
  ],
}

function Logo() {
  return <a href="#top" className="brand"><span className="brand-mark">A</span><span>ABHI <b>AGANCY</b></span></a>
}

export default function Home() {
  const [lang, setLang] = useState<Lang>('en')
  const [menu, setMenu] = useState(false)
  const [settings, setSettings] = useState<Settings>(initialSettings)
  const [copiedCode, setCopiedCode] = useState(false)
  const [openFaq, setOpenFaq] = useState<number | null>(0)
  const [sending, setSending] = useState(false)
  const [sent, setSent] = useState(false)
  const t = copy[lang]
  const configuredFaq = lang === 'en' ? settings.faq_en : settings.faq_ru
  const faqItems = Array.isArray(configuredFaq) && configuredFaq.length ? configuredFaq : faqs[lang]

  useEffect(() => {
    fetch('/api/settings').then(r => r.ok ? r.json() : null).then(x => x && setSettings(x)).catch(() => {})
  }, [])

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
    setSending(true)
    const fd = new FormData(e.currentTarget)
    const data = Object.fromEntries(fd.entries())
    const payload = {
      ...data,
      age_confirmed: fd.get('age_confirmed') === 'on',
      consent: fd.get('consent') === 'on',
      referral_code: '',
      source: window.location.href,
    }
    try {
      const res = await fetch('/api/applications', {
        method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)
      })
      if (!res.ok) {
        const saved = JSON.parse(localStorage.getItem('abhi_demo_applications') || '[]')
        saved.unshift({ id: crypto.randomUUID(), created_at:new Date().toISOString(), status:'New', ...payload })
        localStorage.setItem('abhi_demo_applications', JSON.stringify(saved))
      }
      setSent(true)
      e.currentTarget.reset()
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
      <div className="top-note"><ShieldCheck size={14}/> 18+ • Real broadcasters only • International support</div>
      <header className="header">
        <Logo />
        <nav className="desktop-nav">
          {t.nav.map((x,i)=><a key={x} href={['#how','#benefits','#bonuses','#faq','#apply'][i]}>{x}</a>)}
        </nav>
        <div className="header-actions">
          <button className="lang-switch" onClick={()=>setLang(lang==='en'?'ru':'en')}><Globe2 size={15}/>{lang.toUpperCase()}</button>
          <a className="button small gold" href="#apply">{t.join}</a>
          <button className="menu-btn" onClick={()=>setMenu(!menu)}>{menu?<X/>:<Menu/>}</button>
        </div>
      </header>

      {menu && <div className="mobile-nav">
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
          <div className="phone">
            <div className="phone-top"><span className="live-dot"/> LIVE <span>02:14:37</span></div>
            <div className="creator-stage">
              <div className="creator-avatar">A</div>
              <div className="stream-copy"><small>ABHI CREATOR</small><strong>Build your community.</strong><span>Real conversations. Real growth.</span></div>
            </div>
            <div className="stream-stats">
              <div><Users size={16}/><b>Community</b></div>
              <div><Diamond size={16}/><b>Milestones</b></div>
              <div><Star size={16}/><b>Support</b></div>
            </div>
          </div>
          <div className="float-card card-one"><HeartHandshake/><span>Personal manager<br/><b>from day one</b></span></div>
          <div className="float-card card-two"><Globe2/><span>International<br/><b>RU / EN</b></span></div>
        </div>
      </section>

      <section className="section referral-section">
        <div className="referral-card tango-code-card">
          <div>
            <div className="eyebrow gold-text"><Target size={15}/> TANGO • AGENCY CONNECTION</div>
            <h2>{t.tangoCodeTitle}</h2>
            <p>{t.tangoCodeSub}</p>
          </div>
          <div className="tango-code-box">
            <small>{t.tangoCodeLabel}</small>
            <div className="tango-code">KCu4ZY</div>
            <button className="button gold tango-copy" onClick={copyTangoCode}>
              {copiedCode ? <Check size={17}/> : <Target size={17}/>}
              {copiedCode ? t.copied : t.copyCode}
            </button>
            <p className="tango-code-help">Tango → connect your broadcaster account → enter <b>KCu4ZY</b></p>
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
            <span className="bonus-icon"><Target/></span><small>Education</small>
            <h3>{t.ftrTitle}</h3><p>{t.ftr}</p>
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
          <small>ABHI AGANCY</small>
          <h2>{t.longTitle}<br/><span>{t.longSub}</span></h2>
          <a href="#apply" className="button gold">{t.applyTitle}<ArrowRight size={17}/></a>
        </div>
      </section>

      <section className="section community-section">
        <div className="community-card">
          <div className="community-icon"><Users/></div>
          <div><small>PRIVATE CREATOR SPACE</small><h2>{t.community}</h2><p>{t.communitySub}</p></div>
          {settings.telegram_url ? <a className="button ghost" target="_blank" rel="noreferrer" href={settings.telegram_url}>{t.telegram}<ArrowRight size={16}/></a> : <a className="button ghost" href="#apply">{t.join}<ArrowRight size={16}/></a>}
        </div>
      </section>

      <section className="section faq-section" id="faq">
        <div className="section-head"><div><span className="section-number">05</span><h2>{t.faq}</h2></div></div>
        <div className="faq-list">
          {faqItems.map(([q,a],i)=><div className={'faq-item '+(openFaq===i?'open':'')} key={q}>
            <button onClick={()=>setOpenFaq(openFaq===i?null:i)}><span>{q}</span><ChevronDown/></button>
            <div className="faq-answer"><p>{a}</p></div>
          </div>)}
        </div>
      </section>

      <section className="section application-section" id="apply">
        <div className="application-shell">
          <div className="application-intro">
            <span className="section-number">06</span><h2>{t.applyTitle}</h2><p>{t.applySub}</p>
            <div className="mini-points"><span><Check/>18+</span><span><Check/>Real creators</span><span><Check/>RU / EN support</span></div>
          </div>
          {sent ? <div className="success-panel"><BadgeCheck size={44}/><h3>{t.success}</h3><button className="button ghost" onClick={()=>setSent(false)}>OK</button></div> :
          <form className="application-form" onSubmit={submit}>
            <div className="form-grid">
              <label>{t.form.name}<input name="name" required/></label>
              <label>{t.form.country}<input name="country" required/></label>
              <label>{t.form.languages}<input name="languages"/></label>
              <label>{t.form.telegram}<input name="telegram"/></label>
              <label>{t.form.whatsapp}<input name="whatsapp"/></label>
              <label>{t.form.instagram}<input name="instagram"/></label>
              <label>{t.form.platform}<input name="platform" placeholder="Tango, SuperLive, Bigo..."/></label>
              <label>{t.form.username}<input name="username"/></label>
              <label className="full">{t.form.experience}<textarea name="experience" rows={3}/></label>
              <label>{t.form.hours}<input name="hours_per_week" placeholder="10, 20, 30..."/></label>
              <label className="full">{t.form.message}<textarea name="message" rows={4}/></label>
            </div>
            <label className="check-row"><input type="checkbox" name="age_confirmed" required/><span>{t.age}</span></label>
            <label className="check-row"><input type="checkbox" name="consent" required/><span>{t.consent} <a href="/privacy">Privacy</a> / <a href="/terms">Terms</a></span></label>
            <button className="button gold submit-button" disabled={sending}>{sending?t.sending:t.submit}<ArrowRight size={17}/></button>
          </form>}
        </div>
      </section>

      <footer className="footer">
        <div><Logo/><p>{t.footer}</p></div>
        <div className="footer-links"><a href="/privacy">Privacy Policy</a><a href="/terms">Terms & Conditions</a><a href="/admin">Admin</a></div>
        <div className="footer-socials">{socialLinks.map(([name,url,Icon])=><a key={name as string} href={url as string} target="_blank" rel="noreferrer"><Icon size={17}/>{name as string}</a>)}</div>
        <small>© {new Date().getFullYear()} ABHI AGANCY. 18+ only.</small>
      </footer>

      {socialLinks.length>0 && <div className="floating-socials">{socialLinks.slice(0,2).map(([name,url,Icon])=><a aria-label={name as string} key={name as string} href={url as string} target="_blank" rel="noreferrer"><Icon/></a>)}</div>}
    </main>
  )
}
