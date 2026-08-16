import type { CielEvent, CielState } from '../types'

const stages = [
  { key: 'router', index: '01', name: 'Router', detail: 'Intent + routing' },
  { key: 'tools', index: '02', name: 'Tools', detail: 'Ordered execution' },
  { key: 'ciel', index: '03', name: 'CIEL', detail: 'Response synthesis' },
  { key: 'speech', index: '04', name: 'Voice', detail: 'Blocking output' },
  { key: 'controller', index: '05', name: 'Control', detail: 'History + loop' },
]

function timeLabel(timestamp: number) {
  return new Date(timestamp * 1000).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

function eventLabel(type: string) {
  return type.replaceAll('.', ' / ').toUpperCase()
}

export function Brain({ state, events }: { state: CielState; events: CielEvent[] }) {
  const currentStage = state.stage
  const recentEvents = [...events].reverse().slice(0, 30)

  return (
    <main className="page brain-page">
      <header className="page-heading">
        <div>
          <span className="eyebrow">03 / OBSERVABILITY</span>
          <h1>System state</h1>
        </div>
        <div className="heading-meta">
          <span>cycle {String(state.iteration).padStart(2, '0')}</span>
          <span>{state.status}</span>
        </div>
      </header>

      <section className="pipeline" aria-label="CIEL processing pipeline">
        {stages.map((stage, index) => {
          const active = currentStage === stage.key
          const currentIndex = stages.findIndex((item) => item.key === currentStage)
          const complete = state.status === 'active' && currentIndex > index
          return (
            <article className={active ? 'pipeline-stage active' : complete ? 'pipeline-stage complete' : 'pipeline-stage'} key={stage.key}>
              <span className="pipeline-index">{stage.index}</span>
              <div>
                <h2>{stage.name}</h2>
                <p>{stage.detail}</p>
              </div>
              <span className="pipeline-state">{active ? 'ACTIVE' : complete ? 'DONE' : 'WAIT'}</span>
            </article>
          )
        })}
      </section>

      <div className="brain-grid">
        <section className="brain-panel flags-panel">
          <header><span>Controller flags</span><small>LIVE</small></header>
          <div className="flag-readout">
            <div>
              <small>IS LOOPING</small>
              <strong className={state.flags.isLooping ? 'on' : ''}>{state.flags.isLooping ? 'TRUE' : 'FALSE'}</strong>
            </div>
            <div>
              <small>DO REMEMBER</small>
              <strong className={state.flags.doRemember ? 'on' : ''}>{state.flags.doRemember ? 'TRUE' : 'FALSE'}</strong>
            </div>
          </div>
        </section>

        <section className="brain-panel tools-panel">
          <header><span>Tool queue</span><small>{String(state.tools.length).padStart(2, '0')}</small></header>
          {state.tools.length ? (
            <div className="tool-list">
              {state.tools.map((tool, index) => (
                <article key={`${tool.tool}-${tool.action}-${index}`}>
                  <span>{String(index + 1).padStart(2, '0')}</span>
                  <div><strong>{tool.tool || 'tool'}</strong><code>{tool.action || 'pending'}</code></div>
                  <small className={tool.success === false ? 'failed' : tool.success ? 'passed' : ''}>
                    {tool.success === false ? 'FAILED' : tool.success ? 'DONE' : 'QUEUED'}
                  </small>
                </article>
              ))}
            </div>
          ) : <div className="panel-empty">NO TOOLS QUEUED</div>}
        </section>

        <section className="brain-panel decision-panel">
          <header><span>Router decision</span><small>JSON</small></header>
          <pre>{state.routerDecision ? JSON.stringify(state.routerDecision, null, 2) : '// Awaiting router output'}</pre>
        </section>

        <section className="brain-panel event-panel">
          <header><span>Event trace</span><small>RECENT {recentEvents.length}</small></header>
          <div className="event-list">
            {recentEvents.map((event, index) => (
              <article key={event.id || `${event.type}-${index}`}>
                <time>{timeLabel(event.timestamp)}</time>
                <span className={`event-mark ${event.type.includes('failed') ? 'failed' : ''}`} />
                <p>{eventLabel(event.type)}</p>
              </article>
            ))}
            {!recentEvents.length && <div className="panel-empty">NO EVENTS RECORDED</div>}
          </div>
        </section>
      </div>

      <p className="observability-note">Operational state only. Private model reasoning is never exposed.</p>
    </main>
  )
}
