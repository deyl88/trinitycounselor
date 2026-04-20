import { useState, useEffect } from 'react'

const API = import.meta.env.DEV ? 'http://localhost:8000' : ''

const C = {
  bg: '#0A0A12', card: '#111119', border: '#1C1C2E',
  purple: '#C77DFF', pink: '#FF85C2', mint: '#4FFFC4',
  muted: '#6B6B8A', grad: 'linear-gradient(135deg, #C77DFF 0%, #FF85C2 100%)',
}

function ScoreBar({ value, color }) {
  return (
    <div style={{ background: '#1C1C2E', borderRadius: 6, height: 5, marginTop: 5, overflow: 'hidden' }}>
      <div style={{ width: `${Math.round(value * 100)}%`, height: '100%', borderRadius: 6, background: color }} />
    </div>
  )
}

function RecCard({ rec, onAct }) {
  const [acting, setActing] = useState(false)
  const act = async status => {
    setActing(true)
    await fetch(`${API}/api/recommendations/${rec.id}`, {
      method: 'PATCH', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status }),
    }).catch(() => {})
    onAct(rec.id)
  }
  return (
    <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 24, padding: 20, marginBottom: 14 }}>
      <div style={{ marginBottom: 14 }}>
        <div style={{ fontSize: 18, fontWeight: 800 }}>{rec.song_name}</div>
        <div style={{ color: C.muted, fontSize: 13, marginTop: 3 }}>{rec.song_artist}</div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 12 }}>
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ fontSize: 11, color: C.muted }}>Style Fit</span>
            <span style={{ fontSize: 15, fontWeight: 800, color: C.purple }}>{Math.round(rec.style_fit_score * 100)}%</span>
          </div>
          <ScoreBar value={rec.style_fit_score} color={C.purple} />
        </div>
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ fontSize: 11, color: C.muted }}>Trending</span>
            <span style={{ fontSize: 15, fontWeight: 800, color: C.pink }}>{Math.round(rec.trending_score * 100)}%</span>
          </div>
          <ScoreBar value={rec.trending_score} color={C.pink} />
        </div>
      </div>
      <div style={{ marginBottom: 14 }}>
        <span style={{ background: C.grad, color: '#fff', fontSize: 12, fontWeight: 700, padding: '4px 12px', borderRadius: 20 }}>
          {Math.round(rec.final_score * 100)}% match ✨
        </span>
      </div>
      {rec.tip_text && (
        <div style={{ background: 'rgba(199,125,255,0.08)', borderLeft: `3px solid ${C.purple}`, borderRadius: '0 12px 12px 0', padding: '10px 14px', marginBottom: 16, fontSize: 13, color: '#D4B8FF', lineHeight: 1.6 }}>
          {rec.tip_text}
        </div>
      )}
      <div style={{ display: 'flex', gap: 8 }}>
        <button onClick={() => act('skipped')} disabled={acting} style={{ flex: 1, background: 'transparent', border: `1px solid ${C.border}`, borderRadius: 14, color: C.muted, padding: '11px', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}>Not for me</button>
        <button onClick={() => act('saved')} disabled={acting} style={{ flex: 2, background: C.grad, border: 'none', borderRadius: 14, color: '#fff', padding: '11px', fontSize: 14, fontWeight: 700, cursor: 'pointer' }}>Save this one 🩷</button>
      </div>
    </div>
  )
}

export default function ForYou() {
  const [recs, setRecs] = useState([])
  const [saved, setSaved] = useState([])
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState('pending')

  const load = () => {
    Promise.all([
      fetch(`${API}/api/recommendations/?status=pending`).then(r => r.json()).catch(() => []),
      fetch(`${API}/api/recommendations/?status=saved`).then(r => r.json()).catch(() => []),
    ]).then(([pending, savedList]) => {
      setRecs(Array.isArray(pending) ? pending : [])
      setSaved(Array.isArray(savedList) ? savedList : [])
    }).finally(() => setLoading(false))
  }

  useEffect(load, [])

  const dismiss = id => {
    setRecs(r => r.filter(x => x.id !== id))
    setSaved(s => s.filter(x => x.id !== id))
    setTimeout(load, 600)
  }

  const tabStyle = active => ({ flex: 1, padding: '9px', fontSize: 13, fontWeight: active ? 700 : 500, background: active ? C.grad : 'transparent', border: active ? 'none' : `1px solid ${C.border}`, borderRadius: 12, color: active ? '#fff' : C.muted, cursor: 'pointer' })
  const display = tab === 'pending' ? recs : saved

  return (
    <div style={{ padding: '28px 16px 16px', background: C.bg, minHeight: '100%' }}>
      <div style={{ marginBottom: 20 }}>
        <p style={{ color: C.muted, fontSize: 13, marginBottom: 4 }}>matched to your style</p>
        <h1 style={{ fontSize: 26, fontWeight: 900, margin: 0 }}>For You 🎵</h1>
      </div>
      <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
        <button style={tabStyle(tab === 'pending')} onClick={() => setTab('pending')}>New {recs.length > 0 ? `(${recs.length})` : ''}</button>
        <button style={tabStyle(tab === 'saved')} onClick={() => setTab('saved')}>Saved {saved.length > 0 ? `(${saved.length})` : ''}</button>
      </div>
      {loading && <div style={{ textAlign: 'center', color: C.muted, padding: 48 }}>Loading...</div>}
      {!loading && display.length === 0 && (
        <div style={{ textAlign: 'center', padding: '48px 20px', color: C.muted }}>
          <div style={{ fontSize: 52, marginBottom: 16 }}>{tab === 'pending' ? '✨' : '🎀'}</div>
          <p style={{ fontSize: 15, fontWeight: 700, color: '#fff', marginBottom: 8 }}>{tab === 'pending' ? 'All caught up!' : 'Nothing saved yet'}</p>
          <p style={{ fontSize: 13 }}>{tab === 'pending' ? 'Add trending songs in the Trends tab to get recs.' : 'Save songs you want to cover from New.'}</p>
        </div>
      )}
      {display.map(rec => <RecCard key={rec.id} rec={rec} onAct={dismiss} />)}
    </div>
  )
}
