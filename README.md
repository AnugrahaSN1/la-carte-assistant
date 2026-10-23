# La Carte

**A cocktail-menu assistant for bars and restaurants, built on the Pernod Ricard portfolio.**
Describe the venue in one sentence, in French or English, and get a costed menu: price, pour cost, margin per serve, alcohol per serve, and the weekly bottle order.

### ▶ [Try it live in your browser](https://anugrahasn1.github.io/la-carte-assistant/)

## Why

On-trade sales in Europe are under pressure. A bar owner does not need another brand presentation; they need a menu that sells and pays. A menu that does both also decides which bottles the bar orders every week.

## What it does

> *"Bar à cocktails à Lyon, 8 cocktails, prix max 12 €, été, 250 cocktails par semaine"*

| | |
|---|---|
| **Understands** | Venue type (student bar, rooftop, brasserie, hotel bar, club…), price cap, number of cocktails, season, style (classics, French apéritif, spritz), flavours, spirits wanted or excluded, fast service, weekly volume |
| **Builds the menu** | 35 recipes on 20 Pernod Ricard brands, chosen for fit, variety (no brand twice unless asked) and price |
| **Prices it** | Price at a 22% target pour cost, capped by the owner's maximum; champagne serves allowed a higher pour cost; alcohol-free drinks priced at ~65% of the menu average |
| **Stays responsible** | Every menu has alcohol-free options; each drink shows its alcohol in standard drinks (10 g); "dry january" or "plus de sans alcool" shifts the mix |
| **Orders** | Bottles per brand for the week, with the cost |
| **Handles competitors** | "un spritz comme l'Aperol" → Ramazzotti Rosato or Italicus, and the request is logged |
| **Follows up** | "remplace le Mojito", "pas de rhum", "prix max 11", "plus premium", "autre" |
| **Reports** | `insights`: which brands make it onto menus, price caps, no/low share, bottles generated per account, competitor requests. Exported to `carte_insights.csv` |

<p align="center"><img src="docs/demo_insights.png" width="560" alt="Insights panel"></p>

## Run it

**Browser:** open https://anugrahasn1.github.io/la-carte-assistant/ (nothing to install).

**Colab:** click the badge above and run the cell.

**Locally:**
```bash
pip install -r requirements.txt
jupyter notebook La_Carte.ipynb     # chat window
python carte_assistant.py           # or plain terminal chat
```

No API key, no paid service: Python and pandas only.

## Files

| File | Contents |
|---|---|
| `carte_assistant.py` | The assistant: parsing, menu engine, pricing, stock, insights, chat window |
| `cocktails_illustratif.csv` | 35 recipes with flavours, seasons, speed, style, no/low flag, indicative popularity |
| `ingredients_illustratif.csv` | 20 brand references and 24 generic ingredients with ABV, bottle size and an illustrative trade price |
| `make_data.py` | Rebuilds both CSVs |
| `index.html` | Browser version (same rules and data, ported to JavaScript), served by GitHub Pages |
| `web/` | Source of the browser version: `engine.js` and `build_web.py`, which builds `index.html` from the Python data |

## Honest limits

- **Trade prices, ABVs and recipes are illustrative**, not Pernod Ricard data. Margins and orders show the method, not real economics.
- The weekly order assumes the volume is split evenly across the menu.
- Popularity scores are my own judgement.
- The insights in the screenshot come from a 10-menu test session.

## About

Built by **Anugraha SN**, BBA student at EDHEC Business School.
Independent student prototype, not affiliated with or endorsed by Pernod Ricard. Brand names belong to their owners. Intended for licensed on-trade professionals.

*L'abus d'alcool est dangereux pour la santé, à consommer avec modération.*
