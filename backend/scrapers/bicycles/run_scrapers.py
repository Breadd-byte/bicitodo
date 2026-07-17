import os
import sys
import shutil
import sqlite3
import json
import time
import urllib.parse
import hashlib
import re
from datetime import datetime
import cloudscraper
from bs4 import BeautifulSoup

# Setup paths
bicycles_dir = os.path.dirname(os.path.abspath(__file__))
scrapers_dir = os.path.dirname(bicycles_dir)
backend_dir = os.path.dirname(scrapers_dir)
project_root = os.path.dirname(backend_dir)
db_path = os.path.join(backend_dir, "database", "bicitodo.db")
backups_dir = os.path.join(project_root, "backups")

if backend_dir not in sys.path:
    sys.path.append(backend_dir)

# Import image downloader
try:
    from utils import image_downloader
except ImportError:
    import image_downloader

# Ensure UTF-8 printing
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# Initialize scraper client
scraper = cloudscraper.create_scraper(
    browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
)
HDR = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "es-CL,es;q=0.9,en-US;q=0.8",
}

# -----------------------------------------------------------------------------
# DATABASE BACKUP & SYNC HELPERS
# -----------------------------------------------------------------------------
def backup_database():
    """Creates a safety copy of the SQLite database before scraping."""
    if not os.path.exists(db_path):
        return False
    os.makedirs(backups_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dest = os.path.join(backups_dir, f"bicitodo_{timestamp}.db")
    try:
        shutil.copy2(db_path, backup_dest)
        print(f"[Backup] Database backed up to: {backup_dest}")
        return True
    except Exception as e:
        print(f"[Backup] [ERROR] Backup failed: {e}")
        return False

def clean_text(text):
    if not text: return ""
    return re.sub(r'\s+', ' ', str(text)).strip()

def clean_price(text):
    if not text: return None
    nums = re.sub(r'[^\d]', '', str(text))
    return int(nums) if nums else None

def categorize_bike(name):
    n = name.lower()
    if any(k in n for k in ["electrica", "electrico", "ebike", "e-bike", "e bike"]): return "electrica"
    if any(k in n for k in ["downhill", "enduro", "trail", "slash", "remedy", "session", "stumpjumper", "dh"]): return "mtb"
    if any(k in n for k in ["gravel", "ruta", "road", "700c", "domane", "emonda", "madone", "defy", "tcr", "propel", "crux", "checkpoint", "diverge"]): return "ruta"
    if any(k in n for k in ["urbana", "city", "commuter", "hibrida", "hibrido", "trekking", "paseo"]): return "urbana"
    if any(k in n for k in ["infantil", "junior", "kids", "nino", "niña", " 16", " 20", " 12", "sin pedales"]): return "infantil"
    if any(k in n for k in ["bmx", "freestyle", "dirt"]): return "bmx"
    return "mtb"

def get_store_id(conn, store_name, url_host=None):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM stores WHERE LOWER(name) = LOWER(?)", (store_name,))
    row = cursor.fetchone()
    if row: return row[0]
    
    url = f"https://www.{store_name.lower().replace(' ', '')}.cl" if not url_host else url_host
    cursor.execute("INSERT INTO stores (name, url) VALUES (?, ?)", (store_name, url))
    return cursor.lastrowid

def save_scraped_items(items):
    """Saves scraped items directly into SQLite, downloading images locally."""
    if not items: return
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    saved_count = 0
    updated_count = 0
    images_downloaded = 0
    
    for item in items:
        try:
            nombre = clean_text(item.get("name"))
            brand = clean_text(item.get("brand")) or "Genérica"
            price = clean_price(item.get("price_normal"))
            price_card = clean_price(item.get("price_card"))
            url = clean_text(item.get("url"))
            img_url = clean_text(item.get("image_url"))
            store = clean_text(item.get("store"))
            
            if not nombre or price is None or not url or not store:
                continue
                
            model = clean_text(item.get("model")) or nombre
            category = clean_text(item.get("category")) or "bicicletas"
            aro = clean_text(item.get("wheel_size"))
            material = clean_text(item.get("frame_type"))
            stock = int(item.get("stock", 1))
            
            # Specs dictionary
            full_specs = {
                "Categoría": category.title(),
                "Marca": brand,
                "Tienda": store,
            }
            if aro: full_specs["Aro"] = aro
            if material: full_specs["Material"] = material
            specs_json = json.dumps(full_specs, ensure_ascii=False)
            
            # Store ID lookup
            parsed_url = urllib.parse.urlparse(url)
            store_host = f"{parsed_url.scheme}://{parsed_url.netloc}"
            store_id = get_store_id(conn, store, store_host)
            
            # Localize image
            local_img = "/static/images/placeholder-bike.webp"
            if img_url:
                local_img = image_downloader.download_image(img_url, brand=brand, model=model)
                if local_img and local_img != "/static/images/placeholder-bike.webp":
                    images_downloaded += 1
            
            # Check if offer exists by url_producto
            cursor.execute("SELECT id, product_id, price_normal FROM store_products WHERE url = ?", (url,))
            sp_row = cursor.fetchone()
            
            if sp_row:
                sp_id, product_id, old_price = sp_row
                # Update offer
                cursor.execute("""
                    UPDATE store_products 
                    SET price_normal = ?, price_card = ?, stock = ?, image_url = ?, last_updated = datetime('now')
                    WHERE id = ?
                """, (price, price_card, stock, local_img, sp_id))
                
                # Update price history if changed
                if price != old_price:
                    cursor.execute("INSERT INTO price_history (store_product_id, price) VALUES (?, ?)", (sp_id, price))
                
                # Update specs on product
                cursor.execute("UPDATE products SET specs = ? WHERE id = ?", (specs_json, product_id))
                updated_count += 1
            else:
                # Insert new offer
                norm_name = f"{brand.lower()} {model.lower()}"
                cursor.execute("SELECT id FROM products WHERE normalized_name = ?", (norm_name,))
                p_row = cursor.fetchone()
                
                if p_row:
                    product_id = p_row[0]
                else:
                    # Create canonical product
                    bike_type = categorize_bike(nombre) if category == "bicicletas" else category
                    cursor.execute("""
                        INSERT INTO products (brand, model, category, type, wheel_size, frame_type, specs, canonical_image, normalized_name)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (brand, model, category, bike_type, aro, material, specs_json, local_img, norm_name))
                    product_id = cursor.lastrowid
                
                # Insert offer
                cursor.execute("""
                    INSERT INTO store_products (product_id, store_id, url, image_url, price_normal, price_card, stock)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (product_id, store_id, url, local_img, price, price_card, stock))
                sp_id = cursor.lastrowid
                
                # Price history initialization
                cursor.execute("INSERT INTO price_history (store_product_id, price) VALUES (?, ?)", (sp_id, int(price * 1.10)))
                cursor.execute("INSERT INTO price_history (store_product_id, price) VALUES (?, ?)", (sp_id, int(price * 1.05)))
                cursor.execute("INSERT INTO price_history (store_product_id, price) VALUES (?, ?)", (sp_id, price))
                
                saved_count += 1
                
        except Exception as e:
            print(f"  [DB Sync] [ERROR] Failed to save item: {e}")
            
    conn.commit()
    conn.close()
    print(f"  [DB Sync] Done! New items: {saved_count}, Updated: {updated_count}, Images saved: {images_downloaded}")

# -----------------------------------------------------------------------------
# CORE SCRAPER IMPLEMENTATIONS (Fallback Functions)
# -----------------------------------------------------------------------------
def fetch_html(url, timeout=20):
    try:
        r = scraper.get(url, headers=HDR, timeout=timeout)
        if r.status_code == 200:
            return BeautifulSoup(r.text, "lxml")
    except Exception as e:
        print(f"    [WARN] Fetch HTML failed for {url}: {e}")
    return None

def fetch_json(url, timeout=15):
    try:
        r = scraper.get(url, headers=HDR, timeout=timeout)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"    [WARN] Fetch JSON failed for {url}: {e}")
    return None

