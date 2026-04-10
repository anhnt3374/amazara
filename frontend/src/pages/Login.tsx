import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import '../auth.css'
import { ArrowLeftIcon, ButterflyLogo, EyeIcon, EyeOffIcon, FacebookIcon, GoogleIcon } from '../components/Icons'
import { useAuth } from '../hooks/useAuth'
import { ApiError } from '../services/auth'

export default function Login() {
  const navigate = useNavigate()
  const { login } = useAuth()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [termsAccepted, setTermsAccepted] = useState(false)
  const [termsError, setTermsError] = useState(false)
  const [apiError, setApiError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setApiError('')

    if (!termsAccepted) {
      setTermsError(true)
      return
    }

    setLoading(true)
    try {
      await login(email, password)
      navigate('/success')
    } catch (err) {
      if (err instanceof ApiError && err.message === 'Invalid email or password') {
        setApiError('Email hoặc mật khẩu không đúng.')
      } else {
        setApiError('Đã có lỗi xảy ra. Vui lòng thử lại.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page auth-page--login">
      <div className="auth-card">
        {/* Left decorative panel */}
        <div className="auth-card__left auth-card__left--login">
          <ButterflyLogo className="auth-logo" />
          <div className="auth-glow" />
        </div>

        {/* Right form panel */}
        <div className="auth-card__right">
          <button className="auth-back" onClick={() => navigate(-1)} type="button">
            <ArrowLeftIcon />
          </button>

          <h1 className="auth-title">Log in</h1>
          <p className="auth-subtitle">
            Don&apos;t have an account?{' '}
            <Link to="/signup">Create an Account</Link>
          </p>

          <form className="auth-form" onSubmit={handleSubmit}>
            {apiError && <div className="global-error">{apiError}</div>}

            <div className="form-field">
              <label className="form-label" htmlFor="login-email">Email Address</label>
              <input
                id="login-email"
                className="form-input"
                type="email"
                placeholder="john52martinez@gmail.com"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
                autoComplete="email"
              />
            </div>

            <div className="form-field">
              <label className="form-label" htmlFor="login-password">Password</label>
              <div className="password-wrapper">
                <input
                  id="login-password"
                  className="form-input"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  className="eye-toggle"
                  onClick={() => setShowPassword(prev => !prev)}
                  aria-label={showPassword ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
                >
                  {showPassword ? <EyeOffIcon /> : <EyeIcon />}
                </button>
              </div>
            </div>

            <div className="forgot-row">
              <button type="button" className="forgot-link">Forgot Password?</button>
            </div>

            <button type="submit" className="submit-btn" disabled={loading}>
              {loading ? 'Đang đăng nhập...' : 'Log in'}
            </button>

            <div className="terms-row">
              <input
                id="login-terms"
                type="checkbox"
                className={`terms-checkbox${termsError ? ' terms-checkbox--error' : ''}`}
                checked={termsAccepted}
                onChange={e => {
                  setTermsAccepted(e.target.checked)
                  if (e.target.checked) setTermsError(false)
                }}
              />
              <label
                htmlFor="login-terms"
                className={`terms-label${termsError ? ' terms-label--error' : ''}`}
              >
                I agree to the <a href="#">Terms &amp; Condition</a>
              </label>
            </div>

            <div className="auth-divider">or</div>

            <div className="social-row">
              <button type="button" className="social-btn" disabled>
                <GoogleIcon />
                Continue with Google
              </button>
              <button type="button" className="social-btn" disabled>
                <FacebookIcon />
                Continue with Facebook
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
