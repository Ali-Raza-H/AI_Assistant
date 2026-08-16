import { FormEvent, useRef, useState } from 'react'

interface ComposerProps {
  onSubmit: (message: string) => Promise<boolean>
  disabled?: boolean
  compact?: boolean
  error?: string | null
  onFocusChange?: (focused: boolean) => void
}

export function Composer({ onSubmit, disabled, compact, error, onFocusChange }: ComposerProps) {
  const [message, setMessage] = useState('')
  const [sending, setSending] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  async function submit(event: FormEvent) {
    event.preventDefault()
    if (!message.trim() || sending || disabled) return
    setSending(true)
    const accepted = await onSubmit(message)
    if (accepted) setMessage('')
    setSending(false)
    inputRef.current?.focus()
  }

  return (
    <div className={compact ? 'composer-wrap compact' : 'composer-wrap'}>
      <form className="composer" onSubmit={submit}>
        <span className="prompt-mark">&gt;</span>
        <input
          ref={inputRef}
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          onFocus={() => onFocusChange?.(true)}
          onBlur={() => onFocusChange?.(false)}
          placeholder={disabled ? 'CIEL IS OCCUPIED' : 'MESSAGE CIEL'}
          aria-label="Message CIEL"
          disabled={disabled}
          autoComplete="off"
        />
        <button type="submit" disabled={!message.trim() || sending || disabled}>
          {sending ? 'WAIT' : 'SEND'} <span>↗</span>
        </button>
      </form>
      {error && <div className="composer-error">{error}</div>}
    </div>
  )
}
