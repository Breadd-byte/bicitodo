import os
import sys
import sqlite3
import json
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from PIL import Image
import io

# Add backend directory to sys.path to import image_downloader
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

import image_downloader

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "fronted"
DATA_PATH = FRONTEND_DIR / "data.json"
DB_PATH = BASE_DIR / "backend" / "database" / "bicitodo.db"
STATIC_IMAGES_DIR = BASE_DIR / "static" / "images"

STATIC_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Encoding safety for Windows
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

def process_single_url(url):
    """Processes a single URL/path and returns (original, local_path_url)."""
    if not url or not isinstance(url, str):
        return url, None
        
    url = url.strip()
    # Already migrated
    if url.startswith("/static/images/"):
        return url, url
        
    # Check if it is a local asset from the old setup
    if url.startswith("assets/bikes/") or url.startswith("fronted/assets/bikes/"):
        filename = os.path.basename(url)
        old_local_path = FRONTEND_DIR / "assets" / "bikes" / filename
        if not old_local_path.exists():
            # If not in assets/bikes, try relative from base
            old_local_path = BASE_DIR / url
            
        if old_local_path.exists():
            try:
                # Read content, convert to WebP
                content = old_local_path.read_bytes()
                if image_downloader.validate_image_bytes(content):
                    content_hash = hashlib.md5(content).hexdigest()
                    new_filename = f"img_{content_hash[:16]}.webp"
                    dest_path = STATIC_IMAGES_DIR / new_filename
                    new_url = f"/static/images/{new_filename}"
                    
                    if not dest_path.exists():
                        try:
                            # Optimize with PIL
                            img = Image.open(io.BytesIO(content))
                            if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                                img.save(dest_path, format="WEBP", quality=80, method=4)
                            else:
                                img.convert("RGB").save(dest_path, format="WEBP", quality=80, method=4)
                        except Exception:
                            # Fallback write original bytes
                            dest_path.write_bytes(content)
                            
                    return url, new_url
            except Exception as e:
                print(f"[WARN] Failed to process old local asset {url}: {e}")
                
        # If the local file doesn't exist, we fall back to the remote URL (if we can find it)
        # or we return the placeholder
        return url, "/static/images/placeholder-bike.png"

    # If it is an HTTP/S URL, download and optimize
    if url.startswith(("http://", "https://")):
        local_url = image_downloader.download_image(url, str(STATIC_IMAGES_DIR))
        if local_url:
            return url, local_url
            
    return url, "/static/images/placeholder-bike.png"

