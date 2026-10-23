# =====================================================================
# LA CARTE  |  cocktail-menu assistant for bars & restaurants  |  one cell, no API
# Works in Google Colab. Run the cell, then chat in the box that appears.
# Describe the venue in French or English:
#   "bar à cocktails à Lyon, 8 cocktails, prix max 12 €, été, 250 cocktails par semaine"
#   "rooftop haut de gamme, 6 cocktails, plus de sans alcool"   /   "brasserie, apéro français, service rapide"
# It builds a costed menu from the Pernod Ricard portfolio (price, pour cost, margin, alcohol per serve),
# always includes alcohol-free options, and prints the weekly bottle order.
# Follow-ups: "remplace le Mojito", "prix max 12", "10 cocktails", "pas de rhum", "plus premium", "autre".
# Type "insights" for the trade-marketing report.
# Independent student prototype, not affiliated with Pernod Ricard. For licensed on-trade professionals.
# Prices, ABVs and recipes are illustrative. L'abus d'alcool est dangereux pour la santé.
# =====================================================================
import re, os, math, unicodedata, html as _html
from collections import Counter
import pandas as pd

ING_PATH, COC_PATH = "ingredients_illustratif.csv", "cocktails_illustratif.csv"

# ---------- 1. LOAD DATA ----------
if not (os.path.exists(ING_PATH) and os.path.exists(COC_PATH)):
    try:
        from google.colab import files
        print("Upload BOTH CSVs (ingredients_illustratif.csv and cocktails_illustratif.csv):")
        files.upload()
    except ImportError:
        raise FileNotFoundError("Put ingredients_illustratif.csv and cocktails_illustratif.csv next to this script.")

def norm(s):
    s = str(s).lower().replace("œ", "oe").replace("’", "'")
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c))

ING = pd.read_csv(ING_PATH, encoding="utf-8-sig").fillna({"Brand": ""}).set_index("Ingredient")
ING["Category"] = ING.Category.replace({"whiskey": "whisky"})
ING["eur_cl"] = ING.Price_EUR_illustr / ING.Bottle_cl
COC = pd.read_csv(COC_PATH, encoding="utf-8-sig").fillna({"Garnish": ""})
GARNISH_EUR, VAT = 0.15, 1.20

def _recipe(s): return [(p.split(":")[0], float(p.split(":")[1])) for p in s.split(";")]
COC["recipe"] = COC.Recipe_cl.map(_recipe)
COC["cost"] = COC.recipe.map(lambda r: round(sum(cl * ING.loc[i, "eur_cl"] for i, cl in r) + GARNISH_EUR, 2))
COC["alc_g"] = COC.recipe.map(lambda r: round(sum(cl * 10 * ING.loc[i, "ABV"] / 100 * 0.789 for i, cl in r), 1))
COC["brands"] = COC.recipe.map(lambda r: [ING.loc[i, "Brand"] for i, _ in r if ING.loc[i, "Brand"]])
COC["base"] = COC.recipe.map(lambda r: next((ING.loc[i, "Category"] for i, _ in r if ING.loc[i, "Brand"]), "none"))
COC["premium"] = COC.recipe.map(lambda r: any(ING.loc[i, "Premium"] == 1 for i, _ in r))
COC["flav"] = COC.Flavours.str.split("|").apply(set)
COC["seas"] = COC.Seasons.str.split("|").apply(set)
COC["n_fr"], COC["n_en"] = COC.Cocktail_FR.map(norm), COC.Cocktail_EN.map(norm)

# ---------- 2. VOCABULARY ----------
VENUES = {"cocktail_bar": r"bar a cocktails?|cocktail bar|speakeasy|mixolog", "brasserie": r"brasserie|\bcafe\b|bistro|bar.?tabac|\bpmu\b",
          "restaurant": r"restaurant|\bresto\b", "rooftop": r"rooftop|terrasse|terrace|guinguette|plage|beach",
          "club": r"\bclub|discotheque|boite de nuit|nightclub", "hotel": r"hotel|lobby", "student": r"etudiant|student|campus|\bbde\b"}
VENUE_LABEL = {"cocktail_bar": ("bar à cocktails", "cocktail bar"), "brasserie": ("brasserie / café", "brasserie / café"), "restaurant": ("restaurant", "restaurant"),
               "rooftop": ("rooftop / terrasse", "rooftop / terrace"), "club": ("club", "club"), "hotel": ("bar d'hôtel", "hotel bar"), "student": ("bar étudiant", "student bar")}
SEASONS = {"summer": r"\bete\b|summer|estival|terrasse|plage|beach|soleil|sunny|chaleur", "winter": r"hiver|winter|froid|cosy|cozy|apres.?ski|\bski\b",
           "festive": r"noel|christmas|fetes|festive|nouvel an|new year|reveillon|celebration|mariage|wedding"}
SEASON_LABEL = {"summer": ("été", "summer"), "winter": ("hiver", "winter"), "festive": ("fêtes", "festive")}
STYLES = {"french": r"francais|french|provencal|marseille|pastis|a la francaise", "apero": r"apero|aperitif|italien|italian|italie|spritz|apericena",
          "classic": r"classiques?|classic|vintage|speakeasy|annees 20|twenties|intemporel", "highball": r"highball|long drinks?|simples?|easy"}
STYLE_LABEL = {"french": ("apéro français", "French apéritif"), "apero": ("apéritif", "apéritif"), "classic": ("classiques", "classics"), "highball": ("long drinks", "long drinks")}
FLAVOURS = {"fresh": r"frais|fraich|fresh|leger|light|desalterant|refreshing", "bitter": r"\bamers?\b|amertume|bitter", "sweet": r"sucre|\bdoux\b|sweet|gourmand",
            "citrus": r"agrume|citron|citrus|acidul|\bsours?\b", "fruity": r"fruite|fruity|fruits? rouges", "coffee": r"\bcoffee|espresso|a base de cafe|cafe gourmand",
            "spicy": r"epice|gingembre|spicy|ginger", "strong": r"\bforts?\b|\bstrong|corse|boozy|spirit.?forward", "herbal": r"herbac|herbal|botani",
            "sparkling": r"bulles|petillant|champagne|sparkling|bubbles", "tropical": r"tropical|tiki|caraibes|exotique|exotic"}
