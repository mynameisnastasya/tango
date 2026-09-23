# ABHI AGANCY

Premium bilingual recruiting and onboarding website for **ABHI AGANCY**.

## Included

- EN / RU mobile-first homepage
- Premium black / white / champagne-gold design
- Main referral code: `KCu4ZY`
- Referral URLs: `/join?ref=KCu4ZY` or `/?ref=KCu4ZY`
- Referral persistence and automatic form prefill
- Application form with 18+ confirmation
- Real-broadcaster / no-prerecorded-stream messaging
- Benefits, milestones, FTR explanation, FAQ and creator community
- Privacy Policy and Terms & Conditions
- Admin dashboard at `/admin`
- Applicant search and filters
- Applicant statuses: New / Contacted / Approved / Rejected / Active / FTR Completed
- CSV export
- Referral-code management
- Referral analytics
- Editable bonus, milestone, contact and FAQ settings
- Supabase-backed persistence through secure server routes
- Local browser demo fallback when Supabase is not configured

## Run locally

```bash
npm install
cp .env.example .env.local
npm run dev
```

Open `http://localhost:3000`.

## Production database

1. Create a Supabase project.
2. Open the Supabase SQL Editor.
3. Run `supabase/schema.sql`.
4. Add these environment variables to your hosting platform:

```
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_SERVICE_ROLE_KEY=YOUR_SERVICE_ROLE_KEY
ADMIN_KEY=a-long-random-password
```

Never expose `SUPABASE_SERVICE_ROLE_KEY` in browser code or variables prefixed with `NEXT_PUBLIC_`.

## Admin

Open `/admin` and enter the value of `ADMIN_KEY`.

The admin dashboard can:

- view applications
- search and filter by country, recruiter and status
- change applicant status
- export CSV
- create or update referral codes
- view applications / approved / active / FTR metrics by referral code
- edit bonus and milestone copy
- edit Telegram / WhatsApp / Instagram / email contacts
- override EN and RU FAQs

## Referral flow

The initial code is:

```
KCu4ZY
```

Example:

```
https://your-domain.com/?ref=KCu4ZY
```

When a visitor opens a referral link, the code is validated, stored locally, displayed as applied, and automatically attached to the application.

## Deployment

The app is designed for a Next.js server deployment such as Vercel because the public form and admin dashboard use secure server routes.

Build check:

```bash
npm run build
```

## Notes

ABHI AGANCY does not guarantee earnings, bonuses, withdrawals, viewer counts or creator success. Bonus and campaign conditions can change and should be confirmed individually by an agency manager.

The public form intentionally does not collect passports or other sensitive identity documents.
