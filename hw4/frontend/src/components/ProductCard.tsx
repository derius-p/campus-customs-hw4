import { Link } from 'react-router-dom'
import { formatPrice } from '../api'
import { swatch } from '../chatEvents'

// The fields a grid card needs; both catalog products and chat results provide them.
export interface CardProduct {
  product_id: string
  name: string
  price: number
  image_url: string
  image_tone?: 'dark' | 'light'
  description: string
  total_stock: number
  label?: string // small line above the name, e.g. the category
  colors?: string[]
  sizes_in_stock?: string[]
}

const ALL_SIZES = 6

function badge(product: CardProduct): { text: string; kind: string } | null {
  if (product.total_stock === 0) return { text: 'Sold out', kind: 'soldout' }
  const sizes = product.sizes_in_stock?.length
  if (sizes !== undefined && sizes <= 2) return { text: `Only ${sizes === 1 ? '1 size' : '2 sizes'} left`, kind: 'low' }
  if (sizes === ALL_SIZES) return { text: 'All sizes', kind: 'full' }
  return null
}

export default function ProductCard({ product, index = 0 }: { product: CardProduct; index?: number }) {
  const tag = badge(product)
  const swatches = [...new Set((product.colors ?? []).map(swatch).filter(Boolean))].slice(0, 5) as string[]
  return (
    <Link
      to={`/products/${product.product_id}`}
      className="product-card reveal"
      style={{ '--i': index % 8 } as React.CSSProperties}
    >
      <div className={`product-card-image tone-${product.image_tone ?? 'light'}`}>
        <img src={product.image_url} alt={product.name} loading="lazy" />
        {tag && <span className={`badge badge-${tag.kind}`}>{tag.text}</span>}
        <span className="quick-view">View details →</span>
      </div>
      <div className="product-card-body">
        {product.label && <p className="card-label">{product.label}</p>}
        <h3>{product.name}</h3>
        <p className="short-description">{product.description}</p>
        <div className="card-footer">
          <span className="price">{formatPrice(product.price)}</span>
          {swatches.length > 0 && (
            <span className="swatches" aria-label={`Colors: ${product.colors?.join(', ')}`}>
              {swatches.map((color) => (
                <span key={color} className="swatch" style={{ background: color }} />
              ))}
            </span>
          )}
        </div>
      </div>
    </Link>
  )
}
