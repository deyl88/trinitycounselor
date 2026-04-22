import { useState, useEffect } from 'react'

const C = {
  bg: '#0A0A12', card: '#111119', border: '#1C1C2E',
  purple: '#C77DFF', pink: '#FF85C2', mint: '#4FFFC4',
  muted: '#6B6B8A', grad: 'linear-gradient(135deg, #C77DFF 0%, #FF85C2 100%)',
}
const inp = { background: '#16161F', border: '1px solid #1C1C2E', borderRadius: 10, color: '#fff', padding: '8px 10px', width: '100%', fontSize: 13, boxSizing: 'border-box' }
const EMPTY = () => ({ song_name: '', artist: '' })

export default function Setup() {
  const [fp, setFp] = useState(null)
  const [songs, setSongs] = useState(Array.from({ length: 10 }, EMPTY))
  const [loading, setLoading] = useState(false)
  const [checking, setChecking] = useState(true)
  const [msg, setMsg] = useState(null)

  useEffect(() => {
    fetch('/api/fingerprint').then(r => r.json())
      .then(d => { if (d.fingerprint) setFp(d.fingerprint) })
      .finally(() => setChecking(false))
  }, [])

  const update = (i, f, v) => setSongs(s => s.map((r, idx) => idx === i ? { ...r, [f]: v } : r))

  const build = async () => {
    const valid = songs.filter(s => s.song_name.trim())
    if (valid.length < 3) { setMsg({ ok: false, text: 'Add at least 3 songs.' }); return }
    setLoading(true)
    setMsg(null)
    try {
      const res = await fetch('/api/fingerprint', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ songs: valid }),
      }).then(r => r.json())
      if (res.error) throw new Error(res.error)
      setFp(res.fingerprint)
      setMsg({ ok: true, text: 'Profile built! Head to For You to find songs.' })
    } catch (e) {
      setMsg({ ok: false, text: e.message })
    }
    setLoading(false)
  }

  if (checking) return <div style={{ padding: 40, textAlign: 'center', color: C.muted }}>Loading...</div>

  return (
    <div style={{ padding: '28px 16px 16px', background: C.bg, minHeight: '100%' }}>
      <p style={{ color: C.muted, fontSize: 13, marginBottom: 4 }}>one-time setup</p>
      <h1 style={{ fontSize: 26, fontWeight: 900, margin: '0 0 20px', background: C.grad, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
        Sound Profile ✨
      </h1>

      {fp && (
        <div style={{ background: 'rgba(199,125,255,0.08)', border: '1px solid rgba(199,125,255,0.25)', borderRadius: 20, padding: 18, marginBottom: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <span style={{ fontWeight: 700, fontSize: 15 }}>Your Profile</span>
            <button onClick={() => setFp(null)} style={{ background: 'none', border: '1px solid #1C1C2E', borderRadius: 10, color: C.muted, padding: '4px 10px', fontSize: 12, cursor: 'pointer' }}>Rebuild</button>
          </div>
          <p style={{ fontSize: 13, color: '#D4B8FF', lineHeight: 1.6, margin: '0 0 12px' }}>{fp.summary}</p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 10 }}>
            {Object.entries(fp.genres || {}).slice(0, 4).map(([g, p]) => (
              <span key={g} style={{ background: 'rgba(199,125,255,0.15)', color: C.purple, fontSize: 12, padding: '3px 10px', borderRadius: 20, fontWeight: 600 }}>
                {g} {Math.round(p * 100)}%
              </span>
            ))}
            {Object.entries(fp.emotional_tones || {}).slice(0, 2).map(([t, p]) => (
              <span key={t} style={{ background: 'rgba(255,133,194,0.15)', color: C.pink, fontSize: 12, padding: '3px 10px', borderRadius: 20, fontWeight: 600 }}>
                {t} {Math.round(p * 100)}%
              </span>
            ))}
          </div>
          {fp.preferred_arrangements?.length > 0 && (
            <p style={{ fontSize: 12, color: C.muted, margin: 0 }}>Best with <span style={{ color: '#D4B8FF' }}>{fp.preferred_arrangements.join(' · ')}</span></p>
          )}
        </div>
      )}

      {!fp && (
        <>
          <div style={{ background: 'rgba(199,125,255,0.07)', border: '1px solid rgba(199,125,255,0.2)', borderRadius: 16, padding: '12px 14px', marginBottom: 20, fontSize: 13, color: '#C4A8FF', lineHeight: 1.5 }}>
            Enter Summer’s best-performing TikTok covers. Claude will analyze them once and build her style fingerprint. You only need to do this once.
          </div>

          <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 20, padding: 16, marginBottom: 16 }}>
            {songs.map((s, i) => (
              <div key={i} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 24px', gap: 8, marginBottom: i < songs.length - 1 ? 10 : 0, alignItems: 'center' }}>
                <input style={inp} placeholder={`Song ${i + 1}`} value={s.song_name} onChange={e => update(i, 'song_name', e.target.value)} />
                <input style={inp} placeholder="Artist" value={s.artist} onChange={e => update(i, 'artist', e.target.value)} />
                {songs.length > 3
                  ? <button onClick={() => setSongs(s => s.filter((_, idx) => idx !== i))} style={{ background: 'none', border: 'none', color: C.muted, cursor: 'pointer', fontSize: 18, padding: 0 }}>×</button>
                  : <span />}
              </div>
            ))}
            <button onClick={() => setSongs(s => [...s, EMPTY()])} style={{ marginTop: 12, width: '100%', background: 'transparent', border: `1px solid ${C.border}`, borderRadius: 12, color: C.muted, padding: '9px', fontSize: 13, cursor: 'pointer' }}>+ Add song</button>
          </div>

          <button onClick={build} disabled={loading} style={{ width: '100%', background: loading ? '#1C1C2E' : C.grad, border: 'none', borderRadius: 14, color: loading ? C.muted : '#fff', padding: '14px', fontSize: 15, fontWeight: 700, cursor: loading ? 'default' : 'pointer' }}>
            {loading ? 'Analyzing with Claude… (~15s)' : 'Build My Profile ✨'}
          </button>
        </>
      )}

      {msg && (
        <div style={{ marginTop: 14, background: msg.ok ? 'rgba(79,255,196,0.08)' : 'rgba(255,100,100,0.08)', border: `1px solid ${msg.ok ? 'rgba(79,255,196,0.3)' : 'rgba(255,100,100,0.3)'}`, borderRadius: 14, padding: '12px 14px', fontSize: 13, color: msg.ok ? C.mint : '#FF9090', textAlign: 'center' }}>
          {msg.text}
        </div>
      )}
    </div>
  )
}