def main():
    print("[>] Starting image migration to local WebP serving...")
    
    # 1. Ensure placeholder exists
    placeholder_path = STATIC_IMAGES_DIR / "placeholder-bike.png"
    if not placeholder_path.exists():
        print("[>] Creating default placeholder...")
        from create_placeholder import create_gradient_placeholder
        create_gradient_placeholder(str(placeholder_path))

    # 2. Gather all image URLs from DB & data.json
    all_urls = set()
    
    # Read from data.json if exists
    data_json = None
    if DATA_PATH.exists():
        print(f"[>] Gathering URLs from {DATA_PATH}...")
        try:
            with open(DATA_PATH, "r", encoding="utf-8") as f:
                data_json = json.load(f)
            for category in ["bicicletas", "accesorios", "repuestos"]:
                for item in data_json.get(category, []):
                    if item.get("image"):
                        all_urls.add(item["image"])
                    if item.get("original_img_url"):
                        all_urls.add(item["original_img_url"])
                    for offer in item.get("offers", []):
                        if offer.get("imageUrl"):
                            all_urls.add(offer["imageUrl"])
        except Exception as e:
            print(f"[ERROR] Failed to load data.json: {e}")

    # Read from DB if exists
    db_exists = DB_PATH.exists()
    db_urls = set()
    if db_exists:
        print(f"[>] Gathering URLs from database {DB_PATH}...")
        try:
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.cursor()
            
            cursor.execute("SELECT DISTINCT canonical_image FROM products WHERE canonical_image IS NOT NULL")
            for r in cursor.fetchall():
                if r[0]:
                    db_urls.add(r[0])
                    
            cursor.execute("SELECT DISTINCT image_url FROM store_products WHERE image_url IS NOT NULL")
            for r in cursor.fetchall():
                if r[0]:
                    db_urls.add(r[0])
                    
            conn.close()
            all_urls.update(db_urls)
        except Exception as e:
            print(f"[ERROR] Failed to load URLs from database: {e}")

    # Filter out already migrated or empty/invalid URLs
    urls_to_migrate = [
        u for u in all_urls 
        if u and not u.startswith("/static/images/") and u != "/static/images/placeholder-bike.png"
    ]
    
    print(f"[>] Total unique URLs to migrate: {len(urls_to_migrate)}")
    if not urls_to_migrate:
        print("[OK] All images are already migrated!")
        return

    # 3. Concurrently download and process images
    url_mapping = {}
    workers = 16
    print(f"[>] Launching concurrent downloader with {workers} workers...")
    
    processed = 0
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(process_single_url, url): url for url in urls_to_migrate}
        for future in as_completed(futures):
            orig_url, local_url = future.result()
            processed += 1
            if local_url:
                url_mapping[orig_url] = local_url
            if processed % 50 == 0 or processed == len(urls_to_migrate):
                successes = sum(1 for v in url_mapping.values() if v and not v.endswith("placeholder-bike.png"))
                placeholders = sum(1 for v in url_mapping.values() if v and v.endswith("placeholder-bike.png"))
                print(f"  Processed {processed}/{len(urls_to_migrate)} (Success: {successes}, Placeholder: {placeholders})")

    # 4. Update data.json with new local URLs
    if data_json:
        print(f"[>] Updating {DATA_PATH} with migrated paths...")
        updated_count = 0
        for category in ["bicicletas", "accesorios", "repuestos"]:
            for item in data_json.get(category, []):
                # Update main canonical image
                img = item.get("image")
                if img in url_mapping:
                    item["image"] = url_mapping[img]
                    updated_count += 1
                elif img and not img.startswith("/static/images/"):
                    item["image"] = "/static/images/placeholder-bike.png"
                
                # Update offers
                for offer in item.get("offers", []):
                    o_img = offer.get("imageUrl")
                    if o_img in url_mapping:
                        offer["imageUrl"] = url_mapping[o_img]
                        updated_count += 1
                    elif o_img and not o_img.startswith("/static/images/"):
                        offer["imageUrl"] = "/static/images/placeholder-bike.png"
                        
        try:
            with open(DATA_PATH, "w", encoding="utf-8") as f:
                json.dump(data_json, f, ensure_ascii=False, indent=2)
            print(f"[OK] data.json updated successfully ({updated_count} fields updated).")
        except Exception as e:
            print(f"[ERROR] Failed to save updated data.json: {e}")

    # 5. Update SQLite database with new local URLs
    if db_exists:
        print(f"[>] Updating SQLite database {DB_PATH}...")
        try:
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.cursor()
            
            # Fetch products to update
            cursor.execute("SELECT id, canonical_image FROM products WHERE canonical_image IS NOT NULL")
            products = cursor.fetchall()
            p_updated = 0
            for p_id, canonical in products:
                if canonical in url_mapping:
                    cursor.execute("UPDATE products SET canonical_image = ? WHERE id = ?", (url_mapping[canonical], p_id))
                    p_updated += 1
                elif canonical and not canonical.startswith("/static/images/"):
                    cursor.execute("UPDATE products SET canonical_image = ? WHERE id = ?", ("/static/images/placeholder-bike.png", p_id))
                    p_updated += 1
                    
            # Fetch store offers to update
            cursor.execute("SELECT id, image_url FROM store_products WHERE image_url IS NOT NULL")
            offers = cursor.fetchall()
            o_updated = 0
            for o_id, o_url in offers:
                if o_url in url_mapping:
                    cursor.execute("UPDATE store_products SET image_url = ? WHERE id = ?", (url_mapping[o_url], o_id))
                    o_updated += 1
                elif o_url and not o_url.startswith("/static/images/"):
                    cursor.execute("UPDATE store_products SET image_url = ? WHERE id = ?", ("/static/images/placeholder-bike.png", o_id))
                    o_updated += 1
                    
            conn.commit()
            conn.close()
            print(f"[OK] Database updated successfully (Products: {p_updated}, Offers: {o_updated}).")
        except Exception as e:
            print(f"[ERROR] Failed to update database: {e}")

    print("\n=== MIGRATION COMPLETE ===")
    print(f"Total images saved in static/images/: {len(os.listdir(str(STATIC_IMAGES_DIR)))}")

if __name__ == "__main__":
    main()
