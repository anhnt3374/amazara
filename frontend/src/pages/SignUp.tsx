import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import '../auth.css'
import { ArrowLeftIcon, ButterflyLogo, EyeIcon, EyeOffIcon, FacebookIcon, GoogleIcon } from '../components/Icons'
import { useAuth } from '../hooks/useAuth'
import { ApiError } from '../services/auth'

interface FieldErrors {
  email?: string
  username?: string
  password?: string
}

function validatePassword(password: string): string | null {
  if (password.length < 8) return 'Mật khẩu quá yếu (tối thiểu 8 ký tự)'
  return null
}

export default function SignUp() {
  const navigate = useNavigate()
  const { register } = useAuth()

  const [fullname, setFullname] = useState('')
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [termsAccepted, setTermsAccepted] = useState(false)
  const [termsError, setTermsError] = useState(false)
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({})
  const [loading, setLoading] = useState(false)

  const setFieldError = (field: keyof FieldErrors, msg: string) =>
    setFieldErrors(prev => ({ ...prev, [field]: msg }))

  const clearFieldError = (field: keyof FieldErrors) =>
    setFieldErrors(prev => ({ ...prev, [field]: undefined }))

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setFieldErrors({})

    // Client-side validation
    const pwdError = validatePassword(password)
    if (pwdError) {
      setFieldError('password', pwdError)
      return
    }

    if (!termsAccepted) {
      setTermsError(true)
      return
    }

    setLoading(true)
    try {
      await register({ email, username, fullname, password })
      navigate('/success')
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.message === 'Email already registered') {
          setFieldError('email', 'Email này đã được sử dụng')
        } else if (err.message === 'Username already taken') {
          setFieldError('username', 'Username này đã được sử dụng')
        } else {
          setFieldError('email', 'Đã có lỗi xảy ra. Vui lòng thử lại.')
        }
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page auth-page--signup">
      <div className="auth-card">
        {/* Left decorative panel */}
        <div className="auth-card__left auth-card__left--signup">
          <ButterflyLogo className="auth-logo" />
          <div className="auth-glow" />
        </div>

        {/* Right form panel */}
        <div className="auth-card__right">
          <button className="auth-back" onClick={() => navigate(-1)} type="button">
            <ArrowLeftIcon />
          </button>

          <h1 className="auth-title">Create an Account</h1>
          <p className="auth-subtitle">
            Already have an account? <Link to="/login">Log in</Link>
          </p>

          <form className="auth-form" onSubmit={handleSubmit}>
            <div className="form-field">
              <label className="form-label" htmlFor="signup-fullname">Full Name</label>
              <input
                id="signup-fullname"
                className="form-input"
                type="text"
                placeholder="John Doe"
                value={fullname}
                onChange={e => setFullname(e.target.value)}
                required
                autoComplete="name"
              />
            </div>

            <div className="form-field">
              <label className="form-label" htmlFor="signup-username">Username</label>
              <input
                id="signup-username"
                className={`form-input${fieldErrors.username ? ' form-input--error' : ''}`}
                type="text"
                placeholder="johndoe"
                value={username}
                onChange={e => {
                  setUsername(e.target.value)
                  clearFieldError('username')
                }}
                required
                autoComplete="username"
              />
              {fieldErrors.username && (
                <span className="field-error">{fieldErrors.username}</span>
              )}
            </div>

            <div className="form-field">
              <label className="form-label" htmlFor="signup-email">Email Address</label>
              <input
                id="signup-email"
                className={`form-input${fieldErrors.email ? ' form-input--error' : ''}`}
                type="email"
                placeholder="Email Address"
                value={email}
                onChange={e => {
                  setEmail(e.target.value)
                  clearFieldError('email')
                }}
                required
                autoComplete="email"
              />
              {fieldErrors.email && (
                <span className="field-error">{fieldErrors.email}</span>
              )}
            </div>

            <div className="form-field">
              <label className="form-label" htmlFor="signup-password">Password</label>
              <div className="password-wrapper">
                <input
                  id="signup-password"
                  className={`form-input${fieldErrors.password ? ' form-input--error' : ''}`}
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Password"
                  value={password}
                  onChange={e => {
                    setPassword(e.target.value)
                    clearFieldError('password')
                  }}
                  required
                  autoComplete="new-password"
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
              {fieldErrors.password && (
                <span className="field-error">{fieldErrors.password}</span>
              )}
            </div>

            <button type="submit" className="submit-btn" disabled={loading}>
              {loading ? 'Đang tạo tài khoản...' : 'Create Account'}
            </button>

            <div className="terms-row">
              <input
                id="signup-terms"
                type="checkbox"
                className={`terms-checkbox${termsError ? ' terms-checkbox--error' : ''}`}
                checked={termsAccepted}
                onChange={e => {
                  setTermsAccepted(e.target.checked)
                  if (e.target.checked) setTermsError(false)
                }}
              />
              <label
                htmlFor="signup-terms"
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
