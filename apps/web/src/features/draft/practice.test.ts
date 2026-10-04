import values from './fixtures/values-2026-27.json'
import { teamState, type DraftPlayer } from './live'
import {
  ME,
  bid,
  bidExpired,
  fitLine,
  needs,
  verdict,
  fastForward,
  myAdvice,
  myState,
  nominate,
  nominateExpired,
  pass,
  resume,
  start,
  undoLast,
  type Practice,
  type Settings,
} from './practice'

const players = values.players as DraftPlayer[]
const settings: Settings = { seed: 5, styles: 'mix', punted: null, pace: 'real' }

/** The most valuable player still available. */
const firstAvailable = (p: Practice) => {
  const taken = new Set(p.room.sales.map((x) => x.pid))
  return players.find((x) => !taken.has(x.id)) as DraftPlayer
}

/** Passes on every lot until it's the owner's turn to nominate. */
function toMyNomination(p: Practice): Practice {
  let cur = p
  while (cur.phase === 'lot') cur = pass(cur)
  return cur
}

describe('practice draft (DRAFT-014)', () => {
  it('starts with a lot the owner can bid on, or the owner nominating', () => {
    const p = start(players, settings)
    expect(['lot', 'nominate']).toContain(p.phase)
    if (p.phase === 'lot') {
      expect(p.lot?.price).toBeGreaterThanOrEqual(1)
      expect(p.lot?.high).not.toBe(ME)
    }
  })

  it('an owner nomination opens the lot and rivals bid it up to their settling point', () => {
    const p = toMyNomination(start(players, settings))
    expect(p.phase).toBe('nominate')
    const top = firstAvailable(p)
    const lot = nominate(p, top.id).lot
    expect(lot?.pid).toBe(top.id)
    const walk = Object.values(lot?.walk ?? {}).sort((a, b) => b - a)
    // the top rival holds the lot at the second-best walk-away + 1 (or $1 + 1 when only one wants it)
    expect(lot?.price).toBe(Math.min(walk[0] as number, Math.max(1, walk[1] as number) + 1))
  })

  it('blocks a bid over the max bid, with the reason', () => {
    const p = start(players, settings)
    const lot = toMyNomination(p)
    const opened = nominate(lot, firstAvailable(lot).id)
    const r = bid(opened, 200)
    // 14 open spots: $200 − $1 for each of the other 13
    expect(r.error).toMatch(/Your max bid is \$187/)
    expect(r.practice).toBe(opened)
  })

  it('a winning bid sells at once when no rival will go higher', () => {
    const q = toMyNomination(start(players, settings))
    const pick = firstAvailable(q)
    const p = nominate(q, pick.id)
    const top = Math.max(...Object.values(p.lot?.walk ?? {}))
    const r = bid(p, top + 1)
    expect(r.error).toBeNull()
    const mine = r.practice.room.sales.filter((s) => s.team === ME)
    expect(mine).toEqual([{ pid: pick.id, team: ME, price: top + 1 }])
  })

  it('timer expiry: the nomination goes to the top target; a bid timer sells to the high bidder', () => {
    const p = toMyNomination(start(players, settings))
    const target = myAdvice(p).targets[0]
    const opened = nominateExpired(p)
    expect(opened.lot?.pid).toBe(target)
    const high = opened.lot?.high
    const sold = bidExpired(opened)
    expect(sold.room.sales.at(-1)).toMatchObject({ pid: target, team: high })
  })

  it('undo returns to before the last lot the owner took part in', () => {
    const q = toMyNomination(start(players, settings))
    const p = nominate(q, firstAvailable(q).id)
    const before = p.undo.at(-1)?.sales.length
    const top = Math.max(...Object.values(p.lot?.walk ?? {}))
    const won = bid(p, top + 1).practice
    expect(won.room.sales.filter((s) => s.team === ME)).toHaveLength(1)
    const undone = undoLast(won)
    expect(undone.room.sales).toHaveLength(before as number)
    expect(undone.room.sales.filter((s) => s.team === ME)).toHaveLength(0)
  })

  it('"sim the rest" finishes the draft with a full roster for the owner', () => {
    const done = fastForward(start(players, settings), false)
    expect(done.phase).toBe('done')
    expect(done.room.sales).toHaveLength(224)
    expect(myState(done).count).toBe(14)
  }, 30_000)

  it('"sim to my next nomination" stops at the owner\'s turn', () => {
    const p = fastForward(start(players, settings), true)
    expect(p.phase === 'nominate' || p.phase === 'done').toBe(true)
  })

  it('resume rebuilds the same room from the saved sales', () => {
    let p = start(players, settings)
    for (let i = 0; i < 20 && p.phase !== 'done'; i++)
      p = p.phase === 'lot' ? pass(p) : nominateExpired(p)
    const restored = resume(players, { settings, sales: p.room.sales, turn: p.room.turn })
    expect(restored.room.sales).toEqual(p.room.sales)
    expect(teamState(restored.room.sales, restored.room.teams, 200, 14)).toEqual(
      teamState(p.room.sales, p.room.teams, 200, 14),
    )
    // an owner-nominated lot reopens as the owner's nomination; a rival's lot reopens as the same lot
    if (p.phase === 'nominate' || p.lot?.nominatedBy === ME) expect(restored.phase).toBe('nominate')
    else expect(restored.lot?.pid).toBe(p.lot?.pid)
  })
})

