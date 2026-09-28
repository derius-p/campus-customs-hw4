import { useEffect, useState } from 'react'

// The Yale Bulldog Blue wordmark, stacked like the official logo (yalebulldogblue.com):
// YALE in the athletic slab, BULLDOG BLUE in condensed caps, a rule, and a tagline
// spread to the same width. The two lettering images come from the official logo
// (public/brand/, not in the repository) and are tinted with CSS. If they aren't
// installed, the same lockup is set in regular fonts instead.
const TAGLINE = 'By Campus Customs'
const LETTERING = '/brand/yale-wordmark.png'

export default function BrandLockup({ className = '' }: { className?: string }) {
  const [hasArtwork, setHasArtwork] = useState(true)

  useEffect(() => {
    const probe = new Image()
    probe.onerror = () => setHasArtwork(false)
    probe.src = LETTERING
  }, [])

  return (
    <span
      className={`brand-lockup ${hasArtwork ? '' : 'text-only'} ${className}`}
      role="img"
      aria-label="Yale Bulldog Blue by Campus Customs"
    >
      {hasArtwork ? (
        <>
          <span className="lockup-yale" />
          <span className="lockup-bulldog" />
        </>
      ) : (
        <>
          <span className="lockup-yale-text">YALE</span>
          <span className="lockup-bulldog-text">
            <b>BULLDOG</b>BLUE
          </span>
        </>
      )}
      <span className="lockup-rule" />
      <span className="lockup-tagline" aria-hidden="true">
        {TAGLINE.split('').map((ch, i) => (
          <span key={i}>{ch === ' ' ? ' ' : ch}</span>
        ))}
      </span>
    </span>
  )
}
