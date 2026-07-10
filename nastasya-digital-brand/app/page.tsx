import { ArrowUpRight, Check, MessageCircle, Send, Sparkles } from "lucide-react";

const services = [
  {
    number: "01",
    title: "Сайт под заявки",
    forWhom: "Для экспертов, услуг и малого бизнеса, которым нужен понятный и сильный сайт.",
    inside: "Структура, тексты, дизайн, адаптив, кнопки заявки и визуальная упаковка.",
    result: "Сайт объясняет ценность продукта и ведёт клиента к заявке.",
  },
  {
    number: "02",
    title: "Digital-упаковка бизнеса",
    forWhom: "Для тех, кто хочет выглядеть дороже и продавать увереннее.",
    inside: "Сайт, оффер, визуал, структура профиля и Telegram-точка входа.",
    result: "Бизнес выглядит цельно, дорого и понятно.",
  },
  {
    number: "03",
    title: "Telegram-воронка",
    forWhom: "Для экспертов и проектов, которым нужен путь от интереса до покупки.",
    inside: "Точка входа, лид-магнит, прогрев, структура канала, посты и CTA.",
    result: "Человек не теряется после первого касания и доходит до заявки.",
  },
  {
    number: "04",
    title: "AI-визуал и аватары",
    forWhom: "Для личного бренда, запусков, Reels, обложек и визуальной упаковки.",
    inside: "Концепция, стилистика, генерация и серия согласованных визуалов.",
    result: "Запоминающийся визуал усиливает бренд и делает его узнаваемым.",
  },
];

const process = [
  ["Диагностика", "Смотрю продукт, аудиторию, текущую упаковку и точки, где теряются заявки."],
  ["Оффер и структура", "Формулирую, что нужно сказать клиенту, чтобы он понял вашу ценность."],
  ["Прототип", "Собираю логику страницы: блоки, порядок, смыслы и сценарий движения."],
  ["Дизайн", "Создаю визуал, который выглядит дорого, понятно и не перегружает."],
  ["Воронка", "Добавляю путь до заявки: кнопки, Telegram, форму, сообщения и прогрев."],
  ["Запуск", "Вы получаете готовую digital-упаковку, которую не стыдно показывать клиентам."],
];

const fit = [
  "у вас сильный продукт, но слабая упаковка",
  "вы хотите выглядеть дороже и увереннее",
  "вам стыдно давать ссылку на старый сайт",
  "люди заходят, но не оставляют заявки",
  "непонятно, что писать на первом экране",
  "нужна не просто картинка, а система",
  "сайт, Telegram и визуал должны говорить на одном языке",
];

const includes = [
  "анализ продукта",
  "упаковка оффера",
  "структура сайта",
  "тексты под заявку",
  "дизайн и адаптив",
  "визуальная система",
  "Telegram-воронка",
  "AI-визуал при необходимости",
];

function SectionHeading({ eyebrow, title, text }: { eyebrow: string; title: string; text?: string }) {
  return (
    <div className="max-w-3xl">
      <p className="eyebrow">{eyebrow}</p>
      <h2 className="section-title mt-4">{title}</h2>
      {text && <p className="mt-6 max-w-2xl text-lg leading-8 text-graphite/65">{text}</p>}
    </div>
  );
}

