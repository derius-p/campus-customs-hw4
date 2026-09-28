import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchProduct, formatPrice, type Product } from '../api'
import { askChat, swatch } from '../chatEvents'
import { CHAT_RESULTS_PATH, useChatResults } from '../chatResults'

const LOW_STOCK = 3

export default function ProductDetail() {
  const { productId = '' } = useParams()
  const { results } = useChatResults()
  const [product, setProduct] = useState<Product | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [size, setSize] = useState<string | null>(null)

  useEffect(() => {
    setProduct(null)
    setError(null)
    setSize(null)
    window.scrollTo({ top: 0 })
    fetchProduct(productId)
      .then(setProduct)
      .catch((err: Error) => setError(err.message))
  }, [productId])

  if (error) {
    return (
      <section className="section">
        <p className="error">{error === 'Not found' ? "We couldn't find that product." : error}</p>
        <Link to="/products">← Back to all products</Link>
      </section>
    )
  }
  if (!product) return <section className="section detail-loading">Loading…</section>

  const inventory = product.inventory ?? []
  const inStock = inventory.filter((s) => s.quantity > 0)
  const selected = inventory.find((s) => s.size === size)
  const stockLine =
    inStock.length === 0
      ? 'Sold out in every size'
      : inStock.length === inventory.length
        ? 'In stock in every size'
        : `In stock in ${inStock.map((s) => s.size).join(', ')}`

  return (
    <section className="section">
      <nav className="breadcrumb" aria-label="Breadcrumb">
        <Link to={results ? CHAT_RESULTS_PATH : '/products'}>
          {results ? `← Back to results: ${results.title}` : '← All products'}
        </Link>
      </nav>
      <div className="product-detail reveal">
        <div className={`product-detail-image tone-${product.image_tone ?? 'light'}`}>
          <img src={product.image_url} alt={product.name} />
        </div>
        <div className="product-detail-info">
          <p className="eyebrow">{product.garment_type}</p>
          <h1>{product.name}</h1>
          <p className="price large">{formatPrice(product.price)}</p>
          <p className={`stock-line ${inStock.length === 0 ? 'out' : ''}`}>
            <span className="stock-dot" /> {stockLine}
          </p>
          <p className="detail-description">{product.description}</p>

          {product.colors.length > 0 && (
            <div className="detail-block">
              <p className="detail-label">Colors</p>
              <div className="color-list">
                {product.colors.map((color) => (
                  <span key={color} className="color-chip">
                    {swatch(color) && <span className="swatch" style={{ background: swatch(color)! }} />}
                    {color}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div className="detail-block">
            <p className="detail-label">
              Size {selected && <span className="muted">· {selected.size}</span>}
            </p>
            {inventory.length > 0 ? (
              <>
                <div className="size-picker" role="radiogroup" aria-label="Choose a size to check stock">
                  {inventory.map((stock) => (
                    <button
                      key={stock.size}
                      role="radio"
                      aria-checked={size === stock.size}
                      className={`size-button ${stock.quantity === 0 ? 'out' : ''} ${size === stock.size ? 'selected' : ''}`}
                      onClick={() => setSize(stock.size)}
                    >
                      {stock.size}
                      {stock.quantity > 0 && stock.quantity <= LOW_STOCK && <span className="size-flag" />}
                    </button>
                  ))}
                </div>
                <p className="size-status" aria-live="polite">
                  {!selected
                    ? 'Choose a size to see how many we have.'
                    : selected.quantity === 0
                      ? `Size ${selected.size} is sold out. Ask our assistant for similar items in ${selected.size}.`
                      : selected.quantity <= LOW_STOCK
                        ? `Only ${selected.quantity} left in ${selected.size}. Don't wait too long!`
                        : `${selected.quantity} in stock in ${selected.size}.`}
                </p>
              </>
            ) : (
              <p className="muted">Stock information isn't available for this item.</p>
            )}
          </div>

          <div className="detail-actions">
            <button
              className="button"
              onClick={() =>
                askChat(
                  selected && selected.quantity === 0
                    ? `Size ${selected.size} is sold out. What similar items do you have in ${selected.size}?`
                    : 'Tell me about this one: what sizes are in stock, and who is it a good fit for?',
                )
              }
            >
              💬 Ask about this item
            </button>
            <span className="muted small">Our assistant sees this page and checks live stock.</span>
          </div>

          <ul className="detail-perks">
            <li>Officially licensed Yale merchandise</li>
            <li>From Campus Customs, 57 Broadway, New Haven</li>
          </ul>
        </div>
      </div>
    </section>
  )
}