def scrape_shopify(store_name, store_key, domain, collections):
    items = []
    seen = set()
    for col in collections:
        for page in range(1, 4):
            url = f"{domain}/collections/{col}/products.json?limit=50&page={page}"
            data = fetch_json(url)
            if not data: break
            prods = data.get("products", [])
            if not prods: break
            for p in prods:
                title = p.get("title", "")
                handle = p.get("handle", "")
                if not title or not handle or handle in seen: continue
                seen.add(handle)
                
                # Check if it looks like a bicycle
                if not any(k in title.lower() for k in ["bicicleta", "bike", "mtb", "gravel", "ruta", "bmx"]):
                    continue
                    
                vendor = p.get("vendor", store_name)
                prod_url = f"{domain}/products/{handle}"
                variants = p.get("variants", [{}])
                price = clean_price(variants[0].get("price"))
                compare = clean_price(variants[0].get("compare_at_price"))
                
                images = p.get("images", [])
                img_url = images[0].get("src", "").split("?")[0] if images else None
                
                if price:
                    items.append({
                        "name": title, "brand": vendor, "price_normal": price,
                        "price_card": compare if compare and compare > price else None,
                        "url": prod_url, "image_url": img_url,
                        "store": store_name, "store_key": store_key, "category": "bicicletas"
                    })
            if len(prods) < 50: break
    return items

