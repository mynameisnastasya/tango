import { NextRequest, NextResponse } from 'next/server'
import { isAdmin, isConfigured, supabase } from '@/lib/server'

const allowedStatuses = ['New', 'Contacted', 'Approved', 'Rejected', 'Active', 'FTR Completed']

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    if (!body?.name || !body?.country || !body?.age_confirmed || !body?.consent) {
      return NextResponse.json({ error: 'Missing required fields' }, { status: 400 })
    }
    if (!isConfigured()) {
      return NextResponse.json({ error: 'Backend not configured' }, { status: 503 })
    }

    const payload = {
      name: String(body.name).slice(0, 120),
      country: String(body.country).slice(0, 100),
      languages: String(body.languages || '').slice(0, 200),
      telegram: String(body.telegram || '').slice(0, 150),
      whatsapp: String(body.whatsapp || '').slice(0, 150),
      instagram: String(body.instagram || '').slice(0, 150),
      platform: String(body.platform || '').slice(0, 100),
      experience: String(body.experience || '').slice(0, 1000),
      username: String(body.username || '').slice(0, 150),
      referral_code: String(body.referral_code || '').slice(0, 80),
      hours_per_week: String(body.hours_per_week || '').slice(0, 80),
      message: String(body.message || '').slice(0, 2000),
      age_confirmed: Boolean(body.age_confirmed),
      consent: Boolean(body.consent),
      status: 'New',
      source: String(body.source || 'website').slice(0, 160),
    }

    const res = await supabase('applications', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
    if (!res.ok) return NextResponse.json({ error: await res.text() }, { status: 500 })
    return NextResponse.json({ ok: true }, { status: 201 })
  } catch {
    return NextResponse.json({ error: 'Invalid request' }, { status: 400 })
  }
}

export async function GET(request: NextRequest) {
  if (!isAdmin(request)) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  if (!isConfigured()) return NextResponse.json({ error: 'Backend not configured' }, { status: 503 })
  const res = await supabase('applications?select=*&order=created_at.desc')
  if (!res.ok) return NextResponse.json({ error: await res.text() }, { status: 500 })
  return NextResponse.json(await res.json())
}

export async function PATCH(request: NextRequest) {
  if (!isAdmin(request)) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  try {
    const { id, status } = await request.json()
    if (!id || !allowedStatuses.includes(status)) {
      return NextResponse.json({ error: 'Invalid status update' }, { status: 400 })
    }
    const res = await supabase(`applications?id=eq.${encodeURIComponent(id)}`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    })
    if (!res.ok) return NextResponse.json({ error: await res.text() }, { status: 500 })
    return NextResponse.json({ ok: true })
  } catch {
    return NextResponse.json({ error: 'Invalid request' }, { status: 400 })
  }
}
