import { useState } from 'react'

const API = window.API_URL || 'http://localhost:8000'

const C = {
  bg: '#0A0A12',
  card: '#111119',
  border: '#1C1C2E',
  purple: '#C77DFF',
  pink: '#FF85C2',
  mint: '#4FFFC4',
  muted: '#6B6B8A',
  grad: 'linear-gradient(135deg, #C77DFF 0%, #FF85C2 100%)',
}

const EMPTY = () => ({ song_name: '', artist: '', trending_score: '0.8' })

const HOT_LABELS = { '1.0': '🔥🔥🔥', '0.9': '🔥🔥', '0.8': '🔥', '0.7': '📈', '0.6': '📈', '0.5': '~' }

const input = {
  background: '#16161F', border: '1px solid #1C1C2E',
  borderRadius: 12, color: '#fff', padding: '9px 12px',
  fontSize: 13, width: '100%', boxSizing: 'border-box',
}

export default function Trends() {
  const [songs, setSongs] = useState([EMPTY()])
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(false)

  const update = (i, f, v) =>
    setSongs(s => s.map((row, idx) => idx === i ? { ...row, [f]: v } : row))

  const generate = async () => {
    const valid = songs.filter(s => s.song_name.trim())
    if (!valid.length) return
    setLoading(true)
    setStatus(null)
    try {
      const res = await fetch(`${API}/api/recommendations/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          songs: valid.map(s => ({
            song_name: s.song_name.trim(),
            artist: s.artist.trim() || 'Unknown',
            trending_score: parseFloat(s.trending_score) || 0.5,
          })),
          trending_weight: 0.3,
        }),
      }).then(r => r.json())
      setStatus({ ok: true, msg: `Scoring ${res.song_count} song${res.song_count !== 1 ? 's' : ''} — check For You in ~30s ✨` })
      setSongs([EMPTY()])
    } catch (e) {
      setStatus({ ok: false, msg: `Something went wrong: ${e.message}` })
    }
    setLoading(false)
  }

  const validCount = songs.filter(s => s.song_name.trim()).length

  return (
    <div style={{ padding: '28px 16px 16px', background: C.bg, minHeight: '100%' }}>
      <div style={{ marginBottom: 20 }}>
        <p style={{ color: C.muted, fontSize: 13, marginBottom: 4 }}>score it against your sound</p>
        <h1 style={{ fontSize: 26, fontWeight: 900, margin: 0 }}>Trending Songs 📈</h1>
      </div>

      <div style={{
        background: 'rgba(199,125,255,0.07)', border: '1px solid rgba(199,125,255,0.2)',
        borderRadius: 18, padding: '14px 16px', marginBottom: 20,
        fontSize: 13, color: '#C4A8FF', lineHeight: 1.5,
      }}>
        Enter songs blowing up right now — TikTok FYP, Spotify charts, whatever’s living rent-free in your head.
        I’ll score each one against your proven style and write a tip for the best fits.
      </div>

      <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 24, padding: 18, marginBottom: 16 }}>
        {songs.map((song, i) => (
          <div key={i} style={{
            paddingBottom: i < songs.length - 1 ? 16 : 0,
            marginBottom: i < songs.length - 1 ? 16 : 0,
            borderBottom: i < songs.length - 1 ? `1px solid ${C.border}` : 'none',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
              <span style={{ fontSize: 12, fontWeight: 700, color: C.purple }}>Song {i + 1}</span>
              {songs.length > 1 && (
                <button
                  onClick={() => setSongs(s => s.filter((_, idx) => idx !== i))}
                  style={{ background: 'none', border: 'none', color: C.muted, cursor: 'pointer', fontSize: 20, padding: 0 }}
                >×</button>
              )}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 10 }}>
              <div>
                <div style={{ fontSize: 11, color: C.muted, marginBottom: 4 }}>Song name *</div>
                <input style={input} value={song.song_name} onChange={e => update(i, 'song_name', e.target.value)} placeholder="Espresso" />
              </div>
              <div>
                <div style={{ fontSize: 11, color: C.muted, marginBottom: 4 }}>Artist</div>
                <input style={input} value={song.artist} onChange={e => update(i, 'artist', e.target.value)} placeholder="Sabrina Carpenter" />
              </div>
            </div>

            <div>
              <div style={{ fontSize: 11, color: C.muted, marginBottom: 6 }}>
                How hot is it? <span style={{ color: C.pink }}>{HOT_LABELS[song.trending_score] || ''}</span>
              </div>
              <div style={{ display: 'flex', gap: 6 }}>
                {['0.5', '0.6', '0.7', '0.8', '0.9', '1.0'].map(val => (
                  <button
                    key={val}
                    onClick={() => update(i, 'trending_score', val)}
                    style={{
                      flex: 1, padding: '8px 0', fontSize: 12, fontWeight: 600,
                      borderRadius: 10, cursor: 'pointer',
                      background: song.trending_score === val ? C.grad : '#1C1C2E',
                      border: 'none',
                      color: song.trending_score === val ? '#fff' : C.muted,
                    }}
                  >
                    {val}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ))}

        <div style={{ display: 'flex', gap: 8, marginTop: 18 }}>
          <button
            onClick={() => setSongs(s => [...s, EMPTY()])}
            style={{
              flex: 1, background: 'transparent', border: `1px solid ${C.border}`,
              borderRadius: 14, color: C.muted, padding: '11px', fontSize: 13,
              fontWeight: 600, cursor: 'pointer',
            }}
          >
            + Add song
          </button>
          <button
            onClick={generate}
            disabled={loading || validCount === 0}
            style={{
              flex: 2,
              background: loading || validCount === 0 ? '#1C1C2E' : C.grad,
              border: 'none', borderRadius: 14,
              color: loading || validCount === 0 ? C.muted : '#fff',
              padding: '11px', fontSize: 14, fontWeight: 700,
              cursor: loading || validCount === 0 ? 'default' : 'pointer',
            }}
          >
            {loading ? 'Starting…' : `Analyze ${validCount || ''} Song${validCount !== 1 ? 's' : ''} ✨`}
          </button>
        </div>
      </div>

      {status && (
        <div style={{
          background: status.ok ? 'rgba(79,255,196,0.08)' : 'rgba(255,100,100,0.08)',
          border: `1px solid ${status.ok ? 'rgba(79,255,196,0.3)' : 'rgba(255,100,100,0.3)'}`,
          borderRadius: 16, padding: '14px 16px',
          fontSize: 13, color: status.ok ? C.mint : '#FF9090',
          textAlign: 'center', lineHeight: 1.5,
        }}>
          {status.msg}
        </div>
      )}
    </div>
  )
}
