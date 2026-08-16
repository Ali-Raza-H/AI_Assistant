import { useState } from 'react'
import { CielCore } from '../components/CielCore'
import { Composer } from '../components/Composer'
import { DataPanel, findItems } from '../components/DataPanel'
import type { CielState, ConnectionState, DashboardSections } from '../types'

interface DashboardProps {
  state: CielState
  connection: ConnectionState
  dashboard: DashboardSections
  submit: (message: string) => Promise<boolean>
  error: string | null
}

export function Dashboard({ state, connection, dashboard, submit, error }: DashboardProps) {
  const [focused, setFocused] = useState(false)
  const disabled = state.status === 'active'
  const hasLeft = findItems(dashboard.tasks).length > 0
  const hasRight = findItems(dashboard.notifications).length > 0 || findItems(dashboard.calendar).length > 0

  return (
    <main className="page dashboard-page">
      <div className={`dashboard-grid ${!hasLeft ? 'no-left' : ''} ${!hasRight ? 'no-right' : ''}`}>
        {hasLeft && (
          <aside className="dashboard-side left-side">
            <DataPanel title="Tasks" value={dashboard.tasks} />
          </aside>
        )}

        <section className="core-stage">
          <div className="axis-label left">INTELLIGENCE CORE</div>
          <CielCore state={state} connection={connection} listening={focused} />
          <Composer onSubmit={submit} disabled={disabled} error={error} onFocusChange={setFocused} />
          <div className="core-meta">
            <span>FLAGS / L:{Number(state.flags.isLooping)} R:{Number(state.flags.doRemember)}</span>
            <span>LOCAL ROUTER</span>
            <span>VOICE LINK</span>
          </div>
        </section>

        {hasRight && (
          <aside className="dashboard-side right-side">
            <DataPanel title="Notifications" value={dashboard.notifications} />
            <DataPanel title="Calendar" value={dashboard.calendar} limit={3} />
          </aside>
        )}
      </div>
    </main>
  )
}
