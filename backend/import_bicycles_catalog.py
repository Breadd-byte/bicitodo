import os
import sys
import shutil
import sqlite3
import json
import csv
import hashlib
from datetime import datetime

# Setup paths
backend_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(backend_dir)
db_path = os.path.join(backend_dir, "database", "bicitodo.db")
backups_dir = os.path.join(project_root, "backups")
imports_dir = os.path.join(project_root, "imports")

if backend_dir not in sys.path:
    sys.path.append(backend_dir)

# Import image downloader
try:
    from utils import image_downloader
except ImportError:
    import image_downloader

# Ensure UTF-8 printing in Windows terminal
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

def backup_database():
    """Creates an automatic copy of the current SQLite database."""
    if not os.path.exists(db_path):
        print("[WARN] SQLite database not found for backup.")
        return False
    os.makedirs(backups_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"bicitodo_{timestamp}.db"
    backup_dest = os.path.join(backups_dir, backup_filename)
    try:
        shutil.copy2(db_path, backup_dest)
        print(f"[Backup] Database backed up successfully to: {backup_dest}")
        return True
    except Exception as e:
        print(f"[Backup] [ERROR] Failed to backup database: {e}")
        return False

def clean_text(text):
    if not text:
        return ""
    return str(text).strip()

def clean_price(val):
    if val is None or val == "":
        return None
    try:
        # Remove any non-numeric characters
        num_str = re.sub(r'[^\d]', '', str(val))
        return int(num_str) if num_str else None
    except Exception:
        return None

def clean_stock(val):
    if val is None or val == "":
        return 1
    val_str = str(val).strip().lower()
    if val_str in ("0", "no", "false", "sin stock", "agotado"):
        return 0
    return 1

import re
def categorize_bike(name):
    n = name.lower()
    # Normalize accents/special chars simplified
    if any(k in n for k in ["electrica", "electrico", "ebike", "e-bike", "e bike"]): return "electrica"
    if any(k in n for k in ["downhill", "enduro", "trail", "slash", "remedy", "session", "stumpjumper", "dh"]): return "mtb"
    if any(k in n for k in ["gravel", "ruta", "road", "700c", "domane", "emonda", "madone", "defy", "tcr", "propel", "crux", "checkpoint", "diverge"]): return "ruta"
    if any(k in n for k in ["urbana", "city", "commuter", "hibrida", "hibrido", "trekking", "paseo"]): return "urbana"
    if any(k in n for k in ["infantil", "junior", "kids", "nino", "niña", " 16", " 20", " 12", "sin pedales"]): return "infantil"
    if any(k in n for k in ["bmx", "freestyle", "dirt"]): return "bmx"
    return "mtb"

def get_store_id(conn, store_name, product_url):
    """Finds store_id or creates one using product host domain if missing."""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM stores WHERE LOWER(name) = LOWER(?)", (store_name,))
    row = cursor.fetchone()
    if row:
        return row[0]
    
    # Store url resolver
    store_url = "#"
    if product_url and product_url.startswith("http"):
        try:
            parsed = urllib.parse.urlparse(product_url)
            store_url = f"{parsed.scheme}://{parsed.netloc}"
        except Exception:
            pass
            
    cursor.execute("INSERT INTO stores (name, url) VALUES (?, ?)", (store_name, store_url))
    store_id = cursor.lastrowid
    print(f"  [Store] Created missing store: {store_name} (ID: {store_id})")
    return store_id

def process_import(rows):
    """Imports rows of dictionary data into the SQLite database."""
    print(f"[>] Starting import of {len(rows)} records...")
    
    # Ensure backup before writing
    backup_database()
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    stats = {
        "inserted": 0,
        "updated": 0,
        "ignored": 0,
        "images_downloaded": 0,
        "images_failed": 0,
        "errors": 0
    }
    
    for idx, row in enumerate(rows, 1):
        try:
            nombre = clean_text(row.get("nombre"))
            marca = clean_text(row.get("marca"))
            precio = clean_price(row.get("precio"))
            tienda = clean_text(row.get("tienda"))
            url_producto = clean_text(row.get("url_producto"))
            
            # Check mandatory fields
            if not nombre or not marca or precio is None or not tienda or not url_producto:
                print(f"  [Row {idx}] Ignored: Missing mandatory fields (name: {nombre}, brand: {marca}, price: {precio}, store: {tienda}, url: {url_producto})")
                stats["ignored"] += 1
                continue
                
            model = clean_text(row.get("modelo")) or nombre
            category = clean_text(row.get("categoria")) or "bicicletas"
            price_card = clean_price(row.get("precio_anterior"))
            url_imagen = clean_text(row.get("url_imagen"))
            stock = clean_stock(row.get("stock"))
            
            # Specifications fields
            aro = clean_text(row.get("aro"))
            talla = clean_text(row.get("talla"))
            material = clean_text(row.get("material"))
            transmision = clean_text(row.get("transmision"))
            frenos = clean_text(row.get("frenos"))
            suspension = clean_text(row.get("suspension"))
            peso = clean_text(row.get("peso"))
            descripcion = clean_text(row.get("descripcion"))
            
            # Specs JSON serialization
            full_specs = {
                "Categoría": category.title(),
                "Marca": marca,
                "Tienda": tienda,
            }
            if aro: full_specs["Aro"] = aro
            if talla: full_specs["Talla"] = talla
            if material: full_specs["Material"] = material
            if transmision: full_specs["Transmisión"] = transmision
            if frenos: full_specs["Frenos"] = frenos
            if suspension: full_specs["Suspensión"] = suspension
            if peso: full_specs["Peso"] = peso
            if descripcion: full_specs["Descripción"] = descripcion
            specs_json = json.dumps(full_specs, ensure_ascii=False)
            
            # Resolve store_id
            store_id = get_store_id(conn, tienda, url_producto)
            
            # 1. Download image locally
            local_img = "/static/images/placeholder-bike.webp"
            if url_imagen:
                print(f"  [Row {idx}] Downloading image: {url_imagen[:60]}...")
                local_img = image_downloader.download_image(url_imagen, brand=marca, model=model)
                if local_img and local_img != "/static/images/placeholder-bike.webp":
                    stats["images_downloaded"] += 1
                else:
                    stats["images_failed"] += 1
            else:
                stats["images_failed"] += 1
                
            # 2. Check if the offer already exists by url_producto
            cursor.execute("SELECT id, product_id, price_normal FROM store_products WHERE url = ?", (url_producto,))
            sp_row = cursor.fetchone()
            
            if sp_row:
                # UPDATE OFFER
                sp_id, product_id, old_price = sp_row
                cursor.execute("""
                    UPDATE store_products 
                    SET price_normal = ?, price_card = ?, stock = ?, image_url = ?, last_updated = datetime('now')
                    WHERE id = ?
                """, (precio, price_card, stock, local_img, sp_id))
                
                # Check price change for history
                if precio != old_price:
                    cursor.execute("INSERT INTO price_history (store_product_id, price) VALUES (?, ?)", (sp_id, precio))
                    
                # Update canonical product information if needed
                cursor.execute("""
                    UPDATE products 
                    SET specs = ?, frame_type = COALESCE(frame_type, ?), wheel_size = COALESCE(wheel_size, ?)
                    WHERE id = ?
                """, (specs_json, material, aro, product_id))
                
                # Update canonical image if it is currently placeholder and we downloaded a valid image
                if local_img != "/static/images/placeholder-bike.webp":
                    cursor.execute("SELECT canonical_image FROM products WHERE id = ?", (product_id,))
                    p_img = cursor.fetchone()
                    if p_img and ("placeholder-bike" in p_img[0] or p_img[0] == ""):
                        cursor.execute("UPDATE products SET canonical_image = ? WHERE id = ?", (local_img, product_id))
                
                print(f"  [Row {idx}] Updated existing offer for product '{model}' (Store: {tienda})")
                stats["updated"] += 1
            else:
                # INSERT NEW OFFER
                # Check if product exists canonically
                norm_name = f"{marca.lower()} {model.lower()}"
                cursor.execute("SELECT id FROM products WHERE normalized_name = ?", (norm_name,))
                p_row = cursor.fetchone()
                
                if p_row:
                    product_id = p_row[0]
                else:
                    # Insert new canonical product
                    bike_type = categorize_bike(nombre) if category == "bicicletas" else category
                    cursor.execute("""
                        INSERT INTO products (brand, model, category, type, wheel_size, frame_type, specs, canonical_image, normalized_name)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (marca, model, category, bike_type, aro, material, specs_json, local_img, norm_name))
                    product_id = cursor.lastrowid
                
                # Insert the offer
                cursor.execute("""
                    INSERT INTO store_products (product_id, store_id, url, image_url, price_normal, price_card, stock)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (product_id, store_id, url_producto, local_img, precio, price_card, stock))
                sp_id = cursor.lastrowid
                
                # Insert simulated history points (price historical curve)
                cursor.execute("INSERT INTO price_history (store_product_id, price) VALUES (?, ?)", (sp_id, int(precio * 1.10)))
                cursor.execute("INSERT INTO price_history (store_product_id, price) VALUES (?, ?)", (sp_id, int(precio * 1.05)))
                cursor.execute("INSERT INTO price_history (store_product_id, price) VALUES (?, ?)", (sp_id, precio))
                
                print(f"  [Row {idx}] Inserted new product/offer '{model}' (Store: {tienda})")
                stats["inserted"] += 1
                
        except Exception as e:
            print(f"  [Row {idx}] [ERROR] Failed to process row: {e}")
            stats["errors"] += 1
            
    conn.commit()
    conn.close()
    
    print("\n" + "="*50)
    print("IMPORT SUMMARY:")
    print(f"  - New products/offers inserted: {stats['inserted']}")
    print(f"  - Products/offers updated:      {stats['updated']}")
    print(f"  - Records ignored:              {stats['ignored']}")
    print(f"  - Images downloaded successfully: {stats['images_downloaded']}")
    print(f"  - Images failed/placeholder:    {stats['images_failed']}")
    print(f"  - Process errors:               {stats['errors']}")
    print("="*50)
    return stats

def run_csv_import(file_path):
    print(f"[>] Reading CSV file: {file_path}")
    rows = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                rows.append(r)
        return process_import(rows)
    except Exception as e:
        print(f"[ERROR] Failed to read CSV {file_path}: {e}")
        return None

def run_xlsx_import(file_path):
    print(f"[>] Reading Excel file: {file_path}")
    try:
        import pandas as pd
    except ImportError:
        print("[WARN] pandas not installed. Attempting to install...")
        os.system("pip install pandas openpyxl -q")
        import pandas as pd
        
    try:
        df = pd.read_excel(file_path)
        # Convert NaN values to None/empty strings
        df = df.where(pd.notnull(df), None)
        rows = df.to_dict(orient="records")
        return process_import(rows)
    except Exception as e:
        print(f"[ERROR] Failed to read Excel {file_path}: {e}")
        return None

def main():
    # If a specific file path is provided as argument
    if len(sys.argv) > 1:
        target_file = sys.argv[1]
        if not os.path.exists(target_file):
            print(f"[ERROR] File not found: {target_file}")
            sys.exit(1)
            
        ext = os.path.splitext(target_file)[1].lower()
        if ext == ".csv":
            run_csv_import(target_file)
        elif ext in (".xlsx", ".xls"):
            run_xlsx_import(target_file)
        else:
            print(f"[ERROR] Unsupported file extension: {ext}")
            sys.exit(1)
    else:
        # Default scan order: imports/bicicletas.xlsx -> imports/bicicletas.csv
        xlsx_path = os.path.join(imports_dir, "bicicletas.xlsx")
        csv_path = os.path.join(imports_dir, "bicicletas.csv")
        
        if os.path.exists(xlsx_path):
            run_xlsx_import(xlsx_path)
        elif os.path.exists(csv_path):
            run_csv_import(csv_path)
        else:
            print(f"[WARN] No catalog file found at defaults: {xlsx_path} or {csv_path}")
            print(f"Please place your catalog file there or run the script with a file path parameter, e.g.:")
            print(f"  python backend/import_bicycles_catalog.py path/to/catalog.csv")

if __name__ == "__main__":
    main()
