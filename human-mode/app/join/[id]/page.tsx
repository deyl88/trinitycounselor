'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { getSession, upsertUser, addParticipant, getOrCreateUserId, getSavedName, saveName } from '@/lib/session'

export default function JoinPage() {
  const { id: sessionId } = useParams<{ id: string }>()
  const router = useRouter()

  const [name, setName] = useState('')

  useEffect(() => {
    const saved = getSavedName()
    if (saved) setName(saved)
  }, [])
  const [duration, setDuration] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)
  const [loadingSession, setLoadingSession] = useState(true)
  const [error, setError] = useState('')
  const [notFound, setNotFound] = useState(false)

  // Load session info to show duration preview
  useEffect(() => {
    if (!sessionId) return
    getSession(sessionId)
      .then((s) => {
        if (s.ended_at) {
          setNotFound(true)
        } else {
          setDuration(s.duration)
        }
      })
      .catch(() => setNotFound(true))
      .finally(() => setLoadingSession(false))
  }, [sessionId])

  async function handleJoin() {
    if (!name.trim()) {
      setError('Enter your name to continue')
      return
    }
    setLoading(true)
    setError('')
    try {
      const userId = getOrCreateUserId()
      saveName(name.trim())
      await upsertUser(userId, name.trim())
      await addParticipant(sessionId, userId)
      router.push(`/session/${sessionId}`)
    } catch (err) {
      console.error(err)
      setError('Could not join session. Please try again.')
      setLoading(false)
    }
  }

  if (loadingSession) {
    return (
      <div className="flex flex-col items-center justify-center flex-1 px-6">
        <div className="w-8 h-8 rounded-full border-2 border-accent/30 border-t-accent animate-spin" />
      </div>
    )
  }

  if (notFound) {
    return (
      <div className="flex flex-col items-center justify-center flex-1 px-6 fade-in">
        <p className="text-2xl mb-3">🔒</p>
        <h2 className="text-xl font-semibold text-ink">Session not found</h2>
        <p className="mt-2 text-sm text-muted text-center">
          This session may have ended or the link is invalid.
        </p>
        <button
          onClick={() => router.push('/')}
          className="mt-8 text-accent text-sm"
        >
          Go home
        </button>
      </div>
    )
  }

  return (
    <div className="flex flex-col flex-1 px-6 py-12 fade-in">
      {/* Header */}
      <div className="flex flex-col items-center mb-10">
        <div className="w-12 h-12 rounded-full bg-accent-glow border border-accent/20 flex items-center justify-center glow mb-4">
          <span className="text-2xl">◎</span>
        </div>
        <h2 className="text-2xl font-semibold text-ink">You&apos;re invited</h2>
        {duration && (
          <p className="mt-2 text-sm text-muted">
            {duration}-minute Human Mode session
          </p>
        )}
      </div>

      {/* Name input */}
      <div>
        <label className="block text-xs font-medium text-muted uppercase tracking-widest mb-3">
          Your name
        </label>
        <input
          type="text"
          value={name}
          onChange={(e) => { setName(e.target.value); setError('') }}
          placeholder="e.g. Alex"
          maxLength={30}
          autoFocus
          className="w-full px-4 py-4 rounded-xl bg-surface border border-white/10 text-ink placeholder-muted/50 text-lg focus:outline-none focus:border-accent/60 transition-colors"
        />
      </div>

      {error && (
        <p className="mt-4 text-sm text-red-400 text-center">{error}</p>
      )}

      <div className="flex-1" />

      {/* Join button */}
      <button
        onClick={handleJoin}
        disabled={loading}
        className="mt-8 w-full py-4 rounded-2xl bg-accent text-white text-lg font-medium tracking-wide glow active:scale-95 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? 'Joining…' : 'Tap In'}
      </button>

      <p className="mt-4 text-xs text-center text-muted/60">
        No account needed — just presence
      </p>
    </div>
  )
}
