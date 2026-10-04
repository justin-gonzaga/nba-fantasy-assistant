// Colour is never the only signal: an icon and words go with it (frontend standard).
export function winState(p: number): { icon: string; word: string; tone: string } {
  if (p >= 0.6) return { icon: '▲', word: 'Winning', tone: 'text-win' }
  if (p <= 0.4) return { icon: '▼', word: 'Losing', tone: 'text-lose' }
  return { icon: '●', word: 'Toss-up', tone: 'text-even' }
}

export function WinLabel({ p, showPct = false }: { p: number; showPct?: boolean }) {
  const s = winState(p)
  return (
    <span className={`text-subhead font-semibold whitespace-nowrap ${s.tone}`}>
      <span aria-hidden="true">{s.icon} </span>
      {showPct ? `${s.word} ${Math.round(p * 100)}%` : s.word}
    </span>
  )
}
