"""Builds index.html (browser version of La Carte) from the same data and vocabulary as carte_assistant.py."""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
os.chdir(ROOT); sys.path.insert(0, ROOT)
import carte_assistant as A

cocktails = []
for r in A.COC.itertuples():
    cocktails.append({"Cocktail_FR": r.Cocktail_FR, "Cocktail_EN": r.Cocktail_EN, "recipe": [[i, cl] for i, cl in r.recipe], "flav": sorted(r.flav), "seas": sorted(r.seas),
                      "Speed": int(r.Speed), "Style": r.Style, "NoLow": int(r.NoLow), "Garnish": r.Garnish, "Popularity": int(r.Popularity), "cost": float(r.cost),
                      "alc_g": float(r.alc_g), "brands": list(r.brands), "base": r.base, "premium": bool(r.premium), "n_fr": r.n_fr, "n_en": r.n_en})
ingredients = {name: {"Brand": g.Brand, "Category": g.Category, "Bottle_cl": float(g.Bottle_cl), "Price": float(g.Price_EUR_illustr)} for name, g in A.ING.iterrows()}
data = {"cocktails": cocktails, "ingredients": ingredients, "FR_W": A.FR_W, "EN_W": A.EN_W, "NUMW": A.NUMW, "VENUES": A.VENUES, "VENUE_LABEL": A.VENUE_LABEL,
        "SEASONS": A.SEASONS, "SEASON_LABEL": A.SEASON_LABEL, "STYLES": A.STYLES, "STYLE_LABEL": A.STYLE_LABEL, "FLAVOURS": A.FLAVOURS, "FLAV_LABEL": A.FLAV_LABEL,
        "SPIRITS": A.SPIRITS, "SPIRIT_LABEL": A.SPIRIT_LABEL, "COMPETITORS": A.COMPETITORS, "GEN_FR": A.GEN_FR, "TXT": A.TXT,
        "colors": {"NAVY": A.NAVY, "DEEP": A.DEEP, "SKY": A.SKY, "MIST": A.MIST, "INKC": A.INKC, "GREY": A.GREY, "LINE": A.LINE, "GREEN": A.GREEN, "RED": A.RED}}
engine = open(os.path.join(HERE, "engine.js"), encoding="utf-8").read().replace("/*DATA*/null", json.dumps(data, ensure_ascii=False))
open(os.path.join(HERE, "engine_built.js"), "w", encoding="utf-8").write(engine)     # for node tests
css = A.CSS.split("<style>", 1)[1].replace("</style>", "")
SEED = ["upscale hotel bar, 6 cocktails, classics, winter, 120 cocktails a week", "brasserie, apéro français, service rapide, 6 cocktails",
        "club, 10 cocktails, prix max 7 €, 600 cocktails par semaine, vodka", "dry january menu for our restaurant, 6 drinks",
        "bar à Lyon, 8 cocktails, prix max 10 €, on veut du Bacardi", "terrasse en été, 8 cocktails, frais, un spritz façon Aperol",
        "restaurant italien, 6 cocktails, apéritif, Aperol spritz demandé", "bar d'hôtel, 8 cocktails, prix max 14 €, whisky"]
CHIPS = [("Bar à cocktails", "Bar à cocktails à Lyon, 8 cocktails, prix max 12 €, été, 250 cocktails par semaine"), ("Rooftop haut de gamme", "Rooftop haut de gamme, été, 8 cocktails"),
         ("Apéro français", "Brasserie, apéro français, service rapide, 6 cocktails"), ("Hotel bar (EN)", "Upscale hotel bar, 6 cocktails, classics, winter"),
         ("+ Sans alcool", "plus de sans alcool"), ("Spritz façon Aperol", "on nous demande un spritz façon Aperol"), ("Autre proposition", "autre"),
         ("Insights", "insights"), ("Reset", "reset")]
chips = "".join(f'<button class="chip" data-q="{q.replace(chr(34), "&quot;")}">{lab}</button>' for lab, q in CHIPS)

