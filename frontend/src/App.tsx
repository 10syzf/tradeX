import { useEffect, useMemo, useState } from 'react'
import type { FormEventHandler } from 'react'
import './App.css'
import { api } from './services/api'
import type { Message, SessionSummary } from './types'

function App() {
  const [sessions, setSessions] = useState<SessionSummary[]>([])
  const [activeSessionId, setActiveSessionId] = useState<string>('')
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [booting, setBooting] = useState(true)
  const [error, setError] = useState('')
  const [warnings, setWarnings] = useState<string[]>([])
  const [health, setHealth] = useState<{
    status: string
    app_name: string
    version: string
    llm_provider: string
    llm_model: string
  } | null>(null)
  const [settings, setSettings] = useState<{
    llm_provider: string
    default_model: string
    temperature: string
    max_context_messages: number
    agent_max_steps: number
    agent_log_level: string
  } | null>(null)
  const [stockStatus, setStockStatus] = useState<{ status: string; message: string } | null>(null)

  useEffect(() => {
    const bootstrap = async () => {
      try {
        const [healthData, sessionList, settingsData, stockData] = await Promise.all([
          api.getHealth(),
          api.getSessions(),
          api.getSettings(),
          api.getStockToolStatus(),
        ])

        setHealth(healthData)
        setSettings(settingsData)
        setStockStatus(stockData)
        setSessions(sessionList)

        const firstSession = sessionList[0] ?? (await api.createSession())
        const finalSessions = sessionList[0] ? sessionList : [firstSession]
        setSessions(finalSessions)
        setActiveSessionId(firstSession.id)
      } catch (err) {
        setError(err instanceof Error ? err.message : '初始化失败')
      } finally {
        setBooting(false)
      }
    }

    void bootstrap()
  }, [])

  useEffect(() => {
    if (!activeSessionId) {
      return
    }

    const loadDetail = async () => {
      try {
        const detail = await api.getSessionDetail(activeSessionId)
        setMessages(detail.messages)
      } catch (err) {
        setError(err instanceof Error ? err.message : '加载会话失败')
      }
    }

    void loadDetail()
  }, [activeSessionId])

  const activeSession = useMemo(
    () => sessions.find((session) => session.id === activeSessionId) ?? null,
    [sessions, activeSessionId],
  )

  const handleCreateSession = async () => {
    try {
      const newSession = await api.createSession(`新会话 ${sessions.length + 1}`)
      setSessions((current) => [newSession, ...current])
      setActiveSessionId(newSession.id)
      setMessages([])
      setWarnings([])
      setError('')
    } catch (err) {
      setError(err instanceof Error ? err.message : '创建会话失败')
    }
  }

  const handleSubmit: FormEventHandler<HTMLFormElement> = async (event) => {
    event.preventDefault()
    if (!input.trim() || !activeSessionId || loading) {
      return
    }

    const draftMessage = input.trim()
    const tempMessage: Message = {
      id: `temp-${Date.now()}`,
      session_id: activeSessionId,
      role: 'user',
      content: draftMessage,
      created_at: new Date().toISOString(),
    }

    setInput('')
    setLoading(true)
    setError('')
    setWarnings([])
    setMessages((current) => [...current, tempMessage])

    try {
      const response = await api.sendMessage(activeSessionId, draftMessage)
      const detail = await api.getSessionDetail(activeSessionId)
      setMessages(detail.messages)
      setWarnings(response.warnings)
      setSessions((current) =>
        current
          .map((item) =>
            item.id === activeSessionId
              ? { ...item, updated_at: new Date().toISOString(), title: item.title || draftMessage.slice(0, 20) }
              : item,
          )
          .sort((a, b) => b.updated_at.localeCompare(a.updated_at)),
      )
    } catch (err) {
      setMessages((current) => current.filter((item) => item.id !== tempMessage.id))
      setError(err instanceof Error ? err.message : '发送消息失败')
    } finally {
      setLoading(false)
    }
  }

  if (booting) {
    return <div className="boot-screen">Tradex 正在启动...</div>
  }

  return (
    <div className="app-shell">
      <aside className="sidebar left-panel">
        <div className="brand-block">
          <div>
            <p className="eyebrow">Tradex</p>
            <h1>股票交易 Agent</h1>
          </div>
          <button className="primary-button" onClick={handleCreateSession} type="button">
            新建会话
          </button>
        </div>

        <div className="panel-section">
          <p className="section-title">会话列表</p>
          <div className="session-list">
            {sessions.map((session) => (
              <button
                key={session.id}
                type="button"
                className={`session-item ${session.id === activeSessionId ? 'active' : ''}`}
                onClick={() => setActiveSessionId(session.id)}
              >
                <span>{session.title}</span>
                <small>{new Date(session.updated_at).toLocaleString()}</small>
              </button>
            ))}
          </div>
        </div>
      </aside>

      <main className="chat-panel">
        <header className="chat-header">
          <div>
            <p className="eyebrow">统一指令面板</p>
            <h2>{activeSession?.title ?? '未选择会话'}</h2>
          </div>
          <div className="status-pill">{health?.status === 'ok' ? '后端在线' : '后端离线'}</div>
        </header>

        <section className="messages-panel">
          {messages.length === 0 ? (
            <div className="empty-state">
              <h3>开始第一轮对话</h3>
              <p>你可以直接输入股票问题，当前版本会保存会话并预留股票工具扩展位。</p>
            </div>
          ) : (
            messages.map((message) => (
              <article key={message.id} className={`message-card ${message.role}`}>
                <div className="message-meta">{message.role === 'user' ? '用户' : '助手'}</div>
                <div className="message-content">{message.content}</div>
              </article>
            ))
          )}

          {loading ? <div className="typing-indicator">模型正在生成回复...</div> : null}
        </section>

        <footer className="composer-panel">
          {error ? <div className="feedback error">{error}</div> : null}
          {warnings.map((warning) => (
            <div key={warning} className="feedback warning">
              {warning}
            </div>
          ))}
          <form className="composer-form" onSubmit={handleSubmit}>
            <textarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="输入你的问题，例如：分析一下贵州茅台近期是否值得关注"
              rows={4}
            />
            <button className="primary-button" disabled={loading || !input.trim()} type="submit">
              发送
            </button>
          </form>
        </footer>
      </main>

      <aside className="sidebar right-panel">
        <div className="panel-section">
          <p className="section-title">系统状态</p>
          <div className="info-card">
            <span>应用</span>
            <strong>{health?.app_name ?? 'Tradex API'}</strong>
          </div>
          <div className="info-card">
            <span>版本</span>
            <strong>{health?.version ?? '0.1.0'}</strong>
          </div>
          <div className="info-card">
            <span>默认模型</span>
            <strong>{settings?.default_model ?? '未配置'}</strong>
          </div>
          <div className="info-card">
            <span>模型提供方</span>
            <strong>{settings?.llm_provider ?? health?.llm_provider ?? '未知'}</strong>
          </div>
          <div className="info-card">
            <span>上下文条数</span>
            <strong>{settings?.max_context_messages ?? 0}</strong>
          </div>
          <div className="info-card">
            <span>Agent 步数</span>
            <strong>{settings?.agent_max_steps ?? 0}</strong>
          </div>
        </div>

        <div className="panel-section">
          <p className="section-title">股票工具</p>
          <div className="status-card muted">
            <strong>{stockStatus?.status ?? 'unknown'}</strong>
            <p>{stockStatus?.message ?? '股票工具状态未知'}</p>
          </div>
        </div>

        <div className="panel-section">
          <p className="section-title">记忆系统</p>
          <div className="status-card muted">
            <strong>memory-stub</strong>
            <p>当前阶段使用最近消息作为上下文，后续接入长期记忆与检索。</p>
          </div>
        </div>
      </aside>
    </div>
  )
}

export default App
