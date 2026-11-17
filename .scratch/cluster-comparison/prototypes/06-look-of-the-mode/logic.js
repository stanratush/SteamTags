// PROTOTYPE (throwaway) for ticket 06. The matching rules of tickets 02, 04 and 05, in the browser.
// Data: window.DATA from export.py. No persistence: state lives in memory and the URL.
"use strict";
const PALETTE = ["#5b7fb0", "#d08a4e", "#6a9c64", "#c0646a", "#6ea8a5", "#c9ad4f", "#9a7fa8", "#d79aa4", "#8f7766",
  "#86aeb0", "#c27d9b", "#93bf88", "#a8945a", "#5f9592", "#e3b9c8", "#837b78"];
const ONE_TAG = "#b8b8b8";
const DS_HUE = { overall: "#3d4555", puzzle: "#7a4fb0", rpg: "#b0503d", strategy: "#2f7d5b", simulation: "#2a6fa8" };
const NAME = (t) => DATA.names[String(t)] || String(t);
const clusterColor = (label, size) => size < 2 ? ONE_TAG : PALETTE[(parseInt(label.slice(1), 10) - 1) % PALETTE.length];

// --- the comparison's state (in memory) ---
const S = {
  include: Object.fromEntries(DATA.datasets.map(d => [d.key, true])),
  cell: Object.fromEntries(DATA.datasets.map(d => [d.key, d.star])), // "g,s"
  source: Object.fromEntries(DATA.datasets.map(d => [d.key, d.star ? "pick" : "none"])), // pick | cell | hand | none
  hand: {}, // key -> {g, s, gamma} typed by hand (prototype keeps the last cell's partition)
  min: 0.10,
  pair: ["overall", "strategy"],
  match: null, // [labelA, labelB]
  cluster: null, // [datasetKey, label] focus in some variants
};
const DS = (k) => DATA.datasets.find(d => d.key === k);
const included = () => DATA.datasets.filter(d => S.include[d.key]);

const _stateCache = {};
function state(k) {
  const d = DS(k), key = S.cell[k];
  const id = k + "|" + key;
  if (_stateCache[id]) return _stateCache[id];
  const c = d.cells[key];
  const label = new Map(), clusters = new Map();
  c.nodes.forEach((t, i) => {
    const l = c.label[i]; label.set(t, l);
    if (!clusters.has(l)) clusters.set(l, new Set());
    clusters.get(l).add(t);
  });
  const all = [...clusters.entries()].map(([l, m]) => ({ ds: k, label: l, members: m, size: m.size }))
    .sort((a, b) => parseInt(a.label.slice(1)) - parseInt(b.label.slice(1)));
  const st = { key: k, d, cell: c, nodes: new Set(c.nodes), edged: new Set(c.edged), label, clusters: all,
    multi: all.filter(x => x.size >= 2), one: all.filter(x => x.size < 2),
    games: d.games, gameById: new Map(d.games.map(g => [g.a, g])) };
  return (_stateCache[id] = st);
}

function matches(A, B) {
  const common = new Set([...A.nodes].filter(t => B.nodes.has(t)));
  const N = common.size, rows = [];
  for (const ca of A.multi) for (const cb of B.multi) {
    const shared = [...ca.members].filter(t => cb.members.has(t));
    const n = shared.length;
    if (!n) continue;
    const a = ca.size, b = cb.size;
    const a2 = [...ca.members].filter(t => common.has(t)).length, b2 = [...cb.members].filter(t => common.has(t)).length;
    const exp = a2 * b2 / N;
    rows.push({ ca, cb, a, b, n, a2, b2, N, shared, j: n / (a + b - n), pa: n / a, pb: n / b,
      jc: (a2 >= 2 && b2 >= 2) ? n / (a2 + b2 - n) : null, exp, lift: n / exp,
      onlyA: [...ca.members].filter(t => !cb.members.has(t)), onlyB: [...cb.members].filter(t => !ca.members.has(t)) });
  }
  return rows.sort((x, y) => y.j - x.j);
}

// where a Tag of A's Cluster (not shared with the match) sits in B: another Cluster, isolated, not in network
function whereInB(t, B) {
  if (!B.nodes.has(t)) return { kind: "absent" };
  const l = B.label.get(t), c = B.clusters.find(x => x.label === l);
  return c.size >= 2 ? { kind: "other", label: l } : { kind: "isolated" };
}

