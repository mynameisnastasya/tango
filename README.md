# ABHIGREEN

Bilingual recruiting, onboarding and operations website for **ABHIGREEN**, focused on real adult live-streaming creators.

## What is included

- EN / RU mobile-first public website
- Tango connection flow with agency code `KCu4ZY`
- Android referral link and iPhone onboarding instructions
- Application form with 18+ confirmation, consent and contact validation
- Recruiter attribution through `?ref=CODE` or `?referral=CODE`
- Anti-spam honeypot and bounded server-side input validation
- Benefits, onboarding support, bonus and milestone messaging
- Privacy Policy and Terms & Conditions
- Admin dashboard at `/admin`
- Applicant search, filters, statuses, detail view and CSV export
- Referral-code management and referral analytics
- Editable bonus, milestone, contact and FAQ settings
- Supabase-backed persistence through server-only credentials
- Timing-safe admin-key comparison
- Baseline security headers, accessible focus states and reduced-motion support
- SEO / Open Graph / Twitter metadata

## Architecture

The repository contains two frontends:

1. **Next.js app** in `src/` — this is the production version. It contains the secure API routes, shared Supabase persistence and the real admin dashboard.
2. **Static GitHub Pages bundle** in the repository root (`index.html`, `site.css`, `site.js`, `admin.html`) — this is a visual/demo build only.

The static bundle does **not** pretend a lead was delivered when no backend exists. On localhost it can store demo applications in that browser. On GitHub Pages or another static-only host, a failed submission is shown as an error instead of a false success message.

For real applicant collection, deploy the **Next.js app** on a server-capable platform and configure Supabase.

## Run locally

```bash
npm install
cp .env.example .env.local
npm run dev
```

Open `http://localhost:3000`.

## Production configuration

Create a Supabase project, open its SQL Editor and run:

```
supabase/schema.sql
```

Then configure these environment variables on the production host:

```
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_SERVICE_ROLE_KEY=YOUR_SERVICE_ROLE_KEY
ADMIN_KEY=a-long-random-password
NEXT_PUBLIC_SITE_URL=https://your-production-domain.example/
```

Never expose `SUPABASE_SERVICE_ROLE_KEY` in browser code or in a variable prefixed with `NEXT_PUBLIC_`.

`NEXT_PUBLIC_SITE_URL` is used for canonical and social-sharing metadata.

## Application flow

The public form requires:

- name
- country
- confirmation that the applicant is 18+
- consent
- at least one contact method: Telegram, WhatsApp or Instagram

The API trims and bounds all submitted strings before saving them. A hidden honeypot is used to silently discard simple bot submissions.

Recruiter attribution can be passed in the landing URL:

```
https://your-domain.example/?ref=RECRUITER_CODE
```

The referral code is stored with the application and can be analyzed in the admin dashboard.

## Admin

Open `/admin` and enter the configured `ADMIN_KEY`.

The dashboard can:

- view applications
- inspect the full applicant message and profile details
- search and filter by country, recruiter and status
- change applicant statuses
- export CSV
- create or update referral codes
- view application and creator activity metrics by referral code
- edit bonus, milestone, contact and FAQ settings

The browser stores the admin key only in `sessionStorage`, so it is cleared when the browser session ends.

## Tango agency connection

Agency code:

```
KCu4ZY
```

Android referral link:

```
https://tango.onelink.me/RCIH/cdw49a6s
```

Current onboarding copy instructs new iPhone users to create the account through `tango.me`, then use **Settings → Join an Agency** and enter the agency code within the first five hours. Platform rules can change, so onboarding instructions should be reviewed periodically.

Website recruiter/referral codes are separate from the Tango agency code.

## Build check

```bash
npm run build
```

GitHub Actions also verifies the Next.js build and the static preview bundle on pushes and pull requests.

## Data and claims

ABHIGREEN does not guarantee earnings, viewer counts or creator success. Bonus and campaign conditions can change and should be confirmed by a manager before participation.

The public application form intentionally does not collect passports, banking credentials, passwords or other highly sensitive documents.
