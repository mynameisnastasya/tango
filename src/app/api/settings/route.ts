import { NextRequest, NextResponse } from 'next/server'
import { DEFAULT_SETTINGS, isAdmin, isConfigured, supabase } from '@/lib/server'

export async function GET() {
  if (!isConfigured()) return NextResponse.json(DEFAULT_SETTINGS)
  const res = await supabase('agency_settings?select=*&id=eq.1&limit=1')
  if (!res.ok) return NextResponse.json(DEFAULT_SETTINGS)
  const rows = await res.json()
  return NextResponse.json({ ...DEFAULT_SETTINGS, ...(rows[0] || {}) })
}

export async function PUT(request: NextRequest) {
  if (!isAdmin(request)) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  try {
    const body = await request.json()
    const payload = {
      id: 1,
      welcome_bonus: String(body.welcome_bonus || '').slice(0, 200),
      milestone_title: String(body.milestone_title || '').slice(0, 200),
      milestone_reward: String(body.milestone_reward || '').slice(0, 500),
      telegram_url: String(body.telegram_url || '').slice(0, 300),
      whatsapp_url: String(body.whatsapp_url || '').slice(0, 300),
      instagram_url: String(body.instagram_url || '').slice(0, 300),
      email: String(body.email || '').slice(0, 200),
      faq_en: Array.isArray(body.faq_en) ? body.faq_en : [],
      faq_ru: Array.isArray(body.faq_ru) ? body.faq_ru : [],
      updated_at: new Date().toISOString(),
    }
    const res = await supabase('agency_settings?on_conflict=id', {
      method: 'POST',
      headers: { Prefer: 'resolution=merge-duplicates,return=representation' },
      body: JSON.stringify(payload),
    })
    if (!res.ok) return NextResponse.json({ error: await res.text() }, { status: 500 })
    return NextResponse.json((await res.json())[0])
  } catch {
    return NextResponse.json({ error: 'Invalid request' }, { status: 400 })
  }
}
