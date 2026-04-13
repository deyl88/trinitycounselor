'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { supabase } from '@/lib/supabase'
import {
  getSession,
  getParticipants,
  startSession,
  endSession,
  getOrCreateUserId,
  getSessionsTogether,
} from '@/lib/session'
import QRCodeDisplay from '@/components/QRCodeDisplay'
import Timer from '@/components/Timer'
import HoldToExitButton from '@/components/HoldToExitButton'

type SessionView = 'loading' | 'waiting' | 'active' | 'completed'

interface Participant {
  user_id: string
  users: { id: string; name: string } | null
}

export default function SessionPage() {
  const { id: sessionId } = useParams<{ id: string }>()
  const router = useRouter()

  const [view, setView] = useState<SessionView>('loading')
  const [session, setSession] = useState<{
    id: string
    duration: number
    started_at: string | null
    ended_at: string | null
  } | null>(null)
  const [participants, setParticipants] = useState<Participant[]>([])
  const [sessionsTogether, setSessionsTogether] = useState(0)
  const [error, setError] = useState('')

  const userId = useRef(getOrCreateUserId())
  const isCreator = useRef(false)

  // ── Helpers ────────────────────────────────────────────────────────────────

  const myName = useCallback((): string => {
    const me = participants.find((p) => p.user_id === userId.current)
    return me?.users?.name ?? 'You'
  }, [participants])

  const partnerName = useCallback((): string => {
    const partner = participants.find((p) => p.user_id !== userId.current)
    return partner?.users?.name ?? 'your partner'
  }, [participants])

  const partnerId = useCallback((): string => {
    const partner = participants.find((p) => p.user_id !== userId.current)
    return partner?.user_id ?? ''
  }, [participants])

  // ── Load initial state ─────────────────────────────────────────────────────

  useEffect(() => {
    if (!sessionId) return

    isCreator.current =
      localStorage.getItem(`humanmode_creator_${sessionId}`) === '1'

    async function load() {
      try {
        const [s, ps] = await Promise.all([
          getSession(sessionId),
          getParticipants(sessionId),
        ])
        setSession(s)
        setParticipants(ps as Participant[])

        if (s.ended_at) {
          setView('completed')
        } else if (s.started_at) {
          setView('active')
        } else {
          setView('waiting')
        }
      } catch {
        setError('Session not found.')
      }
    }
    load()
  }, [sessionId])

  // ── Fetch session stats when completed ────────────────────────────────────

  useEffect(() => {
    if (view !== 'completed') return
    const pid = partnerId()
    if (!pid) return
    getSessionsTogether(userId.current, pid).then(setSessionsTogether)
  }, [view, partnerId])

  // ── Realtime subscriptions ─────────────────────────────────────────────────

  useEffect(() => {
    if (!sessionId || view === 'loading') return

    // Subscribe to participants table — creator uses this to trigger start
    const participantsSub = supabase
      .channel(`participants:${sessionId}`)
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'participants',
          filter: `session_id=eq.${sessionId}`,
        },
        async () => {
          // Reload participants
          const ps = await getParticipants(sessionId)
          setParticipants(ps as Participant[])

          // If creator and now 2 participants → start session
          if (isCreator.current && ps.length >= 2) {
            try {
              await startSession(sessionId)
            } catch {
              // Another client may have already started it — ignore
            }
          }
        }
      )
      .subscribe()

    // Subscribe to sessions row — both users react to state changes
    const sessionSub = supabase
      .channel(`session:${sessionId}`)
      .on(
        'postgres_changes',
        {
          event: 'UPDATE',
          schema: 'public',
          table: 'sessions',
          filter: `id=eq.${sessionId}`,
        },
        (payload) => {
          const updated = payload.new as typeof session
          if (!updated) return
          setSession(updated)
          if (updated.ended_at) {
            setView('completed')
          } else if (updated.started_at) {
            setView('active')
          }
        }
      )
      .subscribe()

    // Catch-up fetch: re-check DB right after subscribing in case we missed
    // the realtime event during the gap between initial load and subscription setup
    if (view === 'waiting') {
      getSession(sessionId).then((fresh) => {
        if (fresh.ended_at) {
          setSession(fresh)
          setView('completed')
        } else if (fresh.started_at) {
          setSession(fresh)
          setView('active')
        }
      }).catch(() => {})
    }

    // Polling fallback: check every 3s while waiting — safety net for missed events
    let pollInterval: ReturnType<typeof setInterval> | null = null
    if (view === 'waiting') {
      pollInterval = setInterval(async () => {
        try {
          const fresh = await getSession(sessionId)
          if (fresh.started_at) {
            setSession(fresh)
            setView('active')
          } else if (fresh.ended_at) {
            setSession(fresh)
            setView('completed')
          }
        } catch {
          // ignore
        }
      }, 3000)
    }

    return () => {
      supabase.removeChannel(participantsSub)
      supabase.removeChannel(sessionSub)
      if (pollInterval) clearInterval(pollInterval)
    }
  }, [sessionId, view])

  // ── Actions ────────────────────────────────────────────────────────────────

  async function handleExit() {
    if (!sessionId) return
    await endSession(sessionId)
    // View update comes via realtime, but set locally too for fast feedback
    setView('completed')
  }

  async function handleTimerComplete() {
    if (!sessionId) return
    await endSession(sessionId)
    setView('completed')
  }

  // ── Render ─────────────────────────────────────────────────────────────────

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center flex-1 px-6 fade-in">
        <p className="text-muted text-center">{error}</p>
        <button
          onClick={() => router.push('/')}
          className="mt-6 text-accent text-sm"
        >
          Go home
        </button>
      </div>
    )
  }

  if (view === 'loading') {
    return (
      <div className="flex flex-col items-center justify-center flex-1 px-6">
        <div className="w-8 h-8 rounded-full border-2 border-accent/30 border-t-accent animate-spin" />
      </div>
    )
  }

  // ── WAITING: show QR code ──────────────────────────────────────────────────
  if (view === 'waiting') {
    return (
      <div className="flex flex-col items-center justify-center flex-1 px-6 py-12 fade-in">
        <div className="mb-2 text-xs font-medium text-muted uppercase tracking-widest">
          {session?.duration} min session
        </div>
        <h2 className="text-2xl font-semibold text-ink mb-2">Tap someone in</h2>
        <p className="text-sm text-muted mb-10">
          Have them scan this to join your session
        </p>

        <QRCodeDisplay sessionId={sessionId} />

        <div className="mt-10 flex items-center gap-2 text-sm text-muted">
          <span className="pulse-dot w-2 h-2 rounded-full bg-accent" />
          Waiting for your person…
        </div>

        {/* Manual share fallback */}
        <button
          onClick={() => {
            const url = `${window.location.origin}/join/${sessionId}`
            if (navigator.share) {
              navigator.share({ url })
            } else {
              navigator.clipboard.writeText(url)
            }
          }}
          className="mt-6 text-xs text-muted/60 underline underline-offset-2"
        >
          Or share link
        </button>
      </div>
    )
  }

  // ── ACTIVE: countdown ─────────────────────────────────────────────────────
  if (view === 'active' && session?.started_at) {
    return (
      <div className="flex flex-col items-center justify-between flex-1 px-6 py-14 fade-in">
        {/* Header */}
        <div className="flex flex-col items-center gap-2">
          <div className="flex items-center gap-2">
            <span className="pulse-dot w-2 h-2 rounded-full bg-green-400" />
            <span className="text-xs font-medium text-green-400 uppercase tracking-widest">
              Human Mode Active
            </span>
          </div>
          <p className="text-muted text-sm mt-1">
            You&apos;re here with{' '}
            <span className="text-ink font-medium">{partnerName()}</span>
          </p>
        </div>

        {/* Timer */}
        <Timer
          startedAt={session.started_at}
          durationMinutes={session.duration}
          onComplete={handleTimerComplete}
        />

        {/* Instructions */}
        <div className="w-full max-w-xs space-y-3">
          <div className="flex items-start gap-3 px-4 py-3 rounded-xl bg-surface">
            <span className="text-lg mt-0.5">🌙</span>
            <p className="text-sm text-muted leading-relaxed">
              Turn on Do Not Disturb
            </p>
          </div>
          <div className="flex items-start gap-3 px-4 py-3 rounded-xl bg-surface">
            <span className="text-lg mt-0.5">📱</span>
            <p className="text-sm text-muted leading-relaxed">
              Place your phone face down
            </p>
          </div>
        </div>

        {/* Exit */}
        <HoldToExitButton onExit={handleExit} />
      </div>
    )
  }

  // ── COMPLETED ─────────────────────────────────────────────────────────────
  if (view === 'completed') {
    const durationDone = session?.duration ?? 0

    return (
      <div className="flex flex-col items-center justify-center flex-1 px-6 py-14 fade-in">
        <div className="w-16 h-16 rounded-full bg-green-500/10 border border-green-500/20 flex items-center justify-center mb-6">
          <span className="text-3xl">✓</span>
        </div>

        <h2 className="text-3xl font-semibold text-ink">Session complete</h2>
        <p className="mt-3 text-muted text-center text-sm leading-relaxed">
          You spent {durationDone} minutes present with{' '}
          <span className="text-ink font-medium">{partnerName()}</span>.
        </p>

        {sessionsTogether > 0 && (
          <div className="mt-8 px-6 py-4 rounded-2xl bg-surface border border-white/8 text-center">
            <p className="text-3xl font-semibold text-accent">{sessionsTogether}</p>
            <p className="text-xs text-muted mt-1 uppercase tracking-widest">
              sessions together
            </p>
          </div>
        )}

        <button
          onClick={() => router.push('/')}
          className="mt-12 w-full max-w-xs py-4 rounded-2xl bg-accent text-white text-lg font-medium tracking-wide glow active:scale-95 transition-transform"
        >
          Done
        </button>

        <button
          onClick={() => router.push('/create')}
          className="mt-4 text-sm text-muted active:opacity-60"
        >
          Start another session
        </button>
      </div>
    )
  }

  return null
}
