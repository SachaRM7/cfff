"""Récupère le catalogue public de qayyim.fr (API WooCommerce Store),
le range par rayons / sous-catégories et produit :
  - data/catalogue.json  (utilisé par la page)
  - data/catalogue.csv   (à ouvrir dans Excel / Sheets)
  - img/<id>.jpg         (vignettes 240 px)
Usage : python3 scripts/build_catalogue.py [--offline DOSSIER_JSON]
"""
import csv, html, io, json, os, re, sys, unicodedata, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://qayyim.fr/wp-json/wc/store/v1/products?per_page=100&page={}"
UA = {"User-Agent": "Mozilla/5.0 (catalogue-builder)"}

# Ordre d'affichage : rayon -> sous-catégories
RAYONS = [
    ("livres", "Livres", ["Coran", "Enfants", "Apprendre l'Islam", "Apprendre l'arabe",
        "Croyance", "Prière & jurisprudence", "Prophète & biographies", "Spiritualité",
        "Invocations & petits livres", "Femmes & mariage", "Mort & au-delà", "Roqya, rêves & santé"]),
    ("jeux", "Jeux éducatifs", ["Jeux de société & quiz", "Cartes d'arabe", "Puzzles"]),
    ("senteurs", "Musc & senteurs", ["Muscs en huile", "Muscs solides", "Parfums voiture",
        "Brumes & parfums d'intérieur", "Encens & bakhour"]),
    ("miel", "Miel & alimentation", ["Miels", "Dattes"]),
    ("nigelle", "Gamme nigelle", ["Huiles & gélules", "Hygiène & soins"]),
    ("soins", "Soins & hygiène", ["Dentifrices & miswak", "Savons & shampoings",
        "Baumes & huiles", "Beauté marocaine"]),
    ("medecine", "Médecine prophétique", ["Hijama", "Plantes & poudres"]),
    ("priere", "Prière & dévotion", ["Tasbih", "Tapis de prière", "Accessoires & décoration"]),
    ("omra", "Omra & Hajj", ["Omra & Hajj"]),
]

NAME_FIX = {3979: " (version fille)", 3975: " (version garçon)"}


def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def classify(p):
    cats = {html.unescape(c["name"]) for c in p["categories"]}
    n = norm(html.unescape(p["name"]))
    has = cats.__contains__
    # ---- hors livres
    if has("Omra et Hajj") or has("Packs & Coffrets") or "omra" in n or "ihram" in n:
        return "omra", "Omra & Hajj"
    if has("Jeux"):
        if has("Apprendre l’arabe"):
            return "jeux", "Cartes d'arabe"
        if "puzzle" in n:
            return "jeux", "Puzzles"
        return "jeux", "Jeux de société & quiz"
    if has("Muscs voiture"): return "senteurs", "Parfums voiture"
    if has("Muscs solides"): return "senteurs", "Muscs solides"
    if has("Parfums intérieurs"): return "senteurs", "Brumes & parfums d'intérieur"
    if has("Bakhour") or has("Tabkhira"): return "senteurs", "Encens & bakhour"
    if has("Muscs") or (has("Senteurs") and "musc" in n): return "senteurs", "Muscs en huile"
    if has("Miel"): return "miel", "Miels"
    if "datte" in n: return "miel", "Dattes"
    if has("Gamme nigelle"):
        if "huile" in n or "gelule" in n: return "nigelle", "Huiles & gélules"
        return "nigelle", "Hygiène & soins"
    if has("Hijama") and not has("Livres"): return "medecine", "Hijama"
    if has("Herbes et minéraux") or "costus" in n: return "medecine", "Plantes & poudres"
    if "dentifrice" in n or "miswak" in n or "siwak" in n: return "soins", "Dentifrices & miswak"
    if has("Produits beautés marocains") or "henne" in n: return "soins", "Beauté marocaine"
    if "savon" in n or "shampoing" in n: return "soins", "Savons & shampoings"
    if "baume" in n or has("Huile"): return "soins", "Baumes & huiles"
    if has("Tasbih"): return "priere", "Tasbih"
    if has("Tapis de prière") or has("Sans boussole") or "tapis" in n: return "priere", "Tapis de prière"
    if has("Accessoires de Prière") or has("Décorations") or "horloge" in n or "sticker" in n:
        return "priere", "Accessoires & décoration"
    # ---- livres (sous-catégorie la plus parlante d'abord)
    if has("Coran") and not has("Enfants"): return "livres", "Coran"
    if has("Enfants"): return "livres", "Enfants"
    if has("Apprendre l’arabe"): return "livres", "Apprendre l'arabe"
    if has("Mort et Monde Invisible"): return "livres", "Mort & au-delà"
    if has("Femmes") or has("Mariage"): return "livres", "Femmes & mariage"
    if has("Biographies") or "prophete" in n: return "livres", "Prophète & biographies"
    if has("Croyance"): return "livres", "Croyance"
    if has("Apprendre l’Islam") and not has("Jurisprudence"): return "livres", "Apprendre l'Islam"
    if has("Jurisprudence") or "priere" in n: return "livres", "Prière & jurisprudence"
    if has("Petits Livres") or "invocation" in n: return "livres", "Invocations & petits livres"
    if has("Spiritualité") or has("Développement personnel"): return "livres", "Spiritualité"
    if has("Médecine prophétique"): return "livres", "Roqya, rêves & santé"
    return "livres", "Roqya, rêves & santé"