FLAV_LABEL = {"fresh": ("frais", "fresh"), "bitter": ("amer", "bitter"), "sweet": ("gourmand", "sweet"), "citrus": ("agrumes", "citrus"), "fruity": ("fruité", "fruity"),
              "coffee": ("café", "coffee"), "spicy": ("épicé", "spicy"), "strong": ("puissant", "spirit-forward"), "herbal": ("herbacé", "herbal"),
              "sparkling": ("bulles", "sparkling"), "tropical": ("tropical", "tropical"), "smooth": ("rond", "smooth"), "anise": ("anisé", "anise"), "dry": ("sec", "dry"), "warm": ("chaud", "warm")}
SPIRITS = {"gin": r"\bgin\b", "vodka": r"vodka", "rum": r"\brhums?\b|\brum\b", "whisky": r"whisk", "cognac": r"cognac", "tequila": r"tequila|mezcal",
           "anise": r"pastis|anis|ricard", "champagne": r"champagne"}
SPIRIT_LABEL = {"gin": ("gin", "gin"), "vodka": ("vodka", "vodka"), "rum": ("rhum", "rum"), "whisky": ("whisky", "whisky"), "cognac": ("cognac", "cognac"),
                "tequila": ("tequila", "tequila"), "anise": ("anisé", "anise"), "champagne": ("champagne", "champagne"), "aperitif": ("apéritif", "apéritif"), "none": ("sans alcool", "alcohol-free")}
COMPETITORS = {"aperol": ("Aperol", "apero", "Spritz Rosato (Ramazzotti) ou Italicus Royal", "Rosato Spritz (Ramazzotti) or Italicus Royale"),
               "campari": ("Campari", "apero", "Negroni Blanc (Plymouth, Lillet, Suze)", "White Negroni (Plymouth, Lillet, Suze)"),
               "bacardi": ("Bacardi", "rum", "Havana Club", "Havana Club"), "captain morgan": ("Captain Morgan", "rum", "Havana Club", "Havana Club"),
               "smirnoff": ("Smirnoff", "vodka", "Absolut", "Absolut"), "grey goose": ("Grey Goose", "vodka", "Absolut", "Absolut"),
               "hendrick": ("Hendrick's", "gin", "Monkey 47 ou Plymouth", "Monkey 47 or Plymouth"), "bombay": ("Bombay", "gin", "Beefeater", "Beefeater"),
               "jack daniel": ("Jack Daniel's", "whisky", "Jameson", "Jameson"), "hennessy": ("Hennessy", "cognac", "Martell", "Martell"),
               "patron": ("Patrón", "tequila", "Olmeca Altos", "Olmeca Altos"), "don julio": ("Don Julio", "tequila", "Olmeca Altos", "Olmeca Altos"),
               "baileys": ("Baileys", "", "Irish Coffee (Jameson)", "Irish Coffee (Jameson)")}

# ---------- 3. PARSING ----------
FR_W = r"\b(bonjour|je|nous|on|pour|avec|sans|mon|ma|notre|une|des|de|le|la|les|et|pas|plus|prix|carte|clientele|cocktails? par semaine|etudiante?s?|ete|hiver|remplace|moins)\b"
EN_W = r"\b(i|we|our|my|the|and|for|with|price|menu|guests|per week|students?|summer|winter|replace|under|cheaper|a|of|bar is)\b"
def is_french(t):
    n = norm(t); return len(re.findall(FR_W, n)) > len(re.findall(EN_W, n))
def is_english(t):
    n = norm(t); return len(re.findall(EN_W, n)) > len(re.findall(FR_W, n))
def rs(p, t): return re.search(p, t)
NUMW = {"six": 6, "huit": 8, "eight": 8, "dix": 10, "ten": 10, "douze": 12, "twelve": 12, "cinq": 5, "five": 5}

def parse(text, S):
    t = norm(text.strip())
    for w, n in NUMW.items(): t = re.sub(rf"\b{w}\b", str(n), t)
    for k, p in VENUES.items():
        if rs(p, t): S["venue"] = k
    if rs(r"haut de gamme|premium|luxe|chic|upscale|high.?end|palace|plus premium", t): S["tier"] = "premium"
    elif rs(r"etudiant|student|pas cher|cheap|petit budget|abordable|happy hour|moins cher|cheaper|populaire", t): S["tier"] = "budget"
    m = (rs(r"(?:prix\s*)?(?:max(?:imum)?|moins de|under|below|jusqu'a|pas plus de|<|maxi)\s*(\d+(?:[.,]\d+)?)\s*(?:€|eur|euros?)?", t)
         or rs(r"(\d+(?:[.,]\d+)?)\s*(?:€|eur|euros?)\s*(?:max|maximum|maxi)", t))
    if m and float(m.group(1).replace(",", ".")) < 40: S["cap"] = float(m.group(1).replace(",", "."))
    for m in re.finditer(r"(\d+)\s*(cocktails?|verres?|serves?|drinks?|boissons?|couverts|clients|covers|guests)\s*(?:par|/|a|per|each|chaque)?\s*(semaine|week|jour|day|soir|night|soiree)?", t):
        n, what, per = int(m.group(1)), m.group(2), m.group(3)
        if per:
            v = n * (7 if per in ("jour", "day", "soir", "night", "soiree") else 1)
            S["volume"] = v if what.startswith(("cocktail", "verre", "serve", "drink", "boisson")) else int(v * 0.5)
        elif what.startswith(("cocktail", "drink", "boisson")) and 3 <= n <= 16: S["n"] = n
        elif what.startswith(("couvert", "client", "cover", "guest")): S["volume"] = int(n * 7 * 0.5)
    m = rs(r"pour.?cost\s*(?:de|of|a|cible|target)?\s*(\d{2})\s*%", t)
    if m: S["target"] = int(m.group(1)) / 100
    for k, p in SEASONS.items():
        if rs(p, t): S["season"] = k
    for k, p in STYLES.items():
        if rs(p, t): S["styles"].add(k)
    neg = r"(?:pas de|pas d'|sans|no|without|except|aucun|pas trop)\s+(?:\w+\s+)?"
    for k, p in FLAVOURS.items():
        if rs(neg + r"(?:" + p + ")", t): S["flav"].discard(k); S["avoid_flav"].add(k)
        elif rs(p, t): S["flav"].add(k)
    for k, p in SPIRITS.items():
        if rs(neg + r"(?:" + p + ")", t): S["spirits"].discard(k); S["no_spirit"].add(k)
        elif rs(p, t): S["spirits"].add(k); S["no_spirit"].discard(k)
    if rs(r"plus de sans alcool|more (?:alcohol.?free|no.?alcohol|mocktails)|mocktails?|no.?low|alcohol.?free|sans alcool|dry january|janvier sobre|sobre", t):
        S["nolow"] = 0.5 if rs(r"dry january|janvier sobre", t) else max(S["nolow"], 0.3)
    if rs(r"rapide|\bvite\b|\brush\b|\bfast\b|\bquick|seul derriere|alone behind|un seul barman|pas de barman|no bartender|debit|high volume", t): S["fast"] = True
    for k, v in COMPETITORS.items():
        if k in t:
            S["comp"].add(k)
            if v[1] in SPIRITS: S["spirits"].add(v[1])
            elif v[1]: S["styles"].add(v[1])
    # follow-ups
    if rs(r"\bautre\b|another|different|d'autres|other options?|encore", t): S["offset"] += 1
    for m in re.finditer(r"(?:remplace|enleve|retire|supprime|sans le|sans la|replace|remove|swap|drop|pas de)\s+(?:le |la |les |l'|the )?([a-z0-9' &-]{3,30})", t):
        key = m.group(1).strip()
        hit = COC[COC.n_fr.str.contains(re.escape(key)) | COC.n_en.str.contains(re.escape(key))]
        if len(hit): S["removed"] |= set(hit.Cocktail_FR)
    return S

