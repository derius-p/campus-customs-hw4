// Types and fetch helpers for the FastAPI backend (backend/main.py).
// In development Vite proxies /api and /media to http://127.0.0.1:8000.

export interface StockLevel {
  size: string
  quantity: number
}

export interface Product {
  product_id: string
  name: string
  garment_type: string
  description: string
  colors: string[]
  search_tags: string[]
  image_url: string
  image_tone?: 'dark' | 'light' // photo background, for the tile color
  price: number
  total_stock: number
  inventory?: StockLevel[] // only on the single-product endpoint
  // List endpoint only, for the Products page filters:
  category?: string // tidy category, e.g. "Hoodies"
  color_families?: string[] // e.g. ["Navy", "Gray"]
  sizes_in_stock?: string[]
}

export interface FilterOptions {
  categories: string[]
  colors: string[]
  sizes: string[]
}

export const fetchFilterOptions = () => getJson<FilterOptions>('/api/filters')

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(path)
  if (!response.ok) {
    throw new Error(response.status === 404 ? 'Not found' : `Request failed (${response.status})`)
  }
  return response.json() as Promise<T>
}

export const fetchProducts = () => getJson<Product[]>('/api/products')

export const fetchProduct = (productId: string) =>
  getJson<Product>(`/api/products/${encodeURIComponent(productId)}`)

export const formatPrice = (price: number) => `$${price.toFixed(2)}`

// ---- accounts ----------------------------------------------------------------------
// The session lives in an HttpOnly cookie set by the backend; the browser sends it
// automatically, and page scripts can't read it.

export interface User {
  id: number
  name: string
  first_name: string
  last_name: string | null
  email: string
}

export interface RegisterData {
  first_name: string
  last_name: string
  email: string
  password: string
}

async function postJson<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'same-origin',
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  if (!response.ok) {
    const detail = await response.json().then((d) => d.detail).catch(() => null)
    throw new Error(typeof detail === 'string' ? detail : `Request failed (${response.status})`)
  }
  return (response.status === 204 ? undefined : await response.json()) as T
}

export const loginRequest = (email: string, password: string) =>
  postJson<{ user: User }>('/api/auth/login', { email, password }).then((r) => r.user)

export const registerRequest = (data: RegisterData) =>
  postJson<{ user: User }>('/api/auth/register', data).then((r) => r.user)

export const logoutRequest = () => postJson<void>('/api/auth/logout')

export async function fetchCurrentUser(): Promise<User | null> {
  const response = await fetch('/api/auth/me', { credentials: 'same-origin' })
  if (!response.ok) return null
  return ((await response.json()) as { user: User }).user
}

// ---- chat ----------------------------------------------------------------------------

export interface ChatTurn {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatProductCard {
  product_id: string
  name: string
  garment_type: string
  description: string
  price: number
  image_url: string
  image_tone?: 'dark' | 'light'
  url: string
  colors: string[]
  sizes_in_stock: string[]
  total_in_stock: number
}

// Search results the agent sends for the main page (shown on the Products page).
export interface PageResults {
  title: string
  products: ChatProductCard[]
}

export interface ChatReply {
  reply: string
  products: ChatProductCard[] // top picks, shown in the chat
  page_results: PageResults | null // fuller set, shown on the page
}

// What the customer is looking at, sent with each message so the agent knows what "this" means.
export interface PageContext {
  path: string
  product_id: string | null // set on a single-item page
  results_title: string | null // set when viewing chat results
}

// Sends the new message, earlier turns (used for guests), and page context.
export const sendChat = (message: string, history: ChatTurn[], page: PageContext) =>
  postJson<ChatReply & { saved: boolean }>('/api/chat', { message, history, page })

// ---- saved chat history (signed-in customers) ------------------------------------------

export interface HistoryMessage extends ChatTurn {
  products: ChatProductCard[]
  page_results: PageResults | null
  created_at: string
}

export async function fetchChatHistory(): Promise<HistoryMessage[]> {
  const response = await fetch('/api/chat/history', { credentials: 'same-origin' })
  if (!response.ok) return []
  return ((await response.json()) as { messages: HistoryMessage[] }).messages
}

export async function clearChatHistory(): Promise<void> {
  const response = await fetch('/api/chat/history', { method: 'DELETE', credentials: 'same-origin' })
  if (!response.ok) throw new Error("Couldn't clear your chat. Please try again.")
}
