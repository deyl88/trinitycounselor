import { useState, useEffect } from 'react'

const C = {
  bg: '#0A0A12', card: '#111119', border: '#1C1C2E',
  purple: '#C77DFF', pink: '#FF85C2', mint: '#4FFFC4',
  muted: '#6B6B8A', grad: 'linear-gradient(135deg, #C77DFF 0%, #FF85C2 100%)',
}
const inp = { background: '#16161F', border: '1px solid #1C1C2E', borderRadius: 10, color: '#fff', padding: '9px 12px', fontSize: 13, width: '100%', boxSizing: 'border-box' }
const HOT = { 5: '🏳️', 6: '📈', 7: '🔥', 8: '🔥🔥', 9: '🔥🔥🔥', 10: '🤯' }

function ScoreBar({ value, color }) {
  return (
    <div style={{ background: '#1C1C2E', borderRadius: 6, height: 5, overflow: 'hidden', marginTop: 4 }}>
      <div style={{ width: `${value}%`, height: '100%', background: color, borderRadius: 6 }} />
    </div>
  )
}

function RecCard({ rec, onAct }) {
  const [acting, setActing] = useState(false)
  const act = async status => {
    setActing(true)
    await fetch('/api/recs', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id: rec.id, status }) })
    onAct(rec.id)
  }
  return (
    <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 22, padding: 18, marginBottom: 12 }}>
      <div style={{ marginBottom: 12 }}>
        <div style={{ fontSize: 17, fontWeight: 800 }}>{rec.song_name}</div>
        <div style={{ color: C.muted, fontSize: 13, marginTop: 2 }}>{rec.artist}</div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 10 }}>
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ fontSize: 11, color: C.muted }}>Style Fit</span>
            <span style={{ fontSize: 14, fontWeight: 800, color: C.purple }}>{rec.style_fit_score}%</span>
          </div>
          <ScoreBar value={rec.style_fit_score} color={C.purple} />
        </div>
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ fontSize: 11, color: C.muted }}>Match</span>
            <span style={{ fontSize: 14, fontWeight: 800, color: C.pink }}>{rec.final_score}%</span>
          </div>
          <ScoreBar value={rec.final_score} color={C.pink} />
        </div>
      </div>
      {rec.tip_text && (
        <div style={{ background: 'rgba(199,125,255,0.08)', borderLeft: `3px solid ${C.purple}`, borderRadius: '0 10px 10px 0', padding: '9px 12px', marginBottom: 14, fontSize: 13, color: '#D4B8FF', lineHeight: 1.6 }}>
          {rec.tip_text}
        </div>
      )}
      <div style={{ display: 'flex', gap: 8 }}>
        <button onClick={() => act('skipped')} disabled={acting} style={{ flex: 1, background: 'transparent', border: `1px solid ${C.border}`, borderRadius: 12, color: C.muted, padding: '10px', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}>Skip</button>
        <button onClick={() => act('saved')} disabled={acting} style={{ flex: 2, background: C.grad, border: 'none', borderRadius: 12, color: '#fff', padding: '10px', fontSize: 13, fontWeight: 700, cursor: 'pointer' }}>Save this one 🩷</button>
      </div>
    </div>
  )
}

export default function ForYou() {
  const [song, setSong] = useState('')
  const [artist, setArtist] = useState('')
  const [heat, setHeat] = useState(8)
  const [recs, setRecs] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch('/api/recs?status=pending').then(r => r.json()).then(d => setRecs(Array.isArray(d) ? d : []))
  }, [])

  const analyze = async () => {
    if (!song.trim()) return
    setLoading(true)
    setError(null)
    try {
      const res = await fetch('/api/analyze', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ song_name: song.trim(), artist: artist.trim(), trending_score: heat }),
      }).then(r => r.json())
      if (res.error) throw new Error(res.error)
      setRecs(r => [res, ...r])
      setSong('')
      setArtist('')
    } catch (e) {
      setError(e.message)
    }
    setLoading(false)
  }

  const dismiss = id => setRecs(r => r.filter(x => x.id !== id))

  return (
    <div style={{ padding: '28px 16px 16px', background: C.bg, minHeight: '100%' }}>
      <p style={{ color: C.muted, fontSize: 13, marginBottom: 4 }}>what should she cover next?</p>
      <h1 style={{ fontSize: 26, fontWeight: 900, margin: '0 0 20px' }}>For You 🎵</h1>

      <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 22, padding: 16, marginBottom: 20 }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 12 }}>
          <div>
            <div style={{ fontSize: 11, color: C.muted, marginBottom: 4 }}>Song *</div>
            <input style={inp} placeholder="Espresso" value={song} onChange={e => setSong(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && analyze()} />
          </div>
          <div>
            <div style={{ fontSize: 11, color: C.muted, marginBottom: 4 }}>Artist</div>
            <input style={inp} placeholder="Sabrina Carpenter" value={artist} onChange={e => setArtist(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && analyze()} />
          </div>
        </div>
        <div style={{ marginBottom: 12 }}>
          <div style={{ fontSize: 11, color: C.muted, marginBottom: 6 }}>How hot right now? {HOT[heat]}</div>
          <div style={{ display: 'flex', gap: 5 }}>
            {[5, 6, 7, 8, 9, 10].map(v => (
              <button key={v} onClick={() => setHeat(v)} style={{ flex: 1, padding: '7px 0', fontSize: 12, fontWeight: 600, borderRadius: 9, cursor: 'pointer', border: 'none', background: heat === v ? C.grad : '#1C1C2E', color: heat === v ? '#fff' : C.muted }}>{v}</button>
            ))}
          </div>
        </div>
        <button onClick={analyze} disabled={loading || !song.trim()} style={{ width: '100%', background: loading || !song.trim() ? '#1C1C2E' : C.grad, border: 'none', borderRadius: 13, color: loading || !song.trim() ? C.muted : '#fff', padding: '12px', fontSize: 14, fontWeight: 700, cursor: loading || !song.trim() ? 'default' : 'pointer' }}>
          {loading ? 'Asking Claude… (~10s)' : 'Analyze ✨'}
        </button>
        {error && <div style={{ marginTop: 10, fontSize: 13, color: '#FF9090', textAlign: 'center' }}>{error}</div>}
      </div>

      {recs.length === 0 && !loading && (
        <div style={{ textAlign: 'center', padding: '40px 20px', color: C.muted }}>
          <div style={{ fontSize: 48, marginBottom: 12 }}>🎤</div>
          <p style={{ fontSize: 14, color: '#fff', fontWeight: 600, marginBottom: 6 }}>Enter a trending song above</p>
          <p style={{ fontSize: 13 }}>Claude will score it against Summer’s style and write a tip.</p>
        </div>
      )}

      {recs.map(rec => <RecCard key={rec.id} rec={rec} onAct={dismiss} />)}
    </div>
  )
}
