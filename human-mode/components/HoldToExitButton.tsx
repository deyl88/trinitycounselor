'use client'

import { useCallback, useRef, useState } from 'react'

interface HoldToExitButtonProps {
  onExit: () => void
  holdDuration?: number // ms, default 2500
}

const HOLD_MS = 2500

export default function HoldToExitButton({
  onExit,
  holdDuration = HOLD_MS,
}: HoldToExitButtonProps) {
  const [progress, setProgress] = useState(0) // 0–1
  const [holding, setHolding] = useState(false)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const rafRef = useRef<number | null>(null)
  const startTimeRef = useRef<number | null>(null)

  const startHold = useCallback(() => {
    setHolding(true)
    startTimeRef.current = Date.now()

    function tick() {
      const elapsed = Date.now() - (startTimeRef.current ?? Date.now())
      const p = Math.min(elapsed / holdDuration, 1)
      setProgress(p)
      if (p < 1) {
        rafRef.current = requestAnimationFrame(tick)
      }
    }
    rafRef.current = requestAnimationFrame(tick)

    timerRef.current = setTimeout(() => {
      setProgress(1)
      setHolding(false)
      onExit()
    }, holdDuration)
  }, [holdDuration, onExit])

  const cancelHold = useCallback(() => {
    if (timerRef.current) { clearTimeout(timerRef.current); timerRef.current = null }
    if (rafRef.current) { cancelAnimationFrame(rafRef.current); rafRef.current = null }
    setHolding(false)
    setProgress(0)
  }, [])

  // SVG ring
  const size = 80
  const strokeWidth = 3
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const dashOffset = circumference * (1 - progress)

  return (
    <div className="flex flex-col items-center gap-3">
      <button
        onMouseDown={startHold}
        onMouseUp={cancelHold}
        onMouseLeave={cancelHold}
        onTouchStart={(e) => { e.preventDefault(); startHold() }}
        onTouchEnd={cancelHold}
        onTouchCancel={cancelHold}
        aria-label="Hold to exit session"
        className="relative flex items-center justify-center select-none"
      >
        {/* Progress ring */}
        <svg width={size} height={size} className="-rotate-90 absolute">
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="rgba(255,255,255,0.08)"
            strokeWidth={strokeWidth}
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={holding ? '#EF4444' : 'rgba(255,255,255,0.3)'}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={dashOffset}
          />
        </svg>

        {/* Inner circle */}
        <div
          className={`w-16 h-16 rounded-full border flex items-center justify-center transition-all ${
            holding
              ? 'bg-red-500/20 border-red-500/60'
              : 'bg-white/5 border-white/15'
          }`}
        >
          <span className={`text-xs font-medium transition-colors ${holding ? 'text-red-400' : 'text-muted'}`}>
            {holding ? 'Release' : 'Hold'}
          </span>
        </div>
      </button>
      <p className="text-xs text-muted/60">Hold to exit session</p>
    </div>
  )
}
