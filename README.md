# Trinity

A private relationship counseling web app. Works on desktop and phone.

**My Space** — private sessions with your own AI counselor (your partner never sees this)
**Our Space** — a joint session with a relationship counselor who holds both of you
**Connect** — invite your partner via a code

---

## Getting it live (step by step)

You need three things: a Supabase account, an Anthropic API key, and a Vercel account. All have free tiers.

---

### Step 1 — Supabase (database + login)

1. Go to [supabase.com](https://supabase.com) and create a free account
2. Click **New project** — give it a name, create a password, pick a region
3. Wait ~2 minutes for it to spin up
4. Go to **SQL Editor** → **New query**, paste the contents of `supabase/schema.sql`, click **Run**
5. Go to **Settings → API**. Copy:
   - **Project URL** (looks like `https://xxxxx.supabase.co`)
   - **anon / public key** (the long string under "Project API keys")

#### Enable Apple Sign In in Supabase

> ⚠️ Apple Sign In requires an [Apple Developer account](https://developer.apple.com) ($99/year).
> **Skip this for now** — Google login works out of the box (see below).

For Apple Sign In when you're ready:
1. In your Apple Developer account → **Certificates, Identifiers & Profiles**
2. Create an **App ID** with "Sign in with Apple" capability
3. Create a **Services ID** (this is your web client ID)
4. Create a **Key** with "Sign in with Apple" selected — download the `.p8` file
5. In Supabase → **Authentication → Providers → Apple** → fill in the fields

#### Enable Google Sign In in Supabase (easier, free)

1. Go to [console.cloud.google.com](https://console.cloud.google.com) → create a project
2. **APIs & Services → Credentials → Create Credentials → OAuth client ID**
3. Application type: **Web application**
4. Authorized redirect URI: `https://YOUR_PROJECT.supabase.co/auth/v1/callback`
5. Copy the Client ID and Client Secret
6. In Supabase → **Authentication → Providers → Google** → paste them in

---

### Step 2 — Anthropic API key

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. **API Keys → Create Key**
3. Copy it — you'll use it in the next step

---

### Step 3 — Deploy to Vercel

1. Push this code to a GitHub repository (if you haven't)
2. Go to [vercel.com](https://vercel.com) → **Add New → Project** → import your repo
3. In **Environment Variables**, add these three:

   | Name | Value |
   |------|-------|
   | `NEXT_PUBLIC_SUPABASE_URL` | your Supabase Project URL |
   | `NEXT_PUBLIC_SUPABASE_ANON_KEY` | your Supabase anon key |
   | `ANTHROPIC_API_KEY` | your Anthropic key |

4. Click **Deploy**. Done — Vercel gives you a public URL to share.

---

### Running locally (optional)

```bash
# 1. Install dependencies
npm install

# 2. Set up environment
cp .env.local.example .env.local
# Fill in .env.local with your keys

# 3. Start dev server
npm run dev
# Open http://localhost:3000
```

---

## Project structure

```
app/
  page.tsx              ← Login screen (Apple / Google)
  (app)/
    chat/page.tsx       ← My Space (private counselor)
    us/page.tsx         ← Our Space (relationship counselor)
    couple/page.tsx     ← Connect (invite partner)
  api/chat/route.ts     ← API route → calls Claude

components/
  ChatInterface.tsx     ← Chat UI with streaming
  CoupleConnect.tsx     ← Invite / accept partner
  Nav.tsx               ← Bottom navigation

lib/
  agents.ts             ← System prompts for each counselor
  supabase/             ← Supabase client helpers

supabase/
  schema.sql            ← Run this once in Supabase SQL Editor
```

---

## Sharing with friends (MVP)

Once deployed to Vercel:
1. Share the Vercel URL with each couple
2. Each person signs in separately (Apple or Google)
3. One partner goes to **Connect** → creates a code → sends it to the other
4. The other partner enters the code → they're linked
5. **My Space** is private to each person. **Our Space** is shared.

---

## Privacy

- Each person's private session is only visible to them
- The relationship counselor (Our Space) doesn't have access to either person's private chats
- Supabase Row Level Security enforces this at the database level
