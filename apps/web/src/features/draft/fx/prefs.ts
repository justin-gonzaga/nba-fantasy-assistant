export type TickMode = 'off' | 'last10' | 'every'

export type FxPrefs = {
  muted: boolean
  /** 0..1 */
  volume: number
  tick: TickMode
  reduceMotion: boolean
}

export const FX_KEY = 'draft-fx-v1'
export const DEFAULT_FX: FxPrefs = {
  muted: false,
  volume: 0.6,
  tick: 'last10',
  reduceMotion: false,
}

export function loadFx(): FxPrefs {
  try {
    const raw = JSON.parse(localStorage.getItem(FX_KEY) ?? 'null') as Partial<FxPrefs> | null
    if (!raw || typeof raw !== 'object') return DEFAULT_FX
    return {
      muted: typeof raw.muted === 'boolean' ? raw.muted : DEFAULT_FX.muted,
      volume:
        typeof raw.volume === 'number' && Number.isFinite(raw.volume)
          ? Math.min(1, Math.max(0, raw.volume))
          : DEFAULT_FX.volume,
      tick:
        raw.tick === 'off' || raw.tick === 'last10' || raw.tick === 'every' ? raw.tick : 'last10',
      reduceMotion:
        typeof raw.reduceMotion === 'boolean' ? raw.reduceMotion : DEFAULT_FX.reduceMotion,
    }
  } catch {
    return DEFAULT_FX
  }
}

export function saveFx(prefs: FxPrefs): void {
  try {
    localStorage.setItem(FX_KEY, JSON.stringify(prefs))
  } catch {
    // storage blocked: the choice lasts for this visit only
  }
}

/** Reduced motion from the device setting or the room's own switch. */
export function prefersReducedMotion(prefs: FxPrefs): boolean {
  if (prefs.reduceMotion) return true
  try {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches
  } catch {
    return false
  }
}
