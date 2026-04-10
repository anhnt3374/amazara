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
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: '#fff',
    }}>
      <div style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', gap: '12px' }}>
        <p style={{ fontSize: '20px', color: '#333', fontWeight: 500 }}>Successfully</p>
        {user && (
          <div style={{ fontSize: '14px', color: '#666', lineHeight: '1.7' }}>
            <div><strong>Fullname:</strong> {user.fullname}</div>
            <div><strong>Username:</strong> {user.username}</div>
            <div><strong>Email:</strong> {user.email}</div>
          </div>
        )}
        <button
          onClick={handleLogout}
          style={{
            marginTop: '8px',
            padding: '10px 24px',
            background: '#111',
            color: '#fff',
            border: 'none',
            borderRadius: '50px',
            fontSize: '14px',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          Đăng xuất
        </button>
      </div>
    </div>
  )
}
