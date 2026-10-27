"""
ingest_brands.py - Ingestor multi-marca de bicicletas para BiciTodo.

Mejoras respecto a ingest_java_sunpeed.py:
  * Paginacion completa (Shopify products.json y WooCommerce Store API).
  * Marcas objetivo configurables (Trek, Java, Sunpeed, State Bicycle Co, ...).
  * Deduplicacion: si la URL ya existe se ACTUALIZA el precio; si el modelo ya
    existe (misma marca + nombre normalizado) se agrega solo la oferta.
  * NO inventa historial de precios: solo registra el precio real observado.
  * Cada fuente falla de forma aislada (si una tienda cae, las demas siguen).

Uso:
  python ingest_brands.py                # marcas objetivo
  python ingest_brands.py --all-brands   # cualquier bicicleta encontrada
  python ingest_brands.py --dry-run      # solo muestra lo que haria
"""
import argparse
import json
import os
import re
import sqlite3
import ssl
import time
import unicodedata
import urllib.request

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database", "bicitodo.db")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept": "application/json,text/html;q=0.9,*/*;q=0.8",
}

# Marca canonica -> alias que pueden aparecer en vendor/titulo
TARGET_BRANDS = {
    "Trek": ["trek"],
    "Java": ["java"],
    "Sunpeed": ["sunpeed", "sunspeed"],
    "State Bicycle Co": ["state bicycle", "state bike", "statebicycle"],
}

# Marcas conocidas para el modo --all-brands (normaliza el vendor)
KNOWN_BRANDS = {
    "scott": "Scott", "specialized": "Specialized", "giant": "Giant", "liv": "Liv",
    "cannondale": "Cannondale", "marin": "Marin", "cube": "Cube", "polygon": "Polygon",
    "norco": "Norco", "kona": "Kona", "merida": "Merida", "orbea": "Orbea", "bmc": "BMC",
    "santa cruz": "Santa Cruz", "mondraker": "Mondraker", "gt": "GT", "raleigh": "Raleigh",
    "oxford": "Oxford", "bianchi": "Bianchi", "pinarello": "Pinarello", "ridley": "Ridley",
    "megamo": "Megamo", "twitter": "Twitter", "aro": None,
}

# Tiendas Shopify (dominio, nombre en tabla stores)
SHOPIFY_STORES = [
    ("https://fauconbikes.cl", "Faucon Bikes"),
    ("https://bikenewsport.cl", "Bike New Sport"),
    ("https://triphelmets.com", "Trip Helmets"),
    ("https://bikeplus.cl", "BikePlus"),
    ("https://www.copenhague.cl", "Copenhague"),
]

# Tiendas WooCommerce Store API
WOO_STORES = [
    ("https://bluebike.cl", "BlueBike (Sunpeed Oficial)"),
]

NON_BIKE_WORDS = [
    "radar", "gps", "ciclocomputador", "luz ", "acople", "rueda", "ruedas", "tija",
    "horquilla", "manubrio", "porta", "casco", "zapatilla", "neumatico", "camara",
    "pedal", "sillin", "cuadro ", "frameset", "marco ", "rodillo", "repuesto",
    "guante", "jersey", "calza", "botella", "candado", "bombin", "inflador",
    "kit ", "cadena", "cassette", "freno", "grupo", "llanta", "maza", "parrilla",
]
MIN_BIKE_PRICE = 120_000

_ssl_ctx = ssl.create_default_context()


# --------------------------------------------------------------------------- utils
def strip_accents(text):
    return "".join(c for c in unicodedata.normalize("NFD", text or "") if unicodedata.category(c) != "Mn")


def norm(text):
    t = strip_accents(text).lower()
    t = re.sub(r"[^a-z0-9\. ]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def fetch_json(url, retries=2, timeout=20):
    last = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=timeout, context=_ssl_ctx) as resp:
                return json.loads(resp.read().decode("utf-8", errors="replace"))
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(1.5 * (attempt + 1))
    raise last


def detect_brand(vendor, title, all_brands):
    hay = norm(f"{vendor} {title}")
    for canon, aliases in TARGET_BRANDS.items():
        if any(re.search(rf"\b{re.escape(a)}\b", hay) for a in aliases):
            return canon
    if all_brands:
        v = norm(vendor)
        for key, canon in KNOWN_BRANDS.items():
            if canon and (v == key or re.search(rf"\b{re.escape(key)}\b", norm(title))):
                return canon
    return None


def is_bike(title, product_type, tags, price):
    t = norm(title)
    meta = norm(f"{product_type} {' '.join(tags or [])}")
    if price < MIN_BIKE_PRICE:
        return False
    if any(w in f"{t} " for w in NON_BIKE_WORDS) and not t.startswith("bicicleta"):
        return False
    return t.startswith("bicicleta") or "bicicleta" in meta or "bike" in meta or "bicicleta" in t