def strip(s):
    s = re.sub(r"<[^>]+>", " ", html.unescape(s or ""))
    return re.sub(r"\s+", " ", s).strip()


def load(offline):
    out = []
    for page in range(1, 10):
        if offline:
            f = os.path.join(offline, f"p{page}.json")
            if not os.path.exists(f): break
            data = json.load(open(f))
        else:
            req = urllib.request.Request(API.format(page), headers=UA)
            data = json.load(urllib.request.urlopen(req, timeout=60))
        if not data: break
        out += data
    return out


def thumb(p):
    if not p["images"]: return None
    img = p["images"][0]
    cands = re.findall(r"(\S+) (\d+)w", img.get("srcset") or "")
    cands = sorted(((int(w), u) for u, w in cands), key=lambda x: x[0])
    for w, u in cands:
        if w >= 280: return u
    return img["thumbnail"] or img["src"]


def main():
    offline = sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "--offline" else None
    raw = load(offline)
    order = {k: i for i, (k, _, _) in enumerate(RAYONS)}
    sub_order = {(k, s): j for k, _, subs in RAYONS for j, s in enumerate(subs)}
    prods = []
    for p in sorted(raw, key=lambda p: p["id"]):
        r, s = classify(p)
        assert (r, s) in sub_order, (r, s, p["name"])
        pr = p["prices"]
        unit = 10 ** pr.get("currency_minor_unit", 2)
        price = (int(pr["price"]) / unit) if pr.get("price") and int(pr["price"]) > 0 else None
        rng = pr.get("price_range")
        opts = [{"n": a["name"], "v": [t["name"] for t in a["terms"]]} for a in p["attributes"]]
        prods.append({
            "id": p["id"],
            "name": html.unescape(p["name"]).strip() + NAME_FIX.get(p["id"], ""),
            "r": r, "s": s,
            "price": price,
            "priceMax": int(rng["max_amount"]) / unit if rng else None,
            "stock": bool(p["is_in_stock"]),
            "opts": opts,
            "desc": strip(p["short_description"])[:220],
            "url": p["permalink"],
            "sku": p.get("sku") or "",
            "siteCats": [html.unescape(c["name"]) for c in p["categories"]],
            "_img": thumb(p),
        })
    # images
    from PIL import Image
    os.makedirs(os.path.join(ROOT, "img"), exist_ok=True)
    for x in prods:
        dst = os.path.join(ROOT, "img", f"{x['id']}.jpg")
        x["img"] = f"img/{x['id']}.jpg" if x["_img"] else None
        if not x["_img"] or os.path.exists(dst): continue
        req = urllib.request.Request(x["_img"], headers=UA)
        im = Image.open(io.BytesIO(urllib.request.urlopen(req, timeout=60).read()))
        im = im.convert("RGBA")
        bg = Image.new("RGB", im.size, (255, 255, 255)); bg.paste(im, mask=im.split()[3])
        bg.thumbnail((240, 240))
        bg.save(dst, "JPEG", quality=78, optimize=True, progressive=True)
    for x in prods: x.pop("_img")
    data = {
        "source": "https://qayyim.fr",
        "rayons": [{"k": k, "name": n, "subs": s} for k, n, s in RAYONS],
        "products": prods,  # l'ordre (id croissant) sert d'index pour les codes de sélection
    }
    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    json.dump(data, open(os.path.join(ROOT, "data", "catalogue.json"), "w"), ensure_ascii=False, separators=(",", ":"))
    names = {k: n for k, n, _ in RAYONS}
    with open(os.path.join(ROOT, "data", "catalogue.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Rayon", "Sous-catégorie", "Produit", "Prix public (€)", "Variantes", "En stock", "Référence", "Lien"])
        for x in sorted(prods, key=lambda x: (order[x["r"]], sub_order[(x["r"], x["s"])], norm(x["name"]))):
            w.writerow([names[x["r"]], x["s"], x["name"],
                        "" if x["price"] is None else f"{x['price']:.2f}".replace(".", ","),
                        " | ".join(f"{o['n']} : {', '.join(o['v'])}" for o in x["opts"]),
                        "oui" if x["stock"] else "rupture", x["sku"], x["url"]])
    tpl = os.path.join(ROOT, "src", "page.html")
    if os.path.exists(tpl):
        page = open(tpl, encoding="utf-8").read()
        blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
        page = page.replace("/*__DATA__*/null", blob)
        head = ('<!doctype html>\n<html lang="fr">\n<head>\n<meta charset="utf-8">\n'
                '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
                '<style>:root{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}'
                'body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>\n')
        # le <title>, les polices et le <style> de la page vont dans <head>, le reste dans <body>
        split = page.index("</style>") + len("</style>")
        doc = head + page[:split] + "\n</head>\n<body>\n" + page[split:] + "\n</body>\n</html>\n"
        open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(doc)
    from collections import Counter
    c = Counter((x["r"], x["s"]) for x in prods)
    for k, n, subs in RAYONS:
        print(n, sum(c[(k, s)] for s in subs), {s: c[(k, s)] for s in subs})
    print("total", len(prods))


if __name__ == "__main__":
    main()