# ---------- 4. MENU ENGINE ----------
def target_for(r, S):                                             # champagne serves run a higher pour cost
    return S["target"] + (0.06 if "Mumm" in r.brands else 0)

def price_for(r, S):
    p = math.ceil(r.cost * VAT / target_for(r, S) * 2) / 2        # TTC price at target pour cost, rounded up to 0.50
    if S["tier"] == "premium": p = max(p, 12.0 if r.NoLow == 0 else 9.0)
    p = max(p, 4.0)
    if S["cap"]: p = min(p, S["cap"])
    return p

def score(r, S):
    s = 0.8 * r.Popularity + 2.5 * len(r.flav & S["flav"]) - 3 * len(r.flav & S["avoid_flav"])
    if S["season"]: s += 2 if S["season"] in r.seas else (-1.5 if S["season"] in ("summer", "winter") and "all" not in r.seas else 0)
    if S["spirits"]: s += 3 if r.base in S["spirits"] else 0
    if S["styles"]: s += 2 if r.Style in S["styles"] or ("apero" in S["styles"] and r.Style == "french") else 0
    if S["fast"]: s -= {1: 0, 2: 1, 3: 3}[int(r.Speed)]
    if S["nolow"] >= 0.3 and r.NoLow == 1: s += 2 if S["nolow"] >= 0.5 else 1        # more no/low asked: favour low-ABV serves too
    if S["tier"] == "premium": s += 1.5 if r.premium else -0.5
    if S["tier"] == "budget": s -= 1.5 if r.premium else 0
    v = S["venue"]
    if v == "student" and int(r.Speed) == 1: s += 0.5
    if v == "club" and r.Style == "highball": s += 1.5
    if v == "cocktail_bar" and r.Style == "classic": s += 1
    if v == "brasserie" and r.Style in ("french", "apero", "highball"): s += 1
    if v == "rooftop" and ("summer" in r.seas or r.Style == "apero"): s += 1
    if v == "hotel" and (r.premium or r.Style == "classic"): s += 1
    if S["cap"]:
        need = math.ceil(r.cost * VAT / target_for(r, S) * 2) / 2
        if need > S["cap"]: s -= 8 * (need / S["cap"] - 1)
    return s

GEN_FR = {"tonic": "tonic", "soda": "eau gazeuse", "ginger beer": "ginger beer", "ginger ale": "ginger ale", "cola": "cola", "grapefruit soda": "soda pamplemousse",
          "cranberry juice": "jus de cranberry", "pineapple juice": "jus d'ananas", "lime juice": "jus de citron vert", "lemon juice": "jus de citron",
          "coconut cream": "crème de coco", "espresso": "espresso", "hot coffee": "café chaud", "cream": "crème", "sugar syrup": "sirop de sucre",
          "orgeat syrup": "sirop d'orgeat", "grenadine syrup": "sirop de grenadine", "honey-ginger syrup": "sirop miel-gingembre", "rosemary syrup": "sirop de romarin",
          "triple sec": "triple sec", "crème de cassis": "crème de cassis", "aromatic bitters": "bitter aromatique", "aquafaba": "aquafaba"}
def num(x, lang): return (f"{x:g}".replace(".", ",") if lang == "fr" else f"{x:g}")

def item(r, S):
    i = 0 if S["lang"] == "fr" else 1
    price = price_for(r, S); ht = price / VAT
    rec = " · ".join(f"{num(cl, S['lang'])} cl {GEN_FR.get(ing, ing) if i == 0 else ing}" for ing, cl in r.recipe if ing not in ("water",))
    return {"name": r.Cocktail_FR if i == 0 else r.Cocktail_EN, "key": r.Cocktail_FR, "recipe": rec, "brands": r.brands, "base": r.base,
            "price": price, "cost": r.cost, "pc": r.cost / ht, "margin": ht - r.cost, "alc": r.alc_g, "std": r.alc_g / 10,
            "nolow": int(r.NoLow), "garnish": r.Garnish.split(" / ")[i] if " / " in r.Garnish else r.Garnish, "recipe_raw": r.recipe}

