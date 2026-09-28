import { useEffect, useRef, useState, type FormEvent } from 'react'
import Markdown from 'react-markdown'
import { useLocation, useNavigate } from 'react-router-dom'
import {
  clearChatHistory,
  fetchChatHistory,
  sendChat,
  type ChatProductCard,
  type ChatTurn,
  type HistoryMessage,
  type PageContext,
} from '../api'
import { useAuth } from '../auth'
import { ASK_CHAT_EVENT, OPEN_CHAT_EVENT } from '../chatEvents'
import { CHAT_RESULTS_PATH, useChatResults, type ChatResults } from '../chatResults'
import ChatCardScroller from './ChatCardScroller'
import YaleY from './YaleY'

interface ChatMessage extends ChatTurn {
  products?: ChatProductCard[] // top picks shown in the chat
  pageResults?: ChatResults // fuller set the agent sent to the main page
}

function greeting(firstName?: string, returning = false): ChatMessage {
  const hello = firstName ? `${returning ? 'Welcome back' : 'Hi'} ${firstName}!` : 'Hi!'
  const tail = returning
    ? "Here's our conversation from last time. What can I help you find today?"
    : "I'm the Campus Customs assistant. Ask me about Yale gear, sizes, or what's in stock."
  return { role: 'assistant', content: `${hello} ${tail}` }
}

// Saved messages from the backend, in the widget's shape.
function fromHistory(saved: HistoryMessage[]): ChatMessage[] {
  return saved.map((m, i) => ({
    role: m.role,
    content: m.content,
    products: m.products,
    pageResults: m.page_results
      ? { ...m.page_results, question: saved[i - 1]?.role === 'user' ? saved[i - 1].content : m.page_results.title }
      : undefined,
  }))
}

// Clickable starter questions, matched to what the customer is looking at.
const SUGGESTIONS = {
  product: ['What sizes are in stock?', 'What colors does this come in?', 'Show me similar items'],
  results: ['Which of these makes the best gift?', 'Only show ones in stock in L', "What's the cheapest?"],
  general: ['Gifts under $50', 'Hoodies in stock in XL', 'Residential college gear', 'Game day shirts'],
}

