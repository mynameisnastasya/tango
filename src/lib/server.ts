import { NextRequest } from 'next/server'

export const DEFAULT_SETTINGS = {
  welcome_bonus: '4,000–5,000 coins',
  milestone_title: '100,000 Diamond Milestone',
  milestone_reward: 'Additional broadcaster reward may be available.',
  telegram_url: '',
  whatsapp_url: '',
  instagram_url: '',
  email: '',
}

export function isConfigured() {
  return Boolean(process.env.SUPABASE_URL && process.env.SUPABASE_SERVICE_ROLE_KEY)
}

export function isAdmin(request: NextRequest) {
  const expected = process.env.ADMIN_KEY
  const supplied = request.headers.get('x-admin-key')
  return Boolean(expected && supplied && expected === supplied)
}

export async function supabase(path: string, init: RequestInit = {}) {
  if (!isConfigured()) throw new Error('BACKEND_NOT_CONFIGURED')
  const base = process.env.SUPABASE_URL!.replace(/\/$/, '')
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY!
  return fetch(`${base}/rest/v1/${path}`, {
    ...init,
    headers: {
      apikey: key,
      Authorization: `Bearer ${key}`,
      'Content-Type': 'application/json',
      Prefer: 'return=representation',
      ...(init.headers || {}),
    },
    cache: 'no-store',
  })
}
