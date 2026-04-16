import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import BottomNav from './components/BottomNav.jsx'
import Dashboard from './screens/Dashboard.jsx'
import ForYou from './screens/ForYou.jsx'
import Trends from './screens/Trends.jsx'

const styles = {
  app: {
    display: 'flex',
    flexDirection: 'column',
    height: '100dvh',
    backgroundColor: '#0F0F0F',
    color: '#FFFFFF',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    maxWidth: '430px',
    margin: '0 auto',
  },
  screen: {
    flex: 1,
    overflowY: 'auto',
    paddingBottom: '72px',
  },
}

export default function App() {
  return (
    <BrowserRouter>
      <div style={styles.app}>
        <div style={styles.screen}>
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/for-you" element={<ForYou />} />
            <Route path="/trends" element={<Trends />} />
          </Routes>
        </div>
        <BottomNav />
      </div>
    </BrowserRouter>
  )
}