function clusterFlags(A, B, rows, min) {
  const common = new Set([...A.nodes].filter(t => B.nodes.has(t)));
  const inMultiB = new Set(B.multi.flatMap(c => [...c.members]));
  return A.multi.map(ca => {
    const mine = rows.filter(r => r.ca === ca);
    const best = mine.length ? Math.max(...mine.map(r => r.j)) : null;
    let flag = "";
    if (![...ca.members].some(t => common.has(t))) flag = "absent";
    else if (![...ca.members].some(t => inMultiB.has(t))) flag = "nooverlap";
    else if (best < min) flag = "belowmin";
    return { c: ca, mine, best, flag, above: mine.filter(r => r.j >= min) };
  });
}

function ari(x, y) {
  const n = x.length; if (n < 2) return null;
  const cont = new Map(), ra = new Map(), rb = new Map();
  for (let i = 0; i < n; i++) {
    const k = x[i] + "|" + y[i];
    cont.set(k, (cont.get(k) || 0) + 1); ra.set(x[i], (ra.get(x[i]) || 0) + 1); rb.set(y[i], (rb.get(y[i]) || 0) + 1);
  }
  const c2 = v => v * (v - 1) / 2;
  const idx = [...cont.values()].reduce((s, v) => s + c2(v), 0);
  const sa = [...ra.values()].reduce((s, v) => s + c2(v), 0), sb = [...rb.values()].reduce((s, v) => s + c2(v), 0);
  const exp = sa * sb / c2(n), mx = (sa + sb) / 2;
  return mx === exp ? null : (idx - exp) / (mx - exp);
}

function overview(A, B) {
  const common = [...A.nodes].filter(t => B.nodes.has(t));
  const compared = common.filter(t => A.edged.has(t) || B.edged.has(t)).sort((p, q) => p - q);
  const gamesCommon = A.games.filter(g => B.gameById.has(g.a)).length;
  const rows = matches(A, B);
  return { A, B, common: common.length, shareA: common.length / A.nodes.size, shareB: common.length / B.nodes.size,
    compared: compared.length, ari: compared.length >= 2 ? ari(compared.map(t => A.label.get(t)), compared.map(t => B.label.get(t))) : null,
    gamesCommon, rows, above: rows.filter(r => r.j >= S.min).length };
}

function pairs() {
  const inc = included(), out = [];
  for (let i = 0; i < inc.length; i++) for (let j = i + 1; j < inc.length; j++) out.push(overview(state(inc[i].key), state(inc[j].key)));
  return out;
}

function gamesInBoth(A, B, ca, cb) {
  const bothDs = A.games.filter(g => B.gameById.has(g.a));
  const rows = []; let onlyA = 0, onlyB = 0, neither = 0;
  for (const g of bothDs) {
    const gb = B.gameById.get(g.a);
    const ma = g.t.filter(t => ca.members.has(t) && A.nodes.has(t));
    const mb = gb.t.filter(t => cb.members.has(t) && B.nodes.has(t));
    if (ma.length && mb.length) rows.push({ g, gb, ma, mb, tags: [...new Set([...ma, ...mb])] });
    else if (ma.length) onlyA++; else if (mb.length) onlyB++; else neither++;
  }
  rows.sort((x, y) => (y.ma.length + y.mb.length) - (x.ma.length + x.mb.length) || x.g.r - y.g.r || x.gb.r - y.gb.r);
  return { N: bothDs.length, rows, onlyA, onlyB, neither };
}

// --- formatting ---
const f2 = (x) => x == null ? "—" : x.toFixed(2);
const pct = (x) => x == null ? "—" : Math.round(x * 100) + "%";
const esc = (s) => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const FLAG_TEXT = { absent: "not in the other network", nooverlap: "no overlap", belowmin: "no match above the minimum" };
function sourceText(k) {
  const d = DS(k), c = d.cells[S.cell[k]];
  switch (S.source[k]) {
    case "pick": return `★ pick · g ${c.g} · s ${c.s} · γ ${f2(c.gamma)}`;
    case "cell": return `cell you selected · g ${c.g} · s ${c.s} · γ ${f2(c.gamma)}`;
    case "hand": return `set by hand · g ${S.hand[k].g} · s ${S.hand[k].s} · γ ${S.hand[k].gamma} · main seed`;
    default: return "no Automatic Parameter Selection run";
  }
}
function setCell(k, key) {
  S.cell[k] = key; S.source[k] = key === DS(k).star ? "pick" : "cell"; delete S.hand[k]; S.match = null;
}
function setByHand(k, g, s, gamma) {
  const key = `${g},${s}`;
  if (DS(k).cells[key] && gamma == null) return setCell(k, key);
  S.hand[k] = { g, s, gamma: gamma ?? DS(k).cells[S.cell[k]].gamma.toFixed(2) }; S.source[k] = "hand"; S.match = null;
}
