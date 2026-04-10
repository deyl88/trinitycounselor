'use client'

import Link from 'next/link'

export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center flex-1 px-6 py-16 fade-in">
      {/* Logo / wordmark */}
      <div className="mb-3 w-12 h-12 rounded-full bg-accent-glow border border-accent/20 flex items-center justify-center glow">
        <span className="text-2xl">◎</span>
      </div>

      <h1 className="mt-6 text-4xl font-semibold tracking-tight text-ink">
        Human Mode
      </h1>
      <p className="mt-3 text-lg text-muted font-light tracking-wide">
        Tap in. Be here.
      </p>

      <p className="mt-8 text-center text-sm text-muted leading-relaxed max-w-xs">
        Put the phones down. Create a shared session with someone you&apos;re
        with right now and be fully present together.
      </p>

      <Link
        href="/create"
        className="mt-12 w-full max-w-xs py-4 rounded-2xl bg-accent text-white text-center text-lg font-medium tracking-wide glow active:scale-95 transition-transform"
      >
        Tap In
      </Link>

      <p className="mt-6 text-xs text-muted/60">
        No account needed &mdash; just presence
      </p>
    </div>
  )
}