def infer_type(title, meta=""):
    t = norm(f"{title} {meta}")
    rules = [
        ("electrica", ["electrica", "e-bike", "ebike", "e bike", "allant+", "rail ", "powerfly", "pedelec"]),
        ("infantil", ["infantil", "nino", "nina", "kids", "precaliber", "aro 12", "aro 16", "aro 20 nin", "balance"]),
        ("plegable", ["plegable", "folding"]),
        ("gravel", ["gravel", "checkpoint", "charon", "universe", "4130 all-road", "all road"]),
        ("triatlon", ["triatlon", "contra reloj", "speed concept", "interstellar", " tt "]),
        ("ruta", ["ruta", "carretera", "road", "domane", "emonda", "madone", "kepler", "triton",
                  "siluro", "fuoco", "veloce", "invincible", "victory"]),
        ("bmx", ["bmx", "dirt jump"]),
        ("fixie", ["fixie", "fixed", "single speed", "singlespeed", "pista", "track", "core-line",
                   "4130 core", "black label"]),
        ("urbana", ["urbana", "city", "fx ", "dual sport", "verve", "cruiser", "paseo", "hibrida"]),
        ("mtb", ["mtb", "mountain", "montana", "marlin", "roscoe", "procaliber", "supercaliber",
                 "fuel", "slash", "top fuel", "x-caliber", "enduro", "trail", "aro 29", "aro 27.5"]),
    ]
    for btype, keys in rules:
        if any(k in f" {t} " for k in keys):
            return btype
    return "mtb"


def infer_wheel(title, btype):
    t = norm(title)
    m = re.search(r"\b(?:aro|rodado|r)\s?(12|14|16|20|24|26|27\.5|28|29)\b", t) or \
        re.search(r"\b(27\.5|29)\b", t)
    if m:
        return m.group(1)
    if "700" in t or btype in ("ruta", "gravel", "triatlon", "fixie"):
        return "700c"
    if btype == "plegable":
        return "20"
    if btype == "bmx":
        return "20"
    return "29" if btype == "mtb" else None


def infer_frame(title):
    t = norm(title)
    if any(k in t for k in ["carbon", "carbono", " slr", " sl ", "oclv", "di2"]):
        return "Carbono"
    if any(k in t for k in ["4130", "cromoly", "chromoly", "acero", "steel"]):
        return "Acero"
    return "Aluminio"


def bike_model_name(brand, title):
    clean = re.sub(r"\s+", " ", title).strip()
    if norm(brand).split()[0] not in norm(clean):
        clean = f"{brand} {clean}"
    if not norm(clean).startswith("bicicleta"):
        clean = f"Bicicleta {clean}"
    return clean


# --------------------------------------------------------------------------- sources
def scrape_shopify(domain, store_name, all_brands, max_pages=20):
    items = []
    for page in range(1, max_pages + 1):
        data = fetch_json(f"{domain}/products.json?limit=250&page={page}")
        products = data.get("products", [])
        if not products:
            break
        for p in products:
            title = p.get("title", "")
            brand = detect_brand(p.get("vendor", ""), title, all_brands)
            if not brand:
                continue
            variants = p.get("variants") or [{}]
            available = [v for v in variants if v.get("available")] or variants
            v0 = min(available, key=lambda v: float(v.get("price") or 0))
            price = int(float(v0.get("price") or 0))
            compare = int(float(v0.get("compare_at_price") or 0))
            tags = p.get("tags") or []
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",")]
            if not is_bike(title, p.get("product_type", ""), tags, price):
                continue
            images = p.get("images") or []
            btype = infer_type(title, p.get("product_type", ""))
            items.append({
                "brand": brand,
                "model": bike_model_name(brand, title),
                "type": btype,
                "wheel_size": infer_wheel(title, btype),
                "frame_type": infer_frame(title),
                "price_normal": price,
                "price_card": compare if compare > price else None,
                "stock": 1 if any(v.get("available") for v in variants) else 0,
                "url": f"{domain}/products/{p.get('handle')}",
                "image": images[0].get("src", "") if images else "",
                "store_name": store_name,
                "store_url": domain,
            })
        if len(products) < 250:
            break
    return items


def scrape_woocommerce(domain, store_name, all_brands, max_pages=20):
    items = []
    for page in range(1, max_pages + 1):
        prods = fetch_json(f"{domain}/wp-json/wc/store/v1/products?per_page=100&page={page}")
        if not prods:
            break
        for p in prods:
            title = re.sub(r"&#\d+;", "-", p.get("name", "")).strip()
            cats = [c.get("name", "") for c in p.get("categories", [])]
            # BlueBike es tienda oficial Sunpeed: si no se detecta marca, asumimos Sunpeed
            brand = detect_brand("", title, all_brands) or ("Sunpeed" if "bluebike" in domain else None)
            if not brand:
                continue
            prices = p.get("prices", {})
            minor = int(prices.get("currency_minor_unit", 0) or 0)
            div = 10 ** minor
            price = int(int(prices.get("price") or 0) / div)
            regular = int(int(prices.get("regular_price") or 0) / div)
            if not is_bike(title, " ".join(cats), [], price):
                continue
            btype = infer_type(title, " ".join(cats))
            imgs = p.get("images") or []
            items.append({
                "brand": brand,
                "model": bike_model_name(brand, title),
                "type": btype,
                "wheel_size": infer_wheel(title, btype),
                "frame_type": infer_frame(title),
                "price_normal": price,
                "price_card": regular if regular > price else None,
                "stock": 1 if p.get("is_in_stock", True) else 0,
                "url": p.get("permalink"),
                "image": imgs[0].get("src", "") if imgs else "",
                "store_name": store_name,
                "store_url": domain,
            })
        if len(prods) < 100:
            break
    return items


