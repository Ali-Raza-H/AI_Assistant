import { useEffect, useMemo, useRef } from 'react'
import { Composer } from '../components/Composer'
import type { ChatMessage, CielState } from '../types'

function removeRepeatedCyclePrompts(messages: ChatMessage[]) {
  let lastUser = ''
  return messages.filter((message) => {
    if (message.role !== 'user') return true
    if (message.content === lastUser) return false
    lastUser = message.content
    return true
  })
}

export function Chat({
  state,
  messages,
  streaming,
  submit,
  error,
}: {
  state: CielState
  messages: ChatMessage[]
  streaming: string
  submit: (message: string) => Promise<boolean>
  error: string | null
}) {
  const endRef = useRef<HTMLDivElement>(null)
  const transcript = useMemo(() => removeRepeatedCyclePrompts(messages), [messages])

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [transcript.length, streaming])

  return (
    <main className="page chat-page">
      <header className="page-heading">
        <div>
          <span className="eyebrow">02 / COMMUNICATION</span>
          <h1>Conversation</h1>
        </div>
        <div className="heading-meta">
          <span>{transcript.length} entries</span>
          <span>history active</span>
        </div>
      </header>

      <section className="transcript" aria-live="polite">
        {transcript.length === 0 && !streaming && (
          <div className="empty-state">
            <span>NO CONVERSATION DATA</span>
            <p>Send a directive to establish the channel.</p>
          </div>
        )}
        {transcript.map((message, index) => (
          <article className={`message ${message.role}`} key={message.id}>
            <div className="message-identity">
              <span>{message.role === 'assistant' ? 'CIEL' : 'YOU'}</span>
              <small>{String(index + 1).padStart(3, '0')}</small>
            </div>
            <p>{message.content}</p>
            {message.pending && <span className="message-state">QUEUED</span>}
          </article>
        ))}
        {streaming && (
          <article className="message assistant live">
            <div className="message-identity">
              <span>CIEL</span>
              <small>LIVE</small>
            </div>
            <p>{streaming}<i className="cursor" /></p>
          </article>
        )}
        <div ref={endRef} />
      </section>

      <footer className="chat-composer">
        <Composer onSubmit={submit} disabled={state.status === 'active'} compact error={error} />
      </footer>
    </main>
  )
}
