export type CielStage =
  | 'idle'
  | 'context'
  | 'memory'
  | 'brain'
  | 'router'
  | 'tools'
  | 'observation'
  | 'response'
  | 'speech'
  | 'controller'
  | 'error'

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

export interface BrainDecision {
  state?: string
  action?: Record<string, unknown> | null
  memory_request?: Record<string, unknown> | null
  question?: string | null
  response?: string | null
  result?: Record<string, unknown>
  plan?: string[]
  memory_candidates?: Record<string, unknown>[]
  [key: string]: unknown
}

export interface CielState {
  status: 'idle' | 'active' | 'error' | 'offline'
  stage: CielStage
  interactionId: string | null
  iteration: number
  flags: CielFlags
  brainDecision: BrainDecision | null
  routerDecision: RouterDecision | null
  tools: ToolRecord[]
  observations: Record<string, unknown>[]
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