def build_menu(S):
    n = S["n"]
    d = COC[~COC.Cocktail_FR.isin(S["removed"]) & ~COC.base.isin(S["no_spirit"])]
    d = d.assign(sc=d.apply(lambda r: score(r, S), axis=1)).sort_values(["sc", "cost"], ascending=[False, True])
    def rot(rows):
        if not rows: return rows
        o = (S["offset"] * 2) % len(rows); return rows[o:] + rows[:o]
    free = rot([r for r in d.itertuples() if r.NoLow == 2])
    alc = rot([r for r in d.itertuples() if r.NoLow < 2])
    k_free = max(1, round(n * S["nolow"]))
    out = free[:k_free]
    per_base, per_brand = Counter(), Counter()
    cap_base = 3 if S["spirits"] else 2
    for r in alc:
        if len(out) >= n: break
        if per_base[r.base] >= (cap_base + 1 if r.base in S["spirits"] else cap_base): continue
        if any(per_brand[b] >= (2 if ING[ING.Brand == b].Category.iloc[0] in S["spirits"] else 1) for b in set(r.brands)): continue
        out.append(r); per_base[r.base] += 1
        for b in set(r.brands): per_brand[b] += 1
    for r in alc:                                                # relax diversity if still short
        if len(out) >= n: break
        if r not in out: out.append(r)
    items = [item(r, S) for r in out]
    alc_prices = [x["price"] for x in items if x["nolow"] < 2]
    if alc_prices:                                               # alcohol-free serves priced at ~65% of the alcoholic average
        floor = math.ceil(0.65 * sum(alc_prices) / len(alc_prices) * 2) / 2
        for x in items:
            if x["nolow"] == 2 and x["price"] < floor:
                x["price"] = min(floor, S["cap"] or floor); ht = x["price"] / VAT; x["pc"] = x["cost"] / ht; x["margin"] = ht - x["cost"]
    items.sort(key=lambda x: (x["nolow"] == 2, -x["price"]))
    return items

def stock(items, S):
    per = S["volume"] / max(1, len(items))
    need = Counter()
    for it in items:
        for ing, cl in it["recipe_raw"]:
            if ING.loc[ing, "Brand"]: need[ing] += cl * per
    return [(ing, ING.loc[ing, "Bottle_cl"], math.ceil(v / ING.loc[ing, "Bottle_cl"]), round(math.ceil(v / ING.loc[ing, "Bottle_cl"]) * ING.loc[ing, "Price_EUR_illustr"]))
            for ing, v in sorted(need.items(), key=lambda x: -x[1])]

# ---------- 5. TEXTS ----------
TXT = {
 "fr": {"hello": "Bonjour ! Décrivez votre établissement et je compose une carte cocktails chiffrée avec les marques Pernod Ricard : prix, pour cost, marge, et la commande de la semaine.\n"
                 "Essayez : « bar à cocktails à Lyon, 8 cocktails, prix max 12 €, été, 250 cocktails par semaine » ou « rooftop haut de gamme, 6 cocktails, plus de sans alcool ».\n"
                 "Ensuite : « remplace le Mojito », « prix max 12 », « pas de rhum », « autre ». Tapez « insights » pour le rapport trade marketing.",
        "ask": "Pour composer la carte, dites-m'en un peu plus : type d'établissement, nombre de cocktails, prix maximum, saison ou ambiance.",
        "menu": "Votre carte", "pc": "pour cost moyen", "margin": "marge / verre (HT)", "week": "marge / semaine", "order": "Commande hebdo", "bt": "bt",
        "free": "SANS ALCOOL", "low": "LÉGER", "std": "verre std", "over": "Au prix plafond de {c} €, {n} cocktail(s) dépassent 30 % de pour cost : à surveiller.",
        "comp": "{b} ne fait pas partie du portefeuille : alternative proposée, {a}.", "assume": "Hypothèses : {v} cocktails/semaine répartis à parts égales · pour cost cible {t} % · TVA 20 %.",
        "health": "L'abus d'alcool est dangereux pour la santé, à consommer avec modération.", "note": "Prototype indépendant, non affilié à Pernod Ricard · prix et recettes illustratifs · pour les professionnels CHR.",
        "bye": "Belle saison !", "reset": "On repart de zéro. Quel établissement, et combien de cocktails ?"},
 "en": {"hello": "Hi! Describe your venue and I'll build a costed cocktail menu with Pernod Ricard brands: price, pour cost, margin, and the week's bottle order.\n"
                 "Try: \"cocktail bar in Lyon, 8 cocktails, under 12 €, summer, 250 cocktails a week\" or \"upscale rooftop, 6 cocktails, more alcohol-free\".\n"
                 "Then: \"replace the Mojito\", \"max 12 €\", \"no rum\", \"another\". Type \"insights\" for the trade-marketing report.",
        "ask": "To build the menu, tell me a bit more: type of venue, number of cocktails, maximum price, season or mood.",
        "menu": "Your menu", "pc": "average pour cost", "margin": "margin / serve (ex-VAT)", "week": "margin / week", "order": "Weekly order", "bt": "btl",
        "free": "ALCOHOL-FREE", "low": "LOW", "std": "std drink", "over": "At the {c} € price cap, {n} cocktail(s) go above 30% pour cost: keep an eye on them.",
        "comp": "{b} isn't in the portfolio, so here's an alternative: {a}.", "assume": "Assumptions: {v} cocktails/week split evenly · target pour cost {t}% · 20% VAT.",
        "health": "Please drink responsibly.", "note": "Independent prototype, not affiliated with Pernod Ricard · illustrative prices and recipes · for on-trade professionals.",
        "bye": "Have a great season!", "reset": "Fresh start. What kind of venue, and how many cocktails?"},
}
def eur(x, lang): return (f"{x:,.2f} €".replace(",", " ").replace(".", ",") if lang == "fr" else f"€{x:,.2f}")
def eur0(x, lang): return (f"{x:,.0f} €".replace(",", " ") if lang == "fr" else f"€{x:,.0f}")

# ---------- 6. SESSION LOG + INSIGHTS ----------
LOG = []
def log(S, items, flagged):
    row = {"lang": S["lang"], "venue": S["venue"] or "", "tier": S["tier"] or "", "cap": S["cap"], "n": len(items), "season": S["season"] or "",
           "styles": sorted(S["styles"]), "flav": sorted(S["flav"]), "spirits": sorted(S["spirits"]), "excluded": sorted(S["no_spirit"]),
           "comp": sorted(S["comp"]), "brands": [b for it in items for b in set(it["brands"])], "free_share": sum(it["nolow"] == 2 for it in items) / max(1, len(items)),
           "avg_pc": sum(it["pc"] for it in items) / max(1, len(items)), "avg_price": sum(it["price"] for it in items) / max(1, len(items)),
           "bottles": {ing: b for ing, _, b, _ in stock(items, S)}, "flagged": flagged}
    if S.get("log_i") is not None: LOG[S["log_i"]] = row
    else: S["log_i"] = len(LOG); LOG.append(row)

