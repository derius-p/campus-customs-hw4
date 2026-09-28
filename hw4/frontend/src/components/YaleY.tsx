// The athletic Yale "Y" from the YALE wordmark in the official Yale Bulldog Blue logo
// (yalebulldogblue.com): heavy slab serifs, symmetric about the vertical center line.
// Traced from the logo and rebuilt as clean straight-line geometry (97% overlap with the
// original), so it stays crisp at any size. It takes the text color (currentColor).
export default function YaleY({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 185 169" aria-hidden="true" focusable="false">
      <path
        fill="currentColor"
        d="M0 0 H80.5 V25 H58.9 L92.5 76 L126.1 25 H104.5 V0 H185 V25 H167.1 L112.5 105 V144 H134.5 V169 H50.5 V144 H72.5 V105 L17.9 25 H0 Z"
      />
    </svg>
  )
}
