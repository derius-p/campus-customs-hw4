// Lets any page open the chat or ask it a question (e.g. "Shop by story" tiles,
// "Ask about this item"). ChatWidget listens for these events.

export const OPEN_CHAT_EVENT = 'cc:open-chat'
export const ASK_CHAT_EVENT = 'cc:ask'

export function openChat() {
  window.dispatchEvent(new Event(OPEN_CHAT_EVENT))
}

export function askChat(message: string) {
  window.dispatchEvent(new CustomEvent<string>(ASK_CHAT_EVENT, { detail: message }))
}

// Color names in the catalog -> swatch colors for product cards.
const SWATCHES: [string, string][] = [
  ['navy', '#14254a'], ['royal', '#2a52be'], ['light blue', '#8fb8e8'], ['blue', '#286dc0'],
  ['charcoal', '#4a4f57'], ['dark heather', '#5c6068'], ['heather', '#a7abb1'], ['light gray', '#cfd3d8'], ['gray', '#9aa0a8'],
  ['cream', '#f3ead7'], ['ivory', '#f6f1e3'], ['white', '#ffffff'], ['black', '#161616'],
  ['coral', '#e07a6b'], ['red', '#b5121b'], ['gold', '#c9a227'], ['yellow', '#f2c94c'], ['green', '#2e6b3f'],
]

export function swatch(color: string): string | null {
  const c = color.toLowerCase()
  if (c.includes('multi')) return null
  return SWATCHES.find(([name]) => c.includes(name))?.[1] ?? null
}