def insights(lang):
    fr = lang == "fr"; i = 0 if fr else 1
    if not LOG: return {"type": "text", "lang": lang, "text": "Pas encore de carte dans cette session." if fr else "No menus built in this session yet."}
    df = pd.DataFrame(LOG)
    try: df.assign(**{c: df[c].astype(str) for c in ("styles", "flav", "spirits", "excluded", "comp", "brands", "bottles")}).to_csv("carte_insights.csv", index=False)
    except Exception: pass
    n = len(df); slots = sum(df.n)
    brand = Counter(b for bs in df.brands for b in bs); bott = Counter()
    for d in df.bottles: bott.update(d)
    comp = Counter(c for cs in df.comp for c in cs); flav = Counter(f for fs in df.flav for f in fs)
    ven = Counter(v for v in df.venue if v); asked = Counter(s for ss in df.spirits for s in ss)
    caps = df.cap.dropna()
    rows = [("Cartes construites" if fr else "Menus built", f"{n} · {slots} " + ("cocktails" if fr else "cocktails")),
            ("Établissements" if fr else "Venues", ", ".join(f"{VENUE_LABEL[k][i]} ({v})" for k, v in ven.most_common(3)) or "—"),
            ("Prix plafond médian" if fr else "Median price cap", eur(caps.median(), lang) if len(caps) else "—"),
            ("Goûts demandés" if fr else "Flavours asked", ", ".join(f"{FLAV_LABEL[k][i]} ({v})" for k, v in flav.most_common(3)) or "—"),
            ("Catégories demandées" if fr else "Categories asked", ", ".join(f"{SPIRIT_LABEL[k][i]} ({v})" for k, v in asked.most_common(3)) or "—"),
            ("Marques à la carte" if fr else "Brands on menus", ", ".join(f"{k} {v / slots:.0%}" for k, v in brand.most_common(4))),
            ("Part sans alcool" if fr else "Alcohol-free share", f"{df.free_share.mean():.0%}"),
            ("Pour cost moyen" if fr else "Average pour cost", f"{df.avg_pc.mean():.0%}"),
            ("Bouteilles / semaine (top)" if fr else "Bottles / week (top)", ", ".join(f"{k} {v}" for k, v in bott.most_common(3)))]
    gaps = [(f"Demande concurrente : {COMPETITORS[k][0]} × {v} → {COMPETITORS[k][2]}" if fr else f"Competitor ask: {COMPETITORS[k][0]} × {v} → {COMPETITORS[k][3]}") for k, v in comp.most_common(3)]
    fl = int(df.flagged.sum())
    if fl: gaps.append(f"{fl} cocktail(s) au-dessus de 30 % de pour cost à cause d'un prix plafond bas" if fr else f"{fl} cocktail(s) above 30% pour cost because of a low price cap")
    return {"type": "insights", "lang": lang, "rows": rows, "gaps": gaps,
            "note": ("Exporté dans carte_insights.csv : quelles marques entrent dans les cartes, à quel prix, quelles demandes concurrentes reviennent, et le volume de bouteilles généré par compte. De quoi préparer la visite d'un commercial."
                     if fr else "Exported to carte_insights.csv: which brands make it onto menus, at what price, which competitor requests come up, and the bottle volume each account generates. Useful prep for a sales visit.")}

# ---------- 7. CHAT ENGINE ----------
def fresh(): return {"log_i": None, "venue": None, "tier": None, "cap": None, "n": 8, "volume": 200, "target": 0.22, "season": None, "styles": set(),
                     "flav": set(), "avoid_flav": set(), "spirits": set(), "no_spirit": set(), "nolow": 0.15, "fast": False, "comp": set(),
                     "removed": set(), "offset": 0, "lang": "fr", "touched": False}
STATE = fresh()

def is_new_request(t):
    if re.match(r"\s*(autre|another|encore|plus |moins |remplace|enleve|retire|replace|remove|swap|pas de|sans|no |et |and |prix|max|price|under)", t): return False
    sig = [any(rs(p, t) for p in VENUES.values()), bool(rs(r"\d+\s*cocktails?\b(?!\s*(?:par|/|a|per))", t)), bool(rs(r"\d+\s*(?:€|eur)|max", t)),
           any(rs(p, t) for p in SEASONS.values()), bool(rs(r"par semaine|per week|a week|par jour|per day", t)), bool(rs(r"haut de gamme|premium|etudiant|student", t))]
    return sum(sig) >= 2

def chat_data(text):
    global STATE
    S, t = STATE, norm(text.strip())
    if is_french(text): S["lang"] = "fr"
    elif is_english(text): S["lang"] = "en"
    L, i = TXT[S["lang"]], 0 if S["lang"] == "fr" else 1
    if t in ("quit", "exit", "bye", "quitter", "au revoir"): return {"type": "text", "lang": S["lang"], "text": L["bye"], "end": True}
    if t in ("reset", "restart", "recommencer", "nouvelle carte"):
        lang = S["lang"]; STATE = fresh(); STATE["lang"] = lang; return {"type": "text", "lang": lang, "text": L["reset"]}
    if t in ("hi", "hello", "hey", "salut", "bonjour", "help", "aide"): return {"type": "text", "lang": S["lang"], "text": L["hello"]}
    if rs(r"^\s*(insights?|rapport|report|stats)\b", t):
        if rs(r"english|anglais", t): S["lang"] = "en"
        elif rs(r"francais|french", t): S["lang"] = "fr"
        return insights(S["lang"])
    if is_new_request(t):
        lang = S["lang"]; STATE = fresh(); STATE["lang"] = lang; S = STATE
    before = repr(sorted((k, str(v)) for k, v in S.items() if k not in ("lang", "log_i")))
    parse(text, S)
    changed = before != repr(sorted((k, str(v)) for k, v in S.items() if k not in ("lang", "log_i")))
    if changed: S["touched"] = True
    if not S["touched"]: return {"type": "text", "lang": S["lang"], "text": L["ask"]}
    items = build_menu(S)
    flagged = sum(1 for it in items if it["pc"] > 0.30)
    log(S, items, flagged)
    ctx = [VENUE_LABEL[S["venue"]][i]] if S["venue"] else []
    if S["tier"]: ctx.append({"premium": ("haut de gamme", "upscale"), "budget": ("petit budget", "budget")}[S["tier"]][i])
    if S["season"]: ctx.append(SEASON_LABEL[S["season"]][i])
    ctx += [STYLE_LABEL[s][i] for s in sorted(S["styles"])] + [FLAV_LABEL[f][i] for f in sorted(S["flav"])]
    ctx += [SPIRIT_LABEL[s][i] for s in sorted(S["spirits"])] + [("sans " if i == 0 else "no ") + SPIRIT_LABEL[s][i] for s in sorted(S["no_spirit"])]
    if S["cap"]: ctx.append(("max " if i == 0 else "max ") + eur(S["cap"], S["lang"]).replace(",00", ""))
    if S["fast"]: ctx.append("service rapide" if i == 0 else "fast service")
    notes = [L["comp"].format(b=COMPETITORS[c][0], a=COMPETITORS[c][2 + i]) for c in sorted(S["comp"])]
    if flagged and S["cap"]: notes.append(L["over"].format(c=f"{S['cap']:g}", n=flagged))
    avg_m = sum(it["margin"] for it in items) / len(items)
    return {"type": "menu", "lang": S["lang"], "items": items, "ctx": ctx, "notes": notes,
            "summary": {"pc": sum(it["pc"] for it in items) / len(items), "margin": avg_m, "week": avg_m * S["volume"]},
            "stock": stock(items, S), "assume": L["assume"].format(v=S["volume"], t=round(S["target"] * 100))}

