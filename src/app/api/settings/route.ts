import { NextRequest, NextResponse } from 'next/server'
import { DEFAULT_SETTINGS, isAdmin, isConfigured, supabase } from '@/lib/server'

const clean = (value: unknown, max: number) => String(value ?? '').trim().slice(0, max)

function normalizeHttpUrl(value: unknown) {
  const raw = clean(value, 300)
  if (!raw) return ''
  try {
    const url = new URL(raw)
    if (url.protocol !== 'https:' && url.protocol !== 'http:') return null
    return url.toString().slice(0, 300)
  } catch {
    return null
  }
}

function normalizeFaq(value: unknown): string[][] {
  if (!Array.isArray(value)) return []
  return value
    .slice(0, 30)
    .filter((row): row is unknown[] => Array.isArray(row) && row.length >= 2)
    .map(row => [clean(row[0], 240), clean(row[1], 1600)])
    .filter(([question, answer]) => Boolean(question && answer))
}

export async function GET() {
  if (!isConfigured()) return NextResponse.json(DEFAULT_SETTINGS)
  const res = await supabase('agency_settings?select=*&id=eq.1&limit=1')
  if (!res.ok) return NextResponse.json(DEFAULT_SETTINGS)
  const rows = await res.json()
  return NextResponse.json({ ...DEFAULT_SETTINGS, ...(rows[0] || {}) })
}

export async function PUT(request: NextRequest) {
  if (!isAdmin(request)) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  if (!isConfigured()) return NextResponse.json({ error: 'Backend not configured' }, { status: 503 })

  try {
    const body = await request.json()
    const telegramUrl = normalizeHttpUrl(body.telegram_url)
    const whatsappUrl = normalizeHttpUrl(body.whatsapp_url)
    const instagramUrl = normalizeHttpUrl(body.instagram_url)
    const email = clean(body.email, 200)

    if ([telegramUrl, whatsappUrl, instagramUrl].some(value => value === null)) {
      return NextResponse.json({ error: 'Contact links must use http:// or https://' }, { status: 400 })
    }
    if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      return NextResponse.json({ error: 'Invalid email address' }, { status: 400 })
    }

    const payload = {
      id: 1,
      welcome_bonus: clean(body.welcome_bonus, 200),
      milestone_title: clean(body.milestone_title, 200),
      milestone_reward: clean(body.milestone_reward, 500),
      telegram_url: telegramUrl || '',
      whatsapp_url: whatsappUrl || '',
      instagram_url: instagramUrl || '',
      email,
      faq_en: normalizeFaq(body.faq_en),
      faq_ru: normalizeFaq(body.faq_ru),
      updated_at: new Date().toISOString(),
    }

    const res = await supabase('agency_settings?on_conflict=id', {
      method: 'POST',
      headers: { Prefer: 'resolution=merge-duplicates,return=representation' },
      body: JSON.stringify(payload),
    })
    if (!res.ok) return NextResponse.json({ error: 'Could not save settings' }, { status: 500 })
    return NextResponse.json((await res.json())[0])
  } catch {
    return NextResponse.json({ error: 'Invalid request' }, { status: 400 })
  }
}
