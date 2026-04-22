import { useState, useEffect } from 'react'

const C = {
  bg: '#0A0A12', card: '#111119', border: '#1C1C2E',
  purple: '#C77DFF', pink: '#FF85C2', mint: '#4FFFC4',
  muted: '#6B6B8A', grad: 'linear-gradient(135deg, #C77DFF 0%, #FF85C2 100%)',
}

export default function Saved() {
  const [recs, setRecs] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/recs?status=saved').then(r => r.json())
      .then(d => setRecs(Array.isArray(d) ? d : []))
      .finally(() => setLoading(false))
  }, [])

  const unsave = async (id) => {
    await fetch('/api/recs', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id, status: 'pending' }) })
    setRecs(r => r.filter(x => x.id !== id))
  }

  return (
    <div style={{ padding: '28px 16px 16px', background: C.bg, minHeight: '100%' }}>
      <p style={{ color: C.muted, fontSize: 13, marginBottom: 4 }}>covers to record</p>
      <h1 style={{ fontSize: 26, fontWeight: 900, margin: '0 0 20px' }}>Saved 🎀</h1>

      {loading && <div style={{ textAlign: 'center', color: C.muted, padding: 40 }}>Loading...</div>}

      {!loading && recs.length === 0 && (
        <div style={{ textAlign: 'center', padding: '48px 20px', color: C.muted }}>
          <div style={{ fontSize: 48, marginBottom: 12 }}>🎀</div>
          <p style={{ fontSize: 14, color: '#fff', fontWeight: 600, marginBottom: 6 }}>Nothing saved yet</p>
          <p style={{ fontSize: 13 }}>Go to For You and save songs Summer should cover.</p>
        </div>
      )}

      {recs.map(rec => (
        <div key={rec.id} style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 22, padding: 18, marginBottom: 12 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
            <div>
              <div style={{ fontSize: 17, fontWeight: 800 }}>{rec.song_name}</div>
              <div style={{ color: C.muted, fontSize: 13, marginTop: 2 }}>{rec.artist}</div>
            </div>
            <span style={{ background: C.grad, color: '#fff', fontSize: 12, fontWeight: 700, padding: '3px 10px', borderRadius: 20, flexShrink: 0, marginLeft: 8 }}>
              {rec.final_score}%
            </span>
          </div>
          {rec.tip_text && (
            <div style={{ background: 'rgba(199,125,255,0.08)', borderLeft: `3px solid ${C.purple}`, borderRadius: '0 10px 10px 0', padding: '9px 12px', marginBottom: 14, fontSize: 13, color: '#D4B8FF', lineHeight: 1.6 }}>
              {rec.tip_text}
            </div>
          )}
          <button onClick={() => unsave(rec.id)} style={{ background: 'transparent', border: `1px solid ${C.border}`, borderRadius: 10, color: C.muted, padding: '7px 14px', fontSize: 12, cursor: 'pointer' }}>Move back to For You</button>
        </div>
      ))}
    </div>
  )
}
