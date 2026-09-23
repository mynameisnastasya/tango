import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'ABHI AGENCY — Live Streaming Talent Agency',
  description: 'Join ABHI AGENCY for personal onboarding, creator support, live-streaming guidance, milestones and an international creator community.',
  metadataBase: new URL('https://example.com'),
  openGraph: {
    title: 'ABHI AGENCY',
    description: 'Your manager from day one. Your agency for the long run.',
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
