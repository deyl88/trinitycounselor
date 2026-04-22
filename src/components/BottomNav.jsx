import { NavLink } from 'react-router-dom'

const tabs = [
  { to: '/', label: 'For You', icon: '🎵' },
  { to: '/saved', label: 'Saved', icon: '🎀' },
  { to: '/setup', label: 'Profile', icon: '✨' },
]

export default function BottomNav() {
  return (
    <nav style={{
      position: 'fixed', bottom: 0, left: '50%', transform: 'translateX(-50%)',
      width: '100%', maxWidth: 430, backgroundColor: '#0E0E18',
      borderTop: '1px solid #1C1C2E', display: 'flex',
      justifyContent: 'space-around', paddingBottom: 'env(safe-area-inset-bottom)', zIndex: 100,
    }}>
      {tabs.map(({ to, label, icon }) => (
        <NavLink key={to} to={to} end={to === '/'} style={({ isActive }) => ({
          display: 'flex', flexDirection: 'column', alignItems: 'center',
          gap: 2, textDecoration: 'none', padding: '10px 28px',
          color: isActive ? '#C77DFF' : '#6B6B8A',
          fontSize: 11, fontWeight: isActive ? 700 : 400,
        })}>
          <span style={{ fontSize: 20 }}>{icon}</span>
          <span>{label}</span>
        </NavLink>
      ))}
    </nav>
  )
}