# --------------------------------------------------------------------------- persistence
def get_or_create_store(cur, name, url):
    cur.execute("SELECT id FROM stores WHERE name = ?", (name,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute("INSERT INTO stores (name, url) VALUES (?, ?)", (name, url))
    return cur.lastrowid


def find_product(cur, brand, model):
    key = norm(f"{brand} {model}")
    cur.execute("SELECT id FROM products WHERE category='bicicletas' AND brand = ? AND normalized_name = ?",
                (brand, key))
    row = cur.fetchone()
    return (row[0] if row else None), key


def persist(items, dry_run=False):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    stats = {"new_products": 0, "new_offers": 0, "updated_offers": 0}
    for it in items:
        if not it["url"] or it["price_normal"] <= 0:
            continue
        store_id = get_or_create_store(cur, it["store_name"], it["store_url"])

        cur.execute("SELECT id, price_normal FROM store_products WHERE url = ?", (it["url"],))
        existing = cur.fetchone()
        if existing:
            sp_id, old_price = existing
            cur.execute("""UPDATE store_products SET price_normal=?, price_card=?, stock=?,
                           image_url=COALESCE(NULLIF(?, ''), image_url), last_updated=CURRENT_TIMESTAMP
                           WHERE id=?""",
                        (it["price_normal"], it["price_card"], it["stock"], it["image"], sp_id))
            if old_price != it["price_normal"]:
                cur.execute("INSERT INTO price_history (store_product_id, price) VALUES (?, ?)",
                            (sp_id, it["price_normal"]))
            stats["updated_offers"] += 1
            continue

        product_id, key = find_product(cur, it["brand"], it["model"])
        if not product_id:
            specs = " • ".join(x for x in [it["brand"], it["type"].upper(),
                                            f"Aro {it['wheel_size']}" if it["wheel_size"] else None,
                                            f"Cuadro {it['frame_type']}"] if x)
            cur.execute("""INSERT INTO products (brand, model, category, type, wheel_size, frame_type,
                           specs, canonical_image, normalized_name, is_international)
                           VALUES (?, ?, 'bicicletas', ?, ?, ?, ?, ?, ?, 0)""",
                        (it["brand"], it["model"], it["type"], it["wheel_size"], it["frame_type"],
                         specs, it["image"], key))
            product_id = cur.lastrowid
            stats["new_products"] += 1

        cur.execute("""INSERT INTO store_products (product_id, store_id, url, image_url, price_normal,
                       price_card, stock, last_updated) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                    (product_id, store_id, it["url"], it["image"], it["price_normal"],
                     it["price_card"], it["stock"]))
        cur.execute("INSERT INTO price_history (store_product_id, price) VALUES (?, ?)",
                    (cur.lastrowid, it["price_normal"]))
        stats["new_offers"] += 1

    if dry_run:
        conn.rollback()
    else:
        conn.commit()
    conn.close()
    return stats


# --------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all-brands", action="store_true", help="Ingerir cualquier marca conocida")
    ap.add_argument("--dry-run", action="store_true", help="No guarda cambios")
    args = ap.parse_args()

    all_items = []
    for domain, name in SHOPIFY_STORES:
        try:
            got = scrape_shopify(domain, name, args.all_brands)
            print(f"[OK]  {name:<30} {len(got):>4} bicicletas")
            all_items += got
        except Exception as e:  # noqa: BLE001
            print(f"[ERR] {name:<30} {str(e)[:80]}")
    for domain, name in WOO_STORES:
        try:
            got = scrape_woocommerce(domain, name, args.all_brands)
            print(f"[OK]  {name:<30} {len(got):>4} bicicletas")
            all_items += got
        except Exception as e:  # noqa: BLE001
            print(f"[ERR] {name:<30} {str(e)[:80]}")

    by_brand = {}
    for it in all_items:
        by_brand[it["brand"]] = by_brand.get(it["brand"], 0) + 1
    print("\nPor marca:", dict(sorted(by_brand.items(), key=lambda x: -x[1])))

    stats = persist(all_items, dry_run=args.dry_run)
    print(("[DRY-RUN] " if args.dry_run else "") + f"Resultado: {stats}")


if __name__ == "__main__":
    main()
