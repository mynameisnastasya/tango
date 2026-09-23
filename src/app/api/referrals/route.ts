import { NextRequest, NextResponse } from 'next/server'
import { isAdmin, isConfigured, supabase } from '@/lib/server'

export async function GET(request: NextRequest) {
  const code = request.nextUrl.searchParams.get('code')

  if (code) {
    if (!isConfigured()) {
      return NextResponse.json({ error: 'Referral code not found' }, { status: 404 })
    }
    const res = await supabase(`referral_codes?select=*&code=eq.${encodeURIComponent(code)}&active=eq.true&limit=1`)
    if (!res.ok) return NextResponse.json({ error: await res.text() }, { status: 500 })
    const rows = await res.json()
    if (!rows.length) return NextResponse.json({ error: 'Referral code not found' }, { status: 404 })
    return NextResponse.json(rows[0])
  }

  if (!isAdmin(request)) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  if (!isConfigured()) return NextResponse.json([])
  const res = await supabase('referral_codes?select=*&order=created_at.desc')
  if (!res.ok) return NextResponse.json({ error: await res.text() }, { status: 500 })
  return NextResponse.json(await res.json())
}

export async function POST(request: NextRequest) {
  if (!isAdmin(request)) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  try {
    const body = await request.json()
    if (!body?.code) return NextResponse.json({ error: 'Code required' }, { status: 400 })
    const payload = {
      code: String(body.code).trim().slice(0, 80),
      agency_name: 'ABHI AGENCY',
      recruiter: String(body.recruiter || '').slice(0, 150),
      market: String(body.market || 'International').slice(0, 100),
      onboarding_bonus: String(body.onboarding_bonus || '').slice(0, 300),
      active: body.active !== false,
    }
    const res = await supabase('referral_codes?on_conflict=code', {
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
