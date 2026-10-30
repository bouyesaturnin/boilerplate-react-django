import { Link } from 'react-router-dom'
import { LogOut, LayoutDashboard } from 'lucide-react'
import { useAuth } from '../../features/auth/AuthContext'

export default function Navbar() {
  const { isAuthenticated, logout } = useAuth()

  return (
    <header className="border-b border-gray-200 bg-white">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
        <Link to="/" className="flex items-center gap-2 font-semibold text-gray-900">
          <LayoutDashboard size={20} />
          Boilerplate
        </Link>

        <nav className="flex items-center gap-4">
          {isAuthenticated ? (
            <>
              <Link to="/dashboard" className="text-sm text-gray-600 hover:text-gray-900">
                Tableau de bord
              </Link>
              <button
                onClick={logout}
                className="flex items-center gap-1.5 text-sm text-gray-600 hover:text-gray-900"
              >
                <LogOut size={16} />
                Déconnexion
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="text-sm text-gray-600 hover:text-gray-900">
                Connexion
              </Link>
              <Link
                to="/register"
                className="rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700"
              >
                S'inscrire
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  )
}
