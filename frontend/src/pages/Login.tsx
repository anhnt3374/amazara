import clsx from 'clsx'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ArrowLeftIcon, ButterflyLogo, EyeIcon, EyeOffIcon, FacebookIcon, GoogleIcon } from '../components/Icons'
import { useAuth } from '../hooks/useAuth'
import { ApiError } from '../services/auth'

const inputBase =
  'h-[44px] border border-warm-silver rounded-pin px-[15px] text-sm text-plum outline-none transition-colors w-full bg-white placeholder:text-warm-silver focus:border-[color:var(--color-focus-blue)] focus:ring-2 focus:ring-[color:var(--color-focus-blue)]/30'

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
    if (!termsAccepted) { setTermsError(true); return }
    setLoading(true)
    try {
      await login(email, password)
      navigate('/success')
    } catch (err) {
      if (err instanceof ApiError && err.message === 'Invalid email or password') {
        setApiError('Incorrect email or password.')
      } else {
        setApiError('Something went wrong. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      className="min-h-screen flex items-center justify-center p-6 bg-fog"
    >
      <div className="flex w-full max-w-[860px] min-h-[510px] rounded-pin-2xl overflow-hidden shadow-[0_20px_50px_rgba(33,25,34,0.18)] bg-white">

        {/* Left decorative panel */}
        <div
          className="w-[42%] shrink-0 relative flex items-start p-7 overflow-hidden"
          style={{ background: 'linear-gradient(150deg, #e60023 0%, #ad081b 55%, #33332e 100%)' }}
        >
          <ButterflyLogo className="w-[38px] h-[38px] relative z-10" />
          <div
            className="absolute rounded-full pointer-events-none"
            style={{
              width: 280, height: 280, bottom: '15%', left: '20%',
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

          <h1 className="text-[34px] font-bold text-plum tracking-[-1px] m-0 mb-1.5 leading-tight">Log in</h1>
          <p className="text-[13px] text-olive m-0 mb-[22px]">
            Don&apos;t have an account?{' '}
            <Link to="/signup" className="text-brand-red font-semibold underline">Create an Account</Link>
          </p>

          <form className="flex flex-col gap-[13px] flex-1" onSubmit={handleSubmit}>
            {apiError && (
              <div className="bg-[#FFF5F5] border border-[#FED7D7] rounded-pin py-[9px] px-3.5 text-[13px] text-[color:var(--color-error-red)] leading-snug">
                {apiError}
              </div>
            )}

            {/* Email */}
            <div className="flex flex-col gap-[5px]">
              <label className="text-[13px] font-medium text-plum" htmlFor="login-email">
                Email Address
              </label>
              <input
                id="login-email"
                className={inputBase}
                type="email"
                placeholder="john52martinez@gmail.com"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
                autoComplete="email"
              />
            </div>

            {/* Password */}
            <div className="flex flex-col gap-[5px]">
              <label className="text-[13px] font-medium text-plum" htmlFor="login-password">
                Password
              </label>
              <div className="relative">
                <input
                  id="login-password"
                  className={clsx(inputBase, 'pr-10')}
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
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
            </div>

            {/* Forgot password */}
            <div className="flex justify-end -mt-1.5">
              <button type="button" className="bg-transparent border-none p-0 text-xs text-olive underline hover:text-brand-red cursor-pointer">
                Forgot Password?
              </button>
            </div>

            {/* Submit */}
            <button
              type="submit"
              className="h-[46px] bg-brand-red text-white border-none rounded-pin text-[15px] font-semibold cursor-pointer transition-colors mt-0.5 hover:bg-[var(--color-brand-red-hover)] disabled:opacity-[0.65] disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-[color:var(--color-focus-blue)] focus:ring-offset-2"
              disabled={loading}
            >
              {loading ? 'Logging in...' : 'Log in'}
            </button>

            {/* Terms */}
            <div className="flex items-center gap-2">
              <input
                id="login-terms"
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
                htmlFor="login-terms"
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
