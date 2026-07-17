"""
Importa bicicletas oficiales desde tiendas Shopify chilenas.

Uso:
  python backend/import_shopify_bikes.py --dry-run
  python backend/import_shopify_bikes.py

Fuentes actuales:
- Satiro Bikes: https://satiro.cl/collections/bicicletas/products.json
- Totem Chile: https://totem.cl/collections/bicicletas/products.json
- Faucon Bikes: ruta y gravel desde colecciones oficiales Shopify
"""
import argparse
import json
import os
import re
import shutil
import sqlite3
import sys
import time
import unicodedata
from datetime import datetime
from html.parser import HTMLParser
from urllib.parse import urljoin

import requests

try:
    import cloudscraper
except Exception:
    cloudscraper = None

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
DB_PATH = os.path.join(BACKEND_DIR, "database", "bicitodo.db")
BACKUP_DIR = os.path.join(PROJECT_ROOT, "backups")

if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

try:
    from utils import image_downloader
except Exception:
    image_downloader = None

SOURCES = [
    {
        "store_name": "Satiro Bikes",
        "store_url": "https://satiro.cl",
        "products_url": "https://satiro.cl/collections/bicicletas/products.json",
        "brand": "Sátiro",
    },
    {
        "store_name": "Totem Chile",
        "store_url": "https://totem.cl",
        "products_url": "https://totem.cl/collections/bicicletas/products.json",
        "brand": "Totem",
    },
    {
        "store_name": "Faucon Bikes",
        "store_url": "https://fauconbikes.cl",
        "products_url": "https://fauconbikes.cl/collections/ruta/products.json",
        "brand": "Faucon",
        "use_product_vendor": True,
        "forced_type": "ruta",
    },
    {
        "store_name": "Faucon Bikes",
        "store_url": "https://fauconbikes.cl",
        "products_url": "https://fauconbikes.cl/collections/bicicletas-de-gravel/products.json",
        "brand": "Faucon",
        "use_product_vendor": True,
        "forced_type": "gravel",
    },
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "es-CL,es;q=0.9,en-US;q=0.8",
}


def fetch_products_json(url):
    clients = [requests]
    if cloudscraper:
        clients.append(cloudscraper.create_scraper(browser={"browser": "chrome", "platform": "windows", "mobile": False}))

    last_error = None
    for attempt in range(4):
        client = clients[min(attempt, len(clients) - 1)]
        try:
            response = client.get(url, headers=HEADERS, timeout=30)
            if response.status_code in {403, 429, 503}:
                last_error = requests.HTTPError(f"HTTP {response.status_code} for {url}", response=response)
                time.sleep(2 * (attempt + 1))
                continue
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            last_error = exc
            time.sleep(1.5 * (attempt + 1))

    raise last_error


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        text = data.strip()
        if text:
            self.parts.append(text)


def clean_text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def strip_accents(value):
    return "".join(
        c for c in unicodedata.normalize("NFKD", value or "")
        if not unicodedata.combining(c)
    )


def norm_text(value):
    return strip_accents(clean_text(value)).lower()


def html_to_text(html):
    parser = TextExtractor()
    parser.feed(html or "")
    return clean_text(" | ".join(parser.parts))


def clean_price(value):
    if value in (None, ""):
        return None
    try:
        return int(round(float(str(value).replace(",", "."))))
    except Exception:
        digits = re.sub(r"[^\d]", "", str(value))
        return int(digits) if digits else None


def product_url(store_url, handle):
    return urljoin(store_url, f"/products/{handle}")


def image_url(product):
    images = product.get("images") or []
    if images:
        return images[0].get("src") or ""
    image = product.get("image") or {}
    return image.get("src") or ""


def available_variants(product):
    variants = product.get("variants") or []
    available = [v for v in variants if v.get("available")]
    return available or variants


def variant_prices(product):
    prices = []
    compare_prices = []
    for variant in available_variants(product):
        price = clean_price(variant.get("price"))
        compare_at = clean_price(variant.get("compare_at_price"))
        if price:
            prices.append(price)
        if compare_at:
            compare_prices.append(compare_at)
    return prices, compare_prices


def detect_type(title, description):
    title_text = norm_text(title)
    text = norm_text(f"{title} {description}")
    if "infantil" in text or "aro 12" in text or "aro 16" in text or "aro 20" in text:
        return "infantil"
    if "mtb" in title_text or "mountain" in title_text:
        return "mtb"
    if "gravel" in text:
        return "gravel"
    if "hibrida" in text or "urbana" in text or "ciudad" in text:
        return "urbana"
    if "ruta" in text or "rutera" in text or "road" in text or "sinclair" in text:
        return "ruta"
    if "mtb" in text or "mountain" in text:
        return "mtb"
    return "mtb"


