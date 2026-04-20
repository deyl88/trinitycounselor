import { useState, useEffect } from 'react'

const API = import.meta.env.DEV ? 'http://localhost:8000' : ''

const C = {
  bg: '#0A0A12',
  card: '#111119',
  border: '#1C1C2E',
  purple: '#C77DFF',
  pink: '#FF85C2',
  mint: '#4FFFC4',
  muted: '#6B6B8A',
  grad: 'linear-gradient(135deg, #C77DFF 0%, #FF85C2 100%)',
  gradSoft: 'linear-gradient(135deg, rgba(199,125,255,0.12) 0%, rgba(255,133,194,0.12) 100%)',
}

const fmt = n =>
  n >= 1_000_000 ? `${(n / 1_000_000).toFixed(1)}M`
  : n >= 1_000 ? `${(n / 1_000).toFixed(1)}K`
  : String(n || 0)

export default function Dashboard() {
  const [videos, setVideos] = useState([])
  const [fp, setFp] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      fetch(`${API}/api/videos/`).then(r => r.json()).catch(() => []),
      fetch(`${API}/api/fingerprint/latest`).then(r => r.json()).catch(() => ({})),
    ]).then(([vids, fpData]) => {
      setVideos(Array.isArray(vids) ? vids : [])
      if (fpData?.fingerprint) setFp(fpData.fingerprint)
    }).finally(() => setLoading(false))
  }, [])

  const totalViews = videos.reduce((s, v) => s + (v.views || 0), 0)
  const totalLikes = videos.reduce((s, v) => s + (v.likes || 0), 0)
  const covers = videos.filter(v => v.is_cover).length
  const avgEng = videos.length
    ? (videos.reduce((s, v) => s + (v.views > 0 ? (v.likes + v.comments + v.shares) / v.views * 100 : 0), 0) / videos.length).toFixed(1)
    : '0.0'

  return (
    <div style={{ padding: '28px 16px 16px', background: C.bg, minHeight: '100%' }}>
      <div style={{ marginBottom: 24 }}>
        <p style={{ color: C.muted, fontSize: 13, marginBottom: 4 }}>welcome back 🌸</p>
        <h1 style={{ fontSize: 28, fontWeight: 900, margin: 0, background: C.grad, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          Summer Victoria
        </h1>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 20 }}>
        {[
          { label: 'Videos', value: videos.length, icon: '🎬', color: C.purple },
          { label: 'Total Views', value: fmt(totalViews), icon: '👁️', color: C.pink },
          { label: 'Avg Engagement', value: `${avgEng}%`, icon: '📊', color: C.mint },
          { label: 'Covers', value: covers, icon: '🎵', color: C.pink },
        ].map(({ label, value, icon, color }) => (
          <div key={label} style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 20, padding: '16px 14px' }}>
            <div style={{ fontSize: 22, marginBottom: 6 }}>{icon}</div>
            <div style={{ fontSize: 24, fontWeight: 800, color, lineHeight: 1 }}>{value}</div>
            <div style={{ fontSize: 12, color: C.muted, marginTop: 4 }}>{label}</div>
          </div>
        ))}
      </div>

      {fp && (
        <div style={{ background: C.gradSoft, border: '1px solid rgba(199,125,255,0.2)', borderRadius: 22, padding: 18, marginBottom: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
            <span style={{ fontWeight: 700, fontSize: 15 }}>Your Sound ✨</span>
            <span style={{ fontSize: 11, color: C.muted, background: C.card, padding: '3px 8px', borderRadius: 20 }}>{fp.sample_size} top videos</span>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 12 }}>
            {Object.entries(fp.genre || {}).slice(0, 3).map(([g, pct]) => (
              <span key={g} style={{ background: 'rgba(199,125,255,0.2)', color: C.purple, fontSize: 12, padding: '4px 11px', borderRadius: 20, border: '1px solid rgba(199,125,255,0.3)', fontWeight: 600 }}>
                {g} · {Math.round(pct * 100)}%
              </span>
            ))}
            {Object.entries(fp.emotional_tone || {}).slice(0, 2).map(([t, pct]) => (
              <span key={t} style={{ background: 'rgba(255,133,194,0.2)', color: C.pink, fontSize: 12, padding: '4px 11px', borderRadius: 20, border: '1px solid rgba(255,133,194,0.3)', fontWeight: 600 }}>
                {t} · {Math.round(pct * 100)}%
              </span>
            ))}
          </div>
          {fp.preferred_arrangements?.length > 0 && (
            <div style={{ fontSize: 12, color: C.muted }}>Best with <span style={{ color: '#D4B8FF', fontWeight: 600 }}>{fp.preferred_arrangements.slice(0, 3).join(' · ')}</span></div>
          )}
          {fp.avg_chorus_recognizability && (
            <div style={{ marginTop: 8, fontSize: 12, color: C.muted }}>Chorus recognizability avg <span style={{ color: C.mint, fontWeight: 700 }}>{fp.avg_chorus_recognizability}/10</span></div>
          )}
        </div>
      )}

      {videos.length > 0 && (
        <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 22, padding: 18 }}>
          <p style={{ fontWeight: 700, fontSize: 15, marginBottom: 14 }}>Top Performers 🏆</p>
          {[...videos].sort((a, b) => (b.views || 0) - (a.views || 0)).slice(0, 3).map((v, i) => (
            <div key={v.id} style={{ display: 'flex', alignItems: 'center', gap: 12, paddingBottom: i < 2 ? 12 : 0, marginBottom: i < 2 ? 12 : 0, borderBottom: i < 2 ? `1px solid ${C.border}` : 'none' }}>
              <div style={{ width: 30, height: 30, borderRadius: 10, flexShrink: 0, background: C.grad, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 13, fontWeight: 800, color: '#fff' }}>{i + 1}</div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 13, fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{v.song_name || v.title || 'Untitled'}</div>
                <div style={{ fontSize: 11, color: C.muted }}>{v.song_artist || '—'}</div>
              </div>
              <div style={{ fontSize: 14, fontWeight: 700, color: C.purple, flexShrink: 0 }}>{fmt(v.views)}</div>
            </div>
          ))}
        </div>
      )}

      {!loading && videos.length === 0 && (
        <div style={{ textAlign: 'center', padding: '48px 20px', color: C.muted }}>
          <div style={{ fontSize: 52, marginBottom: 12 }}>🎤</div>
          <p style={{ fontSize: 15, fontWeight: 700, color: '#fff', marginBottom: 6 }}>No videos yet</p>
          <p style={{ fontSize: 13 }}>Head to Import to add your TikToks.</p>
        </div>
      )}
    </div>
  )
}
