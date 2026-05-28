import { Outlet, NavLink } from 'react-router-dom'
import { useAuth } from '../App'
import { logout as apiLogout } from '../api/client'

export default function Layout() {
  const { user, logout } = useAuth()

  const handleLogout = async () => {
    try { await apiLogout() } catch (_) {}
    logout()
  }

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col">
      {/* Top nav */}
      <nav className="bg-gray-900 border-b border-gray-800 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-8">
          <span className="text-green-400 font-mono font-semibold text-lg tracking-tight">
            breathe<span className="text-white">/esg</span>
          </span>
          <div className="flex gap-1">
            <NavLink
              to="/upload"
              className={({ isActive }) =>
                `px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                  isActive ? 'bg-gray-700 text-white' : 'text-gray-400 hover:text-white'
                }`
              }
            >
              Upload
            </NavLink>
            <NavLink
              to="/review"
              className={({ isActive }) =>
                `px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                  isActive ? 'bg-gray-700 text-white' : 'text-gray-400 hover:text-white'
                }`
              }
            >
              Review
            </NavLink>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-gray-500 text-xs font-mono">{user?.username}</span>
          <button
            onClick={handleLogout}
            className="text-xs text-gray-500 hover:text-red-400 transition-colors"
          >
            logout
          </button>
        </div>
      </nav>

      <main className="flex-1 p-6">
        <Outlet />
      </main>
    </div>
  )
}
