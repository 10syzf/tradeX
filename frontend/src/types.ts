export type Role = 'user' | 'assistant' | 'system'

export interface SessionSummary {
  id: string
  title: string
  created_at: string
  updated_at: string
}

export interface Message {
  id: string
  session_id: string
  role: Role
  content: string
  created_at: string
}

export interface SessionDetail extends SessionSummary {
  messages: Message[]
}

export interface ChatResponse {
  session_id: string
  reply: string
  tool_calls: Array<Record<string, unknown>>
  warnings: string[]
}
