import { useState, useEffect, createContext, useContext } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import LoginPage from './pages/LoginPage'
import UploadPage from './pages/UploadPage'
import ReviewPage from './pages/ReviewPage'
import Layout from './components/Layout'
import { getMe } from './api/client'

const AuthContext = createContext(null)
export const useAuth = () => useContext(AuthContext)

export default function App() {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('auth_token')
    if (token) {
      getMe()
        .then((res) => setUser(res.data))
        .catch(() => localStorage.removeItem('auth_token'))
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const login = (userData, token) => {
    localStorage.setItem('auth_token', token)
    setUser(userData)
  }

  const logout = () => {
    localStorage.removeItem('auth_token')
    setUser(null)
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-green-400 font-mono text-sm animate-pulse">initializing...</div>
      </div>
    )
  }

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={!user ? <LoginPage /> : <Navigate to="/" />} />
          <Route element={user ? <Layout /> : <Navigate to="/login" />}>
            <Route path="/" element={<Navigate to="/upload" />} />
            <Route path="/upload" element={<UploadPage />} />
            <Route path="/review" element={<ReviewPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthContext.Provider>
  )
}
