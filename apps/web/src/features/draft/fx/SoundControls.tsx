import { Button } from '../../../components/ui/Button'
import type { Fx } from './useFx'
import type { TickMode } from './prefs'

const TICKS: [TickMode, string][] = [
  ['last10', 'Last 10 seconds'],
  ['every', 'Every second'],
  ['off', 'Off'],
]

/** Mute, volume, tick style and a reduce-motion switch; the choice stays on this device. */
export function SoundControls({ fx }: { fx: Fx }) {
  const { prefs, update, status, enable } = fx
  return (
    <div className="flex flex-col gap-2" role="group" aria-label="Sound and motion">
      <div className="flex flex-wrap items-center gap-2">
        <Button variant="secondary" onClick={() => update({ muted: !prefs.muted })}>
          {prefs.muted ? 'Sound: off' : 'Sound: on'}
        </Button>
        {!prefs.muted && status === 'suspended' && (
          <Button variant="secondary" onClick={() => void enable()}>
            Sound is off — tap to enable
          </Button>
        )}
      </div>
      <details className="text-subhead">
        <summary className="min-h-11 cursor-pointer py-2.5 text-muted">
          Sound and motion settings
        </summary>
        <div className="flex flex-wrap items-end gap-x-4 gap-y-3 pb-2">
          <label className="flex flex-col gap-1 text-caption tracking-eyebrow text-muted uppercase">
            Volume
            <input
              type="range"
              min={0}
              max={100}
              step={5}
              value={Math.round(prefs.volume * 100)}
              onChange={(e) => update({ volume: Number(e.target.value) / 100 })}
              className="min-h-11 w-40 accent-[var(--accent)]"
            />
          </label>
          <label className="flex flex-col gap-1 text-caption tracking-eyebrow text-muted uppercase">
            Clock ticks
            <select
              value={prefs.tick}
              onChange={(e) => update({ tick: e.target.value as TickMode })}
              className="surface min-h-11 rounded-chip px-2.5 text-subhead text-ink normal-case"
            >
              {TICKS.map(([v, l]) => (
                <option key={v} value={v}>
                  {l}
                </option>
              ))}
            </select>
          </label>
          <label className="flex min-h-11 items-center gap-2 text-subhead text-ink">
            <input
              type="checkbox"
              checked={prefs.reduceMotion}
              onChange={(e) => update({ reduceMotion: e.target.checked })}
            />
            Reduce motion
          </label>
        </div>
      </details>
    </div>
  )
}
