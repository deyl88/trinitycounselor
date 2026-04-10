# Human Mode

> Tap in. Be here.

A mobile-first web app that helps two people be fully present together. One person creates a session, shares a QR code, the other scans to join — both see a shared countdown timer and a calming "Human Mode Active" screen.

---

## Stack

- **Next.js 14** (App Router, TypeScript)
- **Supabase** — database + realtime sync
- **Tailwind CSS**
- **qrcode.react**

---

## Setup

### 1. Supabase project

Create a free project at [supabase.com](https://supabase.com).

In the **SQL Editor**, run:

```sql
-- Users
CREATE TABLE users (
  id          UUID PRIMARY KEY,
  name        TEXT NOT NULL,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Sessions
CREATE TABLE sessions (
  id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  duration    INTEGER NOT NULL,
  created_at  TIMESTAMPTZ DEFAULT NOW(),
  started_at  TIMESTAMPTZ,
  ended_at    TIMESTAMPTZ
);

-- Participants
CREATE TABLE participants (
  id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  session_id  UUID REFERENCES sessions(id) ON DELETE CASCADE,
  user_id     UUID REFERENCES users(id),
  joined_at   TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Realtime
ALTER PUBLICATION supabase_realtime ADD TABLE sessions;
ALTER PUBLICATION supabase_realtime ADD TABLE participants;
```

> **Note:** RLS is disabled for this MVP (public access). Before a production launch, add row-level security policies.

### 2. Environment variables

```bash
cp .env.example .env.local
```

Fill in your Supabase project URL and anon key (found in Supabase → Settings → API).

### 3. Install & run

```bash
cd human-mode
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in two browser tabs to simulate two people.

---

## App Flow

```
/ (Home)
  └─ /create          → enter name + pick duration
       └─ /session/[id]  → QR code screen (waiting)
                           → Human Mode Active (countdown)  ← joined via:
                           → Session complete
/join/[id]            → second person enters name + taps in
     └─ /session/[id]  → Human Mode Active (same session)
```

---

## Deploying to Vercel

1. Push this directory (or the whole repo) to GitHub
2. Import into [vercel.com](https://vercel.com)
3. Set environment variables:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
4. Deploy — Vercel auto-detects Next.js

---

## Future Extension Points

| Feature | Where to add |
|---|---|
| NFC tap (instead of QR) | `app/create/page.tsx` — use Web NFC API to write session URL to tag |
| Native iOS/Android | Replace Next.js with React Native + Expo; keep Supabase backend |
| Push notifications | Add `expo-notifications` or Web Push API; store device tokens in `participants` |
| Auto Do Not Disturb | iOS Focus Filter API (native only) |
| Live heat map | New `session_locations` table + Mapbox GL |
| Social graph / friends | Add `friendships` table; filter session history by friend |
| Full auth | Add Supabase Auth; replace `localStorage` UUID with `auth.uid()` |
| Streak tracking | Query `sessions` ordered by `ended_at`; compute consecutive days |

---

## How Realtime Sync Works

1. **Person A** creates session → added as participant → sees QR code
2. **Person A** subscribes to `participants` table filtered by `session_id`
3. **Person B** scans QR → joins → `participants` insert fires Person A's subscription
4. Person A detects 2 participants → calls `startSession()` (sets `sessions.started_at`)
5. **Both** subscribe to their `sessions` row → react to `started_at` being set → switch to Active view
6. Timer counts down from `started_at + duration` (server anchor, not local clock)
7. When timer ends or Hold-to-Exit fires → `endSession()` sets `ended_at` → both switch to Complete
