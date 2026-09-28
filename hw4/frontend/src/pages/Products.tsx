import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { fetchProducts, type Product } from '../api'
import { CHAT_RESULTS_PATH, useChatResults } from '../chatResults'
import ProductCard from '../components/ProductCard'
import ProductFilters, { applyFilters, hasActiveFilters } from '../components/ProductFilters'

export default function Products() {
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const { results } = useChatResults()
  const [products, setProducts] = useState<Product[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  // /products?view=chat shows what the chat agent found; plain /products shows everything.
  const showingChat = params.get('view') === 'chat' && results !== null

  useEffect(() => {
    if (showingChat || products) return
    fetchProducts()
      .then(setProducts)
      .catch((err: Error) => setError(err.message))
  }, [showingChat, products])

  const visible = products ? applyFilters([...products], params) : []

  if (showingChat) {
    return (
      <section className="section">
        <div className="chat-results-header">
          <div>
            <p className="eyebrow">💬 From your chat</p>
            <h1>{results.title}</h1>
            <p className="muted">
              {results.products.length} {results.products.length === 1 ? 'product' : 'products'} for “{results.question}”
            </p>
          </div>
          <button className="button secondary" onClick={() => navigate('/products')}>
            Show all products
          </button>
        </div>
        <div className="product-grid">
          {results.products.map((product, i) => (
            <ProductCard
              key={product.product_id}
              index={i}
              product={{ ...product, total_stock: product.total_in_stock, label: product.garment_type }}
            />
          ))}
        </div>
      </section>
    )
  }

  return (
    <section className="section">
      <p className="eyebrow">The full collection</p>
      <h1>Shop All</h1>
      {error && <p className="error">Couldn't load products: {error}. Is the backend running?</p>}
      {!products && !error && <p>Loading products…</p>}
      {products && (
        <>
          <ProductFilters />
          <p className="muted">
            {hasActiveFilters(params)
              ? `Showing ${visible.length} of ${products.length} products`
              : `${products.length} products`}
            {results && (
              <>
                {' · '}
                <button className="link-button" onClick={() => navigate(CHAT_RESULTS_PATH)}>
                  Back to your chat results ({results.title})
                </button>
              </>
            )}
          </p>
          {visible.length === 0 ? (
            <p className="empty-state">
              No products match these filters. Try clearing a filter, or ask our assistant in the chat.
            </p>
          ) : (
            <div className="product-grid">
              {visible.map((product, i) => (
                <ProductCard key={product.product_id} index={i} product={{ ...product, label: product.category }} />
              ))}
            </div>
          )}
        </>
      )}
    </section>
  )
}