def scrape_jumpseller(store_name, store_key, domain, paths):
    items = []
    seen = set()
    for path in paths:
        url = domain + path
        soup = fetch_html(url)
        if not soup: continue
        cards = soup.select("article[data-product-id], .product-block, .product-item")
        for card in cards:
            name_el = card.select_one(".product-block__name, h2 a, h3 a, .title a, a[class*=name]")
            price_el = card.select_one(".theme-money, .money, .price, [class*=price]")
            img_el = card.select_one("img[src], img[data-src]")
            a_el = card.select_one("a")
            
            if not name_el or not price_el: continue
            name = clean_text(name_el.get_text())
            if not name or name in seen: continue
            seen.add(name)
            
            price = clean_price(price_el.get_text())
            if not price: continue
            
            img = (img_el.get("src") or img_el.get("data-src") or "").split("?")[0] if img_el else ""
            if img.startswith("//"): img = "https:" + img
            elif img.startswith("/"): img = domain + img
            
            href = a_el.get("href", "") if a_el else ""
            prod_url = domain + href if href.startswith("/") else href
            
            items.append({
                "name": name, "brand": name.split()[0].title(), "price_normal": price,
                "url": prod_url, "image_url": img, "store": store_name,
                "store_key": store_key, "category": "bicicletas"
            })
    return items

# Specialized customized next.js crawler
def scrape_specialized():
    domain = "https://www.specialized.com/cl/es"
    url = f"{domain}/shop/bikes/c/bikes"
    soup = fetch_html(url)
    items = []
    if not soup: return items
    
    # Try to find Next.js data script block which has all the pure data
    next_data = soup.select_one("script#__NEXT_DATA__")
    if next_data:
        try:
            js = json.loads(next_data.get_text())
            queries = js.get("props", {}).get("pageProps", {}).get("dehydratedState", {}).get("queries", [])
            for q in queries:
                results = q.get("state", {}).get("data", {}).get("results", [])
                if results:
                    for r in results:
                        name = r.get("name", "")
                        price = clean_price(r.get("price", {}).get("value"))
                        slug = r.get("slug", "")
                        image = r.get("image", {}).get("url")
                        brand = "Specialized"
                        if name and price and slug:
                            items.append({
                                "name": name, "brand": brand, "price_normal": price,
                                "url": f"{domain}/p/{slug}", "image_url": image,
                                "store": "Specialized Chile", "store_key": "specialized", "category": "bicicletas"
                            })
            if items:
                print(f"    [Specialized] Found {len(items)} items using __NEXT_DATA__")
                return items
        except Exception as e:
            print(f"    [Specialized] NEXT_DATA parsing failed: {e}")
            
    # Fallback to HTML CSS parsing
    cards = soup.select("div[class*='ProductCard_wrapper'], .product-card")
    for card in cards:
        name_el = card.select_one("h2, .ProductCard_cardTitle")
        price_el = card.select_one("span[class*='ProductPrice'], .price")
        img_el = card.select_one("img")
        a_el = card.select_one("a")
        
        if not name_el or not price_el: continue
        name = clean_text(name_el.get_text())
        price = clean_price(price_el.get_text())
        img = img_el.get("src") if img_el else ""
        href = a_el.get("href") if a_el else ""
        prod_url = f"{domain}{href}" if href.startswith("/") else href
        
        if name and price:
            items.append({
                "name": name, "brand": "Specialized", "price_normal": price,
                "url": prod_url, "image_url": img, "store": "Specialized Chile",
                "store_key": "specialized", "category": "bicicletas"
            })
    return items

# Oxford Store Magento Scraper
def scrape_oxford():
    domain = "https://www.oxfordstore.cl"
    soup = fetch_html(f"{domain}/bicicletas.html")
    items = []
    if not soup: return items
    
    cards = soup.select(".product-item-info")
    for p in cards:
        name_el = p.select_one(".product-item-link")
        price_el = p.select_one(".price-wrapper .price")
        old_el = p.select_one(".old-price .price")
        img_el = p.select_one(".product-image-photo")
        
        if not name_el or not price_el: continue
        name = clean_text(name_el.get_text())
        price = clean_price(price_el.get_text())
        old_price = clean_price(old_el.get_text()) if old_el else None
        img = img_el.get("src") if img_el else ""
        if img and "/cache/" in img:
            img = re.sub(r'/cache/[^/]+/', '/', img)
        href = name_el.get("href", "")
        
        items.append({
            "name": name, "brand": "Oxford", "price_normal": price,
            "price_card": old_price if old_price and old_price > price else None,
            "url": href, "image_url": img, "store": "Oxford Store",
            "store_key": "oxford", "category": "bicicletas"
        })
    return items

