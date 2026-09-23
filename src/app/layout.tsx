import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'ABHIGREEN — Live Streaming Talent Agency',
  description: 'ABHIGREEN helps women 18+ start live streaming on Tango, grow an audience, learn monetization and get personal creator support.',
  metadataBase: new URL('https://mynameisnastasya.github.io/tango/'),
  alternates: { canonical: 'https://mynameisnastasya.github.io/tango/' },
  robots: { index: true, follow: true },
  openGraph: {
    title: 'ABHIGREEN',
    description: 'Start live streaming with ABHIGREEN. Training, personal support, Tango connection and a $15 joining bonus for eligible new creators.',
    type: 'website',
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
