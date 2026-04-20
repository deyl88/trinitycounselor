import { NavLink } from 'react-router-dom'

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: '📊' },
  { to: '/for-you',   label: 'For You',   icon: '🎵' },
  { to: '/trends',    label: 'Trends',    icon: '📈' },
  { to: '/import',    label: 'Import',    icon: '＋' },
]

const navStyle = {
  position: 'fixed',
  bottom: 0,
  left: '50%',
  transform: 'translateX(-50%)',
  width: '100%',
  maxWidth: '430px',
  backgroundColor: '#1A1A1A',
  borderTop: '1px solid #2A2A2A',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-around',
  paddingBottom: 'env(safe-area-inset-bottom)',
  zIndex: 100,
}

export default function BottomNav() {
  return (
    <nav style={navStyle}>
      {navItems.map(({ to, label, icon }) => (
        <NavLink
          key={to}
          to={to}
          style={({ isActive }) => ({
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '2px',
            textDecoration: 'none',
            color: isActive ? '#FF6B35' : '#888888',
            fontSize: '11px',
            fontWeight: isActive ? '600' : '400',
            padding: '10px 20px',
          })}
        >
          <span style={{ fontSize: '20px' }}>{icon}</span>
          <span>{label}</span>
        </NavLink>
      ))}
    </nav>
  )
}
