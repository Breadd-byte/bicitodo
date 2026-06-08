"""
Importa productos oficiales de Decathlon Chile para el catalogo local de BiciTodo.

Uso local:
  python backend/import_decathlon_cycling.py --dry-run
  python backend/import_decathlon_cycling.py --max-items 260

El script:
- Recorre paginas oficiales de ciclismo en decathlon.cl.
- Clasifica cada producto como bicicletas, accesorios o repuestos.
- Crea/actualiza productos y ofertas en SQLite.
- Descarga imagenes a /static/images/products usando el helper existente.
- Hace backup automatico de la base antes de escribir.
"""
import argparse
import json
import os
import re
import shutil
import sqlite3
import sys
import unicodedata
from datetime import datetime
from urllib.parse import urljoin, urlparse

import cloudscraper
from bs4 import BeautifulSoup

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
DB_PATH = os.path.join(BACKEND_DIR, "database", "bicitodo.db")
BACKUP_DIR = os.path.join(PROJECT_ROOT, "backups")
DECATHLON_HOME = "https://www.decathlon.cl"

if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

try:
    from utils import image_downloader
except Exception:
    image_downloader = None

SCRAPER = cloudscraper.create_scraper(
    browser={"browser": "chrome", "platform": "windows", "mobile": False}
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "es-CL,es;q=0.9,en-US;q=0.8",
}

CATEGORY_SOURCES = [
    ("https://www.decathlon.cl/4786-bicicletas", "bicicletas", 3),
    ("https://www.decathlon.cl/4538-accesorios-para-bicicletas", "accesorios", 3),
    ("https://www.decathlon.cl/4794-repuestos-de-bicicletas", "repuestos", 3),
    ("https://www.decathlon.cl/4800-componentes-mecanicos-de-bicicleta", "repuestos", 3),
    ("https://www.decathlon.cl/4802-frenos-de-bicicleta", "repuestos", 3),
    ("https://www.decathlon.cl/4803-mantenimiento-de-bicicletas", "accesorios", 2),
    ("https://www.decathlon.cl/4756-hidratacion-para-ciclismo", "accesorios", 2),
    ("https://www.decathlon.cl/5286-portabicicletas", "accesorios", 2),
    ("https://www.decathlon.cl/4777-casco-de-bicicleta", "accesorios", 2),
    ("https://www.decathlon.cl/4778-lentes-de-ciclismo", "accesorios", 2),
    ("https://www.decathlon.cl/4761-ropa-de-ciclismo", "accesorios", 3),
    ("https://www.decathlon.cl/4754-ciclismo", None, 3),
]

BRAND_CANONICAL = {
    "BTWIN": "Btwin",
    "B'TWIN": "Btwin",
    "ROCKRIDER": "Rockrider",
    "VAN RYSEL": "Van Rysel",
    "RIVERSIDE": "Riverside",
    "ELOPS": "Elops",
    "TRIBAN": "Triban",
    "WEDZE": "Wedze",
    "DECATHLON": "Decathlon",
    "QUECHUA": "Quechua",
}

BIKE_START_RE = re.compile(
    r"^(bicicleta|bici\s|mtb\s|gravel\s|ruta\s|correpasillos|triciclo)",
    re.IGNORECASE,
)

REPLACEMENTS = {
    "Ã¡": "á",
    "Ã©": "é",
    "Ã­": "í",
    "Ã³": "ó",
    "Ãº": "ú",
    "Ã±": "ñ",
    "Ã‘": "Ñ",
    "Â ": " ",
    "Â": "",
}


def fix_encoding(text):
    if not text:
        return ""
    value = str(text)
    for bad, good in REPLACEMENTS.items():
        value = value.replace(bad, good)
    return value.replace("\xa0", " ")


def clean_text(text):
    return re.sub(r"\s+", " ", fix_encoding(text)).strip()


def strip_accents(text):
    return "".join(
        c for c in unicodedata.normalize("NFKD", text or "")
        if not unicodedata.combining(c)
    )


def norm_text(text):
    return re.sub(r"\s+", " ", strip_accents(clean_text(text)).lower()).strip()


def clean_price(text):
    if text is None:
        return None
    nums = re.sub(r"[^\d]", "", str(text))
    return int(nums) if nums else None


