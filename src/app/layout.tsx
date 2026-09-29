import type { Metadata } from 'next'
import './globals.css'

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://mynameisnastasya.github.io/tango/'
const socialImage = 'https://images.pexels.com/photos/7676397/pexels-photo-7676397.jpeg?auto=compress&cs=tinysrgb&w=1600'

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: 'ABHIGREEN — Live Streaming Talent Agency',
    template: '%s | ABHIGREEN',
  },
  description: 'ABHIGREEN helps women 18+ start live streaming on Tango, build an audience, learn monetization and get personal creator support.',
  applicationName: 'ABHIGREEN',
  alternates: { canonical: siteUrl },
  robots: { index: true, follow: true },
  openGraph: {
    title: 'ABHIGREEN — Live Streaming Talent Agency',
    description: 'Start live streaming with ABHIGREEN. Training, personal support, Tango connection and onboarding guidance for eligible women 18+.',
    type: 'website',
    url: siteUrl,
    siteName: 'ABHIGREEN',
    images: [{ url: socialImage, alt: 'ABHIGREEN live streaming creator' }],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'ABHIGREEN — Live Streaming Talent Agency',
    description: 'Training, personal support and Tango onboarding for eligible women 18+.',
    images: [socialImage],
  },
  formatDetection: { telephone: false },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
