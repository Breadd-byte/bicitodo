import sqlite3
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "backend", "database", "bicitodo.db")
JSON_PATH = os.path.join(BASE_DIR, "fronted", "data.json")

def sync():
    print("Sincronizando Java y Sunpeed con fronted/data.json...")
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Get Java and Sunpeed products from DB
    c.execute("""
        SELECT p.id, p.brand, p.model, p.type, p.wheel_size, p.frame_type, p.specs, p.canonical_image, p.category
        FROM products p
        WHERE LOWER(p.brand) IN ('java', 'sunpeed')
    """)
    products = c.fetchall()
    print(f"Productos Java y Sunpeed en DB: {len(products)}")

    # Remove any existing Java/Sunpeed in data['bicicletas'] to avoid duplicates
    data['bicicletas'] = [b for b in data.get('bicicletas', []) if b.get('brand', '').lower() not in ['java', 'sunpeed']]

    for p in products:
        p_id = p["id"]
        # get offers
        c.execute("""
            SELECT s.name as store_name, sp.price_normal, sp.price_card, sp.url, sp.image_url
            FROM store_products sp
            JOIN stores s ON sp.store_id = s.id
            WHERE sp.product_id = ?
            ORDER BY sp.price_normal ASC
        """, (p_id,))
        offers_rows = c.fetchall()

        offers = []
        for o in offers_rows:
            store_key = o["store_name"].lower().replace(" ", "").replace("_", "").replace("(", "").replace(")", "")
            offers.append({
                "store": o["store_name"],
                "storeKey": store_key,
                "price": o["price_normal"],
                "oldPrice": o["price_card"],
                "url": o["url"],
                "imageUrl": o["image_url"] or p["canonical_image"]
            })

        # get history
        c.execute("""
            SELECT ph.price
            FROM price_history ph
            JOIN store_products sp ON ph.store_product_id = sp.id
            WHERE sp.product_id = ?
            ORDER BY ph.timestamp ASC
        """, (p_id,))
        hist_rows = c.fetchall()
        history = [h["price"] for h in hist_rows] if hist_rows else [offers[0]["price"] if offers else 0]

        prod_obj = {
            "id": p_id,
            "brand": p["brand"],
            "model": p["model"],
            "type": p["type"] or "mtb",
            "wheelSize": p["wheel_size"] or "29",
            "frameType": p["frame_type"] or "Aluminio",
            "specs": p["specs"] or f"{p['brand']} • {p['model']}",
            "image": p["canonical_image"],
            "history": history,
            "fullSpecs": {},
            "offers": offers
        }
        data['bicicletas'].append(prod_obj)

    conn.close()

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"data.json actualizado exitosamente! Total bicicletas: {len(data['bicicletas'])}")

if __name__ == "__main__":
    sync()
