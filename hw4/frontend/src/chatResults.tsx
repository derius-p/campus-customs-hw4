// Search results found by the chat agent, shared so the Products page can show them.
// Kept in sessionStorage so they survive a page refresh within the same browser tab.
import { createContext, useContext, useState, type ReactNode } from 'react'
import type { PageResults } from './api'

export interface ChatResults extends PageResults {
  question: string // the customer message that produced these results
}

interface ChatResultsState {
  results: ChatResults | null
  showResults: (results: ChatResults) => void
  clearResults: () => void
}

const STORAGE_KEY = 'cc-chat-results'
const ChatResultsContext = createContext<ChatResultsState | null>(null)

function loadSaved(): ChatResults | null {
  try {
    const saved = sessionStorage.getItem(STORAGE_KEY)
    return saved ? (JSON.parse(saved) as ChatResults) : null
  } catch {
    return null
  }
}

export function ChatResultsProvider({ children }: { children: ReactNode }) {
  const [results, setResults] = useState<ChatResults | null>(loadSaved)

  const value: ChatResultsState = {
    results,
    showResults: (next) => {
      setResults(next)
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(next))
    },
    clearResults: () => {
      setResults(null)
      sessionStorage.removeItem(STORAGE_KEY)
    },
  }
  return <ChatResultsContext.Provider value={value}>{children}</ChatResultsContext.Provider>
}

export function useChatResults(): ChatResultsState {
  const context = useContext(ChatResultsContext)
  if (!context) throw new Error('useChatResults must be used inside <ChatResultsProvider>')
  return context
}

// URL of the Products page view that shows chat results.
export const CHAT_RESULTS_PATH = '/products?view=chat'
