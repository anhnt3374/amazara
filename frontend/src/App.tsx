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
import Orders from './pages/Orders'
import StoreProducts from './pages/StoreProducts'
import ProductList from './pages/ProductList'
import ProductDetail from './pages/ProductDetail'

interface ProtectedRouteProps {
  children: React.ReactNode
  requiredType?: 'user' | 'store'
}

function ProtectedRoute({ children, requiredType }: ProtectedRouteProps) {
  const { account, loading } = useAuth()
  if (loading) return null
  if (!account) return <Navigate to="/login" replace />
  if (requiredType && account.type !== requiredType) {
    const fallback = account.type === 'store' ? '/store/products' : '/'
    return <Navigate to={fallback} replace />
  }
  return <>{children}</>
}

function GuestRoute({ children }: { children: React.ReactNode }) {
  const { account, loading } = useAuth()
  if (loading) return null
  if (account) {
    const home = account.type === 'store' ? '/store/products' : '/'
    return <Navigate to={home} replace />
  }
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
          <Route path="/product/:productId" element={<Layout><ProductDetail /></Layout>} />
          <Route
            path="/success"
            element={
              <Layout>
                <ProtectedRoute>
                  <Success />
                </ProtectedRoute>
              </Layout>
            }
          />
          <Route
            path="/favorites"
            element={
              <Layout>
                <ProtectedRoute requiredType="user">
                  <Favorites />
                </ProtectedRoute>
              </Layout>
            }
          />
          <Route
            path="/cart"
            element={
              <Layout>
                <ProtectedRoute requiredType="user">
                  <Cart />
                </ProtectedRoute>
              </Layout>
            }
          />
          <Route
            path="/orders"
            element={
              <Layout>
                <ProtectedRoute requiredType="user">
                  <Orders />
                </ProtectedRoute>
              </Layout>
            }
          />
          <Route
            path="/store/products"
            element={
              <Layout>
                <ProtectedRoute requiredType="store">
                  <StoreProducts />
                </ProtectedRoute>
              </Layout>
            }
          />

          {/* Auth pages — full-page design, no Layout */}
          <Route path="/login" element={<GuestRoute><Login /></GuestRoute>} />
          <Route path="/signup" element={<GuestRoute><SignUp /></GuestRoute>} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
