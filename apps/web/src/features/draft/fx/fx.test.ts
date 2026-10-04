import { DEFAULT_FX, FX_KEY, loadFx, prefersReducedMotion, saveFx } from './prefs'

afterEach(() => {
  vi.restoreAllMocks()
  vi.unstubAllGlobals()
  localStorage.clear()
})

describe('sound and motion preferences (DRAFT-020 AC4)', () => {
  it('defaults: sound on, 60 %, ticks in the last 10 s', () => {
    expect(loadFx()).toEqual(DEFAULT_FX)
    expect(DEFAULT_FX).toMatchObject({ muted: false, volume: 0.6, tick: 'last10' })
  })

  it('reads back what was saved', () => {
    saveFx({ muted: true, volume: 0.3, tick: 'every', reduceMotion: true })
    expect(loadFx()).toEqual({ muted: true, volume: 0.3, tick: 'every', reduceMotion: true })
  })

  it('repairs a corrupt or out-of-range save field by field', () => {
    localStorage.setItem(FX_KEY, JSON.stringify({ muted: 'yes', volume: 9, tick: 'loud' }))
    expect(loadFx()).toEqual({ ...DEFAULT_FX, volume: 1 })
    localStorage.setItem(FX_KEY, '{nope')
    expect(loadFx()).toEqual(DEFAULT_FX)
  })

  it('falls back to defaults and does not throw when storage is blocked', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('blocked')
    })
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('blocked')
    })
    expect(loadFx()).toEqual(DEFAULT_FX)
    expect(() => saveFx(DEFAULT_FX)).not.toThrow()
  })

  it('reduced motion: the room switch or the device setting', () => {
    expect(prefersReducedMotion({ ...DEFAULT_FX, reduceMotion: true })).toBe(true)
    expect(prefersReducedMotion(DEFAULT_FX)).toBe(false)
    vi.stubGlobal('matchMedia', () => ({ matches: true }))
    expect(prefersReducedMotion(DEFAULT_FX)).toBe(true)
  })
})
