import { useEffect, useState } from 'react'
import { Sidebar } from './components/Sidebar'
import { StatusBar } from './components/StatusBar'
import { Brain } from './pages/Brain'
import { Chat } from './pages/Chat'
import { Dashboard } from './pages/Dashboard'
import { useCiel } from './useCiel'

type Page = 'main' | 'chat' | 'brain'

function pageFromPath(): Page {
  const path = window.location.pathname.replace(/^\//, '')
  return path === 'chat' || path === 'brain' ? path : 'main'
}

export default function App() {
  const [page, setPage] = useState<Page>(pageFromPath)
  const ciel = useCiel()

  useEffect(() => {
    const update = () => setPage(pageFromPath())
    window.addEventListener('popstate', update)
    return () => window.removeEventListener('popstate', update)
  }, [])

  function navigate(next: Page) {
    const path = next === 'main' ? '/' : `/${next}`
    window.history.pushState({}, '', path)
    setPage(next)
  }

  return (
    <div className="app-shell">
      <Sidebar page={page} navigate={navigate} />
      <div className="app-content">
        <StatusBar state={ciel.state} connection={ciel.connection} />
        {page === 'main' && (
          <Dashboard
            state={ciel.state}
            connection={ciel.connection}
            dashboard={ciel.dashboard}
            submit={ciel.submit}
            error={ciel.requestError}
          />
        )}
        {page === 'chat' && (
          <Chat
            state={ciel.state}
            messages={ciel.messages}
            streaming={ciel.streaming}
            submit={ciel.submit}
            error={ciel.requestError}
          />
        )}
        {page === 'brain' && <Brain state={ciel.state} events={ciel.events} />}
      </div>
    </div>
  )
}
