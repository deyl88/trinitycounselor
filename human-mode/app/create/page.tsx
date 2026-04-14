'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { createSession, upsertUser, addParticipant, getOrCreateUserId, getSavedName, saveName } from '@/lib/session'

export default function CreatePage() {
  const router = useRouter()
  const [name, setName] = useState('')

  useEffect(() => {
    const saved = getSavedName()
    if (saved) setName(saved)
  }, [])
  const [duration, setDuration] = useState<30 | 60>(30)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleCreate() {
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
      const session = await createSession(duration)
      await addParticipant(session.id, userId)
      // Store creator flag so /session/[id] knows to listen for 2nd join
      localStorage.setItem(`humanmode_creator_${session.id}`, '1')
      router.push(`/session/${session.id}`)
    } catch (err) {
      console.error(err)
      setError('Something went wrong. Please try again.')
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col flex-1 px-6 py-12 fade-in">
      <button
        onClick={() => router.back()}
        className="self-start text-muted text-sm mb-8 active:opacity-60 transition-opacity"
      >
        ← Back
      </button>

      <h2 className="text-2xl font-semibold text-ink">New Session</h2>
      <p className="mt-2 text-sm text-muted">
        You&apos;ll share this session with one other person.
      </p>

      {/* Name input */}
      <div className="mt-10">
        <label className="block text-xs font-medium text-muted uppercase tracking-widest mb-3">
          Your name
        </label>
        <input
          type="text"
          value={name}
          onChange={(e) => { setName(e.target.value); setError('') }}
          placeholder="e.g. Jordan"
          maxLength={30}
          className="w-full px-4 py-4 rounded-xl bg-surface border border-white/10 text-ink placeholder-muted/50 text-lg focus:outline-none focus:border-accent/60 transition-colors"
        />
      </div>

      {/* Duration picker */}
      <div className="mt-10">
        <label className="block text-xs font-medium text-muted uppercase tracking-widest mb-3">
          Session length
        </label>
        <div className="grid grid-cols-2 gap-3">
          {([30, 60] as const).map((mins) => (
            <button
              key={mins}
              onClick={() => setDuration(mins)}
              className={`py-4 rounded-xl border text-lg font-medium transition-all active:scale-95 ${
                duration === mins
                  ? 'bg-accent border-accent text-white glow'
                  : 'bg-surface border-white/10 text-muted hover:border-accent/40'
              }`}
            >
              {mins} min
            </button>
          ))}
        </div>
      </div>

      {error && (
        <p className="mt-6 text-sm text-red-400 text-center">{error}</p>
      )}

      {/* Create button */}
      <button
        onClick={handleCreate}
        disabled={loading}
        className="mt-auto mt-12 w-full py-4 rounded-2xl bg-accent text-white text-lg font-medium tracking-wide glow active:scale-95 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? 'Creating…' : 'Create Session'}
      </button>
    </div>
  )
}
