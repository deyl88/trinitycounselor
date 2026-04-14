import { supabase } from './supabase'
import { v4 as uuidv4 } from 'uuid'

// ── User name persistence ─────────────────────────────────────────────────────

export function getSavedName(): string {
  if (typeof window === 'undefined') return ''
  return localStorage.getItem('humanmode_user_name') ?? ''
}

export function saveName(name: string) {
  if (typeof window === 'undefined') return
  localStorage.setItem('humanmode_user_name', name)
}

// ── User identity ────────────────────────────────────────────────────────────

export function getOrCreateUserId(): string {
  if (typeof window === 'undefined') return ''
  let id = localStorage.getItem('humanmode_user_id')
  if (!id) {
    id = uuidv4()
    localStorage.setItem('humanmode_user_id', id)
  }
  return id
}

export async function upsertUser(id: string, name: string) {
  const { error } = await supabase
    .from('users')
    .upsert({ id, name }, { onConflict: 'id' })
  if (error) throw error
}

// ── Session CRUD ─────────────────────────────────────────────────────────────

export async function createSession(duration: number) {
  const { data, error } = await supabase
    .from('sessions')
    .insert({ duration })
    .select()
    .single()
  if (error) throw error
  return data
}

export async function getSession(sessionId: string) {
  const { data, error } = await supabase
    .from('sessions')
    .select('*')
    .eq('id', sessionId)
    .single()
  if (error) throw error
  return data
}

export async function addParticipant(sessionId: string, userId: string) {
  // Check if already a participant (idempotent)
  const { data: existing } = await supabase
    .from('participants')
    .select('id')
    .eq('session_id', sessionId)
    .eq('user_id', userId)
    .maybeSingle()

  if (existing) return existing

  const { data, error } = await supabase
    .from('participants')
    .insert({ session_id: sessionId, user_id: userId })
    .select()
    .single()
  if (error) throw error
  return data
}

export async function getParticipants(sessionId: string) {
  const { data, error } = await supabase
    .from('participants')
    .select('*, users(id, name)')
    .eq('session_id', sessionId)
    .order('joined_at', { ascending: true })
  if (error) throw error
  return data
}

export async function startSession(sessionId: string) {
  const { error } = await supabase
    .from('sessions')
    .update({ started_at: new Date().toISOString() })
    .eq('id', sessionId)
    .is('started_at', null) // Only set if not already started (prevents race)
  if (error) throw error
}

export async function endSession(sessionId: string) {
  const { error } = await supabase
    .from('sessions')
    .update({ ended_at: new Date().toISOString() })
    .eq('id', sessionId)
    .is('ended_at', null) // Only set if not already ended
  if (error) throw error
}

// ── Session stats ────────────────────────────────────────────────────────────

// ── Past sessions for profile ─────────────────────────────────────────────────

export async function getUserSessions(userId: string) {
  const { data: myParts, error } = await supabase
    .from('participants')
    .select('session_id, joined_at')
    .eq('user_id', userId)
    .order('joined_at', { ascending: false })
    .limit(30)

  if (error || !myParts || myParts.length === 0) return []

  const sessionIds = myParts.map((p) => p.session_id)

  const [{ data: sessions }, { data: partnerParts }] = await Promise.all([
    supabase
      .from('sessions')
      .select('id, duration, started_at, ended_at, created_at')
      .in('id', sessionIds)
      .order('created_at', { ascending: false }),
    supabase
      .from('participants')
      .select('session_id, user_id, users(id, name)')
      .in('session_id', sessionIds)
      .neq('user_id', userId),
  ])

  if (!sessions) return []

  return sessions.map((s) => {
    const pp = partnerParts?.find((p) => p.session_id === s.id)
    const partner = pp?.users as { id: string; name: string } | null ?? null
    return { ...s, partner }
  })
}

export async function getSessionsTogether(
  userId: string,
  partnerId: string
): Promise<number> {
  // Count completed sessions where both users participated
  const { data, error } = await supabase
    .from('participants')
    .select('session_id')
    .eq('user_id', userId)

  if (error || !data) return 0

  const sessionIds = data.map((p) => p.session_id)
  if (sessionIds.length === 0) return 0

  const { data: partnerData, error: partnerError } = await supabase
    .from('participants')
    .select('session_id')
    .eq('user_id', partnerId)
    .in('session_id', sessionIds)

  if (partnerError || !partnerData) return 0

  const sharedSessionIds = partnerData.map((p) => p.session_id)
  if (sharedSessionIds.length === 0) return 0

  // Count only completed sessions
  const { count, error: countError } = await supabase
    .from('sessions')
    .select('id', { count: 'exact', head: true })
    .in('id', sharedSessionIds)
    .not('ended_at', 'is', null)

  if (countError) return 0
  return count ?? 0
}
