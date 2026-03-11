-- ─────────────────────────────────────────────────────────────────────────────
-- Trinity — Supabase Database Schema
-- Run this in: supabase.com → your project → SQL Editor → New query → Run
-- ─────────────────────────────────────────────────────────────────────────────

-- Couple invites (Partner A sends a code to Partner B)
create table if not exists public.couple_invites (
  id           uuid primary key default gen_random_uuid(),
  inviter_id   uuid references auth.users(id) on delete cascade not null,
  invite_code  text unique not null,
  accepted     boolean default false not null,
  expires_at   timestamptz not null,
  created_at   timestamptz default now() not null
);

-- Couples (created when Partner B accepts invite)
create table if not exists public.couples (
  id            uuid primary key default gen_random_uuid(),
  partner_a_id  uuid references auth.users(id) on delete cascade not null,
  partner_b_id  uuid references auth.users(id) on delete cascade not null,
  created_at    timestamptz default now() not null
);

-- Row Level Security ──────────────────────────────────────────────────────────

alter table public.couple_invites enable row level security;
alter table public.couples enable row level security;

-- Users can read and create their own invites
create policy "invites: own rows"
  on public.couple_invites for all
  using (auth.uid() = inviter_id);

-- Anyone authenticated can read invites (to accept them by code)
create policy "invites: read by code"
  on public.couple_invites for select
  using (auth.role() = 'authenticated');

-- Users can see couples they're in
create policy "couples: own rows"
  on public.couples for all
  using (auth.uid() = partner_a_id or auth.uid() = partner_b_id);

-- Anyone authenticated can insert a couple (when accepting an invite)
create policy "couples: insert"
  on public.couples for insert
  with check (auth.uid() = partner_b_id);
