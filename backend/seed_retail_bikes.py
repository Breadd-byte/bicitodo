import sqlite3
import json
import os

DB_PATH = r"c:\Users\basti\Desktop\bicitodo\backend\database\bicitodo.db"

def seed_retail():
    print("[>] Starting seeding of retail bicycles for Falabella, Ripley, Paris, and Oxford...")
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Obtener IDs de las tiendas
    stores_to_find = ["Falabella", "Ripley", "Paris", "Oxford Store"]
    store_ids = {}
    for sname in stores_to_find:
        cursor.execute("SELECT id FROM stores WHERE name = ?", (sname,))
        row = cursor.fetchone()
        if row:
            store_ids[sname] = row[0]
        else:
            # Si no existe, crearla
            cursor.execute("INSERT INTO stores (name, url) VALUES (?, ?)", (sname, f"https://www.{sname.lower().replace(' ', '')}.cl"))
            store_ids[sname] = cursor.lastrowid
            print(f"  Created missing store: {sname} (ID: {store_ids[sname]})")

    print("Store IDs:", store_ids)

    # 2. Definición de Bicicletas Retail a agregar
    retail_bikes = [
        # --- FALABELLA ---
        {
            "brand": "Jeep",
            "model": "Bicicleta Mountain Bike Jeep Compass Aro 29",
            "category": "bicicletas",
            "type": "mtb",
            "wheel_size": "29",
            "frame_type": "Aluminio",
            "specs": "Jeep • Mountain Bike • Aro 29 • Frenos de Disco",
            "image": "assets/bikes/bike_6f8c9d8b64a8.jpg",
            "store": "Falabella",
            "price_normal": 219990,
            "price_card": 349990,
            "url": "https://www.falabella.com/falabella-cl/product/16892345/Bicicleta-Mountain-Bike-Jeep-Compass-Aro-29"
        },
        {
            "brand": "Bianchi",
            "model": "Bicicleta MTB Bianchi Duel Aro 29",
            "category": "bicicletas",
            "type": "mtb",
            "wheel_size": "29",
            "frame_type": "Aluminio",
            "specs": "Bianchi • MTB • Aro 29 • Suspensión Delantera",
            "image": "assets/bikes/bike_d0f6580f758d.jpg",
            "store": "Falabella",
            "price_normal": 279990,
            "price_card": 399990,
            "url": "https://www.falabella.com/falabella-cl/product/16901234/Bicicleta-MTB-Bianchi-Duel-Aro-29"
        },
        {
            "brand": "Trek",
            "model": "Bicicleta Mountain Bike Marlin 4 Gen 2 Aro 29",
            "category": "bicicletas",
            "type": "mtb",
            "wheel_size": "29",
            "frame_type": "Aluminio",
            "specs": "Trek • Marlin 4 • Aro 29 • Shimano 3x7",
            "image": "assets/bikes/bike_1fba1a152861.jpg",
            "store": "Falabella",
            "price_normal": 399990,
            "price_card": 499990,
            "url": "https://www.falabella.com/falabella-cl/product/16945678/Bicicleta-Mountain-Bike-Marlin-4-Gen-2-Aro-29"
        },
        {
            "brand": "Oxford",
            "model": "Bicicleta Paseo Oxford Rally Aro 26",
            "category": "bicicletas",
            "type": "urbana",
            "wheel_size": "26",
            "frame_type": "Acero",
            "specs": "Oxford • Urbana • Aro 26 • Con Tapabarros y Parrilla",
            "image": "assets/bikes/bike_29fa8c1955a7.jpg",
            "store": "Falabella",
            "price_normal": 189990,
            "price_card": 249990,
            "url": "https://www.falabella.com/falabella-cl/product/16978901/Bicicleta-Paseo-Oxford-Rally-Aro-26"
        },
        {
            "brand": "Specialized",
            "model": "Bicicleta Specialized Rockhopper Comp 29",
            "category": "bicicletas",
            "type": "mtb",
            "wheel_size": "29",
            "frame_type": "Aluminio",
            "specs": "Specialized • Rockhopper Comp • Aro 29 • 1x9 velocidades",
            "image": "assets/bikes/bike_b431fb7b8d7f.jpg",
            "store": "Falabella",
            "price_normal": 499990,
            "price_card": 649990,
            "url": "https://www.falabella.com/falabella-cl/product/16905533/Bicicleta-Specialized-Rockhopper-Comp-29"
        },

        # --- RIPLEY ---
        {
            "brand": "Jeep",
            "model": "Bicicleta Mountain Bike Jeep Vesuvio Aro 29",
            "category": "bicicletas",
            "type": "mtb",
            "wheel_size": "29",
            "frame_type": "Aluminio",
            "specs": "Jeep • Vesuvio MTB • Aro 29 • Freno Mecánico",
            "image": "assets/bikes/bike_f0a57e644813.jpg",
            "store": "Ripley",
            "price_normal": 229990,
            "price_card": 359990,
            "url": "https://simple.ripley.cl/bicicleta-mountain-bike-jeep-vesuvio-aro-29-2000392345112"
        },
        {
            "brand": "Lahsen",
            "model": "Bicicleta MTB Lahsen Everest Aro 29",
            "category": "bicicletas",
            "type": "mtb",
            "wheel_size": "29",
            "frame_type": "Aluminio",
            "specs": "Lahsen • Everest • Aro 29 • Suspensión Delantera",
            "image": "assets/bikes/bike_1fba1a152861.jpg",
            "store": "Ripley",
            "price_normal": 199990,
            "price_card": 299990,
            "url": "https://simple.ripley.cl/bicicleta-mtb-lahsen-everest-aro-29-2000394851221"
        },
        {
            "brand": "Trek",
            "model": "Bicicleta MTB Trek Marlin 5 Gen 3 Aro 29",
            "category": "bicicletas",
            "type": "mtb",
            "wheel_size": "29",
            "frame_type": "Aluminio",
            "specs": "Trek • Marlin 5 • Aro 29 • Frenos Hidráulicos",
            "image": "assets/bikes/bike_6f8c9d8b64a8.jpg",
            "store": "Ripley",
            "price_normal": 449990,
            "price_card": 549990,
            "url": "https://simple.ripley.cl/bicicleta-mtb-trek-marlin-5-gen-3-aro-29-2000398451223"
        },
        {
            "brand": "Oxford",
            "model": "Bicicleta Urbana Oxford Region Aro 28",
            "category": "bicicletas",
            "type": "urbana",
            "wheel_size": "28",
            "frame_type": "Aluminio",
            "specs": "Oxford • Region • Aro 28 • Con Luces y Guardabarros",
            "image": "assets/bikes/bike_29fa8c1955a7.jpg",
            "store": "Ripley",
            "price_normal": 239990,
            "price_card": 319990,
            "url": "https://simple.ripley.cl/bicicleta-urbana-oxford-region-aro-28-2000384756122"
        },

        # --- PARIS ---
        {
            "brand": "Jeep",
            "model": "Bicicleta MTB Jeep Grand Cherokee Aro 29",
            "category": "bicicletas",
            "type": "mtb",
            "wheel_size": "29",
            "frame_type": "Aluminio",
            "specs": "Jeep • Grand Cherokee • Aro 29 • 21 Velocidades",
            "image": "assets/bikes/bike_f0a57e644813.jpg",
            "store": "Paris",
            "price_normal": 249990,
            "price_card": 379990,
            "url": "https://www.paris.cl/bicicleta-mtb-jeep-grand-cherokee-aro-29-654923999"
        },
        {
            "brand": "Bianchi",
            "model": "Bicicleta MTB Bianchi Stone Aro 27.5",
            "category": "bicicletas",
            "type": "mtb",
            "wheel_size": "27.5",
            "frame_type": "Aluminio",
            "specs": "Bianchi • Stone • Aro 27.5 • Frenos V-Brake",
            "image": "assets/bikes/bike_d0f6580f758d.jpg",
            "store": "Paris",
            "price_normal": 239990,
            "price_card": 329990,
            "url": "https://www.paris.cl/bicicleta-mtb-bianchi-stone-aro-27.5-655012399"
        },
        {
            "brand": "Trek",
            "model": "Bicicleta MTB Trek Marlin 6 Gen 3 Aro 29",
            "category": "bicicletas",
            "type": "mtb",
            "wheel_size": "29",
            "frame_type": "Aluminio",
            "specs": "Trek • Marlin 6 • Aro 29 • Transmisión 1x10 Deore",
            "image": "assets/bikes/bike_1fba1a152861.jpg",
            "store": "Paris",
            "price_normal": 499990,
            "price_card": 599990,
            "url": "https://www.paris.cl/bicicleta-mtb-trek-marlin-6-gen-3-aro-29-655981299"
        },
        {
            "brand": "Oxford",
            "model": "Bicicleta MTB Oxford Merak 2 Aro 29",
            "category": "bicicletas",
            "type": "mtb",
            "wheel_size": "29",
            "frame_type": "Aluminio",
            "specs": "Oxford • Merak 2 • Aro 29 • Frenos Hidráulicos",
            "image": "assets/bikes/bike_29fa8c1955a7.jpg",
            "store": "Paris",
            "price_normal": 259990,
            "price_card": 349990,
            "url": "https://www.paris.cl/bicicleta-mtb-oxford-merak-2-aro-29-654871299"
        },
        {
            "brand": "Lahsen",
            "model": "Bicicleta Urbana Lahsen Paseo Aro 26",
            "category": "bicicletas",
            "type": "urbana",
            "wheel_size": "26",
            "frame_type": "Acero",
            "specs": "Lahsen • Paseo • Aro 26 • Canasto y Parrilla",
            "image": "assets/bikes/bike_6f8c9d8b64a8.jpg",
            "store": "Paris",
            "price_normal": 169990,
            "price_card": 229990,
            "url": "https://www.paris.cl/bicicleta-urbana-lahsen-paseo-aro-26-654012999"
        },

        # --- OXFORD STORE ---
        {
            "brand": "Oxford",
            "model": "Bicicleta Oxford Beast Aro 29 MTB",
            "category": "bicicletas",
            "type": "mtb",
            "wheel_size": "29",
            "frame_type": "Aluminio",
            "specs": "Oxford • Beast • Aro 29 • 21 Velocidades",
            "image": "assets/bikes/bike_29fa8c1955a7.jpg",
            "store": "Oxford Store",
            "price_normal": 299990,
            "price_card": 399990,
            "url": "https://www.oxfordstore.cl/bicicleta-oxford-beast-aro-29-mtb.html"
        },
        {
            "brand": "Oxford",
            "model": "Bicicleta Oxford Capital Aro 28 Urbana",
            "category": "bicicletas",
            "type": "urbana",
            "wheel_size": "28",
            "frame_type": "Aluminio",
            "specs": "Oxford • Capital • Aro 28 • Con Canasto Premium",
            "image": "assets/bikes/bike_6f8c9d8b64a8.jpg",
            "store": "Oxford Store",
            "price_normal": 249990,
            "price_card": 329990,
            "url": "https://www.oxfordstore.cl/bicicleta-oxford-capital-aro-28-urbana.html"
        },
        {
            "brand": "Cannondale",
            "model": "Bicicleta Cannondale Trail 5 Aro 29 MTB",
            "category": "bicicletas",
            "type": "mtb",
            "wheel_size": "29",
            "frame_type": "Aluminio",
            "specs": "Cannondale • Trail 5 • Aro 29 • Frenos de Disco Hidráulico",
            "image": "assets/bikes/bike_1fba1a152861.jpg",
            "store": "Oxford Store",
            "price_normal": 799990,
            "price_card": 949990,
            "url": "https://www.oxfordstore.cl/bicicleta-cannondale-trail-5-aro-29-mtb.html"
        },
        {
            "brand": "Cannondale",
            "model": "Bicicleta Cannondale Habit Carbon 3 Doble Suspensión",
            "category": "bicicletas",
            "type": "mtb",
            "wheel_size": "29",
            "frame_type": "Carbono",
            "specs": "Cannondale • Habit Carbon 3 • Aro 29 • Doble Suspensión • Deore 12v",
            "image": "assets/bikes/bike_b431fb7b8d7f.jpg",
            "store": "Oxford Store",
            "price_normal": 3299900,
            "price_card": 3999900,
            "url": "https://www.oxfordstore.cl/bicicleta-cannondale-habit-carbon-3-doble-suspension.html"
        },
        {
            "brand": "Oxford",
            "model": "Bicicleta Oxford Polux Aro 29 MTB",
            "category": "bicicletas",
            "type": "mtb",
            "wheel_size": "29",
            "frame_type": "Aluminio",
            "specs": "Oxford • Polux • Aro 29 • Suspensión Bloqueable",
            "image": "assets/bikes/bike_f0a57e644813.jpg",
            "store": "Oxford Store",
            "price_normal": 349990,
            "price_card": 449990,
            "url": "https://www.oxfordstore.cl/bicicleta-oxford-polux-aro-29-mtb.html"
        },
        {
            "brand": "Oxford",
            "model": "Bicicleta Oxford Merak 1 Aro 29 MTB",
            "category": "bicicletas",
            "type": "mtb",
            "wheel_size": "29",
            "frame_type": "Aluminio",
            "specs": "Oxford • Merak 1 • Aro 29 • Frenos de Disco",
            "image": "assets/bikes/bike_29fa8c1955a7.jpg",
            "store": "Oxford Store",
            "price_normal": 229990,
            "price_card": 299990,
            "url": "https://www.oxfordstore.cl/bicicleta-oxford-merak-1-aro-29-mtb.html"
        }
    ]

    inserted_count = 0
    offers_count = 0

    for b in retail_bikes:
        # Check if product already exists to avoid duplicates
        cursor.execute("SELECT id FROM products WHERE LOWER(brand) = LOWER(?) AND LOWER(model) = LOWER(?)", (b["brand"], b["model"]))
        p_row = cursor.fetchone()
        
        if p_row:
            p_id = p_row[0]
        else:
            # Insert product
            norm_name = f"{b['brand'].lower()} {b['model'].lower()}"
            cursor.execute("""
                INSERT INTO products (brand, model, category, type, wheel_size, frame_type, specs, canonical_image, normalized_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (b["brand"], b["model"], b["category"], b["type"], b["wheel_size"], b["frame_type"], b["specs"], b["image"], norm_name))
            p_id = cursor.lastrowid
            inserted_count += 1

        # Insert offer
        s_id = store_ids[b["store"]]
        
        # Check if offer already exists
        cursor.execute("SELECT id FROM store_products WHERE product_id = ? AND store_id = ?", (p_id, s_id))
        off_row = cursor.fetchone()
        
        if not off_row:
            cursor.execute("""
                INSERT INTO store_products (product_id, store_id, url, image_url, price_normal, price_card)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (p_id, s_id, b["url"], b["image"], b["price_normal"], b["price_card"]))
            sp_id = cursor.lastrowid
            offers_count += 1

            # Insert initial price history points
            cursor.execute("INSERT INTO price_history (store_product_id, price) VALUES (?, ?)", (sp_id, int(b["price_normal"] * 1.08)))
            cursor.execute("INSERT INTO price_history (store_product_id, price) VALUES (?, ?)", (sp_id, int(b["price_normal"] * 1.04)))
            cursor.execute("INSERT INTO price_history (store_product_id, price) VALUES (?, ?)", (sp_id, b["price_normal"]))

    conn.commit()
    print(f"\n[OK] Seeding finished successfully!")
    print(f"  - New products inserted: {inserted_count}")
    print(f"  - New store offers registered: {offers_count}")
    
    conn.close()

if __name__ == "__main__":
    seed_retail()
