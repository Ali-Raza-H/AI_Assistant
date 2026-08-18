import { useCallback, useEffect, useRef, useState } from 'react'
import { eventSocketURL, getChat, getDashboard, getState, sendMessage } from '../api/client'
import type {
  ChatMessage,
  CielEvent,
  CielState,
  ConnectionState,
  BrainDecision,
  DashboardSections,
  RouterDecision,
  ToolRecord,
} from './types'

const offlineState: CielState = {
  status: 'offline',
  stage: 'idle',
  interactionId: null,
  iteration: 0,
  flags: { isLooping: false, doRemember: false },
  brainDecision: null,
  routerDecision: null,
  tools: [],
  observations: [],
  lastResponse: null,
  error: null,
  updatedAt: Date.now() / 1000,
}

function reduceEvent(state: CielState, event: CielEvent): CielState {
  const data = event.data
  const iteration = typeof data.iteration === 'number' ? data.iteration : state.iteration
  const interactionId = typeof data.interactionId === 'string' ? data.interactionId : state.interactionId
  const next = { ...state, iteration, interactionId, updatedAt: event.timestamp }

  switch (event.type) {
    case 'interaction.started':
      return {
        ...next,
        status: 'active',
        stage: 'context',
        iteration: 1,
        error: null,
        tools: [],
        observations: [],
        brainDecision: null,
        routerDecision: null,
      }
    case 'context.started':
    case 'context.completed':
      return { ...next, status: 'active', stage: 'context' }
    case 'memory.retrieval.started':
    case 'memory.retrieval.completed':
    case 'memory.evaluation.started':
    case 'memory.committed':
      return { ...next, status: 'active', stage: 'memory' }
    case 'brain.started':
      return { ...next, status: 'active', stage: 'brain' }
    case 'brain.decision':
      return { ...next, status: 'active', stage: 'brain', brainDecision: data.decision as BrainDecision }
    case 'router.started':
      return { ...next, status: 'active', stage: 'router' }
    case 'router.decision': {
      const decision = data.decision as RouterDecision
      return { ...next, stage: 'router', routerDecision: decision, flags: decision?.flags || state.flags }
    }
    case 'tools.started':
      return { ...next, stage: 'tools', tools: (data.tools as ToolRecord[]) || [] }
    case 'tool.started':
      return { ...next, stage: 'tools' }
    case 'tool.completed': {
      const index = typeof data.index === 'number' ? data.index : -1
      const tools = [...state.tools]
      if (index >= 0 && index < tools.length) tools[index] = data.result as ToolRecord
      return { ...next, stage: 'tools', tools }
    }
    case 'observation.created':
      return {
        ...next,
        stage: 'observation',
        observations: [...state.observations.slice(-7), data.observation as Record<string, unknown>],
      }
    case 'flags.updated':
      return { ...next, flags: data.flags as CielState['flags'] }
    case 'response.started':
    case 'response.token':
    case 'response.completed':
      return { ...next, stage: 'response', lastResponse: event.type === 'response.completed' ? String(data.response || '') : state.lastResponse }
    case 'ciel.started':
    case 'ciel.token':
    case 'ciel.completed':
      return { ...next, stage: 'response' }
    case 'speech.started':
      return { ...next, stage: 'speech' }
    case 'speech.ended':
    case 'history.saved':
      return { ...next, stage: 'controller' }
    case 'interaction.completed':
      return { ...next, status: 'idle', stage: 'idle', lastResponse: String(data.response || '') }
    case 'interaction.failed':
      return { ...next, status: 'error', stage: 'error', error: String(data.error || 'Unknown error') }
    default:
      return next
  }
}

export function useCiel() {
  const [state, setState] = useState<CielState>(offlineState)
  const [events, setEvents] = useState<CielEvent[]>([])
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [dashboard, setDashboard] = useState<DashboardSections>({})
  const [connection, setConnection] = useState<ConnectionState>('connecting')
  const [streaming, setStreaming] = useState('')
  const [requestError, setRequestError] = useState<string | null>(null)
  const retryRef = useRef<number | undefined>(undefined)

  const refreshChat = useCallback(async () => {
    const result = await getChat()
    setMessages(result.messages)
  }, [])

  const refreshDashboard = useCallback(async () => {
    try {
      const result = await getDashboard()
      setDashboard(result.sections)
    } catch {
      // LifeOS data is optional. Its failure should not create broken UI.
      setDashboard({})
    }
  }, [])

  useEffect(() => {
    let disposed = false
    let socket: WebSocket | undefined

    Promise.allSettled([getState(), getChat(), getDashboard()]).then(([stateResult, chatResult, dashboardResult]) => {
      if (disposed) return
      if (stateResult.status === 'fulfilled') {
        setState(stateResult.value.state)
        setEvents(stateResult.value.events.slice(-120))
      }
      if (chatResult.status === 'fulfilled') setMessages(chatResult.value.messages)
      if (dashboardResult.status === 'fulfilled') setDashboard(dashboardResult.value.sections)
    })

    const connect = () => {
      if (disposed) return
      setConnection('connecting')
      socket = new WebSocket(eventSocketURL())
      socket.onopen = () => setConnection('online')
      socket.onmessage = (message) => {
        const event = JSON.parse(message.data) as CielEvent
        if (event.type === 'system.snapshot') {
          const data = event.data as unknown as { state: CielState; events: CielEvent[] }
          setState(data.state)
          setEvents(data.events.slice(-120))
          return
        }
        setEvents((current) => [...current.slice(-119), event])
        setState((current) => reduceEvent(current, event))
        if (event.type === 'interaction.started') {
          setStreaming('')
          setRequestError(null)
        } else if (event.type === 'response.token' || event.type === 'ciel.token') {
          setStreaming((current) => current + String(event.data.token || ''))
        } else if (event.type === 'history.saved') {
          refreshChat().catch(() => undefined)
        } else if (event.type === 'interaction.completed') {
          setStreaming('')
          refreshChat().catch(() => undefined)
          refreshDashboard().catch(() => undefined)
        } else if (event.type === 'lifeos.notification') {
          refreshDashboard().catch(() => undefined)
        }
      }
      socket.onerror = () => socket?.close()
      socket.onclose = () => {
        if (disposed) return
        setConnection('offline')
        setState((current) => ({ ...current, status: 'offline' }))
        retryRef.current = window.setTimeout(connect, 2200)
      }
    }

    connect()
    return () => {
      disposed = true
      if (retryRef.current) window.clearTimeout(retryRef.current)
      socket?.close()
    }
  }, [refreshChat, refreshDashboard])

  const submit = useCallback(async (message: string) => {
    const cleanMessage = message.trim()
    if (!cleanMessage) return false
    setRequestError(null)
    setMessages((current) => [
      ...current,
      { id: `pending-${Date.now()}`, role: 'user', content: cleanMessage, pending: true },
    ])
    try {
      await sendMessage(cleanMessage)
      return true
    } catch (error) {
      setMessages((current) => current.filter((item) => !item.pending))
      setRequestError(error instanceof Error ? error.message : 'Unable to reach CIEL')
      return false
    }
  }, [])

  return {
    state,
    events,
    messages,
    dashboard,
    connection,
    streaming,
    requestError,
    submit,
    refreshDashboard,
  }
}
