# ABHIGREEN

Premium bilingual recruiting and onboarding website for **ABHIGREEN**.

## Included

- EN / RU mobile-first homepage
- Premium black / white / champagne-gold design
- Prominent Tango Agency Code: `KCu4ZY`
- Clear copy explaining that `KCu4ZY` is entered inside Tango to connect a broadcaster account to ABHIGREEN
- Separate website recruiter/referral-code infrastructure for future campaigns
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

## Tango agency connection code

The Tango Agency Code is:

```
KCu4ZY
```

Broadcasters can connect through the Tango referral link: https://tango.onelink.me/RCIH/cdw49a6s

If the Tango account is brand-new (under 5 hours old), the broadcaster can alternatively enter `KCu4ZY` manually inside Tango. The code is not entered on the website. A detailed step-by-step Tango instruction can be added later.

Website recruiter/referral codes are a separate feature for campaign attribution and should use different codes.

## Deployment

The app is designed for a Next.js server deployment such as Vercel because the public form and admin dashboard use secure server routes.

Build check:

```bash
npm run build
```

## Notes

ABHIGREEN does not guarantee earnings, bonuses, withdrawals, viewer counts or creator success. Bonus and campaign conditions can change and should be confirmed individually by an agency manager.

The public form intentionally does not collect passports or other sensitive identity documents.
