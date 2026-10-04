// Live auction helper arithmetic: a line-for-line mirror of fantasy_models/draft_live.py.
// A parity test (apps/pipeline/tests/test_draft_live_parity.py) runs both on the same picks.
const LIVE = (() => {
  const FIT_CAP = 0.25, FIT_ALPHA = 0.5, W_LO = 0.5, W_HI = 1.5, HINT_POOL = 60, HINT_FIT_BELOW = 0.95;
  const clamp = (x, lo, hi) => Math.min(hi, Math.max(lo, x));
  function teamState(picks, teams, budget, slots) {
    const out = {};
    for (const t of teams) out[t] = { spent: 0, count: 0 };
    for (const p of picks) { out[p.team].spent += p.price; out[p.team].count += 1; }
    for (const t of teams) {
      const s = out[t];
      s.left = budget - s.spent; s.open = slots - s.count;
      s.max_bid = s.open > 0 ? Math.max(0, s.left - Math.max(0, s.open - 1)) : 0;
    }
    return out;
  }
  function inflation(players, taken, state) {
    let money = 0, open = 0;
    // Only teams that can still buy count: a full roster's leftover cash is dead money (review).
    for (const s of Object.values(state)) { if (s.open > 0) money += s.left; open += s.open; }
    const left = players.filter(p => !taken.has(p.id)).map(p => p.usd).sort((a, b) => b - a).slice(0, open);
    const above = left.reduce((a, u) => a + Math.max(0, u - 1), 0);
    if (open <= 0 || above <= 0) return 1;
    return Math.max(0, money - open) / above;
  }
  function categoryWeights(byId, mine, punted) {
    const n = byId[Object.keys(byId)[0]].z.length;
    const w = [];
    for (let i = 0; i < n; i++) {
      if (punted.has(i)) { w.push(0); continue; }
      if (!mine.length) { w.push(1); continue; }
      let s = 0; for (const p of mine) s += byId[p].z[i];
      w.push(clamp(1 - FIT_ALPHA * (s / mine.length), W_LO, W_HI));
    }
    return w;
  }
  function fitMultiplier(z, weights, punted) {
    let base = 0, fit = 0;
    for (let i = 0; i < z.length; i++) { if (!punted.has(i)) base += z[i]; fit += weights[i] * z[i]; }
    if (base <= 0) return 1;
    return clamp(fit / base, 1 - FIT_CAP, 1 + FIT_CAP);
  }
  const byKey = (f) => (a, b) => (f(a) - f(b)) || (a.id < b.id ? -1 : a.id > b.id ? 1 : 0);
  function advise(players, picks, teams, me, budget, slots, punted) {
    punted = punted || new Set();
    const byId = {}; for (const p of players) byId[p.id] = p;
    const taken = new Set(picks.map(p => p.pid));
    const state = teamState(picks, teams, budget, slots);
    const infl = inflation(players, taken, state);
    const mine = picks.filter(p => p.team === me).map(p => p.pid);
    const weights = categoryWeights(byId, mine, punted);
    const myMax = state[me].max_bid;
    const rows = [];
    for (const p of players) {
      if (taken.has(p.id)) continue;
      const adj = 1 + (p.usd - 1) * infl;
      const fit = fitMultiplier(p.z, weights, punted);
      const ceiling = myMax >= 1 ? Math.trunc(Math.min(myMax, adj * fit)) : 0;
      rows.push({ id: p.id, adj, fit, ceiling });
    }
    const targets = [...rows].sort(byKey(r => -r.adj * r.fit)).slice(0, 10);
    const top = [...rows].sort(byKey(r => -r.adj)).slice(0, HINT_POOL);
    const hints = top.filter(r => r.fit < HINT_FIT_BELOW).sort(byKey(r => -r.adj * (1 - r.fit))).slice(0, 5);
    const pmap = {}; for (const r of rows) pmap[r.id] = r;
    return { inflation: infl, weights, my_max_bid: myMax, teams: state, players: pmap,
             targets: targets.map(r => r.id), hints: hints.map(r => r.id) };
  }
  return { teamState, inflation, categoryWeights, fitMultiplier, advise };
})();
if (typeof module !== "undefined") module.exports = LIVE;
