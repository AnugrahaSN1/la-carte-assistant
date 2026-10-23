"""Builds the two CSVs for the menu assistant.
Brand names are real Pernod Ricard brands; prices, ABVs (rounded) and recipes are ILLUSTRATIVE.
Generic (unbranded) ingredients cover mixers, juices and syrups."""
import csv, os
OUT = os.path.dirname(os.path.abspath(__file__))

# ingredient, brand ("" = generic), category, ABV %, bottle cl, illustrative trade price EUR per bottle, premium flag
ING = [
 ("Absolut Vodka", "Absolut", "vodka", 40, 70, 15, 0), ("Absolut Citron", "Absolut", "vodka", 40, 70, 16, 0),
 ("Beefeater London Dry", "Beefeater", "gin", 40, 70, 14, 0), ("Plymouth Gin", "Plymouth", "gin", 41.2, 70, 24, 1),
 ("Monkey 47", "Monkey 47", "gin", 47, 50, 33, 1), ("Malfy Gin Con Limone", "Malfy", "gin", 41, 70, 22, 1),
 ("Havana Club 3 Años", "Havana Club", "rum", 40, 70, 13, 0), ("Havana Club 7 Años", "Havana Club", "rum", 40, 70, 22, 1),
 ("Malibu", "Malibu", "rum", 21, 70, 12, 0),
 ("Jameson", "Jameson", "whiskey", 40, 70, 18, 0), ("Chivas Regal 12", "Chivas Regal", "whisky", 40, 70, 25, 1),
 ("The Glenlivet 12", "The Glenlivet", "whisky", 40, 70, 28, 1),
 ("Martell VS", "Martell", "cognac", 40, 70, 28, 1),
 ("Olmeca Altos Plata", "Olmeca Altos", "tequila", 38, 70, 22, 0),
 ("Ricard", "Ricard", "anise", 45, 100, 18, 0), ("Lillet Blanc", "Lillet", "aperitif", 17, 75, 13, 0),
 ("Suze", "Suze", "aperitif", 15, 100, 14, 0), ("Italicus", "Italicus", "aperitif", 20, 70, 25, 1),
 ("Ramazzotti Aperitivo Rosato", "Ramazzotti", "aperitif", 15, 70, 14, 0),
 ("Mumm Cordon Rouge", "Mumm", "champagne", 12, 75, 28, 1),
 # generic
 ("tonic", "", "mixer", 0, 20, 0.6, 0), ("soda", "", "mixer", 0, 100, 0.8, 0), ("ginger beer", "", "mixer", 0, 20, 0.7, 0),
 ("ginger ale", "", "mixer", 0, 20, 0.6, 0), ("cola", "", "mixer", 0, 33, 0.5, 0), ("grapefruit soda", "", "mixer", 0, 25, 0.7, 0),
 ("cranberry juice", "", "juice", 0, 100, 2.5, 0), ("pineapple juice", "", "juice", 0, 100, 2.2, 0), ("lime juice", "", "juice", 0, 100, 4.0, 0),
 ("lemon juice", "", "juice", 0, 100, 3.5, 0), ("coconut cream", "", "juice", 0, 40, 2.4, 0), ("espresso", "", "juice", 0, 3, 0.25, 0),
 ("hot coffee", "", "juice", 0, 12, 0.3, 0), ("cream", "", "juice", 0, 50, 2.5, 0), ("water", "", "mixer", 0, 100, 0, 0),
 ("sugar syrup", "", "syrup", 0, 70, 3.5, 0), ("orgeat syrup", "", "syrup", 0, 70, 6, 0), ("grenadine syrup", "", "syrup", 0, 70, 5, 0),
 ("honey-ginger syrup", "", "syrup", 0, 70, 6, 0), ("rosemary syrup", "", "syrup", 0, 70, 6, 0), ("triple sec", "", "liqueur", 30, 70, 11, 0),
 ("crème de cassis", "", "liqueur", 15, 70, 10, 0), ("aromatic bitters", "", "liqueur", 44, 20, 12, 0), ("aquafaba", "", "juice", 0, 100, 0.5, 0),
]