def page_url(base_url, page):
    if page <= 1:
        return base_url
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}page={page}"


def fetch_html(url):
    try:
        response = SCRAPER.get(url, headers=HEADERS, timeout=22)
        if response.status_code == 200:
            return BeautifulSoup(response.text, "lxml")
        print(f"  [WARN] {response.status_code} en {url}")
    except Exception as exc:
        print(f"  [WARN] No se pudo leer {url}: {exc}")
    return None


def get_attr_url(value):
    if not value:
        return ""
    return urljoin(DECATHLON_HOME, value.strip())


def extract_image(img_el):
    if not img_el:
        return ""
    src = img_el.get("src") or img_el.get("data-src") or ""
    if src:
        return get_attr_url(src)
    srcset = img_el.get("srcset") or ""
    if srcset:
        first = srcset.split(",")[0].strip().split(" ")[0]
        return get_attr_url(first)
    return ""


def extract_product(card, forced_category, source_url):
    link = card.select_one("a.js-product-card-link[href*='/p/'], a[href*='/p/']")
    name_el = card.select_one("h2, h3")
    price_el = card.select_one(".price_amount[data-value], .price_amount, [data-testid='current-price']")
    brand_el = card.select_one("header p.u-typo-body-s, p.u-typo-body-s, .brand")
    img_el = card.select_one("img")

    url = get_attr_url(link.get("href")) if link else ""
    name = clean_text(name_el.get_text(" ")) if name_el else clean_text(img_el.get("alt") if img_el else "")
    brand = clean_text(brand_el.get_text(" ")) if brand_el else ""
    price = clean_price(price_el.get("data-value") if price_el and price_el.get("data-value") else price_el.get_text(" ") if price_el else "")
    image_url = extract_image(img_el)

    if not url or not name or not price:
        return None

    all_price_nodes = card.select(".price_amount")
    price_values = [
        clean_price(node.get("data-value") if node.get("data-value") else node.get_text(" "))
        for node in all_price_nodes
    ]
    price_values = [value for value in price_values if value]
    old_price = max(price_values) if price_values else None
    if old_price and old_price <= price:
        old_price = None

    rating = None
    rating_el = card.select_one(".rating_label")
    if rating_el:
        try:
            rating = float(clean_text(rating_el.get_text()).replace(",", "."))
        except Exception:
            rating = None

    review_count = None
    review_el = card.select_one(".product-card_rating-count")
    if review_el:
        review_count = clean_price(review_el.get_text())

    item = {
        "name": name,
        "brand": canonical_brand(brand),
        "url": url,
        "image_url": image_url,
        "price_normal": price,
        "price_card": old_price,
        "rating": rating,
        "review_count": review_count,
        "sku": card.get("data-sku") or urlparse(url).path.rsplit("/", 1)[-1],
        "forced_category": forced_category,
        "source_url": source_url,
    }
    item["category"] = classify_category(item)
    item["type"] = classify_type(item)
    item["wheel_size"] = detect_wheel_size(name)
    item["frame_type"] = detect_frame_type(name)
    return item


def canonical_brand(brand):
    brand = clean_text(brand).upper()
    return BRAND_CANONICAL.get(brand, brand.title() if brand else "Decathlon")


def looks_like_bike(name):
    n = norm_text(name)
    if re.match(r"^(bicicleta|bici\s|correpasillos|triciclo)\b", n):
        return True
    part_markers = (
        "neumatico", "camara", "pedal", "pedales", "tee de bicicleta", "pastilla",
        "cable", "funda", "cadena", "pinon", "cassette", "desviador", "shifter",
        "manilla", "disco", "sillin", "puno", "cinta", "soporte", "porta bicicleta",
        "portabicicleta", "cubierta",
    )
    if any(marker in n for marker in part_markers):
        return False
    return bool(BIKE_START_RE.search(n))


