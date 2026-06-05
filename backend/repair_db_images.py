import os
import sys
import sqlite3
import urllib.parse
import time
import cloudscraper
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

# Setup paths
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)
    
import utils.image_downloader as image_downloader

DB_PATH = os.path.join(backend_dir, "database", "bicitodo.db")
STATIC_IMAGES_DIR = os.path.join(os.path.dirname(backend_dir), "static", "images")

scraper = cloudscraper.create_scraper(browser={"browser": "chrome", "platform": "windows", "mobile": False})
HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "es-CL,es;q=0.9,en-US;q=0.8",
}

def is_placeholder(url):
    if not url: return True
    url_lower = url.lower()
    return "placeholder" in url_lower or "no-image" in url_lower or "sin-imagen" in url_lower

def file_exists_and_ok(local_path):
    if not local_path or not local_path.startswith("/static/"):
        return False
    filename = os.path.basename(local_path)
    # Check both products/ folder and images/ folder
    for folder in ["products", ""]:
        full_path = os.path.join(STATIC_IMAGES_DIR, folder, filename)
        if os.path.exists(full_path) and os.path.getsize(full_path) > 1000:
            return True
    return False

def fetch_image_from_page(url):
    try:
        r = scraper.get(url, headers=HEADERS, timeout=12)
        if r.status_code != 200 or not r.text:
            return None
        soup = BeautifulSoup(r.text, "html.parser")
        
        # Look for og:image
        meta_og = soup.select_one('meta[property="og:image"]') or soup.select_one('meta[name="og:image"]')
        if meta_og and meta_og.get("content"):
            return meta_og["content"].strip()
            
        # Look for twitter:image
        meta_tw = soup.select_one('meta[property="twitter:image"]') or soup.select_one('meta[name="twitter:image"]')
        if meta_tw and meta_tw.get("content"):
            return meta_tw["content"].strip()
            
        # Common image classes
        img_el = soup.select_one(".product-main-image img, .product__media img, .product-gallery img, img.product-image-photo, picture img")
        if img_el and img_el.get("src"):
            return img_el["src"].strip()
    except Exception:
        pass
    return None

def repair_product(item):
    sp_id, product_id, brand, model, url, current_img = item
    
    # First check if we can fetch the image
    remote_img = fetch_image_from_page(url)
    if not remote_img:
        # If it's a Shopify store, try products.json
        try:
            parsed = urllib.parse.urlparse(url)
            if any(m in parsed.netloc for m in ["faucon", "satiro", "dsbikes", "crossmountain", "ibikes"]):
                base_prod = url.split("/products/")[0]
                handle = url.split("/products/")[1].split("?")[0]
                json_url = f"{base_prod}/products/{handle}.json"
                r = scraper.get(json_url, timeout=10)
                if r.status_code == 200:
                    remote_img = r.json().get("product", {}).get("images", [{}])[0].get("src")
        except Exception:
            pass
            
    if remote_img:
        if remote_img.startswith("//"):
            remote_img = "https:" + remote_img
            
        local_path = image_downloader.download_image(remote_img, brand=brand, model=model)
        if local_path and not is_placeholder(local_path):
            return {
                "sp_id": sp_id,
                "product_id": product_id,
                "local_path": local_path,
                "status": "success",
                "brand": brand,
                "model": model
            }
            
    return {
        "sp_id": sp_id,
        "product_id": product_id,
        "status": "failed",
        "brand": brand,
        "model": model
    }

def main():
    print("[>] Starting database image repair script...")
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Database not found at {DB_PATH}")
        return
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Query all store products (offers)
    cursor.execute("""
        SELECT sp.id as sp_id, sp.product_id, p.brand, p.model, sp.url, sp.image_url, p.canonical_image 
        FROM store_products sp 
        JOIN products p ON sp.product_id = p.id
    """)
    rows = cursor.fetchall()
    
    to_repair = []
    for r in rows:
        is_missing_sp = not file_exists_and_ok(r["image_url"])
        is_missing_p = not file_exists_and_ok(r["canonical_image"])
        
        if is_missing_sp or is_missing_p or is_placeholder(r["image_url"]) or is_placeholder(r["canonical_image"]):
            to_repair.append((r["sp_id"], r["product_id"], r["brand"], r["model"], r["url"], r["image_url"]))
            
    print(f"[>] Found {len(to_repair)} products with missing or placeholder images.")
    if not to_repair:
        print("[OK] All images are healthy!")
        conn.close()
        return
        
    # Run in parallel with 10 workers (polite limits)
    success_count = 0
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(repair_product, item): item for item in to_repair}
        for future in as_completed(futures):
            res = future.result()
            if res["status"] == "success":
                # Update database
                cursor.execute("UPDATE store_products SET image_url = ? WHERE id = ?", (res["local_path"], res["sp_id"]))
                cursor.execute("UPDATE products SET canonical_image = ? WHERE id = ?", (res["local_path"], res["product_id"]))
                conn.commit()
                success_count += 1
                print(f"  [OK] Updated: {res['brand']} {res['model']} -> {res['local_path']}")
            else:
                print(f"  [FAIL] Could not retrieve image for: {res['brand']} {res['model']}")
                
    conn.close()
    print(f"\n[>] Done! Repaired {success_count}/{len(to_repair)} images.")

if __name__ == "__main__":
    main()