def to_text(d):
    L = TXT[d["lang"]]; lang = d["lang"]
    if d["type"] == "text": return d["text"]
    if d["type"] == "insights":
        w = max(len(k) for k, _ in d["rows"]) + 2
        return "\n".join(["📊 Insights"] + [f"  {k:<{w}}{v}" for k, v in d["rows"]] + [f"  • {g}" for g in d["gaps"]] + [d["note"]])
    out = d["notes"] + [f"{L['menu']} ({' · '.join(d['ctx'])})" if d["ctx"] else L["menu"]]
    for it in d["items"]:
        tag = f" [{L['free']}]" if it["nolow"] == 2 else (f" [{L['low']}]" if it["nolow"] == 1 else "")
        out.append(f"  {it['name']}{tag} .... {eur(it['price'], lang)}\n      {it['recipe']}\n      pour cost {it['pc']:.0%} · {eur(it['margin'], lang)} · {num(round(it['std'], 1), lang)} {L['std']}")
    s = d["summary"]
    out.append(f"{L['pc']}: {s['pc']:.0%} · {L['margin']}: {eur(s['margin'], lang)} · {L['week']}: {eur0(s['week'], lang)}")
    out.append(f"{L['order']}: " + ", ".join(f"{ing} × {b}" for ing, _, b, _ in d["stock"]))
    return "\n".join(out + [d["assume"], L["health"], L["note"]])

def chat(text): return to_text(chat_data(text))

# ---------- 8. CHAT WINDOW (Colab / Jupyter) ----------
# Look: clean product UI in the group's navy / light-blue palette, with light motion:
# messages slide in, menu lines appear one by one, price leaders draw, bars grow, pour cost counts up.
# Logo: put the official logo file next to the script (name containing "logo") or set LOGO_PATH.
import time
NAVY, DEEP, SKY, MIST, WHITE, INKC, GREY, LINE, GREEN, RED = "#123F75", "#0B2A52", "#76A0CD", "#EEF3F9", "#FFFFFF", "#14213D", "#6B7A90", "#DCE5F0", "#2E9E7A", "#C0392B"
FONTS = "https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600;700&family=Barlow+Condensed:wght@500;600;700&display=swap"
CSS = f"""<link rel="stylesheet" href="{FONTS}"><style>
@property --n {{syntax:'<integer>';initial-value:0;inherits:false}}
@keyframes lcUp {{from{{opacity:0;transform:translateY(10px)}}to{{opacity:1;transform:none}}}}
@keyframes lcGrow {{from{{transform:scaleX(0)}}to{{transform:scaleX(1)}}}}
@keyframes lcCount {{from{{--n:0}}to{{--n:var(--to)}}}}
@keyframes lcDot {{0%,80%,100%{{transform:translateY(0);opacity:.35}}40%{{transform:translateY(-5px);opacity:1}}}}
@keyframes lcSheen {{from{{background-position:0% 0}}to{{background-position:200% 0}}}}
.lc {{font-family:Barlow,'Helvetica Neue',Arial,sans-serif;color:{INKC};font-size:14px;line-height:1.45}}
.lc .cond {{font-family:'Barlow Condensed',Barlow,'Arial Narrow',sans-serif}}
.lc .cap {{text-transform:uppercase;letter-spacing:.08em;font-size:11px;font-weight:600}}
.lc .new {{animation:lcUp .45s ease both}}
.lc .new .row {{opacity:0;animation:lcUp .5s ease forwards;animation-delay:calc(var(--i) * 110ms + 150ms)}}
.lc .new .lead {{transform-origin:left;transform:scaleX(0);animation:lcGrow .6s ease forwards;animation-delay:calc(var(--i) * 110ms + 350ms)}}
.lc .new .kpi {{opacity:0;animation:lcUp .5s ease forwards;animation-delay:calc(var(--i) * 140ms + var(--base, 1000ms))}}
.lc .new .bar {{transform-origin:left;transform:scaleX(0);animation:lcGrow .9s cubic-bezier(.2,.8,.2,1) forwards;animation-delay:calc(var(--i) * 90ms + var(--base, 1300ms))}}
.lc .count {{counter-reset:n var(--to)}}
.lc .new .count {{animation:lcCount 1.4s ease-out forwards;animation-delay:var(--base, 1000ms);counter-reset:n var(--n)}}
.lc .count::after {{content:counter(n)}}
.lc .dots span {{display:inline-block;width:7px;height:7px;margin:0 2px;border-radius:50%;background:{NAVY};animation:lcDot 1s infinite}}
.lc .dots span:nth-child(2) {{animation-delay:.15s}} .lc .dots span:nth-child(3) {{animation-delay:.3s}}
.lc-head {{background:linear-gradient(110deg,{NAVY} 0%,{DEEP} 45%,#1B4F8C 50%,{DEEP} 55%,{NAVY} 100%) !important;background-size:200% 100% !important;
  animation:lcSheen 9s linear infinite;border-radius:14px 14px 0 0}}
.lc-chip button, button.lc-chip {{font-family:Barlow,sans-serif !important;font-weight:600 !important;font-size:12.5px !important;background:{WHITE} !important;
  color:{NAVY} !important;border:1px solid {SKY} !important;border-radius:999px !important;margin:4px 6px 4px 0 !important}}
button.lc-send {{font-family:Barlow,sans-serif !important;font-weight:700 !important;color:{WHITE} !important;border-radius:10px !important}}
.lc-input input {{font-family:Barlow,sans-serif !important;border-radius:10px !important;border:1px solid {SKY} !important;padding:0 12px !important;font-size:14px !important}}
</style>"""

