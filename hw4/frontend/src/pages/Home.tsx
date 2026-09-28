import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchProducts, type Product } from '../api'
import { askChat, openChat } from '../chatEvents'
import ProductCard from '../components/ProductCard'

const FEATURED_IDS = [
  'basic-hoodie-big-yale',
  '2025-yale-vs-harvard-t-shirt',
  'davenport-college-crewneck',
  'benjamin-franklin-1-4-zip',
]
const HERO_IDS = ['district-vit-hoodie-vintage-bulldog', 'basic-hoodie-big-yale', 'boola-boola-t-shirt']

// Category tiles: one representative photo each; counts come from the catalog.
const CATEGORY_TILES = [
  { category: 'Hoodies', image: 'crew-left-chest-hoodie' },
  { category: 'Crewnecks & sweatshirts', image: 'baseball-left-chest-crewneck' },
  { category: 'T-shirts', image: 'boola-boola-t-shirt' },
  { category: 'Quarter-zips', image: 'benjamin-franklin-1-4-zip' },
  { category: 'Jackets & fleece', image: 'brooks-brothers-bomber-jacket-yale' },
]

// "Shop by story" asks the chat, which puts matching products on the page.
const STORIES = [
  { title: 'Your residential college', text: 'Crests and colors for your college, from Berkeley to Trumbull.', ask: 'Show me residential college gear', icon: '🏛️' },
  { title: 'Game day', text: 'For The Game and every Saturday at the Bowl.', ask: 'Show me game day and Yale sports gear', icon: '🏈' },
  { title: 'For the whole family', text: 'Yale Mom, Dad, Grandpa, and more.', ask: 'Show me gifts for family members', icon: '💙' },
  { title: 'Grad & professional schools', text: 'SOM, Law, Medicine, Art, and more.', ask: 'Show me graduate and professional school apparel', icon: '🎓' },
]

export default function Home() {
  const [products, setProducts] = useState<Product[]>([])

  useEffect(() => {
    fetchProducts()
      .then(setProducts)
      .catch(() => setProducts([]))
  }, [])

  const byId = new Map(products.map((p) => [p.product_id, p]))
  const featured = FEATURED_IDS.map((id) => byId.get(id)).filter(Boolean) as Product[]
  const hero = HERO_IDS.map((id) => byId.get(id)).filter(Boolean) as Product[]
  const countIn = (category: string) => products.filter((p) => p.category === category).length

  return (
    <>
      <section className="hero">
        <div className="hero-copy reveal">
          <p className="eyebrow light">Officially licensed · New Haven, CT</p>
          <h1>
            Wear your <em>Yale</em> story.
          </h1>
          <p className="hero-lede">
            Hoodies, crewnecks, tees, and quarter-zips for students, alumni, and the families cheering them on, from
            the residential colleges to the sidelines.
          </p>
          <div className="hero-actions">
            <Link to="/products" className="button light">
              Shop All
            </Link>
            <button className="button ghost" onClick={openChat}>
              💬 Ask our assistant
            </button>
          </div>
        </div>
        <div className="hero-collage" aria-hidden="true">
          {hero.map((p, i) => (
            <div key={p.product_id} className={`hero-photo photo-${i} tone-${p.image_tone ?? 'light'}`}>
              <img src={p.image_url} alt="" />
            </div>
          ))}
        </div>
        <div className="pennant-stripes" aria-hidden="true" />
      </section>

      <section className="section">
        <div className="section-head reveal">
          <p className="eyebrow">Shop by category</p>
          <h2>Find your fit</h2>
        </div>
        <div className="category-grid">
          {CATEGORY_TILES.map((tile, i) => {
            const photo = byId.get(tile.image)
            return (
              <Link
                key={tile.category}
                to={`/products?category=${encodeURIComponent(tile.category)}`}
                className={`category-tile reveal tone-${photo?.image_tone ?? 'light'}`}
                style={{ '--i': i } as React.CSSProperties}
              >
                {photo && <img src={photo.image_url} alt="" loading="lazy" />}
                <span className="category-name">{tile.category}</span>
                {products.length > 0 && <span className="category-count">{countIn(tile.category)} styles</span>}
              </Link>
            )
          })}
        </div>
      </section>

      <section className="section">
        <div className="section-head reveal">
          <p className="eyebrow">Fan favorites 💙</p>
          <h2>Campus classics</h2>
          <Link to="/products" className="section-link">
            Shop all {products.length || ''} →
          </Link>
        </div>
        <div className="product-grid">
          {featured.map((product, i) => (
            <ProductCard key={product.product_id} index={i} product={{ ...product, label: product.category }} />
          ))}
        </div>
      </section>

      <section className="section stories">
        <div className="section-head reveal">
          <p className="eyebrow">Shop by story</p>
          <h2>Who are you cheering for?</h2>
          <p className="muted">Pick one and our assistant will pull the matching gear onto the page.</p>
        </div>
        <div className="story-grid">
          {STORIES.map((story, i) => (
            <button
              key={story.title}
              className="story-card reveal"
              style={{ '--i': i } as React.CSSProperties}
              onClick={() => askChat(story.ask)}
            >
              <span className="story-icon" aria-hidden="true">
                {story.icon}
              </span>
              <span className="story-title">{story.title}</span>
              <span className="story-text">{story.text}</span>
              <span className="story-cta">Show me →</span>
            </button>
          ))}
        </div>
      </section>

      <section className="section trust-strip reveal">
        <div>
          <strong>Officially licensed</strong>
          <span>Authentic Yale apparel from a New Haven shop.</span>
        </div>
        <div>
          <strong>Live stock by size</strong>
          <span>See exactly what's available before you decide.</span>
        </div>
        <div>
          <strong>Help that knows the shelves</strong>
          <span>Our assistant checks real stock and suggests alternatives.</span>
        </div>
      </section>
    </>
  )
}
