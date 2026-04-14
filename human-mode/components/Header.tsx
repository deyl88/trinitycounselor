'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

export default function Header() {
  const pathname = usePathname()

  // Hide on home (has its own design) and active session pages
  if (pathname === '/' || pathname.startsWith('/session/')) return null

  return (
    <header className="flex items-center justify-between px-6 pt-5 pb-1 flex-shrink-0">
      <Link
        href="/"
        className="w-9 h-9 rounded-full bg-surface border border-white/10 flex items-center justify-center text-muted active:opacity-60 transition-opacity"
        aria-label="Home"
      >
        <span className="text-base">◎</span>
      </Link>

      <Link
        href="/profile"
        className={`w-9 h-9 rounded-full flex items-center justify-center transition-opacity active:opacity-60 ${
          pathname === '/profile'
            ? 'bg-accent/20 border border-accent/40 text-accent'
            : 'bg-surface border border-white/10 text-muted'
        }`}
        aria-label="Profile"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="8" r="4" />
          <path d="M4 20c0-4 3.6-7 8-7s8 3 8 7" />
        </svg>
      </Link>
    </header>
  )
}
