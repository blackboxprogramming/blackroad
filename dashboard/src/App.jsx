import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Navigation from './components/Navigation'
import Dashboard from './pages/Dashboard'
import Analytics from './pages/Analytics'
import Billing from './pages/Billing'
import Settings from './pages/Settings'
import './index.css'

export default function App() {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Get user from localStorage or query param
    const token = new URLSearchParams(window.location.search).get('token') || 
                  localStorage.getItem('token')
    if (token) {
      localStorage.setItem('token', token)
      setUser({ token, id: `user_${token.slice(0, 8)}` })
    }
    setLoading(false)
  }, [])

  if (loading) return <div className="flex items-center justify-center h-screen">Loading...</div>

  return (
    <BrowserRouter>
      <div className="flex h-screen bg-gray-50">
        <Navigation />
        <main className="flex-1 overflow-auto">
          <Routes>
            <Route path="/" element={<Dashboard user={user} />} />
            <Route path="/analytics" element={<Analytics user={user} />} />
            <Route path="/billing" element={<Billing user={user} />} />
            <Route path="/settings" element={<Settings user={user} />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
