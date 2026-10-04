import { useCallback, useEffect, useRef, useState, useSyncExternalStore } from 'react'
import { audioPort, type AudioStatus } from './audio'
import { createCuePlayer } from './cues'
import { loadFx, prefersReducedMotion, saveFx, type FxPrefs } from './prefs'
import type { Cue } from './voices'

const subscribeAudio = (fn: () => void) => audioPort().subscribe(fn)
const audioStatus = (): AudioStatus => audioPort().status()

/** The room's sound and motion preferences, persisted on this device, and the cue player. */
export function useFx() {
  const [prefs, setPrefs] = useState<FxPrefs>(loadFx)
  // The context starts suspended and resumes a moment after the Start click; follow it.
  const status = useSyncExternalStore(subscribeAudio, audioStatus)
  const latest = useRef(prefs)

  useEffect(() => {
    latest.current = prefs
    audioPort().setVolume(prefs.volume)
    saveFx(prefs)
  }, [prefs])

  const player = useRef<ReturnType<typeof createCuePlayer> | null>(null)
  useEffect(() => {
    const created = createCuePlayer({
      port: audioPort,
      prefs: () => latest.current,
      hidden: () => typeof document !== 'undefined' && document.hidden,
    })
    player.current = created
    return () => {
      created.dispose()
      player.current = null
    }
  }, [])

  const play = useCallback((cue: Cue) => player.current?.play(cue), [])
  const playAll = useCallback((cues: readonly Cue[]) => {
    for (const c of cues) player.current?.play(c)
  }, [])
  const enable = useCallback(async () => void (await audioPort().unlock()), [])
  const update = useCallback((patch: Partial<FxPrefs>) => setPrefs((p) => ({ ...p, ...patch })), [])

  return { prefs, update, play, playAll, enable, status, reduced: prefersReducedMotion(prefs) }
}

export type Fx = ReturnType<typeof useFx>
