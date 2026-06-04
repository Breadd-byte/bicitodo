# seed_aliexpress_products.py - Seed AliExpress cycling products into SQLite database
import sys
import os
import sqlite3
import json

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

DB_PATH = r"c:\Users\basti\Desktop\bicitodo\backend\database\bicitodo.db"

ALIEXPRESS_PRODUCTS = [
    {
        "brand": "ZTTO",
        "model": "Pedales de Ruta de Carbono SPD-SL",
        "category": "repuestos",
        "type": "pedales",
        "specs": "ZTTO • Fibra de carbono • Compatibles con SPD-SL • Eje de titanio",
        "image": "https://images.unsplash.com/photo-1485965120184-e220f721d03e?auto=format&fit=crop&w=600&h=400&q=80",
        "price_normal": 29990,
        "price_card": 39990,
        "url": "https://es.aliexpress.com/item/1005001234567891.html",
        "fullSpecs": {"Material": "Carbono", "Peso": "250g el par", "Compatibilidad": "Shimano SPD-SL"}
    },
    {
        "brand": "Sensah",
        "model": "Grupo de Transmisión Empire Pro 2x11v Carbono",
        "category": "repuestos",
        "type": "transmision",
        "specs": "Sensah • Transmisión 2x11 • Manetas de carbono • Desviador y cambio trasero",
        "image": "https://images.unsplash.com/photo-1532298229144-0ec0c57515c7?auto=format&fit=crop&w=600&h=400&q=80",
        "price_normal": 124990,
        "price_card": 159990,
        "url": "https://es.aliexpress.com/item/1005001234567892.html",
        "fullSpecs": {"Velocidades": "11 velocidades", "Material Manetas": "Fibra de Carbono", "Compatibilidad": "SRAM / Shimano"}
    },
    {
        "brand": "GUB",
        "model": "Casco Aerodinámico In-Mold Pro Mips",
        "category": "accesorios",
        "type": "cascos",
        "specs": "GUB • Casco de ruta • Sistema In-Mold • Canales de ventilación Aero",
        "image": "https://images.unsplash.com/photo-1599819811279-d5ad9cccf838?auto=format&fit=crop&w=600&h=400&q=80",
        "price_normal": 19990,
        "price_card": 29990,
        "url": "https://es.aliexpress.com/item/1005001234567893.html",
        "fullSpecs": {"Peso": "270g", "Ventilación": "21 canales", "Tecnología": "In-Mold / Mips"}
    },
    {
        "brand": "RockBros",
        "model": "Luz Trasera Inteligente con Sensor de Freno USB",
        "category": "accesorios",
        "type": "luces",
        "specs": "RockBros • Sensor de freno inteligente • Recargable USB • Resistente al agua IPX6",
        "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=600&h=400&q=80",
        "price_normal": 12990,
        "price_card": 18990,
        "url": "https://es.aliexpress.com/item/1005001234567894.html",
        "fullSpecs": {"Batería": "500mAh USB", "Modos": "6 modos", "Sensor": "Sensor de desaceleración inteligente"}
    },
    {
        "brand": "iGPSPORT",
        "model": "Ciclocomputador GPS iGS320 con ANT+ y BLE",
        "category": "accesorios",
        "type": "ciclocomputadores",
        "specs": "iGPSPORT • Conexión GPS + BeiDou • Autonomía 72h • Sincronización Strava",
        "image": "https://images.unsplash.com/photo-1517649763962-0c623066013b?auto=format&fit=crop&w=600&h=400&q=80",
        "price_normal": 34990,
        "price_card": 49990,
        "url": "https://es.aliexpress.com/item/1005001234567895.html",
        "fullSpecs": {"Pantalla": "2.4 pulgadas", "Batería": "Hasta 72 horas", "Sensores": "ANT+ (Cadencia, Frecuencia Cardíaca)"}
    },
    {
        "brand": "TOSEEK",
        "model": "Manubrio de Carbono Integrado de Ruta Aero",
        "category": "repuestos",
        "type": "manubrios",
        "specs": "TOSEEK • Fibra de carbono T800 • Manubrio integrado Aero • Cableado interno",
        "image": "https://images.unsplash.com/photo-1485965120184-e220f721d03e?auto=format&fit=crop&w=600&h=400&q=80",
        "price_normal": 48990,
        "price_card": 65990,
        "url": "https://es.aliexpress.com/item/1005001234567896.html",
        "fullSpecs": {"Material": "Fibra de Carbono T800", "Peso": "360g", "Ancho": "400/420/440mm"}
    },
    {
        "brand": "Elite Wheels",
        "model": "Juego de Ruedas de Carbono SLR 50mm Tubeless",
        "category": "repuestos",
        "type": "ruedas",
        "specs": "Elite Wheels • Perfil de 50mm • Carbono Toray T700/T800 • Maza con rodamientos cerámicos",
        "image": "https://images.unsplash.com/photo-1485965120184-e220f721d03e?auto=format&fit=crop&w=600&h=400&q=80",
        "price_normal": 389900,
        "price_card": 480990,
        "url": "https://es.aliexpress.com/item/1005001234567897.html",
        "fullSpecs": {"Perfil": "50mm Aero", "Peso del Set": "1450g", "Material": "Carbono Toray", "Freno": "Disco / Caliper"}
    },
    {
        "brand": "RockBros",
        "model": "Portabotella de Fibra de Carbono Ultra Liviano 24g",
        "category": "accesorios",
        "type": "portabotellas",
        "specs": "RockBros • Fibra de carbono 100% • Peso 24g • Diseño de agarre seguro",
        "image": "https://images.unsplash.com/photo-1485965120184-e220f721d03e?auto=format&fit=crop&w=600&h=400&q=80",
        "price_normal": 8990,
        "price_card": 12990,
        "url": "https://es.aliexpress.com/item/1005001234567898.html",
        "fullSpecs": {"Material": "100% Fibra de Carbono", "Peso": "24 gramos", "Color": "Negro Mate / Brillo"}
    }
]

