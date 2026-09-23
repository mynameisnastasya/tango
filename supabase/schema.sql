-- ABHI AGANCY Supabase schema
-- Run this in Supabase SQL Editor. The website uses the service role key only on the server.

create extension if not exists pgcrypto;

create table if not exists public.applications (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  name text not null,
  country text not null,
  languages text default '',
  telegram text default '',
  whatsapp text default '',
  instagram text default '',
  platform text default '',
  experience text default '',
  username text default '',
  referral_code text default '',
  hours_per_week text default '',
  message text default '',
  age_confirmed boolean not null default false,
  consent boolean not null default false,
  status text not null default 'New' check (status in ('New','Contacted','Approved','Rejected','Active','FTR Completed')),
  source text default 'website'
);

create index if not exists applications_referral_code_idx on public.applications(referral_code);
create index if not exists applications_status_idx on public.applications(status);
create index if not exists applications_country_idx on public.applications(country);

create table if not exists public.referral_codes (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  code text not null unique,
  agency_name text not null default 'ABHI AGANCY',
  recruiter text default '',
  market text default 'International',
  onboarding_bonus text default '',
  active boolean not null default true
);


create table if not exists public.agency_settings (
  id integer primary key default 1 check (id = 1),
  welcome_bonus text default '4,000–5,000 coins',
  milestone_title text default '100,000 Diamond Milestone',
  milestone_reward text default 'Additional broadcaster reward may be available.',
  telegram_url text default '',
  whatsapp_url text default '',
  instagram_url text default '',
  email text default '',
  faq_en jsonb default '[]'::jsonb,
  faq_ru jsonb default '[]'::jsonb,
  updated_at timestamptz not null default now()
);

insert into public.agency_settings (id) values (1) on conflict (id) do nothing;

alter table public.applications enable row level security;
alter table public.referral_codes enable row level security;
alter table public.agency_settings enable row level security;

-- No anon policies are needed: browser requests go through Next.js server routes.
-- Keep SUPABASE_SERVICE_ROLE_KEY only in server-side deployment environment variables.
