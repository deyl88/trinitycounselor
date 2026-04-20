import { useState } from 'react'

const API = window.API_URL || 'http://localhost:8000'

const EMPTY_ROW = () => ({
  song_name: '', song_artist: '', views: '', likes: '',
  comments: '', shares: '', posted_at: '', is_cover: 1,
})

const label = { fontSize: 11, color: '#888', marginBottom: 2, display: 'block' }
const input = {
  background: '#1A1A1A', border: '1px solid #333', borderRadius: 6,
  color: '#fff', padding: '6px 8px', width: '100%', fontSize: 13, boxSizing: 'border-box',
}
const btn = (color = '#FF6B35') => ({
  background: color, border: 'none', borderRadius: 8, color: '#fff',
  padding: '10px 18px', fontSize: 14, fontWeight: 600, cursor: 'pointer',
})

export default function Import() {
  const [rows, setRows] = useState([EMPTY_ROW()])
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(false)

  const update = (i, field, val) =>
    setRows(r => r.map((row, idx) => idx === i ? { ...row, [field]: val } : row))

  const addRow = () => setRows(r => [...r, EMPTY_ROW()])
  const removeRow = i => setRows(r => r.filter((_, idx) => idx !== i))

  const submit = async () => {
    const valid = rows.filter(r => r.song_name.trim())
    if (!valid.length) return
    setLoading(true)
    setStatus(null)
    try {
      const videos = valid.map(r => ({
        song_name: r.song_name.trim(),
        song_artist: r.song_artist.trim() || null,
        views: parseInt(r.views) || 0,
        likes: parseInt(r.likes) || 0,
        comments: parseInt(r.comments) || 0,
        shares: parseInt(r.shares) || 0,
        posted_at: r.posted_at || null,
        is_cover: r.is_cover,
        is_original: r.is_cover ? 0 : 1,
      }))
      const res = await fetch(`${API}/api/import/manual`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ videos }),
      }).then(r => r.json())
      setStatus(`✓ Imported ${res.imported} videos`)
      setRows([EMPTY_ROW()])
    } catch (e) {
      setStatus(`Error: ${e.message}`)
    }
    setLoading(false)
  }

  return (
    <div style={{ padding: '20px 16px' }}>
      <h1 style={{ fontSize: 22, marginBottom: 4 }}>Import Videos</h1>
      <p style={{ color: '#888', fontSize: 13, marginBottom: 20 }}>
        Enter Summer's videos from TikTok Studio. Stats are visible on each post.
      </p>

      {rows.map((row, i) => (
        <div key={i} style={{ background: '#1A1A1A', borderRadius: 10, padding: 14, marginBottom: 12, border: '1px solid #2A2A2A' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
            <span style={{ fontSize: 13, fontWeight: 600, color: '#FF6B35' }}>Video {i + 1}</span>
            {rows.length > 1 && (
              <button onClick={() => removeRow(i)} style={{ background: 'none', border: 'none', color: '#555', cursor: 'pointer', fontSize: 18 }}>×</button>
            )}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 10 }}>
            <div>
              <label style={label}>Song Name *</label>
              <input style={input} value={row.song_name} onChange={e => update(i, 'song_name', e.target.value)} placeholder="e.g. Flowers" />
            </div>
            <div>
              <label style={label}>Artist</label>
              <input style={input} value={row.song_artist} onChange={e => update(i, 'song_artist', e.target.value)} placeholder="e.g. Miley Cyrus" />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 8, marginBottom: 10 }}>
            {['views', 'likes', 'comments', 'shares'].map(f => (
              <div key={f}>
                <label style={label}>{f.charAt(0).toUpperCase() + f.slice(1)}</label>
                <input style={input} type="number" value={row[f]} onChange={e => update(i, f, e.target.value)} placeholder="0" />
              </div>
            ))}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            <div>
              <label style={label}>Posted Date</label>
              <input style={input} type="date" value={row.posted_at} onChange={e => update(i, 'posted_at', e.target.value)} />
            </div>
            <div>
              <label style={label}>Type</label>
              <select style={{ ...input, cursor: 'pointer' }} value={row.is_cover} onChange={e => update(i, 'is_cover', parseInt(e.target.value))}>
                <option value={1}>Cover</option>
                <option value={0}>Original</option>
              </select>
            </div>
          </div>
        </div>
      ))}

      <div style={{ display: 'flex', gap: 10, marginBottom: 16 }}>
        <button onClick={addRow} style={{ ...btn('#2A2A2A'), flex: 1 }}>+ Add another video</button>
        <button onClick={submit} disabled={loading} style={{ ...btn(), flex: 2, opacity: loading ? 0.6 : 1 }}>
          {loading ? 'Importing…' : `Import ${rows.filter(r => r.song_name).length || ''} Videos`}
        </button>
      </div>

      {status && (
        <div style={{ background: status.startsWith('✓') ? '#1A3A1A' : '#3A1A1A', borderRadius: 8, padding: 12, fontSize: 14, color: status.startsWith('✓') ? '#4CAF50' : '#f44336' }}>
          {status}
        </div>
      )}
    </div>
  )
}
