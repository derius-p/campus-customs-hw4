import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { formatPrice, type ChatProductCard } from '../api'

// A horizontal row of product cards with soft arrows that appear when there's more to scroll.
export default function ChatCardScroller({ products }: { products: ChatProductCard[] }) {
  const rowRef = useRef<HTMLDivElement>(null)
  const [canLeft, setCanLeft] = useState(false)
  const [canRight, setCanRight] = useState(false)

  function updateArrows() {
    const row = rowRef.current
    if (!row) return
    setCanLeft(row.scrollLeft > 4)
    setCanRight(row.scrollLeft + row.clientWidth < row.scrollWidth - 4)
  }

  useEffect(() => {
    updateArrows()
    const row = rowRef.current
    if (!row) return
    const observer = new ResizeObserver(updateArrows)
    observer.observe(row)
    return () => observer.disconnect()
  }, [products])

  function scrollBy(direction: 1 | -1) {
    const row = rowRef.current
    if (row) row.scrollBy({ left: direction * row.clientWidth * 0.8, behavior: 'smooth' })
  }

  return (
    <div className="chat-scroller">
      {canLeft && (
        <button className="scroll-arrow left" onClick={() => scrollBy(-1)} aria-label="Scroll left">
          ‹
        </button>
      )}
      <div className="chat-cards" ref={rowRef} onScroll={updateArrows}>
        {products.map((product) => (
          <Link key={product.product_id} to={product.url} className="chat-card">
            <img src={product.image_url} alt={product.name} />
            <span className="chat-card-name">{product.name}</span>
            <span className="chat-card-price">{formatPrice(product.price)}</span>
          </Link>
        ))}
      </div>
      {canRight && (
        <button className="scroll-arrow right" onClick={() => scrollBy(1)} aria-label="Scroll right">
          ›
        </button>
      )}
    </div>
  )
}
