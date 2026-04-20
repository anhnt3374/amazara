import { useAuth } from '../hooks/useAuth'
import { ChatProvider } from '../contexts/ChatContext'
import Header from './Header'
import ChatWidget from './ChatWidget'

export default function Layout({ children }: { children: React.ReactNode }) {
  const { account } = useAuth()
  const showFloatingWidget = !account || account.type === 'user'

  return (
    <ChatProvider>
      <div className="min-h-screen flex flex-col bg-fog">
        <Header />
        <main className="flex-1">{children}</main>
        {showFloatingWidget && <ChatWidget />}
      </div>
    </ChatProvider>
  )
}