def _pill(txt, bg, fg):
    return f'<span class="cap" style="background:{bg};color:{fg};padding:2px 8px;border-radius:999px;font-size:10px;white-space:nowrap">{txt}</span>'

def _menu_html(d, L, i):
    lang = d["lang"]; out = []
    for n in d["notes"]:
        out.append(f'<div style="background:#F3F7FC;border-left:3px solid {SKY};border-radius:6px;padding:6px 10px;margin-bottom:10px;font-size:13px">{_html.escape(n)}</div>')
    chips = "".join(f'<span style="background:{MIST};color:{NAVY};border-radius:999px;padding:2px 10px;font-size:12px;font-weight:500;margin:0 6px 6px 0;display:inline-block">{_html.escape(c)}</span>' for c in d["ctx"])
    out.append(f'<div style="font-weight:700;font-size:22px;color:{NAVY};line-height:1.1">{L["menu"]}</div><div style="margin:8px 0 6px">{chips}</div>')
    for k, it in enumerate(d["items"]):
        tag = (_pill(L["free"], "#E3F5EE", GREEN) if it["nolow"] == 2 else _pill(L["low"], "#E8F0FA", NAVY) if it["nolow"] == 1 else "")
        pcs = f'color:{RED};font-weight:600' if it["pc"] > 0.30 else f'color:{GREY}'
        out.append(f'<div class="row" style="--i:{k};padding:10px 0;border-bottom:1px solid {LINE}">'
                   f'<div style="display:flex;align-items:baseline;gap:8px"><span style="font-weight:600;font-size:16px;white-space:nowrap">{_html.escape(it["name"])}</span>{tag}'
                   f'<span class="lead" style="--i:{k};flex:1;border-bottom:2px dotted {SKY};transform-origin:left;margin:0 4px;position:relative;top:-4px"></span>'
                   f'<span class="cond" style="font-weight:700;font-size:21px;color:{NAVY};white-space:nowrap">{eur(it["price"], lang)}</span></div>'
                   f'<div style="font-size:12.5px;color:{GREY};margin-top:1px">{_html.escape(it["recipe"])}' + (f' · <i>{_html.escape(it["garnish"])}</i>' if it["garnish"] else "") + '</div>'
                   f'<div style="font-size:11.5px;margin-top:3px;{pcs}">Pour cost {it["pc"]:.0%} &nbsp;·&nbsp; ' + ("Marge" if i == 0 else "Margin")
                   + f' {eur(it["margin"], lang)} &nbsp;·&nbsp; {num(round(it["std"], 1), lang)} {L["std"]}</div></div>')
    s = d["summary"]; base = 150 + 110 * len(d["items"]) + 300
    tile = lambda k, big, lab: (f'<div class="kpi" style="--i:{k};--base:{base}ms;flex:1;background:#F3F7FC;border-radius:10px;padding:10px 12px">'
                                f'<div class="cond" style="font-weight:700;font-size:30px;color:{NAVY};line-height:1">{big}</div>'
                                f'<div style="font-size:11.5px;color:{GREY};margin-top:4px">{lab}</div></div>')
    pc_html = f'<span class="count" style="--to:{round(s["pc"] * 100)};--base:{base}ms"></span>%'
    out.append(f'<div style="display:flex;gap:10px;margin-top:14px">' + tile(0, pc_html, L["pc"]) + tile(1, eur(s["margin"], lang), L["margin"])
               + tile(2, eur0(s["week"], lang), L["week"]) + '</div>')
    mx = max(b for _, _, b, _ in d["stock"]) if d["stock"] else 1
    bars = "".join(f'<div style="display:flex;align-items:center;gap:10px;margin:5px 0;font-size:12.5px">'
                   f'<span style="width:190px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{_html.escape(ing)}</span>'
                   f'<span style="flex:1;background:{MIST};border-radius:4px;height:12px"><span class="bar" style="--i:{k};--base:{base + 450}ms;display:block;height:12px;'
                   f'width:{b / mx * 100:.0f}%;background:linear-gradient(90deg,{NAVY},{SKY});border-radius:4px"></span></span>'
                   f'<span style="width:96px;text-align:right;font-weight:600">{b} {L["bt"]} · {eur0(cost, lang)}</span></div>'
                   for k, (ing, cl, b, cost) in enumerate(d["stock"]))
    out.append(f'<div style="margin-top:16px"><div class="cap" style="color:{NAVY};margin-bottom:4px">{L["order"]}</div>{bars}</div>')
    out.append(f'<div style="font-size:11.5px;color:{GREY};margin-top:10px">{_html.escape(d["assume"])}</div>'
               f'<div style="font-size:11px;color:{GREY};margin-top:6px;border-top:1px solid {LINE};padding-top:6px"><b>{L["health"]}</b> {L["note"]}</div>')
    return "".join(out)

def to_html(d):
    L, i = TXT[d["lang"]], 0 if d["lang"] == "fr" else 1
    if d["type"] == "text": return _html.escape(d["text"]).replace("\n", "<br>")
    if d["type"] == "insights":
        rows = "".join(f'<div class="row" style="--i:{k};display:flex;padding:8px 0;border-bottom:1px solid {LINE};gap:14px">'
                       f'<span style="width:210px;color:{GREY};font-size:12.5px">{_html.escape(a)}</span><span style="flex:1;font-weight:600">{_html.escape(v)}</span></div>'
                       for k, (a, v) in enumerate(d["rows"]))
        gaps = "".join(f'<div class="kpi" style="--i:{k};--base:{150 + 110 * len(d["rows"])}ms;background:#F3F7FC;border-left:3px solid {NAVY};border-radius:6px;padding:7px 10px;margin-top:6px;font-size:13px">{_html.escape(g)}</div>'
                       for k, g in enumerate(d["gaps"]))
        return (f'<div class="cap" style="color:{SKY}">Insights · trade marketing</div><div style="font-weight:700;font-size:22px;color:{NAVY};margin-bottom:6px">'
                + ("Ce que disent les cartes" if i == 0 else "What the menus say") + f'</div>{rows}<div style="margin-top:10px">{gaps}</div>'
                f'<div style="font-size:12px;color:{GREY};margin-top:10px">{_html.escape(d["note"])}</div>')
    return _menu_html(d, L, i)