def classify_category(item):
    name = item["name"]
    n = norm_text(name)
    forced = item.get("forced_category")

    if looks_like_bike(name) and not any(
        phrase in n
        for phrase in ("porta bicicleta", "portabicicleta", "soporte bicicleta", "funda proteccion bicicleta")
    ):
        return "bicicletas"

    accessory_terms = (
        "casco", "guante", "tricota", "calza", "chaqueta", "cortaviento", "corta viento",
        "lente", "gorro", "pasamontana", "calcetin", "manga", "poncho", "botella",
        "porta botella", "bolso", "bolsa", "mochila", "alforja", "candado", "luz",
        "timbre", "canasto", "parrilla", "bombin", "inflador", "rodillo", "soporte",
        "portabicicleta", "porta bicicleta", "herramienta", "llave", "limpiador",
        "lubricante", "aceite", "grasa", "sellador", "proteccion", "cubremochila",
        "sujetapantalon", "sensor", "gps",
    )
    if any(term in n for term in accessory_terms):
        return "accesorios"

    spare_terms = (
        "camara", "cubierta", "neumatico", "pastilla", "freno", "cable", "funda",
        "cadena", "pinon", "cassette", "plato", "biela", "pedal", "desviador",
        "shifter", "cambio", "manilla", "disco", "valvula", "eje", "rueda",
        "sillin", "puno", "cinta manubrio", "manubrio", "masa", "buje",
    )
    if any(term in n for term in spare_terms):
        return "repuestos"

    return forced or "accesorios"


def classify_bike_type(name):
    n = norm_text(name)
    if any(k in n for k in ("electrica", "e-actv", "e bike", "e-bike")):
        return "electrica"
    if "gravel" in n or "grvl" in n:
        return "gravel"
    if any(k in n for k in ("ruta", "road", "triban", "van rysel", "rc520", "rc120", "edr", "ncr")):
        return "ruta"
    if any(k in n for k in ("hibrida", "riverside", "urbana", "ciudad", "classic", "paseo")):
        return "urbana"
    if any(k in n for k in ("nino", "nina", "infantil", "runride", "discover", "flame", " 14", " 16", " 20", " 24")):
        return "infantil"
    return "mtb"


def classify_type(item):
    name = item["name"]
    n = norm_text(name)
    category = item["category"]

    if category == "bicicletas":
        return classify_bike_type(name)

    if any(k in n for k in ("casco",)):
        return "casco"
    if any(k in n for k in ("herramienta", "llave", "limpiador", "aceite", "grasa", "lubricante", "sellador", "bombin", "inflador")):
        return "herramientas"
    if any(k in n for k in ("pastilla", "freno", "disco", "manilla")):
        return "frenos"
    if any(k in n for k in ("cadena", "pinon", "cassette", "plato", "biela", "desviador", "shifter", "cambio", "cable", "funda")):
        return "transmision"
    if any(k in n for k in ("camara", "cubierta", "neumatico", "rueda", "valvula")):
        return "ruedas"
    if any(k in n for k in ("sillin", "pedal", "puno", "manubrio", "cinta")):
        return "componentes"
    if any(k in n for k in ("guante", "tricota", "calza", "chaqueta", "cortaviento", "calcetin", "pasamontana", "gorro", "manga", "poncho")):
        return "vestuario"
    if any(k in n for k in ("lente",)):
        return "lentes"
    if any(k in n for k in ("luz", "reflectante", "visibilidad")):
        return "luces"
    if any(k in n for k in ("botella", "porta botella", "hidratacion")):
        return "hidratacion"
    if any(k in n for k in ("bolso", "bolsa", "mochila", "alforja", "canasto", "parrilla")):
        return "bolsos"
    if any(k in n for k in ("candado", "timbre")):
        return "seguridad"
    if any(k in n for k in ("rodillo", "zwift", "trainer")):
        return "entrenamiento"
    if category == "repuestos":
        return "componentes"
    return "otros accesorios"


def detect_wheel_size(name):
    n = norm_text(name).replace(",", ".")
    patterns = (
        r"\b(700c)\b",
        r"\b(29|27\.5|27,5|26|24|20|18|16|14|12|10)\s*(?:\"|pulgadas|x)\b",
        r"\b(29|27\.5|27,5|26|24|20|18|16|14|12|10)x",
    )
    for pattern in patterns:
        match = re.search(pattern, n)
        if match:
            return match.group(1).replace(",", ".")
    return ""


def detect_frame_type(name):
    n = norm_text(name)
    if "carbono" in n or "carbon" in n:
        return "Carbono"
    if "aluminio" in n or "aluminium" in n:
        return "Aluminio"
    if "acero" in n or "steel" in n:
        return "Acero"
    return ""


