import clsx from 'clsx'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ArrowLeftIcon, ButterflyLogo, EyeIcon, EyeOffIcon, FacebookIcon, GoogleIcon } from '../components/Icons'
import { useAuth } from '../hooks/useAuth'
import { ApiError } from '../services/auth'

const inputBase =
  'h-[42px] border-[1.5px] rounded-lg px-3 text-sm text-[#111] outline-none transition-colors duration-[180ms] w-full bg-white placeholder:text-[#BBB]'

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
      className="min-h-screen flex items-center justify-center p-6"
      style={{ background: 'radial-gradient(ellipse at 65% 55%, #7B1A1A 0%, #3A0A0A 55%, #1C0404 100%)' }}
    >
      <div className="flex w-full max-w-[860px] min-h-[510px] rounded-3xl overflow-hidden shadow-[0_30px_70px_rgba(0,0,0,0.55)]">

        {/* Left decorative panel */}
        <div
          className="w-[42%] shrink-0 relative flex items-start p-7 overflow-hidden"
          style={{ background: 'linear-gradient(150deg, #3D0A0A 0%, #8B2010 45%, #D04520 80%, #E05A15 100%)' }}
        >
          <ButterflyLogo className="w-[38px] h-[38px] relative z-10" />
          <div
            className="absolute rounded-full pointer-events-none"
            style={{
              width: 280, height: 280, bottom: '15%', left: '20%',
              background: 'radial-gradient(circle, rgba(255,140,40,0.35) 0%, transparent 70%)',
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

          <h1 className="text-[34px] font-bold text-[#111] m-0 mb-1.5 leading-tight">Log in</h1>
          <p className="text-[13px] text-[#666] m-0 mb-[22px]">
            Don&apos;t have an account?{' '}
            <Link to="/signup" className="text-[#111] font-semibold underline">Create an Account</Link>
          </p>

          <form className="flex flex-col gap-[13px] flex-1" onSubmit={handleSubmit}>
            {apiError && (
              <div className="bg-[#FFF5F5] border border-[#FED7D7] rounded-lg py-[9px] px-3.5 text-[13px] text-[#C53030] leading-snug">
                {apiError}
              </div>
            )}

            {/* Email */}
            <div className="flex flex-col gap-[5px]">
              <label className="text-[13px] font-medium text-[#333]" htmlFor="login-email">
                Email Address
              </label>
              <input
                id="login-email"
                className={clsx(inputBase, 'border-[#E0E0E0] focus:border-[#555]')}
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
              <label className="text-[13px] font-medium text-[#333]" htmlFor="login-password">
                Password
              </label>
              <div className="relative">
                <input
                  id="login-password"
                  className={clsx(inputBase, 'border-[#E0E0E0] focus:border-[#555] pr-10')}
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
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
            </div>

            {/* Forgot password */}
            <div className="flex justify-end -mt-1.5">
              <button type="button" className="bg-transparent border-none p-0 text-xs text-[#333] underline cursor-pointer">
                Forgot Password?
              </button>
            </div>

            {/* Submit */}
            <button
              type="submit"
              className="h-[46px] bg-[#111] text-white border-none rounded-full text-[15px] font-semibold cursor-pointer transition-colors mt-0.5 hover:bg-[#333] disabled:opacity-[0.65] disabled:cursor-not-allowed"
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
                htmlFor="login-terms"
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
