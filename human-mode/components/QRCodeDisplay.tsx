'use client'

import { useEffect, useState } from 'react'
import { QRCodeSVG } from 'qrcode.react'

interface QRCodeDisplayProps {
  sessionId: string
}

export default function QRCodeDisplay({ sessionId }: QRCodeDisplayProps) {
  const [url, setUrl] = useState('')

  useEffect(() => {
    // Build full URL client-side (window.location not available on server)
    setUrl(`${window.location.origin}/join/${sessionId}`)
  }, [sessionId])

  if (!url) return (
    <div className="w-48 h-48 bg-surface rounded-2xl animate-pulse" />
  )

  return (
    <div className="p-4 bg-white rounded-2xl">
      <QRCodeSVG
        value={url}
        size={176}
        bgColor="#ffffff"
        fgColor="#080810"
        level="M"
      />
    </div>
  )
}
