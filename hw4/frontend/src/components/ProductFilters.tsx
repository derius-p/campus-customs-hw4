// Filter and sort controls for the Products page. State lives in the URL
// (?category=Hoodies&size=XL&sort=price-asc) so Back, refresh, and sharing keep it.
import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { fetchFilterOptions, type FilterOptions, type Product } from '../api'

export const PRICE_OPTIONS = [
  { value: '', label: 'Any price' },
  { value: '40', label: 'Under $40' },
  { value: '60', label: 'Under $60' },
  { value: '75', label: 'Under $75' },
]

export const SORT_OPTIONS = [
  { value: '', label: 'Name (A–Z)' },
  { value: 'price-asc', label: 'Price: low to high' },
  { value: 'price-desc', label: 'Price: high to low' },
  { value: 'stock', label: 'Most in stock' },
]

const FILTER_KEYS = ['category', 'color', 'size', 'max', 'sort'] as const

export function applyFilters(products: Product[], params: URLSearchParams): Product[] {
  const category = params.get('category')
  const color = params.get('color')
  const size = params.get('size')
  const max = Number(params.get('max')) || null
  const result = products.filter(
    (p) =>
      (!category || p.category === category) &&
      (!color || p.color_families?.includes(color)) &&
      (!size || p.sizes_in_stock?.includes(size)) &&
      (!max || p.price < max),
  )
  switch (params.get('sort')) {
    case 'price-asc':
      return result.sort((a, b) => a.price - b.price || a.name.localeCompare(b.name))
    case 'price-desc':
      return result.sort((a, b) => b.price - a.price || a.name.localeCompare(b.name))
    case 'stock':
      return result.sort((a, b) => b.total_stock - a.total_stock)
    default:
      return result.sort((a, b) => a.name.localeCompare(b.name))
  }
}

export function hasActiveFilters(params: URLSearchParams): boolean {
  return FILTER_KEYS.some((key) => key !== 'sort' && params.get(key))
}

export default function ProductFilters() {
  const [params, setParams] = useSearchParams()
  const [options, setOptions] = useState<FilterOptions | null>(null)

  useEffect(() => {
    fetchFilterOptions().then(setOptions).catch(() => setOptions(null))
  }, [])

  function update(key: (typeof FILTER_KEYS)[number], value: string) {
    const next = new URLSearchParams(params)
    if (value) next.set(key, value)
    else next.delete(key)
    setParams(next, { replace: true })
  }

  function clearAll() {
    const next = new URLSearchParams(params)
    FILTER_KEYS.forEach((key) => key !== 'sort' && next.delete(key))
    setParams(next, { replace: true })
  }

  const select = (key: (typeof FILTER_KEYS)[number], label: string, choices: { value: string; label: string }[]) => (
    <label className="filter">
      <span>{label}</span>
      <select value={params.get(key) ?? ''} onChange={(e) => update(key, e.target.value)}>
        {choices.map((c) => (
          <option key={c.value} value={c.value}>
            {c.label}
          </option>
        ))}
      </select>
    </label>
  )

  const list = (all: string, values: string[] = []) => [{ value: '', label: all }, ...values.map((v) => ({ value: v, label: v }))]

  return (
    <div className="filter-bar" role="search" aria-label="Filter products">
      {select('category', 'Category', list('All categories', options?.categories))}
      {select('color', 'Color', list('Any color', options?.colors))}
      {select('size', 'In stock in', list('Any size', options?.sizes))}
      {select('max', 'Price', PRICE_OPTIONS)}
      {select('sort', 'Sort by', SORT_OPTIONS)}
      {hasActiveFilters(params) && (
        <button className="link-button clear-filters" onClick={clearAll}>
          Clear filters
        </button>
      )}
    </div>
  )
}
