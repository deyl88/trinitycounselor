'use client'

import { useEffect, useState } from 'react'
import { getOrCreateUserId, getSavedName, saveName, upsertUser, getUserSessions } from '@/lib/session'

interface Session {
  id: string
  duration: number
  started_at: string | null
  ended_at: string | null
  created_at: string
  partner: { id: string; name: string } | null
}

function formatDate(iso: string) {
  const d = new Date(iso)
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function formatDuration(startedAt: string | null, endedAt: string | null, duration: number) {
  if (!startedAt) return `${duration} min (not started)`
  if (!endedAt) return `${duration} min`
  const actual = Math.round((new Date(endedAt).getTime() - new Date(startedAt).getTime()) / 60000)
  return actual >= duration ? `${duration} min ✓` : `${actual} of ${duration} min`
}

export default function ProfilePage() {
  const [name, setName] = useState('')
  const [editingName, setEditingName] = useState(false)
  const [nameInput, setNameInput] = useState('')
  const [sessions, setSessions] = useState<Session[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const saved = getSavedName()
    setName(saved)
    setNameInput(saved)

    const userId = getOrCreateUserId()
    if (userId) {
      getUserSessions(userId)
        .then((s) => setSessions(s as Session[]))
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  async function handleSaveName() {
    const trimmed = nameInput.trim()
    if (!trimmed) return
    saveName(trimmed)
    setName(trimmed)
    setEditingName(false)
    const userId = getOrCreateUserId()
    if (userId) await upsertUser(userId, trimmed)
  }

  const completedSessions = sessions.filter((s) => s.ended_at && s.started_at)
  const totalMinutes = completedSessions.reduce((acc, s) => acc + s.duration, 0)

  return (
    <div className="flex flex-col flex-1 px-6 py-6 fade-in">
      {/* Name */}
      <div className="mb-8">
        {editingName ? (
          <div className="flex gap-2 items-center">
            <input
              type="text"
              value={nameInput}
              onChange={(e) => setNameInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSaveName()}
              autoFocus
              maxLength={30}
              className="flex-1 px-4 py-3 rounded-xl bg-surface border border-accent/60 text-ink text-lg focus:outline-none"
            />
            <button
              onClick={handleSaveName}
              className="px-4 py-3 rounded-xl bg-accent text-white text-sm font-medium"
            >
              Save
            </button>
          </div>
        ) : (
          <button
            onClick={() => setEditingName(true)}
            className="flex items-center gap-3 group"
          >
            <div className="w-12 h-12 rounded-full bg-accent/20 border border-accent/30 flex items-center justify-center text-accent text-lg font-semibold">
              {name ? name[0].toUpperCase() : '?'}
            </div>
            <div className="text-left">
              <p className="text-ink font-medium text-lg">{name || 'Set your name'}</p>
              <p className="text-xs text-muted">Tap to edit</p>
            </div>
          </button>
        )}
      </div>

      {/* Stats */}
      {completedSessions.length > 0 && (
        <div className="grid grid-cols-2 gap-3 mb-8">
          <div className="px-4 py-4 rounded-2xl bg-surface border border-white/8 text-center">
            <p className="text-3xl font-semibold text-accent">{completedSessions.length}</p>
            <p className="text-xs text-muted mt-1 uppercase tracking-widest">Sessions</p>
          </div>
          <div className="px-4 py-4 rounded-2xl bg-surface border border-white/8 text-center">
            <p className="text-3xl font-semibold text-accent">{totalMinutes}</p>
            <p className="text-xs text-muted mt-1 uppercase tracking-widest">Minutes present</p>
          </div>
        </div>
      )}

      {/* Session history */}
      <p className="text-xs font-medium text-muted uppercase tracking-widest mb-4">
        Past sessions
      </p>

      {loading ? (
        <div className="flex justify-center py-8">
          <div className="w-6 h-6 rounded-full border-2 border-accent/30 border-t-accent animate-spin" />
        </div>
      ) : sessions.length === 0 ? (
        <div className="flex flex-col items-center py-12 text-center">
          <p className="text-muted text-sm">No sessions yet.</p>
          <p className="text-muted/50 text-xs mt-1">Tap In to start your first one.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {sessions.map((s) => (
            <div
              key={s.id}
              className="flex items-center justify-between px-4 py-3 rounded-xl bg-surface border border-white/6"
            >
              <div>
                <p className="text-sm text-ink font-medium">
                  {s.partner ? `with ${s.partner.name}` : 'Solo'}
                </p>
                <p className="text-xs text-muted mt-0.5">{formatDate(s.created_at)}</p>
              </div>
              <div className="text-right">
                <p className="text-sm text-muted">{formatDuration(s.started_at, s.ended_at, s.duration)}</p>
                {!s.started_at && (
                  <p className="text-xs text-muted/40 mt-0.5">never started</p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
