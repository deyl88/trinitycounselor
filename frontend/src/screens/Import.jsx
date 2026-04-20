import { useState } from 'react'

const API = import.meta.env.DEV ? 'http://localhost:8000' : ''

const C = {
  bg: '#0A0A12', card: '#111119', border: '#1C1C2E',
  purple: '#C77DFF', pink: '#FF85C2', mint: '#4FFFC4',
  muted: '#6B6B8A', grad: 'linear-gradient(135deg, #C77DFF 0%, #FF85C2 100%)',
}

const EMPTY_ROW = () => ({ song_name: '', song_artist: '', views: '', likes: '', comments: '', shares: '', posted_at: '', is_cover: 1 })

const inp = { background: '#16161F', border: '1px solid #1C1C2E', borderRadius: 10, color: '#fff', padding: '8px 10px', width: '100%', fontSize: 13, boxSizing: 'border-box' }
const lbl = { fontSize: 11, color: '#6B6B8A', marginBottom: 3, display: 'block' }

export default function Import() {
  const [rows, setRows] = useState([EMPTY_ROW()])
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(false)

  const update = (i, field, val) => setRows(r => r.map((row, idx) => idx === i ? { ...row, [field]: val } : row))

  const submit = async () => {
    const valid = rows.filter(r => r.song_name.trim())
    if (!valid.length) return
    setLoading(true)
    setStatus(null)
    try {
      const res = await fetch(`${API}/api/import/manual`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          videos: valid.map(r => ({
            song_name: r.song_name.trim(),
            song_artist: r.song_artist.trim() || null,
            views: parseInt(r.views) || 0,
            likes: parseInt(r.likes) || 0,
            comments: parseInt(r.comments) || 0,
            shares: parseInt(r.shares) || 0,
            posted_at: r.posted_at || null,
            is_cover: r.is_cover,
            is_original: r.is_cover ? 0 : 1,
          })),
        }),
      }).then(r => r.json())
      setStatus({ ok: true, msg: `✨ Imported ${res.imported} videos` })
      setRows([EMPTY_ROW()])
    } catch (e) {
      setStatus({ ok: false, msg: `Error: ${e.message}` })
    }
    setLoading(false)
  }

  return (
    <div style={{ padding: '28px 16px 16px', background: C.bg, minHeight: '100%' }}>
      <div style={{ marginBottom: 20 }}>
        <p style={{ color: C.muted, fontSize: 13, marginBottom: 4 }}>add your videos</p>
        <h1 style={{ fontSize: 26, fontWeight: 900, margin: 0 }}>Import Videos 🎬</h1>
      </div>
      <div style={{ background: 'rgba(199,125,255,0.07)', border: '1px solid rgba(199,125,255,0.2)', borderRadius: 18, padding: '14px 16px', marginBottom: 20, fontSize: 13, color: '#C4A8FF', lineHeight: 1.5 }}>
        Enter your TikTok videos manually. Find stats in TikTok Studio → each post.
      </div>

      {rows.map((row, i) => (
        <div key={i} style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 20, padding: 16, marginBottom: 12 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <span style={{ fontSize: 13, fontWeight: 700, color: C.purple }}>Video {i + 1}</span>
            {rows.length > 1 && <button onClick={() => setRows(r => r.filter((_, idx) => idx !== i))} style={{ background: 'none', border: 'none', color: C.muted, cursor: 'pointer', fontSize: 20, padding: 0 }}>×</button>}
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 10 }}>
            <div><label style={lbl}>Song Name *</label><input style={inp} value={row.song_name} onChange={e => update(i, 'song_name', e.target.value)} placeholder="Flowers" /></div>
            <div><label style={lbl}>Artist</label><input style={inp} value={row.song_artist} onChange={e => update(i, 'song_artist', e.target.value)} placeholder="Miley Cyrus" /></div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 8, marginBottom: 10 }}>
            {['views', 'likes', 'comments', 'shares'].map(f => (
              <div key={f}><label style={lbl}>{f[0].toUpperCase() + f.slice(1)}</label><input style={inp} type="number" value={row[f]} onChange={e => update(i, f, e.target.value)} placeholder="0" /></div>
            ))}
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            <div><label style={lbl}>Posted Date</label><input style={{ ...inp, colorScheme: 'dark' }} type="date" value={row.posted_at} onChange={e => update(i, 'posted_at', e.target.value)} /></div>
            <div><label style={lbl}>Type</label>
              <select style={{ ...inp, cursor: 'pointer' }} value={row.is_cover} onChange={e => update(i, 'is_cover', parseInt(e.target.value))}>
                <option value={1}>Cover</option>
                <option value={0}>Original</option>
              </select>
            </div>
          </div>
        </div>
      ))}

      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        <button onClick={() => setRows(r => [...r, EMPTY_ROW()])} style={{ flex: 1, background: 'transparent', border: `1px solid ${C.border}`, borderRadius: 14, color: C.muted, padding: '11px', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}>+ Add video</button>
        <button onClick={submit} disabled={loading} style={{ flex: 2, background: loading ? '#1C1C2E' : C.grad, border: 'none', borderRadius: 14, color: loading ? C.muted : '#fff', padding: '11px', fontSize: 14, fontWeight: 700, cursor: loading ? 'default' : 'pointer' }}>
          {loading ? 'Importing…' : `Import ${rows.filter(r => r.song_name).length || ''} Videos ✨`}
        </button>
      </div>

      {status && (
        <div style={{ background: status.ok ? 'rgba(79,255,196,0.08)' : 'rgba(255,100,100,0.08)', border: `1px solid ${status.ok ? 'rgba(79,255,196,0.3)' : 'rgba(255,100,100,0.3)'}`, borderRadius: 16, padding: '14px 16px', fontSize: 13, color: status.ok ? C.mint : '#FF9090', textAlign: 'center' }}>
          {status.msg}
        </div>
      )}
    </div>
  )
}
