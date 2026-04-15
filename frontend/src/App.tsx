import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { useAuth } from './hooks/useAuth'
import Layout from './components/Layout'
import Login from './pages/Login'
import SignUp from './pages/SignUp'
import Success from './pages/Success'
import Home from './pages/Home'
import Favorites from './pages/Favorites'
import Cart from './pages/Cart'
import ProductList from './pages/ProductList'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return null
  if (!user) return <Navigate to="/login" replace />
  return <>{children}</>
}

function GuestRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return null
  if (user) return <Navigate to="/" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Pages with Header via Layout */}
          <Route path="/" element={<Layout><Home /></Layout>} />
          <Route path="/list" element={<Layout><ProductList /></Layout>} />
          <Route path="/success" element={<Layout><ProtectedRoute><Success /></ProtectedRoute></Layout>} />
          <Route path="/favorites" element={<Layout><ProtectedRoute><Favorites /></ProtectedRoute></Layout>} />
          <Route path="/cart" element={<Layout><ProtectedRoute><Cart /></ProtectedRoute></Layout>} />

          {/* Auth pages — full-page design, no Layout */}
          <Route path="/login" element={<GuestRoute><Login /></GuestRoute>} />
          <Route path="/signup" element={<GuestRoute><SignUp /></GuestRoute>} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
