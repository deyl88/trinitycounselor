import { BrowserRouter, Routes, Route } from 'react-router-dom'
import BottomNav from './components/BottomNav.jsx'
import ForYou from './screens/ForYou.jsx'
import Saved from './screens/Saved.jsx'
import Setup from './screens/Setup.jsx'

export default function App() {
  return (
    <BrowserRouter>
      <div style={{
        display: 'flex', flexDirection: 'column', height: '100dvh',
        backgroundColor: '#0A0A12', color: '#fff',
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
        maxWidth: 430, margin: '0 auto',
      }}>
        <div style={{ flex: 1, overflowY: 'auto', paddingBottom: 72 }}>
          <Routes>
            <Route path="/" element={<ForYou />} />
            <Route path="/saved" element={<Saved />} />
            <Route path="/setup" element={<Setup />} />
          </Routes>
        </div>
        <BottomNav />
      </div>
    </BrowserRouter>
  )
}