export default function ChatWidget() {
  const { user } = useAuth()
  const { results, showResults, clearResults } = useChatResults()
  const navigate = useNavigate()
  const location = useLocation()
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([greeting()])
  const [draft, setDraft] = useState('')
  const [sending, setSending] = useState(false)
  const listRef = useRef<HTMLDivElement>(null)
  const lastUserId = useRef(user?.id)

  // When someone logs in, load their saved conversation; on log out, start fresh
  // so one customer's chat is never shown to another.
  useEffect(() => {
    if (lastUserId.current !== user?.id) clearResults()
    lastUserId.current = user?.id
    if (!user) {
      setMessages([greeting()])
      return
    }
    let cancelled = false
    fetchChatHistory().then((saved) => {
      if (cancelled) return
      setMessages([greeting(user.first_name, saved.length > 0), ...fromHistory(saved)])
    })
    return () => {
      cancelled = true
    }
  }, [user?.id, user?.first_name])

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, open, sending])

  // Other parts of the site can open the chat or ask it something (see chatEvents.ts).
  const sendRef = useRef<(text: string) => void>(() => {})
  useEffect(() => {
    const onOpen = () => setOpen(true)
    const onAsk = (event: Event) => {
      setOpen(true)
      sendRef.current((event as CustomEvent<string>).detail)
    }
    window.addEventListener(OPEN_CHAT_EVENT, onOpen)
    window.addEventListener(ASK_CHAT_EVENT, onAsk)
    return () => {
      window.removeEventListener(OPEN_CHAT_EVENT, onOpen)
      window.removeEventListener(ASK_CHAT_EVENT, onAsk)
    }
  }, [])

  // What the customer is looking at right now, so "this one" can be understood.
  function pageContext(): PageContext {
    const productMatch = location.pathname.match(/^\/products\/([^/]+)$/)
    const onChatResults = location.pathname === '/products' && new URLSearchParams(location.search).get('view') === 'chat'
    return {
      path: location.pathname,
      product_id: productMatch ? decodeURIComponent(productMatch[1]) : null,
      results_title: onChatResults && results ? results.title : null,
    }
  }

  // Put a set of chat results on the main page (Products page, chat view).
  function openOnPage(pageResults: ChatResults) {
    showResults(pageResults)
    navigate(CHAT_RESULTS_PATH)
  }

  async function handleClear() {
    if (!window.confirm('Delete your saved chat history? This can’t be undone.')) return
    try {
      await clearChatHistory()
      setMessages([greeting(user?.first_name)])
    } catch (err) {
      window.alert((err as Error).message)
    }
  }

  function suggestions(): string[] {
    const page = pageContext()
    if (page.product_id) return SUGGESTIONS.product
    if (page.results_title) return SUGGESTIONS.results
    return SUGGESTIONS.general
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    send(draft)
  }

  sendRef.current = (text: string) => void send(text)

  async function send(raw: string) {
    const text = raw.trim()
    if (!text || sending) return
    // Earlier turns give guests' chats context (signed-in memory comes from the server).
    const history: ChatTurn[] = messages.slice(1).map(({ role, content }) => ({ role, content }))
    setMessages((current) => [...current, { role: 'user', content: text }])
    setDraft('')
    setSending(true)
    try {
      const reply = await sendChat(text, history, pageContext())
      const pageResults = reply.page_results ? { ...reply.page_results, question: text } : undefined
      setMessages((current) => [
        ...current,
        { role: 'assistant', content: reply.reply, products: reply.products, pageResults },
      ])
      if (pageResults) openOnPage(pageResults)
    } catch (err) {
      setMessages((current) => [...current, { role: 'assistant', content: (err as Error).message }])
    } finally {
      setSending(false)
    }
  }

  if (!open) {
    return (
      <button className="chat-launcher" onClick={() => setOpen(true)} aria-label="Open chat">
        <span className="launcher-icon" aria-hidden="true">
          💬
        </span>
        <span>Ask us anything</span>
      </button>
    )
  }

  return (
    <section className="chat-panel" aria-label="Campus Customs chat">
      <header className="chat-header">
        <span className="chat-avatar" aria-hidden="true">
          <YaleY />
        </span>
        <span className="chat-title">
          <strong>Campus Customs Assistant</strong>
          <span className="chat-status">
            <span className="status-dot" /> Online · checks live stock
          </span>
        </span>
        <button onClick={() => setOpen(false)} aria-label="Close chat">
          ×
        </button>
      </header>
      <div className="chat-subheader">
        {user ? (
          <>
            <span>Chat saved to your account</span>
            <button className="link-button" onClick={handleClear}>
              Clear history
            </button>
          </>
        ) : (
          <span>Log in to save this chat</span>
        )}
      </div>
      <div className="chat-messages" ref={listRef}>
        {messages.map((message, i) => (
          <div key={i} className={`chat-turn ${message.role}`}>
            <div className={`chat-bubble ${message.role}`}>
              {message.role === 'assistant' ? <Markdown>{message.content}</Markdown> : message.content}
            </div>
            {message.products && message.products.length > 0 && <ChatCardScroller products={message.products} />}
            {message.pageResults && (
              <button className="see-on-page" onClick={() => openOnPage(message.pageResults!)}>
                See all {message.pageResults.products.length} on the page →
              </button>
            )}
          </div>
        ))}
        {sending && (
          <div className="chat-bubble assistant typing" aria-label="Assistant is typing">
            <span />
            <span />
            <span />
          </div>
        )}
      </div>
      {!sending && (
        <div className="chat-suggestions" aria-label="Suggested questions">
          {suggestions().map((text) => (
            <button key={text} className="suggestion-chip" onClick={() => send(text)}>
              {text}
            </button>
          ))}
        </div>
      )}
      <form className="chat-input" onSubmit={handleSubmit}>
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Ask about gear, sizes, stock…"
          aria-label="Message"
          maxLength={2000}
        />
        <button type="submit" disabled={!draft.trim() || sending}>
          Send
        </button>
      </form>
    </section>
  )
}