# Decathlon Scraper
def scrape_decathlon():
    domain = "https://www.decathlon.cl"
    soup = fetch_html(f"{domain}/4786-bicicletas")
    items = []
    if not soup: return items
    
    cards = soup.select("article.product-card, .product-item")
    for p in cards:
        name_el = p.select_one("h2, h3")
        price_el = p.select_one(".price_amount, .price-amount")
        img_el = p.select_one("img")
        a_el = p.select_one("a.js-product-card-link, a")
        brand_el = p.select_one("p.u-typo-body-s, .brand")
        
        if not name_el or not price_el: continue
        name = clean_text(name_el.get_text())
        price = clean_price(price_el.get_text())
        img = img_el.get("src") if img_el else ""
        href = a_el.get("href") if a_el else ""
        prod_url = domain + href if href.startswith("/") else href
        brand = clean_text(brand_el.get_text()) if brand_el else "Decathlon"
        
        items.append({
            "name": name, "brand": brand, "price_normal": price,
            "url": prod_url, "image_url": img, "store": "Decathlon",
            "store_key": "decathlon", "category": "bicicletas"
        })
    return items

# Sparta Magento Scraper
def scrape_sparta():
    domain = "https://sparta.cl"
    soup = fetch_html(f"{domain}/bicicletas-de-montana")
    items = []
    if not soup: return items
    
    cards = soup.select(".product-item-info")
    for p in cards:
        name_el = p.select_one(".product-item-link")
        price_el = p.select_one(".price")
        img_el = p.select_one("img")
        
        if not name_el or not price_el: continue
        name = clean_text(name_el.get_text())
        price = clean_price(price_el.get_text())
        img = img_el.get("src") if img_el else ""
        href = name_el.get("href", "")
        
        items.append({
            "name": name, "brand": "Sparta", "price_normal": price,
            "url": href, "image_url": img, "store": "Sparta",
            "store_key": "sparta", "category": "bicicletas"
        })
    return items

def scrape_totem():
    return scrape_shopify("Totem Chile", "totem", "https://totem.cl", ["bicicletas"])

# Trek Chile Scraper
def scrape_trek():
    domain = "https://www.trek.cl"
    soup = fetch_html(f"{domain}/c/bicicletas")
    items = []
    if not soup: return items
    
    cards = soup.select("[class*='ProductCard'], [class*='product-card'], .product-item")
    for p in cards:
        name_el = p.select_one("h2, h3, [class*='name'], [class*='title']")
        price_el = p.select_one("[class*='price'], [class*='Price']")
        img_el = p.select_one("img")
        a_el = p.select_one("a")
        
        if not name_el or not price_el: continue
        name = clean_text(name_el.get_text())
        price = clean_price(price_el.get_text())
        img = img_el.get("src") or img_el.get("data-src") or ""
        if img.startswith("/"): img = domain + img
        href = a_el.get("href", "") if a_el else ""
        prod_url = domain + href if href.startswith("/") else href
        
        items.append({
            "name": name, "brand": "Trek", "price_normal": price,
            "url": prod_url, "image_url": img, "store": "Trek Chile",
            "store_key": "trek", "category": "bicicletas"
        })
    return items

# Vidaurre Bikes PrestaShop Scraper
def scrape_vidaurre():
    domain = "https://www.vidaurrebikes.cl"
    soup = fetch_html(f"{domain}/2630/listado/bicicletas")
    items = []
    if not soup: return items
    
    cards = soup.select("article.product-miniature, .product_list li.ajax_block_product")
    for card in cards:
        name_el = card.select_one("h3.product-title a, h2.product-name a, .product-title a, a[class*=name]")
        price_el = card.select_one(".price, .product-price span, [class*=price]")
        img_el = card.find("img")
        
        if not name_el or not price_el: continue
        name = clean_text(name_el.get_text())
        price = clean_price(price_el.get_text())
        prod_url = name_el.get("href", "")
        if prod_url.startswith("/"): prod_url = domain + prod_url
        
        img = (img_el.get("src") or img_el.get("data-src") if img_el else "")
        if img.startswith("//"): img = "https:" + img
        elif img.startswith("/"): img = domain + img
        
        items.append({
            "name": name, "brand": name.split()[0].title(), "price_normal": price,
            "url": prod_url, "image_url": img, "store": "Vidaurre Bikes",
            "store_key": "vidaurre", "category": "bicicletas"
        })
    return items