# name FR, name EN, recipe "ingredient:cl;...", flavours, seasons, speed 1-3, style, no/low (0 full, 1 low, 2 alcohol-free), garnish
C = [
 ("Beefeater Tonic", "Beefeater & Tonic", "Beefeater London Dry:4;tonic:15", "fresh|bitter|herbal", "all|summer", 1, "highball", 0, "zeste de citron / lemon twist"),
 ("Monkey 47 Tonic", "Monkey 47 & Tonic", "Monkey 47:4;tonic:15", "fresh|herbal|bitter", "all|summer", 1, "highball", 0, "baies / berries"),
 ("Malfy Limone Tonic", "Malfy Limone Tonic", "Malfy Gin Con Limone:4;tonic:15", "fresh|citrus", "summer", 1, "highball", 0, "citron / lemon wheel"),
 ("Negroni Blanc", "White Negroni", "Plymouth Gin:3;Lillet Blanc:3;Suze:2", "bitter|herbal", "all|winter", 2, "classic", 0, "zeste / twist"),
 ("Lillet Vive", "Lillet Vive", "Lillet Blanc:5;tonic:10", "fresh|fruity", "summer", 1, "apero", 1, "concombre, fraise / cucumber, strawberry"),
 ("Italicus Royal", "Italicus Royale", "Italicus:3;Mumm Cordon Rouge:7", "citrus|fresh|sparkling", "all|summer|festive", 1, "apero", 0, "olive verte / green olive"),
 ("Spritz Rosato", "Rosato Spritz", "Ramazzotti Aperitivo Rosato:5;tonic:10", "fruity|fresh|bitter", "summer", 1, "apero", 1, "orange"),
 ("Vesper", "Vesper", "Beefeater London Dry:4.5;Absolut Vodka:1.5;Lillet Blanc:0.75", "strong|dry", "all|winter", 2, "classic", 0, "zeste de citron / lemon twist"),
 ("Moscow Mule", "Moscow Mule", "Absolut Vodka:4.5;ginger beer:12;lime juice:1.5", "fresh|spicy", "all|summer", 1, "highball", 0, "citron vert / lime"),
 ("Cosmopolitan", "Cosmopolitan", "Absolut Citron:4;triple sec:1.5;cranberry juice:3;lime juice:1.5", "fruity|citrus", "all|festive", 2, "classic", 0, "zeste d'orange / orange twist"),
 ("Espresso Martini", "Espresso Martini", "Absolut Vodka:5;espresso:3;sugar syrup:1.5", "coffee|sweet", "all|winter", 2, "classic", 0, "grains de café / coffee beans"),
 ("Mojito", "Mojito", "Havana Club 3 Años:5;lime juice:2.5;sugar syrup:2;soda:6", "fresh|citrus|sweet", "summer|all", 3, "classic", 0, "menthe / mint"),
 ("Daiquiri", "Daiquiri", "Havana Club 3 Años:5;lime juice:2.5;sugar syrup:1.5", "citrus|fresh", "summer|all", 2, "classic", 0, "citron vert / lime"),
 ("Cuba Libre", "Cuba Libre", "Havana Club 3 Años:5;cola:12;lime juice:1", "sweet|fresh", "all", 1, "highball", 0, "citron vert / lime"),
 ("Piña Colada", "Piña Colada", "Havana Club 3 Años:4;Malibu:2;pineapple juice:9;coconut cream:3", "tropical|sweet", "summer", 2, "classic", 0, "ananas / pineapple"),
 ("Malibu Ananas", "Malibu Pineapple", "Malibu:4;pineapple juice:12", "tropical|sweet", "summer", 1, "highball", 1, "ananas / pineapple"),
 ("Old Fashioned Havana 7", "Havana 7 Old Fashioned", "Havana Club 7 Años:5;sugar syrup:0.5;aromatic bitters:0.2", "strong|sweet", "all|winter", 2, "classic", 0, "zeste d'orange / orange twist"),
 ("Jameson Ginger & Lime", "Jameson Ginger & Lime", "Jameson:4;ginger ale:12;lime juice:1", "fresh|spicy", "all", 1, "highball", 0, "citron vert / lime"),
 ("Irish Coffee", "Irish Coffee", "Jameson:4;hot coffee:12;sugar syrup:1.5;cream:3", "coffee|sweet|warm", "winter|festive", 2, "classic", 0, "crème / cream"),
 ("Whisky Sour Chivas", "Chivas Whisky Sour", "Chivas Regal 12:5;lemon juice:2.5;sugar syrup:1.5;aquafaba:2", "citrus|smooth", "all", 2, "classic", 0, "cerise / cherry"),
 ("Glenlivet Highball", "Glenlivet Highball", "The Glenlivet 12:4;soda:12", "fresh|smooth", "all", 1, "highball", 0, "zeste / twist"),
 ("Penicillin Chivas", "Chivas Penicillin", "Chivas Regal 12:5;lemon juice:2.5;honey-ginger syrup:2", "spicy|citrus|smooth", "winter|all", 2, "classic", 0, "gingembre confit / candied ginger"),
 ("Sidecar Martell", "Martell Sidecar", "Martell VS:4.5;triple sec:2;lemon juice:2", "citrus|strong", "all|festive", 2, "classic", 0, "bord sucré / sugar rim"),
 ("Martell Tonic", "Martell & Tonic", "Martell VS:4;tonic:12", "fresh|smooth", "all|summer", 1, "highball", 0, "orange"),
 ("Mauresque", "Mauresque", "Ricard:2;orgeat syrup:1;water:10", "anise|fresh|sweet", "summer|all", 1, "french", 1, "glaçons / ice"),
 ("Tomate", "Ricard Tomate", "Ricard:2;grenadine syrup:1;water:10", "anise|sweet", "summer|all", 1, "french", 1, "glaçons / ice"),
 ("Margarita Altos", "Altos Margarita", "Olmeca Altos Plata:5;triple sec:2;lime juice:2.5", "citrus|fresh", "summer|all", 2, "classic", 0, "bord salé / salt rim"),
 ("Paloma", "Paloma", "Olmeca Altos Plata:5;grapefruit soda:12;lime juice:1", "fresh|citrus|bitter", "summer", 1, "highball", 0, "pamplemousse / grapefruit"),
 ("Kir Royal Mumm", "Mumm Kir Royale", "Mumm Cordon Rouge:8;crème de cassis:1", "fruity|sparkling", "festive|all", 1, "french", 0, ""),
 ("Suze Tonic", "Suze & Tonic", "Suze:4;tonic:12", "bitter|fresh|herbal", "summer|all", 1, "apero", 1, "pamplemousse / grapefruit"),
 ("Virgin Mojito", "Virgin Mojito", "lime juice:2.5;sugar syrup:2;soda:12", "fresh|citrus", "summer|all", 2, "no-alcohol", 2, "menthe / mint"),
 ("Garden Tonic (sans alcool)", "Garden Tonic (alcohol-free)", "tonic:15;rosemary syrup:1;lime juice:0.5", "fresh|herbal|bitter", "all|summer", 1, "no-alcohol", 2, "romarin, concombre / rosemary, cucumber"),
 ("Virgin Colada", "Virgin Colada", "pineapple juice:12;coconut cream:4;lime juice:1", "tropical|sweet", "summer", 2, "no-alcohol", 2, "ananas / pineapple"),
 ("Café Tonic", "Espresso Tonic", "espresso:3;tonic:12", "coffee|bitter|fresh", "all|summer", 1, "no-alcohol", 2, "orange"),
 ("Ginger Lime Fizz", "Ginger Lime Fizz", "ginger beer:12;lime juice:2;honey-ginger syrup:1", "spicy|fresh", "all|winter", 1, "no-alcohol", 2, "citron vert / lime"),
]
POP = {'Beefeater Tonic': 3, 'Monkey 47 Tonic': 2, 'Malfy Limone Tonic': 2, 'Negroni Blanc': 2, 'Lillet Vive': 2, 'Italicus Royal': 1, 'Spritz Rosato': 3, 'Vesper': 1, 'Moscow Mule': 3, 'Cosmopolitan': 2, 'Espresso Martini': 3, 'Mojito': 3, 'Daiquiri': 2, 'Cuba Libre': 2, 'Piña Colada': 3, 'Malibu Ananas': 2, 'Old Fashioned Havana 7': 2, 'Jameson Ginger & Lime': 2, 'Irish Coffee': 2, 'Whisky Sour Chivas': 2, 'Glenlivet Highball': 1, 'Penicillin Chivas': 2, 'Sidecar Martell': 1, 'Martell Tonic': 1, 'Mauresque': 2, 'Tomate': 1, 'Margarita Altos': 3, 'Paloma': 2, 'Kir Royal Mumm': 2, 'Suze Tonic': 1, 'Virgin Mojito': 3, 'Garden Tonic (sans alcool)': 2, 'Virgin Colada': 2, 'Café Tonic': 1, 'Ginger Lime Fizz': 2}  # indicative 1-3
with open(os.path.join(OUT, "ingredients_illustratif.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f); w.writerow(["Ingredient", "Brand", "Category", "ABV", "Bottle_cl", "Price_EUR_illustr", "Premium"]); w.writerows(ING)
with open(os.path.join(OUT, "cocktails_illustratif.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f); w.writerow(["Cocktail_FR", "Cocktail_EN", "Recipe_cl", "Flavours", "Seasons", "Speed", "Style", "NoLow", "Garnish", "Popularity"]); w.writerows([c + (POP[c[0]],) for c in C])
names = {i[0] for i in ING}
for c in C:
    for part in c[2].split(";"):
        assert part.split(":")[0] in names, part
print(len(ING), "ingredients,", len(C), "cocktails")
