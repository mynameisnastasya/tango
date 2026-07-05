import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Настасья — маркетолог и создатель сайтов',
  description: 'Премиальный лендинг Настасьи: маркетинг, визуальная эстетика и сайты, которые продают, раскрывают бренд и приводят клиентов.',
  openGraph: {
    title: 'Настасья — сайты, которые выглядят дорого и приводят клиентов',
    description: 'Маркетинг + дизайн + структура. Сайты для экспертов, брендов и бизнеса.',
    type: 'website',
    locale: 'ru_RU',
    images: ['/og.svg']
  },
  icons: {
    icon: '/favicon.svg'
  }
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>{children}</body>
    </html>
  )
}