page = f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>La Carte · cocktail-menu assistant</title>
<meta name="description" content="Assistant qui compose la carte cocktails d'un bar à partir du portefeuille Pernod Ricard : prix, pour cost, marge, commande hebdomadaire. Prototype étudiant indépendant.">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{A.FONTS}">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%23123F75'/%3E%3Ctext x='32' y='42' font-family='Arial' font-weight='700' font-size='28' fill='white' text-anchor='middle'%3ELC%3C/text%3E%3C/svg%3E">
<style>{css}
*{{box-sizing:border-box}}
html,body{{margin:0;height:100%}}
body{{background:linear-gradient(160deg,#0B2A52 0%,#123F75 55%,#1E4F86 100%);font-family:Barlow,'Helvetica Neue',Arial,sans-serif;color:{A.INKC};display:flex;flex-direction:column;align-items:center}}
#app{{width:min(860px,100% - 32px);margin:24px 16px 10px;flex:1;min-height:0;display:flex;flex-direction:column;border-radius:16px;overflow:hidden;background:{A.MIST};box-shadow:0 24px 70px rgba(0,0,0,.35)}}
.head{{display:flex;align-items:center;gap:14px;padding:14px 18px}}
.head .t{{flex:1;min-width:0}} .head h1{{margin:0;font-size:24px;color:#fff;font-weight:700;line-height:1.1}} .head p{{margin:0;color:#B9CDE6;font-size:13px}}
.badge{{width:46px;height:46px;border-radius:12px;background:#fff;display:flex;align-items:center;justify-content:center;flex:none}}
.proto{{color:#fff;border:1px solid {A.SKY};border-radius:999px;padding:3px 10px;font-size:10px}}
#log{{flex:1;overflow-y:auto;padding:0 18px;min-height:0}}
.msg-u{{display:flex;justify-content:flex-end;margin:14px 0}} .msg-u>div{{background:{A.NAVY};color:#fff;padding:10px 15px;border-radius:14px 14px 4px 14px;max-width:80%;font-weight:500}}
.msg-b{{display:flex;align-items:flex-start;margin:14px 0}} .msg-b>.card{{background:#fff;padding:14px 18px;border-radius:4px 14px 14px 14px;max-width:calc(100% - 42px);border:1px solid {A.LINE};box-shadow:0 6px 18px rgba(18,63,117,.08);min-width:0}}
.av{{width:32px;min-width:32px;height:32px;border-radius:50%;background:{A.NAVY};color:#fff;display:flex;align-items:center;justify-content:center;margin:2px 10px 0 0;font-weight:700;font-size:13px}}
#chips{{display:flex;gap:6px;overflow-x:auto;padding:10px 14px 4px;background:#fff;border-top:1px solid {A.LINE};scrollbar-width:thin}}
.chip{{font-family:inherit;font-weight:600;font-size:12.5px;background:#fff;color:{A.NAVY};border:1px solid {A.SKY};border-radius:999px;padding:6px 12px;cursor:pointer;white-space:nowrap;transition:background .15s,transform .1s}}
.chip:hover{{background:{A.MIST}}} .chip:active{{transform:scale(.96)}}
form{{display:flex;gap:8px;padding:8px 14px 14px;background:#fff}}
#q{{flex:1;min-width:0;font:inherit;font-size:15px;border:1px solid {A.SKY};border-radius:10px;padding:10px 12px;outline:none;color:{A.INKC}}}
#q:focus{{border-color:{A.NAVY};box-shadow:0 0 0 3px rgba(118,160,205,.35)}}
#go{{font:inherit;font-weight:700;background:{A.NAVY};color:#fff;border:0;border-radius:10px;padding:0 18px;cursor:pointer;transition:transform .1s,background .15s}}
#go:hover{{background:{A.DEEP}}} #go:active{{transform:scale(.96)}}
footer{{color:#B9CDE6;font-size:12px;text-align:center;padding:4px 16px 16px;max-width:860px;line-height:1.5}}
footer a{{color:#fff}}
@media (max-width:600px){{ .head p{{display:none}} .proto{{display:none}} .stk-n{{width:120px !important}} #app{{margin:12px 16px 8px}} #go{{padding:0 12px}} }}
@media (prefers-reduced-motion:reduce){{ .lc *{{animation:none !important}} .lc .new .row,.lc .new .kpi{{opacity:1}} .lc .new .lead,.lc .new .bar{{transform:none}} }}
</style></head>
<body>
<div id="app" class="lc">
  <div class="head lc-head"><div class="badge"><span class="cond" style="font-weight:700;font-size:22px;color:{A.NAVY}">LC</span></div>
    <div class="t"><h1>La Carte</h1><p>Assistant carte cocktails · on-trade · FR / EN</p></div><span class="cap proto">Prototype</span></div>
  <div id="log"><div id="inner"></div><div style="height:10px"></div></div>
  <div id="chips">{chips}</div>
  <form id="f" autocomplete="off"><input id="q" placeholder="Décrivez votre établissement / Describe your venue" aria-label="Message"><button id="go" type="submit">Composer</button></form>
</div>
<footer>Prototype étudiant indépendant par <b>Anugraha SN</b> · BBA, EDHEC Business School · non affilié à Pernod Ricard · prix et recettes illustratifs · pour les professionnels CHR.<br>
<b>L'abus d'alcool est dangereux pour la santé, à consommer avec modération.</b></footer>
<script>
{engine}
const inner = document.getElementById('inner'), logEl = document.getElementById('log'), q = document.getElementById('q');
const AV = '<div class="av cond">LC</div>';
const sleep = ms => new Promise(r => setTimeout(r, ms));
function add(html) {{ inner.querySelectorAll('.new').forEach(n => n.classList.remove('new')); inner.insertAdjacentHTML('beforeend', html); return inner.lastElementChild; }}
function scrollToEl(el) {{ logEl.scrollTo({{top: Math.max(0, el.offsetTop - 60), behavior: 'smooth'}}); }}
let busy = false;
async function say(text) {{
  if (!text.trim() || busy) return; busy = true;
  add(`<div class="msg-u new"><div>${{esc(text)}}</div></div>`);
  const typing = add(`<div class="msg-b new">${{AV}}<div class="card"><div class="dots" style="padding:2px"><span></span><span></span><span></span></div></div></div>`);
  logEl.scrollTo({{top: logEl.scrollHeight, behavior: 'smooth'}});
  const d = chatData(text); await sleep(650); typing.remove();
  const b = add(`<div class="msg-b new">${{AV}}<div class="card">${{toHtml(d)}}</div></div>`);
  scrollToEl(b.previousElementSibling || b); busy = false;
}}
document.getElementById('f').addEventListener('submit', e => {{ e.preventDefault(); const t = q.value; q.value = ''; say(t); }});
document.querySelectorAll('.chip').forEach(c => c.addEventListener('click', () => say(c.dataset.q)));
seed({json.dumps(SEED, ensure_ascii=False)});
add(`<div class="msg-b new">${{AV}}<div class="card">${{toHtml({{type:'text', lang:'fr', text: D.TXT.fr.hello}})}}</div></div>`);
</script></body></html>"""
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(page)
print("index.html", len(page) // 1024, "KB")