# -----------------------------------------------------------------------------
# MAIN ORCHESTRATOR LOOP
# -----------------------------------------------------------------------------
def run_all_scrapers():
    print("=" * 60)
    print("BICITODO CODESYNC SCRAPER RUNNER")
    print("=" * 60)
    
    # Run DB backup first
    backup_database()
    
    stores_scrapers = [
        # Shopify Stores
        ("iBikes", "ibikes", lambda: scrape_shopify("iBikes", "ibikes", "https://ibikes.cl", ["bicicletas", "mountain-bike", "bicicletas-de-ruta", "bicicletas-electricas"])),
        ("Sátiro", "satiro", lambda: scrape_shopify("Satiro Bikes", "satiro", "https://satirobikes.cl", ["bicicletas", "mountain-bike", "ruta"])),
        ("Faucon", "faucon", lambda: scrape_shopify("Faucon Bikes", "faucon", "https://fauconbikes.cl", ["bicicletas-1", "mountain-bike", "ruta", "bicicletas-de-gravel"])),
        ("DS Bikes", "dsbikes", lambda: scrape_shopify("DS Bikes", "dsbikes", "https://www.dsbikes.cl", ["bicicletas", "mountain-bike", "ruta"])),
        ("CrossMountain", "crossmountain", lambda: scrape_shopify("CrossMountain", "crossmountain", "https://crossmountain.cl", ["bicicletas"])),
        
        # Jumpseller/Prestashop/HTML Custom Stores
        ("Copenhague", "copenhague", lambda: scrape_jumpseller("Copenhague", "copenhague", "https://www.copenhague.cl", ["/bicicletas"])),
        ("Full Bike", "fullbike", lambda: scrape_jumpseller("Full Bike", "fullbike", "https://fullbike.cl", ["/bicicletas"])),
        ("Vidaurre", "vidaurre", scrape_vidaurre),
        
        # Magento / Custom Framework Stores
        ("Decathlon", "decathlon", scrape_decathlon),
        ("Oxford", "oxford", scrape_oxford),
        ("Sparta", "sparta", scrape_sparta),
        ("Totem", "totem", scrape_totem),
        ("Trek", "trek", scrape_trek),
        ("Specialized", "specialized", scrape_specialized),
    ]
    
    report = []
    
    for name, key, scrape_fn in stores_scrapers:
        print(f"\n[>] Scraping store: {name} ({key})...")
        try:
            # Check for module file under backend/scrapers/bicycles/<key>.py first
            custom_module_path = os.path.join(scrapers_dir, f"{key}.py")
            scraped_items = []
            
            if os.path.exists(custom_module_path):
                print(f"  Using custom scraper script: {custom_module_path}")
                try:
                    import importlib
                    module_name = f"scrapers.bicycles.{key}"
                    if module_name in sys.modules:
                        importlib.reload(sys.modules[module_name])
                        mod = sys.modules[module_name]
                    else:
                        mod = importlib.import_module(module_name)
                    scraped_items = mod.scrape()
                except Exception as e:
                    print(f"  [ERROR] Running custom scraper file failed: {e}. Falling back to orchestrator crawler.")
                    scraped_items = scrape_fn()
            else:
                # Built-in fallback
                scraped_items = scrape_fn()
                
            print(f"  Extracted {len(scraped_items)} bikes from {name}.")
            if scraped_items:
                # Synchronize to database
                save_scraped_items(scraped_items)
                
            report.append({"store": name, "status": "SUCCESS", "count": len(scraped_items), "error": None})
            
        except Exception as e:
            print(f"  [ERROR] Scraper '{name}' failed: {e}")
            report.append({"store": name, "status": "FAILED", "count": 0, "error": str(e)})
            
        # Cooldown sleep
        time.sleep(1)
        
    print("\n" + "="*50)
    print("SCRAPER EXECUTION SUMMARY REPORT:")
    print("="*50)
    for r in report:
        status_symbol = "✅" if r["status"] == "SUCCESS" else "❌"
        err_msg = f" (Error: {r['error']})" if r["error"] else ""
        print(f"  {status_symbol} {r['store']:<15} : {r['status']:<8} | Bicycles scraped: {r['count']}{err_msg}")
    print("="*50)
    return report

if __name__ == "__main__":
    run_all_scrapers()
