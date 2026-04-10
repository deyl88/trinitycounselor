'use client'

import { useEffect, useState } from 'react'

interface TimerProps {
  startedAt: string       // ISO timestamp from server
  durationMinutes: number
  onComplete: () => void
}

function formatTime(seconds: number): string {
  const s = Math.max(0, seconds)
  const m = Math.floor(s / 60)
  const sec = s % 60
  return `${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`
}

export default function Timer({ startedAt, durationMinutes, onComplete }: TimerProps) {
  const totalSeconds = durationMinutes * 60

  function getRemainingSeconds(): number {
    const endMs = new Date(startedAt).getTime() + totalSeconds * 1000
    return Math.round((endMs - Date.now()) / 1000)
  }

  const [remaining, setRemaining] = useState(getRemainingSeconds)
  const [completed, setCompleted] = useState(false)

  useEffect(() => {
    const interval = setInterval(() => {
      const r = getRemainingSeconds()
      setRemaining(r)
      if (r <= 0 && !completed) {
        setCompleted(true)
        clearInterval(interval)
        onComplete()
      }
    }, 1000)
    return () => clearInterval(interval)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [startedAt, durationMinutes])

  const progress = Math.max(0, Math.min(1, 1 - remaining / totalSeconds))

  // SVG ring progress
  const size = 200
  const strokeWidth = 4
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const dashOffset = circumference * (1 - progress)

  return (
    <div className="flex flex-col items-center">
      {/* Progress ring + time display */}
      <div className="relative">
        <svg width={size} height={size} className="-rotate-90">
          {/* Track */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="rgba(123,104,238,0.12)"
            strokeWidth={strokeWidth}
          />
          {/* Progress */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="#7B68EE"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={dashOffset}
            style={{ transition: 'stroke-dashoffset 1s linear' }}
          />
        </svg>
        {/* Time text centered over ring */}
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-4xl font-light tabular-nums text-ink tracking-widest">
            {formatTime(remaining)}
          </span>
        </div>
      </div>
    </div>
  )
}