LOGO_PATH = ""   # optional: official logo file; leave empty to auto-detect an image whose name contains "logo"
BADGE = (f'<div class="lc" style="margin-right:14px;width:46px;height:46px;border-radius:12px;background:{WHITE};display:flex;align-items:center;justify-content:center">'
         f'<span class="cond" style="font-weight:700;font-size:22px;color:{NAVY};letter-spacing:-.02em">LC</span></div>')
TITLE = (f'<div class="lc" style="display:flex;align-items:center;justify-content:space-between;width:640px"><div>'
         f'<div style="font-weight:700;font-size:24px;color:{WHITE};line-height:1.1">La Carte</div>'
         f'<div style="color:#B9CDE6;font-size:13px">Assistant carte cocktails · on-trade</div></div>'
         f'<span class="cap" style="color:{WHITE};border:1px solid {SKY};border-radius:999px;padding:3px 10px;font-size:10px">Prototype</span></div>')

def _logo_widget(w):
    path = LOGO_PATH if LOGO_PATH and os.path.exists(LOGO_PATH) else None
    if not path:
        for f in (".", "/content"):
            if os.path.isdir(f):
                for n in os.listdir(f):
                    if "logo" in n.lower() and n.lower().endswith((".png", ".jpg", ".jpeg", ".webp")): path = os.path.join(f, n); break
            if path: break
    if path:
        print("Logo loaded:", path)
        fmt = os.path.splitext(path)[1].lower().strip(".").replace("jpg", "jpeg")
        return w.Image(value=open(path, "rb").read(), format=fmt, layout=w.Layout(height="46px", width="auto", margin="0 14px 0 0"))
    return w.HTML(BADGE)

AVATAR = (f'<div style="width:32px;min-width:32px;height:32px;border-radius:50%;background:{NAVY};color:{WHITE};display:flex;align-items:center;justify-content:center;'
          f'margin:2px 10px 0 0" class="cond"><b style="font-size:13px">LC</b></div>')
def bubble(kind, inner, new=False):
    cls = ' class="new"' if new else ""
    if kind == "user":
        return (f'<div{cls} style="display:flex;justify-content:flex-end;margin:14px 0"><div style="background:{NAVY};color:{WHITE};padding:10px 15px;'
                f'border-radius:14px 14px 4px 14px;max-width:75%;font-weight:500">{inner}</div></div>')
    return (f'<div{cls} style="display:flex;align-items:flex-start;margin:14px 0">{AVATAR}'
            f'<div style="background:{WHITE};padding:14px 18px;border-radius:4px 14px 14px 14px;max-width:88%;border:1px solid {LINE};box-shadow:0 6px 18px rgba(18,63,117,.08)">{inner}</div></div>')
TYPING = '<div class="dots" style="padding:4px 2px"><span></span><span></span><span></span></div>'

def chat_window():
    import ipywidgets as w
    from IPython.display import display, HTML
    display(HTML(CSS))
    msgs = []                                        # (kind, html)
    log_box = w.HTML(layout=w.Layout(width="100%"))
    def refresh(extra=""):
        body = "".join(bubble(k, h, new=(j >= len(msgs) - 2)) for j, (k, h) in enumerate(msgs)) + extra
        log_box.value = (f'{CSS}<div class="lc" style="display:flex;flex-direction:column-reverse;height:620px;overflow-y:auto;background:{MIST};padding:0 18px">'
                         f'<div>{body}<div style="height:10px"></div></div></div>')
    header = w.HBox([_logo_widget(w), w.HTML(TITLE)], layout=w.Layout(width="100%", align_items="center", padding="14px 18px"))
    header.add_class("lc-head")
    box = w.Text(placeholder="Décrivez votre établissement / Describe your venue", layout=w.Layout(width="80%", height="40px")); box.add_class("lc-input")
    send = w.Button(description="Composer la carte", layout=w.Layout(width="18%", height="40px")); send.style.button_color = NAVY; send.add_class("lc-send")
    def say(text):
        if not text.strip(): return
        msgs.append(("user", _html.escape(text))); refresh(bubble("bot", TYPING, new=True))
        d = chat_data(text); time.sleep(0.7)
        msgs.append(("bot", to_html(d))); refresh()
    def on_send(_=None): t = box.value; box.value = ""; say(t)
    send.on_click(on_send); box.on_submit(on_send)
    chips = []
    for label, cmd in [("Bar à cocktails", "bar à cocktails, 8 cocktails, prix max 12 €, 250 cocktails par semaine"), ("Rooftop été", "rooftop haut de gamme, été, 8 cocktails"),
                       ("Apéro français", "brasserie, apéro français, service rapide, 6 cocktails"), ("+ Sans alcool", "plus de sans alcool"),
                       ("Autre proposition", "autre"), ("Insights", "insights"), ("Reset", "reset")]:
        b = w.Button(description=label, layout=w.Layout(width="auto")); b.add_class("lc-chip"); b.on_click(lambda _, c=cmd: say(c)); chips.append(b)
    msgs.append(("bot", to_html({"type": "text", "lang": "fr", "text": TXT["fr"]["hello"]}))); refresh()
    display(w.VBox([header, log_box, w.HBox(chips, layout=w.Layout(flex_flow="row wrap", padding="8px 0 2px")),
                    w.HBox([box, send], layout=w.Layout(justify_content="space-between"))], layout=w.Layout(width="800px")))

# ---------- 9. START ----------
def run_terminal():
    print(TXT["fr"]["hello"], "\n")
    while True:
        try: msg = input("Vous / You: ")
        except EOFError: break
        if not msg.strip(): continue
        d = chat_data(msg); print("\nAssistant:\n" + to_text(d) + "\n")
        if d.get("end"): break

try:
    get_ipython()
    chat_window()
except NameError:
    if __name__ == "__main__": run_terminal()
