export type CielStage = 'idle' | 'router' | 'tools' | 'ciel' | 'speech' | 'controller' | 'error'

export interface CielFlags {
  isLooping: boolean
  doRemember: boolean
}

export interface ToolRecord {
  tool?: string
  action?: string
  arguments?: Record<string, unknown>
  success?: boolean
  output?: string
  error?: string
  [key: string]: unknown
}

export interface RouterDecision {
  flags?: CielFlags
  tools?: ToolRecord[]
  [key: string]: unknown
}

export interface CielState {
  status: 'idle' | 'active' | 'error' | 'offline'
  stage: CielStage
  interactionId: string | null
  iteration: number
  flags: CielFlags
  routerDecision: RouterDecision | null
  tools: ToolRecord[]
  lastResponse: string | null
  error: string | null
  updatedAt: number
}

export interface CielEvent {
  id?: string
  type: string
  timestamp: number
  data: Record<string, unknown>
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  record?: number
  pending?: boolean
}

export type DashboardSections = Record<string, unknown>

export type ConnectionState = 'connecting' | 'online' | 'offline'
