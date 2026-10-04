import { ME, type Practice } from '../practice'
import { URGENT_AT, WARN_AT } from './clock'
import type { AudioPort } from './audio'
import type { FxPrefs, TickMode } from './prefs'
import type { Cue } from './voices'

/** The cues for one owner action: what changed between two practice states (pure). */
export function cuesFor(
  prev: Practice,
  next: Practice,
  opts: { fastForward?: boolean } = {},
): Cue[] {
  const before = prev.room.sales.length
  const after = next.room.sales.length
  if (after < before) return [] // undo
  if (next.phase === 'done' && prev.phase !== 'done') return ['done']
  if (opts.fastForward) return []
  const out: Cue[] = []
  if (after > before) {
    const sale = next.room.sales[before]
    if (sale) out.push(sale.team === ME ? 'soldYou' : 'soldOther')
  } else if (
    prev.lot &&
    next.lot &&
    prev.lot.pid === next.lot.pid &&
    next.lot.price > prev.lot.price
  ) {
    out.push('bid')
    if (next.lot.high !== ME) out.push('outbid')
    return out
  }
  if (next.phase === 'lot' && next.lot && next.lot.pid !== prev.lot?.pid) out.push('nominate')
  return out
}

/** The clock cue at half-second index `h` (h = ceil(ms left / 500)); null when none is due. */
export function tickCue(h: number, mode: TickMode): Cue | null {
  if (mode === 'off' || h <= 0) return null
  const sec = Math.ceil(h / 2)
  const onSecond = h % 2 === 0
  if (sec <= URGENT_AT) return 'tickUrgent'
  if (!onSecond) return null
  return sec <= WARN_AT || mode === 'every' ? 'tick' : null
}

export const CUE_GAP_MS = 150
const MAX_BACKLOG = 3

type PlayerDeps = {
  port: () => AudioPort
  prefs: () => FxPrefs
  hidden: () => boolean
  now?: () => number
}

/**
 * Plays cues through the port, honouring mute and a hidden tab at the moment of playing, one cue per
 * CUE_GAP_MS; a cue that would wait longer than a few slots is dropped (no flood).
 */
export function createCuePlayer({ port, prefs, hidden, now = Date.now }: PlayerDeps) {
  let free = 0
  const pending = new Set<ReturnType<typeof setTimeout>>()
  const allowed = () => !prefs().muted && !hidden() && port().status() === 'running'
  const fire = (cue: Cue) => {
    if (allowed()) port().play(cue)
  }
  return {
    play(cue: Cue) {
      if (!allowed()) return
      const t = now()
      const at = Math.max(t, free)
      if (at - t > MAX_BACKLOG * CUE_GAP_MS) return
      free = at + CUE_GAP_MS
      if (at === t) fire(cue)
      else {
        const id = setTimeout(() => {
          pending.delete(id)
          fire(cue)
        }, at - t)
        pending.add(id)
      }
    },
    /** Drops cues still waiting (the room closed). */
    dispose() {
      pending.forEach(clearTimeout)
      pending.clear()
    },
  }
}
