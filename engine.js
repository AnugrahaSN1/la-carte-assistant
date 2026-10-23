// La Carte engine: browser port of carte_assistant.py (same rules, same data). No DOM here.
const D = /*DATA*/null;
const VAT = 1.2;
const C = D.colors;
const RX = {};
const rx = (p, f = "") => RX[p + "|" + f] || (RX[p + "|" + f] = new RegExp(p, f));
const rs = (p, t) => rx(p).exec(t);
function norm(s) {
  return String(s).toLowerCase().replace(/œ/g, "oe").replace(/’/g, "'").normalize("NFKD").replace(/[̀-ͯ]/g, "");
}
function esc(s) { return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#x27;"); }
function pyRound(x, d = 0) {                       // Python's round-half-even
  const m = Math.pow(10, d), v = x * m, f = Math.floor(v), diff = v - f;
  let r = diff > 0.5 + 1e-9 ? f + 1 : diff < 0.5 - 1e-9 ? f : (f % 2 === 0 ? f : f + 1);
  return r / m;
}
const pct = x => (x * 100).toFixed(0) + "%";
function groupThousands(s, sep) { return s.replace(/\B(?=(\d{3})+(?!\d))/g, sep); }
function eur(x, lang) {
  const [a, b] = x.toFixed(2).split(".");
  return lang === "fr" ? `${groupThousands(a, " ")},${b} €` : `€${groupThousands(a, ",")}.${b}`;
}
function eur0(x, lang) {
  const a = x.toFixed(0);
  return lang === "fr" ? `${groupThousands(a, " ")} €` : `€${groupThousands(a, ",")}`;
}
function num(x, lang) { const s = String(+x); return lang === "fr" ? s.replace(".", ",") : s; }
const fmt = (s, o) => s.replace(/\{(\w+)\}/g, (_, k) => o[k]);
function mostCommon(counter, n) {                // counter: Map, insertion-ordered; stable by count desc
  return [...counter.entries()].map((e, i) => [e, i]).sort((a, b) => b[0][1] - a[0][1] || a[1] - b[1]).slice(0, n).map(x => x[0]);
}
function inc(m, k, v = 1) { m.set(k, (m.get(k) || 0) + v); }

const COC = D.cocktails;            // precomputed rows
const ING = D.ingredients;          // name -> {Brand, Category, Bottle_cl, Price}
const BRAND_CAT = {};
for (const [name, g] of Object.entries(ING)) if (g.Brand && !(g.Brand in BRAND_CAT)) BRAND_CAT[g.Brand] = g.Category;

// ---------- parsing ----------
function isFrench(t) { const n = norm(t); return (n.match(rx(D.FR_W, "g")) || []).length > (n.match(rx(D.EN_W, "g")) || []).length; }
function isEnglish(t) { const n = norm(t); return (n.match(rx(D.EN_W, "g")) || []).length > (n.match(rx(D.FR_W, "g")) || []).length; }

function parse(text, S) {
  let t = norm(text.trim());
  for (const [w, n] of Object.entries(D.NUMW)) t = t.replace(rx(`\\b${w}\\b`, "g"), String(n));
  for (const [k, p] of Object.entries(D.VENUES)) if (rs(p, t)) S.venue = k;
  if (rs("haut de gamme|premium|luxe|chic|upscale|high.?end|palace|plus premium", t)) S.tier = "premium";
  else if (rs("etudiant|student|pas cher|cheap|petit budget|abordable|happy hour|moins cher|cheaper|populaire", t)) S.tier = "budget";
  const m = rs("(?:prix\\s*)?(?:max(?:imum)?|moins de|under|below|jusqu'a|pas plus de|<|maxi)\\s*(\\d+(?:[.,]\\d+)?)\\s*(?:€|eur|euros?)?", t)
         || rs("(\\d+(?:[.,]\\d+)?)\\s*(?:€|eur|euros?)\\s*(?:max|maximum|maxi)", t);
  if (m && parseFloat(m[1].replace(",", ".")) < 40) S.cap = parseFloat(m[1].replace(",", "."));
  for (const mm of t.matchAll(rx("(\\d+)\\s*(cocktails?|verres?|serves?|drinks?|boissons?|couverts|clients|covers|guests)\\s*(?:par|/|a|per|each|chaque)?\\s*(semaine|week|jour|day|soir|night|soiree)?", "g"))) {
    const n = parseInt(mm[1]), what = mm[2], per = mm[3];
    const sw = arr => arr.some(a => what.startsWith(a));
    if (per) {
      const v = n * (["jour", "day", "soir", "night", "soiree"].includes(per) ? 7 : 1);
      S.volume = sw(["cocktail", "verre", "serve", "drink", "boisson"]) ? v : Math.trunc(v * 0.5);
    } else if (sw(["cocktail", "drink", "boisson"]) && n >= 3 && n <= 16) S.n = n;
    else if (sw(["couvert", "client", "cover", "guest"])) S.volume = Math.trunc(n * 7 * 0.5);
  }
  const pc = rs("pour.?cost\\s*(?:de|of|a|cible|target)?\\s*(\\d{2})\\s*%", t);
  if (pc) S.target = parseInt(pc[1]) / 100;
  for (const [k, p] of Object.entries(D.SEASONS)) if (rs(p, t)) S.season = k;
  for (const [k, p] of Object.entries(D.STYLES)) if (rs(p, t)) S.styles.add(k);
  const neg = "(?:pas de|pas d'|sans|no|without|except|aucun|pas trop)\\s+(?:\\w+\\s+)?";
  for (const [k, p] of Object.entries(D.FLAVOURS)) {
    if (rs(neg + "(?:" + p + ")", t)) { S.flav.delete(k); S.avoid_flav.add(k); }
    else if (rs(p, t)) S.flav.add(k);
  }
  for (const [k, p] of Object.entries(D.SPIRITS)) {
    if (rs(neg + "(?:" + p + ")", t)) { S.spirits.delete(k); S.no_spirit.add(k); }
    else if (rs(p, t)) { S.spirits.add(k); S.no_spirit.delete(k); }
  }
  if (rs("plus de sans alcool|more (?:alcohol.?free|no.?alcohol|mocktails)|mocktails?|no.?low|alcohol.?free|sans alcool|dry january|janvier sobre|sobre", t))
    S.nolow = rs("dry january|janvier sobre", t) ? 0.5 : Math.max(S.nolow, 0.3);
  if (rs("rapide|\\bvite\\b|\\brush\\b|\\bfast\\b|\\bquick|seul derriere|alone behind|un seul barman|pas de barman|no bartender|debit|high volume", t)) S.fast = true;
  for (const [k, v] of Object.entries(D.COMPETITORS)) {
    if (t.includes(k)) {
      S.comp.add(k);
      if (v[1] in D.SPIRITS) S.spirits.add(v[1]); else if (v[1]) S.styles.add(v[1]);
    }
  }
  if (rs("\\bautre\\b|another|different|d'autres|other options?|encore", t)) S.offset += 1;
  for (const mm of t.matchAll(rx("(?:remplace|enleve|retire|supprime|sans le|sans la|replace|remove|swap|drop|pas de)\\s+(?:le |la |les |l'|the )?([a-z0-9' &-]{3,30})", "g"))) {
    const key = mm[1].trim();
    for (const r of COC) if (r.n_fr.includes(key) || r.n_en.includes(key)) S.removed.add(r.Cocktail_FR);
  }
  return S;
}

// ---------- menu engine ----------
const targetFor = (r, S) => S.target + (r.brands.includes("Mumm") ? 0.06 : 0);
function priceFor(r, S) {
  let p = Math.ceil(r.cost * VAT / targetFor(r, S) * 2) / 2;
  if (S.tier === "premium") p = Math.max(p, r.NoLow === 0 ? 12 : 9);
  p = Math.max(p, 4);
  if (S.cap) p = Math.min(p, S.cap);
  return p;
}
function score(r, S) {
  const inter = (a, b) => a.filter(x => b.has(x)).length;
  let s = 0.8 * r.Popularity + 2.5 * inter(r.flav, S.flav) - 3 * inter(r.flav, S.avoid_flav);
  if (S.season) s += r.seas.includes(S.season) ? 2 : ((S.season === "summer" || S.season === "winter") && !r.seas.includes("all") ? -1.5 : 0);
  if (S.spirits.size) s += S.spirits.has(r.base) ? 3 : 0;
  if (S.styles.size) s += (S.styles.has(r.Style) || (S.styles.has("apero") && r.Style === "french")) ? 2 : 0;
  if (S.fast) s -= { 1: 0, 2: 1, 3: 3 }[r.Speed];
  if (S.nolow >= 0.3 && r.NoLow === 1) s += S.nolow >= 0.5 ? 2 : 1;
  if (S.tier === "premium") s += r.premium ? 1.5 : -0.5;
  if (S.tier === "budget") s -= r.premium ? 1.5 : 0;
  const v = S.venue;
  if (v === "student" && r.Speed === 1) s += 0.5;
  if (v === "club" && r.Style === "highball") s += 1.5;
  if (v === "cocktail_bar" && r.Style === "classic") s += 1;
  if (v === "brasserie" && ["french", "apero", "highball"].includes(r.Style)) s += 1;
  if (v === "rooftop" && (r.seas.includes("summer") || r.Style === "apero")) s += 1;
  if (v === "hotel" && (r.premium || r.Style === "classic")) s += 1;
  if (S.cap) {
    const need = Math.ceil(r.cost * VAT / targetFor(r, S) * 2) / 2;
    if (need > S.cap) s -= 8 * (need / S.cap - 1);
  }
  return s;
}
function item(r, S) {
  const i = S.lang === "fr" ? 0 : 1, price = priceFor(r, S), ht = price / VAT;
  const rec = r.recipe.filter(([ing]) => ing !== "water").map(([ing, cl]) => `${num(cl, S.lang)} cl ${i === 0 ? (D.GEN_FR[ing] || ing) : ing}`).join(" · ");
  const g = r.Garnish.includes(" / ") ? r.Garnish.split(" / ")[i] : r.Garnish;
  return { name: i === 0 ? r.Cocktail_FR : r.Cocktail_EN, key: r.Cocktail_FR, recipe: rec, brands: r.brands, base: r.base, price, cost: r.cost,
           pc: r.cost / ht, margin: ht - r.cost, alc: r.alc_g, std: r.alc_g / 10, nolow: r.NoLow, garnish: g, recipe_raw: r.recipe };
}
function buildMenu(S) {
  const n = S.n;
  let d = COC.filter(r => !S.removed.has(r.Cocktail_FR) && !S.no_spirit.has(r.base)).map(r => ({ r, sc: score(r, S) }));
  d.sort((a, b) => b.sc - a.sc || a.r.cost - b.r.cost);
  const rot = rows => { if (!rows.length) return rows; const o = (S.offset * 2) % rows.length; return rows.slice(o).concat(rows.slice(0, o)); };
  const free = rot(d.filter(x => x.r.NoLow === 2).map(x => x.r));
  const alc = rot(d.filter(x => x.r.NoLow < 2).map(x => x.r));
  const kFree = Math.max(1, pyRound(n * S.nolow));
  const out = free.slice(0, kFree);
  const perBase = new Map(), perBrand = new Map();
  const capBase = S.spirits.size ? 3 : 2;
  for (const r of alc) {
    if (out.length >= n) break;
    if ((perBase.get(r.base) || 0) >= (S.spirits.has(r.base) ? capBase + 1 : capBase)) continue;
    const ub = [...new Set(r.brands)];
    if (ub.some(b => (perBrand.get(b) || 0) >= (S.spirits.has(BRAND_CAT[b]) ? 2 : 1))) continue;
    out.push(r); inc(perBase, r.base);
    for (const b of ub) inc(perBrand, b);
  }
  for (const r of alc) { if (out.length >= n) break; if (!out.includes(r)) out.push(r); }
  const items = out.map(r => item(r, S));
  const alcP = items.filter(x => x.nolow < 2).map(x => x.price);
  if (alcP.length) {
    const floor = Math.ceil(0.65 * alcP.reduce((a, b) => a + b, 0) / alcP.length * 2) / 2;
    for (const x of items) if (x.nolow === 2 && x.price < floor) {
      x.price = Math.min(floor, S.cap || floor); const ht = x.price / VAT; x.pc = x.cost / ht; x.margin = ht - x.cost;
    }
  }
  items.sort((a, b) => ((a.nolow === 2) - (b.nolow === 2)) || (b.price - a.price));
  return items;
}
function stock(items, S) {
  const per = S.volume / Math.max(1, items.length), need = new Map();
  for (const it of items) for (const [ing, cl] of it.recipe_raw) if (ING[ing].Brand) inc(need, ing, cl * per);
  return [...need.entries()].map((e, i) => [e, i]).sort((a, b) => b[0][1] - a[0][1] || a[1] - b[1]).map(([[ing, v]]) => {
    const g = ING[ing], b = Math.ceil(v / g.Bottle_cl);
    return [ing, g.Bottle_cl, b, pyRound(b * g.Price)];
  });
}

// ---------- session log + insights ----------
const LOG = [];
let SEEDED = 0;
function logRow(S, items, flagged) {
  const n = Math.max(1, items.length);
  const row = { venue: S.venue || "", cap: S.cap, n: items.length, flav: [...S.flav].sort(), spirits: [...S.spirits].sort(), comp: [...S.comp].sort(),
                brands: items.flatMap(it => [...new Set(it.brands)]), free_share: items.filter(it => it.nolow === 2).length / n,
                avg_pc: items.reduce((a, it) => a + it.pc, 0) / n, bottles: stock(items, S).map(([ing, , b]) => [ing, b]), flagged };
  if (S.log_i !== null) LOG[S.log_i] = row; else { S.log_i = LOG.length; LOG.push(row); }
}
function median(a) { const s = [...a].sort((x, y) => x - y), m = s.length >> 1; return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2; }
function insights(lang) {
  const fr = lang === "fr", i = fr ? 0 : 1;
  if (!LOG.length) return { type: "text", lang, text: fr ? "Pas encore de carte dans cette session." : "No menus built in this session yet." };
  const n = LOG.length, slots = LOG.reduce((a, r) => a + r.n, 0);
  const brand = new Map(), bott = new Map(), comp = new Map(), flav = new Map(), ven = new Map(), asked = new Map();
  for (const r of LOG) {
    r.brands.forEach(b => inc(brand, b)); r.bottles.forEach(([k, v]) => inc(bott, k, v)); r.comp.forEach(c => inc(comp, c));
    r.flav.forEach(f => inc(flav, f)); if (r.venue) inc(ven, r.venue); r.spirits.forEach(s => inc(asked, s));
  }
  const caps = LOG.map(r => r.cap).filter(c => c !== null && c !== undefined);
  const join = (arr, f) => arr.map(f).join(", ") || "—";
  const rows = [[fr ? "Cartes construites" : "Menus built", `${n} · ${slots} cocktails`],
    [fr ? "Établissements" : "Venues", join(mostCommon(ven, 3), ([k, v]) => `${D.VENUE_LABEL[k][i]} (${v})`)],
    [fr ? "Prix plafond médian" : "Median price cap", caps.length ? eur(median(caps), lang) : "—"],
    [fr ? "Goûts demandés" : "Flavours asked", join(mostCommon(flav, 3), ([k, v]) => `${D.FLAV_LABEL[k][i]} (${v})`)],
    [fr ? "Catégories demandées" : "Categories asked", join(mostCommon(asked, 3), ([k, v]) => `${D.SPIRIT_LABEL[k][i]} (${v})`)],
    [fr ? "Marques à la carte" : "Brands on menus", mostCommon(brand, 4).map(([k, v]) => `${k} ${pct(v / slots)}`).join(", ")],
    [fr ? "Part sans alcool" : "Alcohol-free share", pct(LOG.reduce((a, r) => a + r.free_share, 0) / n)],
    [fr ? "Pour cost moyen" : "Average pour cost", pct(LOG.reduce((a, r) => a + r.avg_pc, 0) / n)],
    [fr ? "Bouteilles / semaine (top)" : "Bottles / week (top)", mostCommon(bott, 3).map(([k, v]) => `${k} ${v}`).join(", ")]];
  const gaps = mostCommon(comp, 3).map(([k, v]) => fr ? `Demande concurrente : ${D.COMPETITORS[k][0]} × ${v} → ${D.COMPETITORS[k][2]}`
                                                      : `Competitor ask: ${D.COMPETITORS[k][0]} × ${v} → ${D.COMPETITORS[k][3]}`);
  const fl = LOG.reduce((a, r) => a + r.flagged, 0);
  if (fl) gaps.push(fr ? `${fl} cocktail(s) au-dessus de 30 % de pour cost à cause d'un prix plafond bas` : `${fl} cocktail(s) above 30% pour cost because of a low price cap`);
  const seedNote = SEEDED ? (fr ? ` Inclut ${SEEDED} cartes de démonstration chargées à l'ouverture.` : ` Includes ${SEEDED} demo menus loaded at start.`) : "";
  return { type: "insights", lang, rows, gaps,
    note: (fr ? "Ce que les cartes révèlent : quelles marques y entrent, à quel prix, quelles demandes concurrentes reviennent, et le volume de bouteilles généré par compte. De quoi préparer la visite d'un commercial."
              : "What the menus reveal: which brands make it on, at what price, which competitor requests come up, and the bottle volume each account generates. Useful prep for a sales visit.") + seedNote };
}

// ---------- chat engine ----------
function fresh() {
  return { log_i: null, venue: null, tier: null, cap: null, n: 8, volume: 200, target: 0.22, season: null, styles: new Set(), flav: new Set(), avoid_flav: new Set(),
           spirits: new Set(), no_spirit: new Set(), nolow: 0.15, fast: false, comp: new Set(), removed: new Set(), offset: 0, lang: "fr", touched: false };
}
let STATE = fresh();
function snap(S) {
  return JSON.stringify(Object.keys(S).filter(k => k !== "lang" && k !== "log_i").sort().map(k => [k, S[k] instanceof Set ? [...S[k]].sort() : S[k]]));
}
function isNewRequest(t) {
  if (rx("^\\s*(autre|another|encore|plus |moins |remplace|enleve|retire|replace|remove|swap|pas de|sans|no |et |and |prix|max|price|under)").test(t)) return false;
  const sig = [Object.values(D.VENUES).some(p => rs(p, t)), !!rs("\\d+\\s*cocktails?\\b(?!\\s*(?:par|/|a|per))", t), !!rs("\\d+\\s*(?:€|eur)|max", t),
               Object.values(D.SEASONS).some(p => rs(p, t)), !!rs("par semaine|per week|a week|par jour|per day", t), !!rs("haut de gamme|premium|etudiant|student", t)];
  return sig.filter(Boolean).length >= 2;
}
function chatData(text) {
  let S = STATE; const t = norm(text.trim());
  if (isFrench(text)) S.lang = "fr"; else if (isEnglish(text)) S.lang = "en";
  const L = D.TXT[S.lang], i = S.lang === "fr" ? 0 : 1;
  if (["quit", "exit", "bye", "quitter", "au revoir"].includes(t)) return { type: "text", lang: S.lang, text: L.bye };
  if (["reset", "restart", "recommencer", "nouvelle carte"].includes(t)) { const lang = S.lang; STATE = fresh(); STATE.lang = lang; return { type: "text", lang, text: L.reset }; }
  if (["hi", "hello", "hey", "salut", "bonjour", "help", "aide"].includes(t)) return { type: "text", lang: S.lang, text: L.hello };
  if (rx("^\\s*(insights?|rapport|report|stats)\\b").test(t)) {
    if (rs("english|anglais", t)) S.lang = "en"; else if (rs("francais|french", t)) S.lang = "fr";
    return insights(S.lang);
  }
  if (isNewRequest(t)) { const lang = S.lang; STATE = fresh(); STATE.lang = lang; S = STATE; }
  const before = snap(S); parse(text, S);
  if (before !== snap(S)) S.touched = true;
  if (!S.touched) return { type: "text", lang: S.lang, text: L.ask };
  const items = buildMenu(S), flagged = items.filter(it => it.pc > 0.30).length;
  logRow(S, items, flagged);
  const ctx = S.venue ? [D.VENUE_LABEL[S.venue][i]] : [];
  if (S.tier) ctx.push({ premium: ["haut de gamme", "upscale"], budget: ["petit budget", "budget"] }[S.tier][i]);
  if (S.season) ctx.push(D.SEASON_LABEL[S.season][i]);
  ctx.push(...[...S.styles].sort().map(s => D.STYLE_LABEL[s][i]), ...[...S.flav].sort().map(f => D.FLAV_LABEL[f][i]));
  ctx.push(...[...S.spirits].sort().map(s => D.SPIRIT_LABEL[s][i]), ...[...S.no_spirit].sort().map(s => (i === 0 ? "sans " : "no ") + D.SPIRIT_LABEL[s][i]));
  if (S.cap) ctx.push("max " + eur(S.cap, S.lang).replace(",00", ""));
  if (S.fast) ctx.push(i === 0 ? "service rapide" : "fast service");
  const notes = [...S.comp].sort().map(c => fmt(L.comp, { b: D.COMPETITORS[c][0], a: D.COMPETITORS[c][2 + i] }));
  if (flagged && S.cap) notes.push(fmt(L.over, { c: String(S.cap), n: flagged }));
  const avgM = items.reduce((a, it) => a + it.margin, 0) / items.length;
  return { type: "menu", lang: S.lang, items, ctx, notes,
           summary: { pc: items.reduce((a, it) => a + it.pc, 0) / items.length, margin: avgM, week: avgM * S.volume },
           stock: stock(items, S), assume: fmt(L.assume, { v: S.volume, t: pyRound(S.target * 100) }) };
}

// ---------- rendering (mirrors to_html in the Python script) ----------
const pill = (txt, bg, fg) => `<span class="cap" style="background:${bg};color:${fg};padding:2px 8px;border-radius:999px;font-size:10px;white-space:nowrap">${txt}</span>`;
function menuHtml(d, L, i) {
  const lang = d.lang, out = [];
  for (const n of d.notes) out.push(`<div style="background:#F3F7FC;border-left:3px solid ${C.SKY};border-radius:6px;padding:6px 10px;margin-bottom:10px;font-size:13px">${esc(n)}</div>`);
  const chips = d.ctx.map(c => `<span style="background:${C.MIST};color:${C.NAVY};border-radius:999px;padding:2px 10px;font-size:12px;font-weight:500;margin:0 6px 6px 0;display:inline-block">${esc(c)}</span>`).join("");
  out.push(`<div style="font-weight:700;font-size:22px;color:${C.NAVY};line-height:1.1">${L.menu}</div><div style="margin:8px 0 6px">${chips}</div>`);
  d.items.forEach((it, k) => {
    const tag = it.nolow === 2 ? pill(L.free, "#E3F5EE", C.GREEN) : it.nolow === 1 ? pill(L.low, "#E8F0FA", C.NAVY) : "";
    const pcs = it.pc > 0.30 ? `color:${C.RED};font-weight:600` : `color:${C.GREY}`;
    out.push(`<div class="row" style="--i:${k};padding:10px 0;border-bottom:1px solid ${C.LINE}">`
      + `<div class="rowtop" style="display:flex;align-items:baseline;gap:8px"><span class="nm" style="font-weight:600;font-size:16px">${esc(it.name)}</span>${tag}`
      + `<span class="lead" style="--i:${k};flex:1;border-bottom:2px dotted ${C.SKY};transform-origin:left;margin:0 4px;position:relative;top:-4px;min-width:12px"></span>`
      + `<span class="cond" style="font-weight:700;font-size:21px;color:${C.NAVY};white-space:nowrap">${eur(it.price, lang)}</span></div>`
      + `<div style="font-size:12.5px;color:${C.GREY};margin-top:1px">${esc(it.recipe)}${it.garnish ? ` · <i>${esc(it.garnish)}</i>` : ""}</div>`
      + `<div style="font-size:11.5px;margin-top:3px;${pcs}">Pour cost ${pct(it.pc)} &nbsp;·&nbsp; ${i === 0 ? "Marge" : "Margin"} ${eur(it.margin, lang)} &nbsp;·&nbsp; ${num(pyRound(it.std, 1), lang)} ${L.std}</div></div>`);
  });
  const s = d.summary, base = 150 + 110 * d.items.length + 300;
  const tile = (k, big, lab) => `<div class="kpi" style="--i:${k};--base:${base}ms;flex:1;min-width:150px;background:#F3F7FC;border-radius:10px;padding:10px 12px">`
    + `<div class="cond" style="font-weight:700;font-size:30px;color:${C.NAVY};line-height:1">${big}</div><div style="font-size:11.5px;color:${C.GREY};margin-top:4px">${lab}</div></div>`;
  const pcHtml = `<span class="count" style="--to:${pyRound(s.pc * 100)};--base:${base}ms"></span>%`;
  out.push(`<div style="display:flex;flex-wrap:wrap;gap:10px;margin-top:14px">` + tile(0, pcHtml, L.pc) + tile(1, eur(s.margin, lang), L.margin) + tile(2, eur0(s.week, lang), L.week) + `</div>`);
  const mx = d.stock.length ? Math.max(...d.stock.map(x => x[2])) : 1;
  const bars = d.stock.map(([ing, cl, b, cost], k) => `<div class="stk" style="display:flex;align-items:center;gap:10px;margin:5px 0;font-size:12.5px">`
    + `<span class="stk-n" style="width:190px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${esc(ing)}</span>`
    + `<span style="flex:1;background:${C.MIST};border-radius:4px;height:12px"><span class="bar" style="--i:${k};--base:${base + 450}ms;display:block;height:12px;`
    + `width:${(b / mx * 100).toFixed(0)}%;background:linear-gradient(90deg,${C.NAVY},${C.SKY});border-radius:4px"></span></span>`
    + `<span style="width:96px;text-align:right;font-weight:600;white-space:nowrap">${b} ${L.bt} · ${eur0(cost, lang)}</span></div>`).join("");
  out.push(`<div style="margin-top:16px"><div class="cap" style="color:${C.NAVY};margin-bottom:4px">${L.order}</div>${bars}</div>`);
  out.push(`<div style="font-size:11.5px;color:${C.GREY};margin-top:10px">${esc(d.assume)}</div>`
    + `<div style="font-size:11px;color:${C.GREY};margin-top:6px;border-top:1px solid ${C.LINE};padding-top:6px"><b>${L.health}</b> ${L.note}</div>`);
  return out.join("");
}
function toHtml(d) {
  const L = D.TXT[d.lang], i = d.lang === "fr" ? 0 : 1;
  if (d.type === "text") return esc(d.text).replace(/\n/g, "<br>");
  if (d.type === "insights") {
    const rows = d.rows.map(([a, v], k) => `<div class="row" style="--i:${k};display:flex;flex-wrap:wrap;padding:8px 0;border-bottom:1px solid ${C.LINE};gap:4px 14px">`
      + `<span style="width:210px;color:${C.GREY};font-size:12.5px">${esc(a)}</span><span style="flex:1;min-width:200px;font-weight:600">${esc(v)}</span></div>`).join("");
    const gaps = d.gaps.map((g, k) => `<div class="kpi" style="--i:${k};--base:${150 + 110 * d.rows.length}ms;background:#F3F7FC;border-left:3px solid ${C.NAVY};border-radius:6px;padding:7px 10px;margin-top:6px;font-size:13px">${esc(g)}</div>`).join("");
    return `<div class="cap" style="color:${C.SKY}">Insights · trade marketing</div><div style="font-weight:700;font-size:22px;color:${C.NAVY};margin-bottom:6px">`
      + (i === 0 ? "Ce que disent les cartes" : "What the menus say") + `</div>${rows}<div style="margin-top:10px">${gaps}</div>`
      + `<div style="font-size:12px;color:${C.GREY};margin-top:10px">${esc(d.note)}</div>`;
  }
  return menuHtml(d, L, i);
}
function seed(list) { for (const m of list) { STATE = fresh(); chatData(m); } SEEDED = list.length; STATE = fresh(); }
if (typeof module !== "undefined") module.exports = { chatData, toHtml, fresh, seed, get STATE() { return STATE; }, set STATE(v) { STATE = v; }, LOG };
