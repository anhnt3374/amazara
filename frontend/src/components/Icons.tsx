export function ButterflyLogo({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M20 20C17 13 9 7 4 9C1 10 0 13 1 16C3 22 10 24 16 21C18 20 20 20 20 20Z" fill="white" fillOpacity="0.92"/>
      <path d="M20 20C23 13 31 7 36 9C39 10 40 13 39 16C37 22 30 24 24 21C22 20 20 20 20 20Z" fill="white" fillOpacity="0.92"/>
      <path d="M20 20C17 27 9 33 4 31C1 30 0 27 1 24C3 18 10 16 16 19C18 20 20 20 20 20Z" fill="white" fillOpacity="0.65"/>
      <path d="M20 20C23 27 31 33 36 31C39 30 40 27 39 24C37 18 30 16 24 19C22 20 20 20 20 20Z" fill="white" fillOpacity="0.65"/>
    </svg>
  )
}

export function EyeIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
      <circle cx="12" cy="12" r="3"/>
    </svg>
  )
}

export function EyeOffIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/>
      <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/>
      <path d="m14.12 14.12a3 3 0 1 1-4.24-4.24"/>
      <line x1="1" y1="1" x2="23" y2="23"/>
    </svg>
  )
}

export function ArrowLeftIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="19" y1="12" x2="5" y2="12"/>
      <polyline points="12 19 5 12 12 5"/>
    </svg>
  )
}

export function GoogleIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24">
      <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
      <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
      <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
      <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
    </svg>
  )
}

export function FacebookIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="#1877F2">
      <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
    </svg>
  )
}

export function NikeSwoosh({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 84 30" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
      <path d="M7.9 24.6C5.3 24.6 3.6 23.4 3.6 21.4C3.6 19 5.5 17.7 9 17.5L14.1 17.2V16.1C14.1 14.2 12.9 13.2 10.7 13.2C8.8 13.2 7.5 14 7.2 15.4H4.2C4.4 12.5 6.9 10.7 10.8 10.7C14.9 10.7 17.2 12.6 17.2 15.9V24.3H14.2V22.1H14.1C13.1 23.7 11.4 24.6 7.9 24.6ZM14.1 20V19L9.5 19.3C7.6 19.4 6.7 20.1 6.7 21.3C6.7 22.5 7.7 23.2 9.3 23.2C11.9 23.2 14.1 21.8 14.1 20ZM0 24.3V11H3.1V24.3H0ZM20.4 11H23.5V24.3H20.4V11ZM27.2 11H30.4L36.4 21.6H36.5L42.5 11H45.7L37.1 24.3H35.8L27.2 11ZM47.7 18C47.7 13.9 50.6 10.7 55.1 10.7C59.3 10.7 62 13.3 62 17.3C62 17.9 61.9 18.4 61.9 18.7H50.8C51 21 52.9 22.5 55.5 22.5C57.4 22.5 58.8 21.7 59.5 20.4H62.4C61.5 23.1 59 24.6 55.4 24.6C50.7 24.6 47.7 21.5 47.7 18ZM59 16.8C58.8 14.6 57.3 13.2 55.1 13.2C52.9 13.2 51.3 14.7 50.9 16.8H59ZM64.5 11H67.7V13.4H67.8C68.8 11.8 70.4 10.7 72.7 10.7C76.3 10.7 78.5 12.9 78.5 16.4V24.3H75.4V17C75.4 14.7 74.2 13.2 72 13.2C69.7 13.2 67.6 14.9 67.6 17.5V24.3H64.5V11Z" />
    </svg>
  )
}

export function JordanLogo({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 30 34" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
      <path d="M15 0C11.5 3.5 8 5 4 5C5 9 8 12 12 13C8 14 5 17 4 21C6 21 8 20.5 10 19.5C8 22 7 25 7.5 28C10 27 12.5 24.5 14 21.5C13.5 25 14 28.5 15 31.5C16 28.5 16.5 25 16 21.5C17.5 24.5 20 27 22.5 28C23 25 22 22 20 19.5C22 20.5 24 21 26 21C25 17 22 14 18 13C22 12 25 9 26 5C22 5 18.5 3.5 15 0Z" />
    </svg>
  )
}

export function SearchIcon({ className }: { className?: string }) {
  return (
    <svg className={className} width="20" height="20" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" />
    </svg>
  )
}

export function HeartIcon({ className }: { className?: string }) {
  return (
    <svg className={className} width="22" height="22" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
    </svg>
  )
}

export function BagIcon({ className }: { className?: string }) {
  return (
    <svg className={className} width="22" height="22" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z" />
      <line x1="3" y1="6" x2="21" y2="6" />
      <path d="M16 10a4 4 0 0 1-8 0" />
    </svg>
  )
}