def detect_wheel_size(title, description):
    text = norm_text(f"{title} {description}").replace(",", ".")
    patterns = (
        r"\b(700c)\b",
        r"\b(700)\s*[*x]\s*\d+\b",
        r"\b(29|27\.5|26|24|20|16)\s*(?:\"|x|[*])",
        r"\baro\s*(29|27\.5|26|24|20|16)\b",
    )
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            value = match.group(1)
            return "700c" if value == "700" else value
    return ""


def detect_frame_type(title, description):
    text = norm_text(f"{title} {description}")
    if "carbono" in text or "carbon" in text:
        return "Carbono"
    if "cromoly" in text or "cromo" in text:
        return "Cromoly"
    if "aluminio" in text:
        return "Aluminio"
    if "acero" in text:
        return "Acero"
    return ""


def pick_spec(description, label):
    pattern = re.compile(rf"{label}\s*:\s*([^|]+)", re.IGNORECASE)
    match = pattern.search(description)
    return clean_text(match.group(1)) if match else ""


def build_specs(source, product, description, item_type, wheel_size, frame_type, brand=None):
    specs = {
        "Marca": brand or source["brand"],
        "Tienda": source["store_name"],
        "Categoria": "Bicicletas",
        "Tipo": item_type,
        "Fuente": source["store_url"],
    }
    for label in ("Transmisión", "Transmision", "Frenos", "Ruedas", "Neumáticos", "Neumaticos", "Cuadro", "Horquilla"):
        value = pick_spec(description, label)
        if value:
            specs[label] = value
    if wheel_size:
        specs["Aro/Medida"] = wheel_size
    if frame_type:
        specs["Material"] = frame_type
    specs["Listado"] = source["products_url"].replace("/products.json", "")
    specs["Producto Shopify ID"] = str(product.get("id") or "")
    return specs


def normalized_product_name(brand, model):
    return f"{clean_text(brand).lower()} {clean_text(model).lower()}"


def localize_image(item, should_download=True):
    if not should_download or not image_downloader or not item.get("image_url"):
        return item.get("image_url") or "/static/images/placeholder-bike.webp"
    return image_downloader.download_image(
        item["image_url"],
        brand=item["brand"],
        model=item["name"],
        base_url=item["store_url"],
    )


def fetch_source(source, max_items=None):
    products = fetch_products_json(source["products_url"]).get("products") or []
    items = []

    for product in products:
        title = clean_text(product.get("title"))
        if not title or "bicicleta" not in norm_text(title):
            continue

        prices, compare_prices = variant_prices(product)
        if not prices:
            continue

        description = html_to_text(product.get("body_html"))
        brand = clean_text(product.get("vendor")) if source.get("use_product_vendor") else ""
        brand = brand or source["brand"]
        item_type = source.get("forced_type") or detect_type(title, description)
        wheel_size = detect_wheel_size(title, description)
        frame_type = detect_frame_type(title, description)
        price = min(prices)
        old_price = max(compare_prices) if compare_prices else None
        if old_price and old_price <= price:
            old_price = None

        item = {
            "name": title,
            "brand": brand,
            "store_name": source["store_name"],
            "store_url": source["store_url"],
            "url": product_url(source["store_url"], product.get("handle")),
            "image_url": image_url(product),
            "price_normal": price,
            "price_card": old_price,
            "sku": str(product.get("id") or product.get("handle")),
            "category": "bicicletas",
            "type": item_type,
            "wheel_size": wheel_size,
            "frame_type": frame_type,
            "specs": build_specs(source, product, description, item_type, wheel_size, frame_type, brand=brand),
        }
        items.append(item)
        if max_items and len(items) >= max_items:
            break

    return items


def scrape_all(max_items=None, store_names=None):
    items = []
    selected_stores = {name.lower() for name in store_names or []}
    for source in SOURCES:
        if selected_stores and source["store_name"].lower() not in selected_stores:
            continue
        source_items = fetch_source(source, max_items=max_items)
        print(f"  [Scrape] {source['store_name']}: {len(source_items)} bicicletas")
        items.extend(source_items)
    return items


