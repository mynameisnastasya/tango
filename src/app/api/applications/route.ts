import { NextRequest, NextResponse } from 'next/server'
import { isAdmin, isConfigured, supabase } from '@/lib/server'

const allowedStatuses = ['New', 'Contacted', 'Approved', 'Rejected', 'Active', 'FTR Completed']
const clean = (value: unknown, max: number) => String(value ?? '').trim().slice(0, max)

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    // Honeypot: silently accept obvious bot submissions without storing them.
    if (clean(body?.website, 200)) {
      return NextResponse.json({ ok: true }, { status: 201 })
    }

    const name = clean(body?.name, 120)
    const country = clean(body?.country, 100)
    const telegram = clean(body?.telegram, 150)
    const whatsapp = clean(body?.whatsapp, 150)
    const instagram = clean(body?.instagram, 150)
    const ageConfirmed = body?.age_confirmed === true
    const consent = body?.consent === true

    if (!name || !country || !ageConfirmed || !consent) {
      return NextResponse.json({ error: 'Missing required fields' }, { status: 400 })
    }
    if (!telegram && !whatsapp && !instagram) {
      return NextResponse.json({ error: 'At least one contact method is required' }, { status: 400 })
    }
    if (!isConfigured()) {
      return NextResponse.json({ error: 'Application service is temporarily unavailable' }, { status: 503 })
    }

    const payload = {
      name,
      country,
      languages: clean(body.languages, 200),
      telegram,
      whatsapp,
      instagram,
      platform: clean(body.platform, 100),
      experience: clean(body.experience, 1000),
      username: clean(body.username, 150),
      referral_code: clean(body.referral_code, 80),
      hours_per_week: clean(body.hours_per_week, 80),
      message: clean(body.message, 2000),
      age_confirmed: ageConfirmed,
      consent,
      status: 'New',
      source: clean(body.source || 'website', 500),
    }

    const res = await supabase('applications', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
    if (!res.ok) {
      console.error('Application insert failed', res.status, await res.text())
      return NextResponse.json({ error: 'Application service is temporarily unavailable' }, { status: 503 })
    }
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
  if (!isConfigured()) return NextResponse.json({ error: 'Backend not configured' }, { status: 503 })

  try {
    const { id, status } = await request.json()
    if (!id || !allowedStatuses.includes(status)) {
      return NextResponse.json({ error: 'Invalid status update' }, { status: 400 })
    }
    const res = await supabase(`applications?id=eq.${encodeURIComponent(String(id))}`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    })
    if (!res.ok) return NextResponse.json({ error: await res.text() }, { status: 500 })
    return NextResponse.json({ ok: true })
  } catch {
    return NextResponse.json({ error: 'Invalid request' }, { status: 400 })
  }
}
