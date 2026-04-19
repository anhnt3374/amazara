import Header from './Header'
import ChatWidget from './ChatWidget'

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col bg-fog">
      <Header />
      <main className="flex-1">{children}</main>
      <ChatWidget />
    </div>
  )
}