def backup_database():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"No existe la base local: {DB_PATH}")
    os.makedirs(BACKUP_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"bicitodo_before_shopify_bikes_{stamp}.db")
    shutil.copy2(DB_PATH, backup_path)
    return backup_path


def get_store_id(cursor, item):
    cursor.execute("SELECT id FROM stores WHERE LOWER(name) = LOWER(?)", (item["store_name"],))
    row = cursor.fetchone()
    if row:
        cursor.execute("UPDATE stores SET url = ? WHERE id = ?", (item["store_url"], row[0]))
        return row[0]
    cursor.execute("INSERT INTO stores (name, url) VALUES (?, ?)", (item["store_name"], item["store_url"]))
    return cursor.lastrowid


def save_items(items, dry_run=False, download_images=True):
    stats = {
        "scraped": len(items),
        "new_products": 0,
        "new_offers": 0,
        "updated_products": 0,
        "updated_offers": 0,
        "by_store": {},
    }
    for item in items:
        stats["by_store"][item["store_name"]] = stats["by_store"].get(item["store_name"], 0) + 1
    if dry_run:
        return stats

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for item in items:
        store_id = get_store_id(cursor, item)
        model = item["name"]
        norm_name = normalized_product_name(item["brand"], model)
        specs_json = json.dumps(item["specs"], ensure_ascii=False)
        image_path = localize_image(item, should_download=download_images)

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
                SET store_id = ?, price_normal = ?, price_card = ?, stock = 1,
                    image_url = ?, sku = ?, last_updated = datetime('now')
                WHERE id = ?
                """,
                (store_id, item["price_normal"], item["price_card"], image_path, item["sku"], store_product_id),
            )
            cursor.execute(
                """
                UPDATE products
                SET brand = ?, model = ?, category = ?, type = ?, wheel_size = ?, frame_type = ?,
                    specs = ?, canonical_image = ?, rating = COALESCE(rating, 4.7),
                    review_count = COALESCE(review_count, 15)
                WHERE id = ?
                """,
                (
                    item["brand"], model, item["category"], item["type"], item["wheel_size"],
                    item["frame_type"], specs_json, image_path, product_id,
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
                    canonical_image = CASE WHEN canonical_image IS NULL OR canonical_image = '' THEN ? ELSE canonical_image END
                WHERE id = ?
                """,
                (item["category"], item["type"], item["wheel_size"], item["frame_type"], specs_json, image_path, product_id),
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
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 4.7, 100, 15, ?)
                """,
                (
                    item["brand"], model, item["category"], item["type"], item["wheel_size"],
                    item["frame_type"], specs_json, image_path, norm_name, discount,
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
            (product_id, store_id, item["sku"], item["url"], image_path, item["price_normal"], item["price_card"]),
        )
        store_product_id = cursor.lastrowid
        stats["new_offers"] += 1
        for history_price in (int(item["price_normal"] * 1.08), int(item["price_normal"] * 1.04), item["price_normal"]):
            cursor.execute(
                "INSERT INTO price_history (store_product_id, price) VALUES (?, ?)",
                (store_product_id, history_price),
            )

    conn.commit()
    conn.close()
    return stats


def print_preview(items):
    print(f"\nPreview de {len(items)} bicicletas:")
    for item in items:
        price = f"${item['price_normal']:,}".replace(",", ".")
        print(f"  - {item['store_name']} | {item['brand']} | {item['type']} | {item['name']} | {price}")


def main():
    parser = argparse.ArgumentParser(description="Importar bicicletas Shopify a SQLite.")
    parser.add_argument("--dry-run", action="store_true", help="Solo scrapea y muestra resumen, no escribe DB.")
    parser.add_argument("--max-items", type=int, default=None, help="Maximo por fuente.")
    parser.add_argument("--no-download-images", action="store_true", help="Guarda URLs remotas en vez de descargar imagenes.")
    parser.add_argument("--stores", nargs="*", help="Importa solo estas tiendas por nombre exacto, ej: Faucon Bikes.")
    args = parser.parse_args()

    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"No existe la DB local: {DB_PATH}")

    print("[>] Scrapeando bicicletas Shopify...")
    items = scrape_all(max_items=args.max_items, store_names=args.stores)
    print_preview(items)

    if not args.dry_run:
        backup_path = backup_database()
        print(f"[Backup] {backup_path}")

    stats = save_items(items, dry_run=args.dry_run, download_images=not args.no_download_images)
    print("\n[OK] Resultado Shopify bikes:")
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
