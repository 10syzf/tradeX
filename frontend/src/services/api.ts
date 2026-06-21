import type { ChatResponse, SessionDetail, SessionSummary } from '../types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    ...init,
  })

  if (!response.ok) {
    const text = await response.text()
    throw new Error(text || '请求失败')
  }

  return (await response.json()) as T
}

export const api = {
  getHealth: () =>
    request<{ status: string; app_name: string; version: string; llm_provider: string; llm_model: string }>('/health'),
  getSessions: () => request<SessionSummary[]>('/sessions'),
  createSession: (title = '新会话') =>
    request<SessionSummary>('/sessions', {
      method: 'POST',
      body: JSON.stringify({ title }),
    }),
  getSessionDetail: (sessionId: string) => request<SessionDetail>(`/sessions/${sessionId}/messages`),
  sendMessage: (sessionId: string, message: string) =>
    request<ChatResponse>('/chat', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId, message, model: 'default' }),
    }),
  getSettings: () =>
    request<{
      llm_provider: string
      default_model: string
      temperature: string
      max_context_messages: number
      agent_max_steps: number
      agent_log_level: string
    }>('/settings'),
  getStockToolStatus: () => request<{ status: string; message: string }>('/stock-tool/status'),
}