export default function Page() {
  return (
    <main className="overflow-hidden">
      <header className="fixed inset-x-0 top-0 z-50 border-b border-graphite/10 bg-milk/80 backdrop-blur-xl">
        <div className="container flex h-20 items-center justify-between">
          <a href="#top" className="display text-xl uppercase tracking-[-0.04em]">Nastasya®</a>
          <nav className="hidden items-center gap-7 text-sm font-semibold md:flex">
            <a href="#services">Услуги</a>
            <a href="#cases">Кейсы</a>
            <a href="#about">Обо мне</a>
            <a href="#audit">Аудит</a>
          </nav>
          <a href="#audit" className="btn btn-dark text-sm">Мини-аудит <ArrowUpRight size={16} /></a>
        </div>
      </header>

      <section id="top" className="hero-grid relative min-h-screen pt-32 md:pt-40">
        <div className="orb orb-one" />
        <div className="orb orb-two" />
        <div className="container relative z-10 grid items-center gap-14 pb-24 md:grid-cols-[1.12fr_.88fr] md:pb-32">
          <div>
            <p className="eyebrow"><Sparkles size={14} /> digital packaging & conversion design</p>
            <h1 className="hero-title mt-7">Сайты, которые приводят <span>заявки</span>, а не просто красиво выглядят</h1>
            <p className="mt-7 max-w-2xl text-lg leading-8 text-graphite/68 md:text-xl">
              Собираю сайт, оффер, визуал и Telegram-воронку, чтобы клиент за 5 секунд понял вашу ценность, доверился и написал.
            </p>
            <div className="mt-9 flex flex-col gap-3 sm:flex-row">
              <a href="#audit" className="btn btn-primary">Получить мини-аудит <ArrowUpRight size={18} /></a>
              <a href="#services" className="btn btn-secondary">Посмотреть услуги</a>
            </div>
            <p className="mt-6 text-sm text-graphite/50">Для экспертов, услуг, личных брендов и малого бизнеса.</p>
          </div>

          <div className="relative mx-auto w-full max-w-[520px]">
            <div className="portrait-card">
              <div className="portrait-glow" />
              <div className="relative z-10 flex h-full flex-col justify-between">
                <div className="flex justify-between text-xs font-black uppercase tracking-[.22em] text-milk/70">
                  <span>premium digital femme</span><span>2026</span>
                </div>
                <div>
                  <p className="script text-5xl text-champagne md:text-6xl">Nastasya</p>
                  <p className="mt-3 max-w-xs text-sm leading-6 text-milk/70">Смысл. Доверие. Визуал. Путь до заявки.</p>
                </div>
              </div>
            </div>
            {[
              ["website", "top-8 -left-5 md:-left-16"],
              ["offer", "top-28 -right-3 md:-right-14"],
              ["telegram funnel", "bottom-28 -left-4 md:-left-20"],
              ["AI visual", "bottom-10 right-2 md:-right-10"],
              ["lead", "top-1/2 left-1/2 -translate-x-1/2"],
            ].map(([label, position]) => <span key={label} className={`floating-tag ${position}`}>{label}</span>)}
          </div>
        </div>
      </section>

      <section className="section-pad bg-graphite text-milk">
        <div className="container grid gap-12 md:grid-cols-[.85fr_1.15fr] md:items-end">
          <div>
            <p className="eyebrow eyebrow-light">Где теряются заявки</p>
            <h2 className="section-title mt-5 text-milk">Ваш сайт может быть красивым, но всё равно сливать клиентов</h2>
          </div>
          <div>
            <p className="text-lg leading-8 text-milk/68">Проблема не всегда в дизайне. Человек заходит и не понимает, что вы продаёте, почему это стоит своих денег, чем вы отличаетесь, можно ли вам доверять и куда нажать.</p>
            <p className="mt-9 border-l-2 border-bordeaux pl-6 text-2xl font-semibold leading-tight md:text-3xl">Красивый сайт без смысла — просто картинка. Сильный сайт ведёт человека к действию.</p>
          </div>
        </div>
      </section>

      <section className="section-pad">
        <div className="container grid gap-12 md:grid-cols-[1.05fr_.95fr]">
          <SectionHeading eyebrow="Система вместо декора" title="Я собираю не просто сайт. Я собираю путь клиента до заявки." text="Соединяю дизайн, маркетинг, оффер, структуру, визуал и Telegram-точку входа. Чтобы клиент не просто посмотрел страницу, а понял: «Да, мне нужно именно сюда»." />
          <div className="grid gap-3 sm:grid-cols-2">
            {includes.map((item, index) => (
              <div key={item} className="soft-card flex items-start gap-4 p-5">
                <span className="number-dot">{String(index + 1).padStart(2, "0")}</span>
                <p className="pt-1 font-semibold">{item}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="services" className="section-pad bg-white/30">
        <div className="container">
          <SectionHeading eyebrow="Что я делаю" title="Упаковка, в которой каждый элемент работает на продажу" />
          <div className="mt-14 grid gap-5 md:grid-cols-2">
            {services.map((service) => (
              <article key={service.title} className="service-card group">
                <div className="flex items-start justify-between gap-4">
                  <span className="display text-5xl text-bordeaux/35">{service.number}</span>
                  <ArrowUpRight className="transition-transform group-hover:translate-x-1 group-hover:-translate-y-1" />
                </div>
                <h3 className="mt-8 text-3xl font-semibold tracking-[-0.04em]">{service.title}</h3>
                <p className="mt-4 leading-7 text-graphite/62">{service.forWhom}</p>
                <div className="mt-7 border-t border-graphite/10 pt-6">
                  <p className="text-xs font-black uppercase tracking-[.18em] text-bordeaux">Что внутри</p>
                  <p className="mt-2 leading-7 text-graphite/72">{service.inside}</p>
                  <p className="mt-5 font-semibold">Результат: <span className="font-normal text-graphite/68">{service.result}</span></p>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="section-pad">
        <div className="container grid gap-12 md:grid-cols-[.9fr_1.1fr]">
          <SectionHeading eyebrow="Кому подойдёт" title="Этот сайт для вас, если…" />
          <div className="space-y-3">
            {fit.map((item) => (
              <div key={item} className="flex items-center gap-4 border-b border-graphite/10 py-4 text-lg">
                <span className="flex size-7 shrink-0 items-center justify-center rounded-full bg-bordeaux text-milk"><Check size={15} /></span>
                <span>{item}</span>
              </div>
            ))}
            <p className="pt-7 text-2xl font-semibold tracking-[-0.03em]">Если продукт сильный, упаковка не должна делать его дешевле.</p>
          </div>
        </div>
      </section>

      <section className="section-pad bg-[#e7ddd1]">
        <div className="container">
          <SectionHeading eyebrow="Процесс" title="Как проходит работа" text="Без хаоса, бесконечных правок и дизайна ради дизайна. Каждый этап отвечает на конкретный вопрос клиента." />
          <div className="mt-14 grid gap-px overflow-hidden rounded-[32px] border border-graphite/10 bg-graphite/10 md:grid-cols-3">
            {process.map(([title, text], index) => (
              <article key={title} className="bg-milk p-7 md:p-9">
                <p className="display text-4xl text-bordeaux/35">{String(index + 1).padStart(2, "0")}</p>
                <h3 className="mt-8 text-2xl font-semibold">{title}</h3>
                <p className="mt-4 leading-7 text-graphite/62">{text}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section id="cases" className="section-pad bg-graphite text-milk">
        <div className="container">
          <SectionHeading eyebrow="До / после" title="Показываю, как упаковка меняет восприятие бизнеса" text="Даже без десятков кейсов можно показать главное — логику, мышление и способность видеть, где бизнес теряет доверие и заявки." />
          <div className="mt-14 grid gap-5 md:grid-cols-3">
            {[
              ["Первый экран", "Непонятный заголовок и общий текст", "Ясный оффер и конкретный следующий шаг"],
              ["Telegram", "Канал без маршрута и призыва", "Точка входа, прогрев и путь к заявке"],
              ["AI-визуал", "Разрозненные картинки без характера", "Единая стилистика, которая усиливает бренд"],
            ].map(([title, before, after]) => (
              <article key={title} className="case-card">
                <p className="text-xs font-black uppercase tracking-[.2em] text-champagne">{title}</p>
                <div className="mt-8">
                  <span className="case-label">До</span><p className="mt-3 text-milk/55">{before}</p>
                </div>
                <div className="mt-7 border-t border-milk/10 pt-7">
                  <span className="case-label case-label-after">После</span><p className="mt-3 text-lg font-semibold">{after}</p>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section id="audit" className="section-pad">
        <div className="container">
          <div className="audit-card">
            <div>
              <p className="eyebrow eyebrow-light">Главная точка входа</p>
              <h2 className="mt-6 max-w-3xl text-4xl font-semibold leading-[1.04] tracking-[-0.055em] text-milk md:text-7xl">Не уверены, что ваш сайт продаёт?</h2>
              <p className="mt-7 max-w-2xl text-lg leading-8 text-milk/68">Посмотрю сайт, профиль или Telegram и покажу 3–5 точек, где теряются заявки: первый экран, оффер, доверие, визуал и путь до действия.</p>
              <a href="mailto:nastasyabaklykova@gmail.com?subject=Мини-аудит%20digital-упаковки&body=Здравствуйте,%20Настасья!%20Хочу%20мини-аудит.%20Ссылка%20на%20мой%20проект:%20" className="btn btn-light mt-9">Хочу мини-аудит <Send size={18} /></a>
              <p className="mt-5 text-sm text-milk/48">Напишите «АУДИТ» и добавьте ссылку на ваш проект.</p>
            </div>
            <div className="audit-orbit" aria-hidden="true">
              <div className="audit-core"><MessageCircle size={42} /></div>
              <span className="orbit-label orbit-one-label">оффер</span>
              <span className="orbit-label orbit-two-label">доверие</span>
              <span className="orbit-label orbit-three-label">CTA</span>
            </div>
          </div>
        </div>
      </section>

      <section id="about" className="section-pad pt-8">
        <div className="container grid items-center gap-12 md:grid-cols-[.8fr_1.2fr]">
          <div className="about-visual">
            <p className="script text-6xl text-champagne">about</p>
            <p className="display mt-auto text-5xl uppercase text-milk">смысл до шрифтов</p>
          </div>
          <div>
            <p className="eyebrow">Обо мне</p>
            <h2 className="section-title mt-5">Я Настасья. Создаю сайты, digital-упаковку и Telegram-воронки.</h2>
            <div className="mt-7 space-y-5 text-lg leading-8 text-graphite/68">
              <p>Я не начинаю работу с цветов и шрифтов. Сначала смотрю, почему клиент может не понять вашу ценность, где теряется доверие и что мешает оставить заявку.</p>
              <p>Для меня сайт — не просто красивая страница. Это первое впечатление, которое либо продаёт, либо обесценивает продукт.</p>
            </div>
            <p className="mt-8 text-2xl font-semibold tracking-[-0.035em]">Моя задача — сделать так, чтобы ваш бизнес выглядел дорого, понятно и уверенно.</p>
          </div>
        </div>
      </section>

      <section className="pb-8 pt-16 md:pb-12">
        <div className="container rounded-[36px] border border-graphite/10 bg-white/35 px-6 py-16 text-center md:px-12 md:py-24">
          <p className="eyebrow justify-center">Готовы усилить упаковку?</p>
          <h2 className="mx-auto mt-6 max-w-4xl text-4xl font-semibold leading-[1.02] tracking-[-0.055em] md:text-7xl">Хотите сайт, который работает на заявки?</h2>
          <p className="mx-auto mt-7 max-w-2xl text-lg leading-8 text-graphite/65">Давайте посмотрим, как сейчас выглядит ваша упаковка и что усилить, чтобы клиент быстрее понимал ценность и писал вам.</p>
          <div className="mt-9 flex flex-col justify-center gap-3 sm:flex-row">
            <a href="#audit" className="btn btn-primary">Получить мини-аудит <ArrowUpRight size={18} /></a>
            <a href="mailto:nastasyabaklykova@gmail.com?subject=Обсудить%20digital-упаковку" className="btn btn-secondary">Написать Настасье</a>
          </div>
        </div>
      </section>

      <footer className="pb-10 pt-6">
        <div className="container flex flex-col gap-4 border-t border-graphite/10 pt-7 text-sm text-graphite/50 sm:flex-row sm:items-center sm:justify-between">
          <p>© 2026 Nastasya Digital Brand</p>
          <p>Сайты · Офферы · Telegram · AI visual</p>
        </div>
      </footer>
    </main>
  );
}
