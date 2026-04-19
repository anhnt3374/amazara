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
  'h-[44px] border border-warm-silver rounded-pin px-[15px] text-sm text-plum outline-none transition-colors w-full bg-white placeholder:text-warm-silver focus:border-[color:var(--color-focus-blue)] focus:ring-2 focus:ring-[color:var(--color-focus-blue)]/30'

const inputError = 'border-[color:var(--color-error-red)] focus:border-[color:var(--color-error-red)] focus:ring-[color:var(--color-error-red)]/30'

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
    <div className="min-h-screen flex items-center justify-center p-6 bg-fog">
      <div className="flex w-full max-w-[860px] min-h-[510px] rounded-pin-2xl overflow-hidden shadow-[0_20px_50px_rgba(33,25,34,0.18)] bg-white">

        {/* Left decorative panel */}
        <div
          className="w-[42%] shrink-0 relative flex items-start p-7 overflow-hidden"
          style={{ background: 'linear-gradient(150deg, #33332e 0%, #62625b 50%, #e60023 100%)' }}
        >
          <ButterflyLogo className="w-[38px] h-[38px] relative z-10" />
          <div
            className="absolute rounded-full pointer-events-none"
            style={{
              width: 280, height: 280, bottom: '20%', left: '10%',
              background: 'radial-gradient(circle, rgba(255,255,255,0.18) 0%, transparent 70%)',
            }}
          />
        </div>

        {/* Right form panel */}
        <div className="flex-1 bg-white px-10 pt-9 pb-8 flex flex-col overflow-y-auto">
          <button
            type="button"
            className="p-0 mb-5 text-olive cursor-pointer flex items-center w-fit transition-colors hover:text-plum bg-transparent border-none"
            onClick={() => navigate(-1)}
          >
            <ArrowLeftIcon />
          </button>

          <h1 className="text-[34px] font-bold text-plum tracking-[-1px] m-0 mb-1.5 leading-tight">Create an Account</h1>
          <p className="text-[13px] text-olive m-0 mb-[22px]">
            Already have an account?{' '}
            <Link to="/login" className="text-brand-red font-semibold underline">Log in</Link>
          </p>

          <form className="flex flex-col gap-[13px] flex-1" onSubmit={handleSubmit}>

            {/* Full Name */}
            <div className="flex flex-col gap-[5px]">
              <label className="text-[13px] font-medium text-plum" htmlFor="signup-fullname">
                Full Name
              </label>
              <input
                id="signup-fullname"
                className={inputBase}
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
              <label className="text-[13px] font-medium text-plum" htmlFor="signup-username">
                Username
              </label>
              <input
                id="signup-username"
                className={clsx(inputBase, fieldErrors.username && inputError)}
                type="text"
                placeholder="johndoe"
                value={username}
                onChange={e => { setUsername(e.target.value); clearFieldError('username') }}
                required
                autoComplete="username"
              />
              {fieldErrors.username && (
                <span className="text-[11.5px] text-[color:var(--color-error-red)]">{fieldErrors.username}</span>
              )}
            </div>

            {/* Email */}
            <div className="flex flex-col gap-[5px]">
              <label className="text-[13px] font-medium text-plum" htmlFor="signup-email">
                Email Address
              </label>
              <input
                id="signup-email"
                className={clsx(inputBase, fieldErrors.email && inputError)}
                type="email"
                placeholder="Email Address"
                value={email}
                onChange={e => { setEmail(e.target.value); clearFieldError('email') }}
                required
                autoComplete="email"
              />
              {fieldErrors.email && (
                <span className="text-[11.5px] text-[color:var(--color-error-red)]">{fieldErrors.email}</span>
              )}
            </div>

            {/* Password */}
            <div className="flex flex-col gap-[5px]">
              <label className="text-[13px] font-medium text-plum" htmlFor="signup-password">
                Password
              </label>
              <div className="relative">
                <input
                  id="signup-password"
                  className={clsx(inputBase, 'pr-10', fieldErrors.password && inputError)}
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Password"
                  value={password}
                  onChange={e => { setPassword(e.target.value); clearFieldError('password') }}
                  required
                  autoComplete="new-password"
                />
                <button
                  type="button"
                  className="absolute right-[11px] top-1/2 -translate-y-1/2 bg-transparent border-none p-0 cursor-pointer text-warm-silver flex items-center transition-colors hover:text-plum"
                  onClick={() => setShowPassword(prev => !prev)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOffIcon /> : <EyeIcon />}
                </button>
              </div>
              {fieldErrors.password && (
                <span className="text-[11.5px] text-[color:var(--color-error-red)]">{fieldErrors.password}</span>
              )}
            </div>

            {/* Submit */}
            <button
              type="submit"
              className="h-[46px] bg-brand-red text-white border-none rounded-pin text-[15px] font-semibold cursor-pointer transition-colors mt-0.5 hover:bg-[var(--color-brand-red-hover)] disabled:opacity-[0.65] disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-[color:var(--color-focus-blue)] focus:ring-offset-2"
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
                    ? 'accent-[color:var(--color-error-red)] outline outline-2 outline-[color:var(--color-error-red)] outline-offset-1 rounded-sm'
                    : 'accent-[color:var(--color-brand-red)]',
                )}
                checked={termsAccepted}
                onChange={e => {
                  setTermsAccepted(e.target.checked)
                  if (e.target.checked) setTermsError(false)
                }}
              />
              <label
                htmlFor="signup-terms"
                className={clsx('text-xs cursor-pointer leading-[1.4]', termsError ? 'text-[color:var(--color-error-red)]' : 'text-olive')}
              >
                I agree to the{' '}
                <a
                  href="#"
                  className={clsx('font-semibold underline', termsError ? 'text-[color:var(--color-error-red)]' : 'text-plum')}
                >
                  Terms &amp; Condition
                </a>
              </label>
            </div>

            {/* Divider */}
            <div className="flex items-center gap-2.5 text-xs text-warm-silver before:content-[''] before:flex-1 before:h-px before:bg-sand after:content-[''] after:flex-1 after:h-px after:bg-sand">
              or
            </div>

            {/* Social buttons */}
            <div className="flex gap-2.5">
              <button
                type="button"
                className="flex-1 h-10 border border-sand rounded-pin bg-fog text-warm-silver flex items-center justify-center gap-[7px] text-xs font-medium opacity-[0.65] pointer-events-none cursor-not-allowed"
                disabled
              >
                <GoogleIcon />
                Continue with Google
              </button>
              <button
                type="button"
                className="flex-1 h-10 border border-sand rounded-pin bg-fog text-warm-silver flex items-center justify-center gap-[7px] text-xs font-medium opacity-[0.65] pointer-events-none cursor-not-allowed"
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
