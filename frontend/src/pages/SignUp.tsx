import clsx from 'clsx'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ArrowLeftIcon, ButterflyLogo, EyeIcon, EyeOffIcon, FacebookIcon, GoogleIcon } from '../components/Icons'
import { useAuth } from '../hooks/useAuth'
import { ApiError, type RegisterPayload } from '../services/auth'

interface FieldErrors {
  email?: string
  username?: string
  password?: string
}

const inputBase =
  'h-[42px] border-[1.5px] rounded-lg px-3 text-sm text-[#111] outline-none transition-colors duration-[180ms] w-full bg-white placeholder:text-[#BBB]'

function validatePassword(password: string): string | null {
  if (password.length < 8) return 'Password is too weak (minimum 8 characters)'
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

    const pwdError = validatePassword(password)
    if (pwdError) { setFieldError('password', pwdError); return }
    if (!termsAccepted) { setTermsError(true); return }

    setLoading(true)
    try {
      const payload: RegisterPayload = { email, username, fullname, password }
      await register(payload)
      navigate('/success')
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.message === 'Email already registered') {
          setFieldError('email', 'This email is already in use.')
        } else if (err.message === 'Username already taken') {
          setFieldError('username', 'This username is already taken.')
        } else {
          setFieldError('email', 'Something went wrong. Please try again.')
        }
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      className="min-h-screen flex items-center justify-center p-6"
      style={{ background: 'radial-gradient(ellipse at 65% 50%, #0D1B3E 0%, #071025 55%, #020810 100%)' }}
    >
      <div className="flex w-full max-w-[860px] min-h-[510px] rounded-3xl overflow-hidden shadow-[0_30px_70px_rgba(0,0,0,0.55)]">

        {/* Left decorative panel */}
        <div
          className="w-[42%] shrink-0 relative flex items-start p-7 overflow-hidden"
          style={{ background: 'linear-gradient(150deg, #060F25 0%, #0C2050 45%, #0E3585 80%, #1550C0 100%)' }}
        >
          <ButterflyLogo className="w-[38px] h-[38px] relative z-10" />
          <div
            className="absolute rounded-full pointer-events-none"
            style={{
              width: 280, height: 280, bottom: '20%', left: '10%',
              background: 'radial-gradient(circle, rgba(50,160,255,0.3) 0%, transparent 70%)',
            }}
          />
        </div>

        {/* Right form panel */}
        <div className="flex-1 bg-white px-10 pt-9 pb-8 flex flex-col overflow-y-auto">
          <button
            type="button"
            className="p-0 mb-5 text-[#555] cursor-pointer flex items-center w-fit transition-colors hover:text-[#111] bg-transparent border-none"
            onClick={() => navigate(-1)}
          >
            <ArrowLeftIcon />
          </button>

          <h1 className="text-[34px] font-bold text-[#111] m-0 mb-1.5 leading-tight">Create an Account</h1>
          <p className="text-[13px] text-[#666] m-0 mb-[22px]">
            Already have an account?{' '}
            <Link to="/login" className="text-[#111] font-semibold underline">Log in</Link>
          </p>

          <form className="flex flex-col gap-[13px] flex-1" onSubmit={handleSubmit}>

            {/* Full Name */}
            <div className="flex flex-col gap-[5px]">
              <label className="text-[13px] font-medium text-[#333]" htmlFor="signup-fullname">
                Full Name
              </label>
              <input
                id="signup-fullname"
                className={clsx(inputBase, 'border-[#E0E0E0] focus:border-[#555]')}
                type="text"
                placeholder="John Doe"
                value={fullname}
                onChange={e => setFullname(e.target.value)}
                required
                autoComplete="name"
              />
            </div>

            {/* Username */}
            <div className="flex flex-col gap-[5px]">
              <label className="text-[13px] font-medium text-[#333]" htmlFor="signup-username">
                Username
              </label>
              <input
                id="signup-username"
                className={clsx(
                  inputBase,
                  fieldErrors.username ? 'border-red-500' : 'border-[#E0E0E0] focus:border-[#555]',
                )}
                type="text"
                placeholder="johndoe"
                value={username}
                onChange={e => { setUsername(e.target.value); clearFieldError('username') }}
                required
                autoComplete="username"
              />
              {fieldErrors.username && (
                <span className="text-[11.5px] text-red-500">{fieldErrors.username}</span>
              )}
            </div>

            {/* Email */}
            <div className="flex flex-col gap-[5px]">
              <label className="text-[13px] font-medium text-[#333]" htmlFor="signup-email">
                Email Address
              </label>
              <input
                id="signup-email"
                className={clsx(
                  inputBase,
                  fieldErrors.email ? 'border-red-500' : 'border-[#E0E0E0] focus:border-[#555]',
                )}
                type="email"
                placeholder="Email Address"
                value={email}
                onChange={e => { setEmail(e.target.value); clearFieldError('email') }}
                required
                autoComplete="email"
              />
              {fieldErrors.email && (
                <span className="text-[11.5px] text-red-500">{fieldErrors.email}</span>
              )}
            </div>

            {/* Password */}
            <div className="flex flex-col gap-[5px]">
              <label className="text-[13px] font-medium text-[#333]" htmlFor="signup-password">
                Password
              </label>
              <div className="relative">
                <input
                  id="signup-password"
                  className={clsx(
                    inputBase,
                    'pr-10',
                    fieldErrors.password ? 'border-red-500' : 'border-[#E0E0E0] focus:border-[#555]',
                  )}
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Password"
                  value={password}
                  onChange={e => { setPassword(e.target.value); clearFieldError('password') }}
                  required
                  autoComplete="new-password"
                />
                <button
                  type="button"
                  className="absolute right-[11px] top-1/2 -translate-y-1/2 bg-transparent border-none p-0 cursor-pointer text-[#999] flex items-center transition-colors hover:text-[#555]"
                  onClick={() => setShowPassword(prev => !prev)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOffIcon /> : <EyeIcon />}
                </button>
              </div>
              {fieldErrors.password && (
                <span className="text-[11.5px] text-red-500">{fieldErrors.password}</span>
              )}
            </div>

            {/* Submit */}
            <button
              type="submit"
              className="h-[46px] bg-[#111] text-white border-none rounded-full text-[15px] font-semibold cursor-pointer transition-colors mt-0.5 hover:bg-[#333] disabled:opacity-[0.65] disabled:cursor-not-allowed"
              disabled={loading}
            >
              {loading ? 'Creating account...' : 'Create Account'}
            </button>

            {/* Terms */}
            <div className="flex items-center gap-2">
              <input
                id="signup-terms"
                type="checkbox"
                className={clsx(
                  'w-[15px] h-[15px] cursor-pointer shrink-0',
                  termsError
                    ? 'accent-red-500 outline outline-2 outline-red-500 outline-offset-1 rounded-sm'
                    : 'accent-[#111]',
                )}
                checked={termsAccepted}
                onChange={e => {
                  setTermsAccepted(e.target.checked)
                  if (e.target.checked) setTermsError(false)
                }}
              />
              <label
                htmlFor="signup-terms"
                className={clsx('text-xs cursor-pointer leading-[1.4]', termsError ? 'text-red-500' : 'text-[#444]')}
              >
                I agree to the{' '}
                <a
                  href="#"
                  className={clsx('font-semibold underline', termsError ? 'text-red-500' : 'text-[#111]')}
                >
                  Terms &amp; Condition
                </a>
              </label>
            </div>

            {/* Divider */}
            <div className="flex items-center gap-2.5 text-xs text-[#AAA] before:content-[''] before:flex-1 before:h-px before:bg-[#E8E8E8] after:content-[''] after:flex-1 after:h-px after:bg-[#E8E8E8]">
              or
            </div>

            {/* Social buttons */}
            <div className="flex gap-2.5">
              <button
                type="button"
                className="flex-1 h-10 border-[1.5px] border-[#D0D0D0] rounded-lg bg-[#E8E8E8] text-[#888] flex items-center justify-center gap-[7px] text-xs font-medium opacity-[0.55] pointer-events-none cursor-not-allowed"
                disabled
              >
                <GoogleIcon />
                Continue with Google
              </button>
              <button
                type="button"
                className="flex-1 h-10 border-[1.5px] border-[#D0D0D0] rounded-lg bg-[#E8E8E8] text-[#888] flex items-center justify-center gap-[7px] text-xs font-medium opacity-[0.55] pointer-events-none cursor-not-allowed"
                disabled
              >
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
