import { useState } from 'react'

/** "Nikola Jokić" → "NJ": the first and last word's first letters. */
export function initials(name: string): string {
  const words = name.split(/\s+/).filter(Boolean)
  const first = words[0]?.[0] ?? ''
  const last = words.length > 1 ? (words[words.length - 1]?.[0] ?? '') : ''
  return (first + last).toUpperCase()
}

/** A round photo, or the initials when it can't load (new player, CDN or network down). Decorative. */
export function Avatar({ src, name, size }: { src: string; name: string; size: number }) {
  // Keyed by the source, so a new source gets a fresh try.
  const [failedSrc, setFailedSrc] = useState<string | null>(null)
  const box = { width: size, height: size }
  if (failedSrc === src)
    return (
      <span
        aria-hidden="true"
        style={box}
        className="flex shrink-0 items-center justify-center rounded-full bg-accent-tint text-subhead font-semibold text-accent-ink"
      >
        {initials(name)}
      </span>
    )
  return (
    <img
      src={src}
      alt=""
      loading="lazy"
      decoding="async"
      style={box}
      onError={() => setFailedSrc(src)}
      className="shrink-0 rounded-full bg-surface-2 object-cover object-top"
    />
  )
}
