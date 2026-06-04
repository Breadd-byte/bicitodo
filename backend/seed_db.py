# seed_db.py - Seed SQLite Database from data.json
import sys
import os
import sqlite3
import json

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "backend", "database", "bicitodo.db")
DATA_PATH = os.path.join(BASE_DIR, "fronted", "data.json")

def main():
    print("[>] Starting database seeding...")
    
    # Ensure database folder exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    # Remove existing db to start fresh
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("🧹 Old database file removed.")
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create SQLite Schema
    print("[>] Creating tables in SQLite...")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        url TEXT,
        last_scrape TEXT
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        brand TEXT,
        model TEXT NOT NULL,
        category TEXT, -- 'bicicletas', 'accesorios', 'repuestos'
        type TEXT, -- subcategory
        wheel_size TEXT,
        frame_type TEXT,
        specs TEXT,
        canonical_image TEXT,
        normalized_name TEXT,
        is_international INTEGER DEFAULT 0,
        rating REAL,
        sales_count INTEGER,
        review_count INTEGER,
        discount_percent INTEGER
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS store_products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        store_id INTEGER,
        sku TEXT,
        url TEXT NOT NULL,
        image_url TEXT,
        price_normal INTEGER,
        price_card INTEGER,
        stock INTEGER DEFAULT 1,
        last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(product_id) REFERENCES products(id),
        FOREIGN KEY(store_id) REFERENCES stores(id)
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS price_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        store_product_id INTEGER,
        price INTEGER NOT NULL,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(store_product_id) REFERENCES store_products(id)
    );
    """)
    
    # Create indexes for high-performance joins and queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_is_international ON products(is_international);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_type ON products(type);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_normalized_name ON products(normalized_name);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_store_products_product_id ON store_products(product_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_store_products_store_id ON store_products(store_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_store_products_price_normal ON store_products(price_normal);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_store_products_price_card ON store_products(price_card);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_history_store_product_id ON price_history(store_product_id);")

    # Load data.json
    print(f"[>] Reading data from {DATA_PATH}...")
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    # Store name to ID mapping
    store_map = {}
    
    # Insert Stores and Products
    products_count = 0
    offers_count = 0
    history_count = 0
    
    for category in ["bicicletas", "accesorios", "repuestos"]:
        items = data.get(category, [])
        print(f"  - Category '{category}': found {len(items)} items")
        
        for item in items:
            # 1. Insert product
            brand = item.get("brand")
            model = item.get("model")
            p_type = item.get("type")
            wheel_size = item.get("wheelSize")
            frame_type = item.get("frameType")
            specs = json.dumps(item.get("fullSpecs", {}), ensure_ascii=False)
            canonical_image = item.get("image")
            normalized_name = (brand + " " + model).lower()
            
            # Check if any offer is from AliExpress or product is marked as international
            is_intl = 0
            for offer in item.get("offers", []):
                s_name = str(offer.get("store", "")).lower()
                if "aliexpress" in s_name or item.get("is_international"):
                    is_intl = 1
                    break
            
            cursor.execute("""
            INSERT INTO products (brand, model, category, type, wheel_size, frame_type, specs, canonical_image, normalized_name, is_international, rating, sales_count, review_count, discount_percent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (brand, model, category, p_type, wheel_size, frame_type, specs, canonical_image, normalized_name, is_intl, 4.5, 100, 15, 0))
            
            product_id = cursor.lastrowid
            products_count += 1
            
            # 2. Insert store offers
            for offer in item.get("offers", []):
                store_name = offer.get("store")
                store_key = offer.get("storeKey", store_name.lower().replace(" ", ""))
                
                # Get or Create Store
                if store_key not in store_map:
                    cursor.execute("INSERT OR IGNORE INTO stores (name, url) VALUES (?, ?)", (store_name, offer.get("url")))
                    cursor.execute("SELECT id FROM stores WHERE name = ?", (store_name,))
                    store_id = cursor.fetchone()[0]
                    store_map[store_key] = store_id
                else:
                    store_id = store_map[store_key]
                    
                price = offer.get("price")
                old_price = offer.get("oldPrice")
                url = offer.get("url")
                image_url = offer.get("imageUrl") or canonical_image
                
                cursor.execute("""
                INSERT INTO store_products (product_id, store_id, url, image_url, price_normal, price_card)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (product_id, store_id, url, image_url, price, old_price))
                
                store_product_id = cursor.lastrowid
                offers_count += 1
                
                # 3. Insert history
                history = item.get("history", [])
                for h_price in history:
                    cursor.execute("""
                    INSERT INTO price_history (store_product_id, price)
                    VALUES (?, ?)
                    """, (store_product_id, h_price))
                    history_count += 1
                    
    conn.commit()
    conn.close()
    
    print("\n=== Seeding completed successfully! ===")
    print(f"  - Products inserted: {products_count}")
    print(f"  - Store offers inserted: {offers_count}")
    print(f"  - History points inserted: {history_count}")
    print(f"  - Unique stores registered: {len(store_map)}")

if __name__ == "__main__":
    main()