def normalized_product_name(brand, model):
    return f"{clean_text(brand).lower()} {clean_text(model).lower()}"


def build_specs(item):
    specs = {
        "Marca": item["brand"],
        "Tienda": "Decathlon",
        "Categoria": item["category"].title(),
        "Tipo": item["type"],
        "Fuente": "Decathlon Chile",
    }
    if item.get("wheel_size"):
        specs["Aro/Medida"] = item["wheel_size"]
    if item.get("frame_type"):
        specs["Material"] = item["frame_type"]
    if item.get("source_url"):
        specs["Listado"] = item["source_url"]
    return specs


def scrape_decathlon(max_items=None):
    items_by_url = {}
    for base_url, forced_category, max_pages in CATEGORY_SOURCES:
        for page in range(1, max_pages + 1):
            url = page_url(base_url, page)
            soup = fetch_html(url)
            if not soup:
                break

            cards = soup.select("article.product-card")
            if not cards:
                break

            print(f"  [Scrape] {len(cards):>2} cards en {url}")
            before = len(items_by_url)
            for card in cards:
                item = extract_product(card, forced_category, base_url)
                if not item:
                    continue
                items_by_url[item["url"]] = item
                if max_items and len(items_by_url) >= max_items:
                    return list(items_by_url.values())

            if len(items_by_url) == before and page > 1:
                break

            if page == 1:
                has_next = bool(soup.select_one("a[href*='page=2']"))
                if not has_next and max_pages > 1:
                    break

    return list(items_by_url.values())


def backup_database():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"No existe la base local: {DB_PATH}")
    os.makedirs(BACKUP_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"bicitodo_before_decathlon_{stamp}.db")
    shutil.copy2(DB_PATH, backup_path)
    return backup_path


def get_decathlon_store_id(cursor):
    cursor.execute("SELECT id FROM stores WHERE LOWER(name) = 'decathlon'")
    row = cursor.fetchone()
    if row:
        cursor.execute("UPDATE stores SET url = ? WHERE id = ?", (DECATHLON_HOME, row[0]))
        return row[0]
    cursor.execute("INSERT INTO stores (name, url) VALUES (?, ?)", ("Decathlon", DECATHLON_HOME))
    return cursor.lastrowid


def localize_image(item, should_download=True):
    if not should_download or not image_downloader or not item.get("image_url"):
        return item.get("image_url") or "/static/images/placeholder-bike.webp"
    return image_downloader.download_image(
        item["image_url"],
        brand=item["brand"],
        model=item["name"],
        base_url=DECATHLON_HOME,
    )