describe('glanceable advice (DRAFT-016)', () => {
  // A tiny 3-category world is enough for the helpers: weights and z come from the engine's shapes.
  it('needs follow the roster: neediest 3 (weight > 1), strongest 2 (weight < 1), punt excluded', () => {
    const w = [0.6, 1.4, 1.2, 1.0, 1.3, 0.8, 1.0, 0, 1.1] // PTS strong, REB needy, FT% punted
    const n = needs(w, 7)
    expect(n.need.map((c) => c.label)).toEqual(['REB', 'BLK', 'AST'])
    expect(n.covered.map((c) => c.label)).toEqual(['PTS', '3PM'])
    expect(n.punted).toBe('FT%')
    const fresh = needs(
      Array.from({ length: 9 }, () => 1),
      null,
    )
    expect(fresh.need).toEqual([])
    expect(fresh.covered).toEqual([])
  })

  it('fit line names the needs a player fills, or what he overlaps', () => {
    const w = [0.6, 1.4, 1.2, 1.0, 1.3, 0.8, 1.0, 1.0, 1.1]
    // strong in REB and BLK (needs), fit above 1.03
    expect(fitLine([0.1, 2, 0.2, 0, 1.5, 0, 0, 0, 0], w, 1.12)).toBe('Fits your needs: REB, BLK')
    // strong in PTS where you're covered, fit below 0.97
    expect(fitLine([2.5, 0, 0, 0, 0, 0.4, 0, 0, 0], w, 0.9)).toBe('Overlaps your team: PTS')
    expect(fitLine([0.3, 0.3, 0, 0, 0, 0, 0, 0, 0], w, 1.0)).toBe('Neutral fit')
    // TOV is needy (1.1) but 4th, so not one of the 3 listed needs: the line stays general
    expect(fitLine([0, 0, 0, 0, 0, 0, 0, 0, 2], w, 1.05)).toBe('Fits your build')
    // AST is a listed need (3rd): named
    expect(fitLine([0, 0, 2, 0, 0, 0, 0, 0, 0], w, 1.05)).toBe('Fits your needs: AST')
  })

  it('verdict follows the next bid against the ceiling', () => {
    expect(verdict(10, 34, true)).toBe('good') // next bid $11 ≤ 85 % of $34
    expect(verdict(30, 34, true)).toBe('near') // $31 ≤ $34
    expect(verdict(34, 34, true)).toBe('pass') // $35 > $34
    expect(verdict(1, 0, true)).toBe('cant')
    expect(verdict(1, 30, false)).toBe('cant')
  })
})
