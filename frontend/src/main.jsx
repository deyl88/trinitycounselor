import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'

window.API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
