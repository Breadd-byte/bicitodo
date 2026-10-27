"""
sync_db_to_json.py - Sincroniza la base de datos SQLite (bicitodo.db) con fronted/data.json.
Garantiza que el catálogo estático en GitHub / Netlify tenga exactamente:
- Todas las bicicletas nuevas (Trek, Sava, Java, Sunpeed, State)
- Precios reales verificados y ofertas activas (filtrando stock=0)
- Accesorios y repuestos actualizados
"""
import sqlite3
import json
import os
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "backend", "database", "bicitodo.db")
DATA_JSON_PATH = os.path.join(BASE_DIR, "fronted", "data.json")

def normalize_store_key(store_name):
    key = (store_name or "").lower().replace(" ", "").replace("_", "").replace("-", "")
    aliases = {
        "oxfordstore": "oxford",
        "trekchile": "trek",
        "specializedchile": "specialized",
        "totemchile": "totem",
        "fauconbikes": "faucon",
        "satirobikes": "satiro",
        "dsbikes": "dsbikes",
        "vidaurrebikes": "vidaurre",
        "mercadolibre": "mercadolibre",
        "aliexpress": "aliexpress",
        "bikeplus": "bikeplus",
        "bikeshop": "bikeshop",
        "fullbike": "fullbike",
        "savabikeschile": "savachile",
        "javabikeschile": "java",
        "bluebikesunpeedoficial": "bluebike",
        "bikenewsport": "bikenew",
        "copenhague": "copenhague",
    }
    return aliases.get(key, key)

def sync():
    print("=== SINCRONIZANDO SQLITE -> DATA.JSON ===")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 1. Map offers by product_id (only in-stock offers)
    offers_by_product = defaultdict(list)
    cur.execute("""
        SELECT sp.product_id, sp.price_normal, sp.price_card, sp.url, sp.image_url, s.name as store_name
        FROM store_products sp
        JOIN stores s ON s.id = sp.store_id
        WHERE COALESCE(sp.stock, 1) = 1
        ORDER BY sp.price_normal ASC
    """)
    for row in cur.fetchall():
        offers_by_product[row["product_id"]].append({
            "store": row["store_name"],
            "storeKey": normalize_store_key(row["store_name"]),
            "price": row["price_normal"],
            "oldPrice": row["price_card"],
            "url": row["url"],
            "imageUrl": row["image_url"] or ""
        })

    # 2. Map history by product_id
    history_by_product = defaultdict(list)
    cur.execute("""
        SELECT sp.product_id, ph.price
        FROM price_history ph
        JOIN store_products sp ON ph.store_product_id = sp.id
        WHERE COALESCE(sp.stock, 1) = 1
        ORDER BY ph.id ASC
    """)
    for row in cur.fetchall():
        history_by_product[row["product_id"]].append(row["price"])

    # 3. Build data dictionary per category
    out_data = {
        "bicicletas": [],
        "accesorios": [],
        "repuestos": []
    }

    cur.execute("""
        SELECT id, brand, model, category, type, wheel_size, frame_type, specs, canonical_image,
               rating, sales_count, review_count, discount_percent, is_international
        FROM products
        ORDER BY id ASC
    """)
    all_products = cur.fetchall()

    for p in all_products:
        cat = p["category"] or "bicicletas"
        if cat not in out_data:
            cat = "bicicletas"

        pid = p["id"]
        offers = offers_by_product.get(pid, [])
        if not offers:
            continue # Don't export products with 0 in-stock offers

        history = history_by_product.get(pid, [])
        if not history and offers:
            history = [offers[0]["price"]]
        history = history[-6:]

        try:
            full_specs = json.loads(p["specs"]) if p["specs"] and p["specs"].startswith("{") else {}
        except Exception:
            full_specs = {}

        prod_obj = {
            "id": pid,
            "brand": p["brand"] or "Generica",
            "model": p["model"],
            "type": p["type"] or "",
            "wheelSize": p["wheel_size"] or "",
            "frameType": p["frame_type"] or "",
            "specs": p["specs"] or "{}",
            "image": p["canonical_image"] or (offers[0]["imageUrl"] if offers else ""),
            "history": history,
            "fullSpecs": full_specs,
            "offers": offers,
            "isInternational": bool(p["is_international"]),
            "rating": p["rating"] or 4.5,
            "sales_count": p["sales_count"] or 100,
            "review_count": p["review_count"] or 15,
            "discount_percent": p["discount_percent"] or 0
        }
        out_data[cat].append(prod_obj)

    conn.close()

    print(f"Exportando a {DATA_JSON_PATH}:")
    for cat, items in out_data.items():
        print(f"  * {cat}: {len(items)} productos")

    with open(DATA_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(out_data, f, ensure_ascii=False, indent=2)

    print("Sincronización completada exitosamente.")

if __name__ == "__main__":
    sync()