def main():
    print("[>] Starting database seeding for AliExpress products...")
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}. Please run seed_db.py first.")
        return
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Ensure AliExpress store exists
    cursor.execute("INSERT OR IGNORE INTO stores (name, url) VALUES ('AliExpress', 'https://aliexpress.com')")
    cursor.execute("SELECT id FROM stores WHERE name = 'AliExpress'")
    store_id = cursor.fetchone()[0]
    print(f"🇨🇳 Registered AliExpress store with ID: {store_id}")
    
    inserted_products = 0
    inserted_offers = 0
    inserted_history = 0
    
    for item in ALIEXPRESS_PRODUCTS:
        brand = item["brand"]
        model = item["model"]
        category = item["category"]
        p_type = item["type"]
        specs_summary = item["specs"]
        canonical_image = item["image"]
        normalized_name = (brand + " " + model).lower()
        
        # Check if already exists
        cursor.execute("SELECT id FROM products WHERE normalized_name = ? AND is_international = 1", (normalized_name,))
        existing = cursor.fetchone()
        
        if existing:
            product_id = existing[0]
            print(f"  - Product '{brand} {model}' already exists. Updating...")
            cursor.execute("""
            UPDATE products 
            SET brand=?, model=?, category=?, type=?, specs=?, canonical_image=?
            WHERE id=?
            """, (brand, model, category, p_type, json.dumps(item["fullSpecs"], ensure_ascii=False), canonical_image, product_id))
        else:
            cursor.execute("""
            INSERT INTO products (brand, model, category, type, specs, canonical_image, normalized_name, is_international)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """, (brand, model, category, p_type, json.dumps(item["fullSpecs"], ensure_ascii=False), canonical_image, normalized_name))
            product_id = cursor.lastrowid
            inserted_products += 1
            
        # Insert store product offer
        url = item["url"]
        price_normal = item["price_normal"]
        price_card = item["price_card"]
        
        # Delete existing offers for this product from AliExpress
        cursor.execute("DELETE FROM store_products WHERE product_id = ? AND store_id = ?", (product_id, store_id))
        
        cursor.execute("""
        INSERT INTO store_products (product_id, store_id, url, image_url, price_normal, price_card)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (product_id, store_id, url, canonical_image, price_normal, price_card))
        
        store_product_id = cursor.lastrowid
        inserted_offers += 1
        
        # Insert history points
        cursor.execute("DELETE FROM price_history WHERE store_product_id = ?", (store_product_id,))
        history_prices = [
            int(price_normal * 1.15),
            int(price_normal * 1.08),
            int(price_normal * 1.03),
            price_normal
        ]
        for h_price in history_prices:
            cursor.execute("""
            INSERT INTO price_history (store_product_id, price)
            VALUES (?, ?)
            """, (store_product_id, h_price))
            inserted_history += 1
            
    conn.commit()
    conn.close()
    
    print("\n=== AliExpress Seeding Completed Successfully! ===")
    print(f"  - International products inserted/updated: {len(ALIEXPRESS_PRODUCTS)}")
    print(f"  - Store offers registered: {inserted_offers}")
    print(f"  - History points logged: {inserted_history}")

if __name__ == "__main__":
    main()
