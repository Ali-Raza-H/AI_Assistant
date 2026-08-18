import type { ChatMessage, CielState, DashboardSections } from '../state/types'

const configuredRoot = import.meta.env.VITE_CIEL_API_URL as string | undefined
export const API_ROOT = (configuredRoot || 'http://127.0.0.1:8765').replace(/\/$/, '')

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_ROOT}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })
  if (!response.ok) {
    const payload = await response.json().catch(() => null)
    throw new Error(payload?.detail || `Request failed (${response.status})`)
  }
  return response.json() as Promise<T>
}

export async function getState() {
  return request<{ state: CielState; events: import('../state/types').CielEvent[] }>('/api/state')
}

export async function getChat() {
  return request<{ messages: ChatMessage[] }>('/api/chat')
}

export async function getDashboard() {
  return request<{ sections: DashboardSections }>('/api/dashboard')
}

export async function sendMessage(message: string) {
  return request<{ accepted: boolean; interactionId: string }>('/api/messages', {
    method: 'POST',
    body: JSON.stringify({ message }),
  })
}

export function eventSocketURL() {
  const url = new URL(API_ROOT)
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
  url.pathname = '/ws/events'
  return url.toString()
}
