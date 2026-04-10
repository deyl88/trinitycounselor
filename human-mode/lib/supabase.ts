import { createClient, SupabaseClient } from '@supabase/supabase-js'

// Lazy singleton — only created on first use (not at module load time)
// This prevents build-time errors when env vars are not set.
let _client: SupabaseClient | null = null

export function getSupabase(): SupabaseClient {
  if (_client) return _client
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
  if (!url || !key) {
    throw new Error(
      'Missing NEXT_PUBLIC_SUPABASE_URL or NEXT_PUBLIC_SUPABASE_ANON_KEY. ' +
        'Copy .env.example to .env.local and fill in your Supabase credentials.'
    )
  }
  _client = createClient(url, key)
  return _client
}

// Convenience proxy — behaves like a direct export but is lazy under the hood
export const supabase = new Proxy({} as SupabaseClient, {
  get(_target, prop) {
    return (getSupabase() as unknown as Record<string | symbol, unknown>)[prop]
  },
})

export type Database = {
  public: {
    Tables: {
      users: {
        Row: {
          id: string
          name: string
          created_at: string
        }
        Insert: {
          id: string
          name: string
          created_at?: string
        }
        Update: {
          id?: string
          name?: string
        }
      }
      sessions: {
        Row: {
          id: string
          duration: number
          created_at: string
          started_at: string | null
          ended_at: string | null
        }
        Insert: {
          id?: string
          duration: number
          created_at?: string
          started_at?: string | null
          ended_at?: string | null
        }
        Update: {
          started_at?: string | null
          ended_at?: string | null
        }
      }
      participants: {
        Row: {
          id: string
          session_id: string
          user_id: string
          joined_at: string
        }
        Insert: {
          id?: string
          session_id: string
          user_id: string
          joined_at?: string
        }
        Update: Record<string, never>
      }
    }
  }
}
