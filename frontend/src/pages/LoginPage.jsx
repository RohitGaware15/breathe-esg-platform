import { useState } from 'react'
import { useAuth } from '../App'
import { login as apiLogin } from '../api/client'

export default function LoginPage() {
  const { login } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await apiLogin(username, password)
      login({ username: res.data.username, id: res.data.user_id }, res.data.token)
    } catch (err) {
      setError(err.response?.data?.error || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <div className="text-green-400 font-mono text-2xl font-semibold mb-1">
            breathe<span className="text-white">/esg</span>
          </div>
          <p className="text-gray-500 text-sm">Data Ingestion Platform</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-gray-900 border border-gray-800 rounded-lg p-6 space-y-4">
          {error && (
            <div className="bg-red-950 border border-red-800 rounded px-3 py-2 text-red-300 text-sm">
              {error}
            </div>
          )}
          <div>
            <label className="block text-xs text-gray-400 mb-1 font-mono">username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-green-500"
              required
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1 font-mono">password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-green-500"
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-green-600 hover:bg-green-500 disabled:opacity-50 text-white font-medium py-2 rounded text-sm transition-colors"
          >
            {loading ? 'signing in...' : 'sign in'}
          </button>
        </form>
      </div>
    </div>
  )
}
