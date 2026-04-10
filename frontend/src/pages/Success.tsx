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
    <div className="min-h-screen flex items-center justify-center bg-white">
      <div className="text-center flex flex-col gap-3">
        <p className="text-xl text-[#333] font-medium">Successfully</p>
        {user && (
          <div className="text-sm text-[#666] leading-[1.7]">
            <div><strong>Fullname:</strong> {user.fullname}</div>
            <div><strong>Username:</strong> {user.username}</div>
            <div><strong>Email:</strong> {user.email}</div>
          </div>
        )}
        <button
          onClick={handleLogout}
          className="mt-2 px-6 py-[10px] bg-[#111] text-white rounded-full text-sm font-semibold cursor-pointer hover:bg-[#333] transition-colors"
        >
          Log out
        </button>
      </div>
    </div>
  )
}
