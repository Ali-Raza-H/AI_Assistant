import type { CielState, ConnectionState } from '../types'

export function StatusBar({ state, connection }: { state: CielState; connection: ConnectionState }) {
  const status = connection === 'online' ? state.status : connection
  const label = connection !== 'online'
    ? connection === 'connecting' ? 'Establishing link' : 'Link unavailable'
    : state.stage === 'idle' ? 'System ready' : `${state.stage} / cycle ${state.iteration}`

  return (
    <header className="status-bar">
      <div className="system-title">
        <span>CIEL</span>
        <small>Central Intelligence and Execution Layer</small>
      </div>
      <div className="status-readout">
        <span className={`status-dot ${status}`} />
        <span>{label}</span>
        <span className="connection-label">{connection}</span>
      </div>
    </header>
  )
}
