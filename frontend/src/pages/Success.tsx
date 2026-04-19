import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export default function Success() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-fog">
      <div className="bg-white rounded-pin-lg border border-sand px-10 py-10 text-center flex flex-col gap-3 shadow-[0_12px_30px_rgba(33,25,34,0.08)]">
        <p className="text-xl text-plum font-semibold tracking-[-0.4px]">Successfully</p>
        {user && (
          <div className="text-sm text-olive leading-[1.7]">
            <div><strong className="text-plum">Fullname:</strong> {user.fullname}</div>
            <div><strong className="text-plum">Username:</strong> {user.username}</div>
            <div><strong className="text-plum">Email:</strong> {user.email}</div>
          </div>
        )}
        <button
          onClick={handleLogout}
          className="mt-2 px-6 h-11 bg-brand-red text-white rounded-pin text-sm font-semibold cursor-pointer hover:bg-[var(--color-brand-red-hover)] transition-colors focus:outline-none focus:ring-2 focus:ring-[color:var(--color-focus-blue)] focus:ring-offset-2"
        >
          Log out
        </button>
      </div>
    </div>
  )
}