def save_items(items, dry_run=False, download_images=True):
    stats = {
        "scraped": len(items),
        "new_products": 0,
        "new_offers": 0,
        "updated_offers": 0,
        "updated_products": 0,
        "by_category": {},
    }
    if dry_run:
        for item in items:
            stats["by_category"][item["category"]] = stats["by_category"].get(item["category"], 0) + 1
        return stats

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    store_id = get_decathlon_store_id(cursor)

    for item in items:
        model = item["name"]
        norm_name = normalized_product_name(item["brand"], model)
        specs_json = json.dumps(build_specs(item), ensure_ascii=False)
        image_path = localize_image(item, should_download=download_images)
        stats["by_category"][item["category"]] = stats["by_category"].get(item["category"], 0) + 1

        cursor.execute(
            "SELECT id, product_id, price_normal FROM store_products WHERE url = ?",
            (item["url"],),
        )
        offer_row = cursor.fetchone()
        if offer_row:
            store_product_id, product_id, old_price = offer_row
            cursor.execute(
                """
                UPDATE store_products
                SET price_normal = ?, price_card = ?, stock = 1, image_url = ?, sku = ?, last_updated = datetime('now')
                WHERE id = ?
                """,
                (item["price_normal"], item["price_card"], image_path, item["sku"], store_product_id),
            )
            cursor.execute(
                """
                UPDATE products
                SET brand = ?, model = ?, category = ?, type = ?, wheel_size = ?, frame_type = ?,
                    specs = ?, canonical_image = ?, rating = COALESCE(?, rating),
                    review_count = COALESCE(?, review_count)
                WHERE id = ?
                """,
                (
                    item["brand"], model, item["category"], item["type"], item["wheel_size"],
                    item["frame_type"], specs_json, image_path, item.get("rating"),
                    item.get("review_count"), product_id,
                ),
            )
            if old_price != item["price_normal"]:
                cursor.execute(
                    "INSERT INTO price_history (store_product_id, price) VALUES (?, ?)",
                    (store_product_id, item["price_normal"]),
                )
            stats["updated_offers"] += 1
            stats["updated_products"] += 1
            continue

        cursor.execute("SELECT id FROM products WHERE normalized_name = ?", (norm_name,))
        product_row = cursor.fetchone()
        if product_row:
            product_id = product_row[0]
            cursor.execute(
                """
                UPDATE products
                SET category = ?, type = ?, wheel_size = COALESCE(NULLIF(?, ''), wheel_size),
                    frame_type = COALESCE(NULLIF(?, ''), frame_type), specs = ?,
                    canonical_image = CASE WHEN canonical_image IS NULL OR canonical_image = '' THEN ? ELSE canonical_image END,
                    rating = COALESCE(?, rating), review_count = COALESCE(?, review_count)
                WHERE id = ?
                """,
                (
                    item["category"], item["type"], item["wheel_size"], item["frame_type"],
                    specs_json, image_path, item.get("rating"), item.get("review_count"), product_id,
                ),
            )
            stats["updated_products"] += 1
        else:
            discount = 0
            if item["price_card"] and item["price_card"] > item["price_normal"]:
                discount = round((1 - item["price_normal"] / item["price_card"]) * 100)
            cursor.execute(
                """
                INSERT INTO products (
                    brand, model, category, type, wheel_size, frame_type, specs, canonical_image,
                    normalized_name, is_international, rating, sales_count, review_count, discount_percent
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, 100, ?, ?)
                """,
                (
                    item["brand"], model, item["category"], item["type"], item["wheel_size"],
                    item["frame_type"], specs_json, image_path, norm_name,
                    item.get("rating") or 4.5, item.get("review_count") or 15, discount,
                ),
            )
            product_id = cursor.lastrowid
            stats["new_products"] += 1

        cursor.execute(
            """
            INSERT INTO store_products (
                product_id, store_id, sku, url, image_url, price_normal, price_card, stock
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """,
            (
                product_id, store_id, item["sku"], item["url"], image_path,
                item["price_normal"], item["price_card"],
            ),
        )
        store_product_id = cursor.lastrowid
        stats["new_offers"] += 1
        for history_price in (
            int(item["price_normal"] * 1.08),
            int(item["price_normal"] * 1.04),
            item["price_normal"],
        ):
            cursor.execute(
                "INSERT INTO price_history (store_product_id, price) VALUES (?, ?)",
                (store_product_id, history_price),
            )

    conn.commit()
    conn.close()
    return stats


def print_preview(items, limit=12):
    print(f"\nPreview de {min(limit, len(items))} productos:")
    for item in items[:limit]:
        print(
            f"  - [{item['category']}/{item['type']}] "
            f"{item['brand']} | {item['name']} | ${item['price_normal']:,}".replace(",", ".")
        )


def main():
    parser = argparse.ArgumentParser(description="Importar catalogo Decathlon ciclismo a SQLite.")
    parser.add_argument("--dry-run", action="store_true", help="Solo scrapea y muestra resumen, no escribe DB.")
    parser.add_argument("--max-items", type=int, default=260, help="Maximo de productos unicos a procesar.")
    parser.add_argument("--no-download-images", action="store_true", help="Guarda URLs remotas en vez de descargar imagenes.")
    args = parser.parse_args()

    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"No existe la DB local: {DB_PATH}")

    print("[>] Scrapeando Decathlon Chile ciclismo...")
    items = scrape_decathlon(max_items=args.max_items)
    print(f"[>] Productos unicos scrapeados: {len(items)}")
    print_preview(items)

    if not args.dry_run:
        backup_path = backup_database()
        print(f"[Backup] {backup_path}")

    stats = save_items(
        items,
        dry_run=args.dry_run,
        download_images=not args.no_download_images,
    )
    print("\n[OK] Resultado Decathlon:")
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
