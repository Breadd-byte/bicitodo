import os
import re
import sys
import json
import time
import hashlib
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup
import cloudscraper

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

BASE_DIR = r"c:\Users\basti\Desktop\bicitodo"
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
FRONTED_DIR = os.path.join(BASE_DIR, "fronted")
ASSETS_DIR = os.path.join(FRONTED_DIR, "assets", "bikes")
CACHE_PATH = os.path.join(BASE_DIR, "scratch", "aliexpress_direct_cache.json")

sys.path.append(BACKEND_DIR)
from import_aliexpress import PRODUCT_TEMPLATES

os.makedirs(ASSETS_DIR, exist_ok=True)

# Unsplash Curated High-Quality Fallbacks in case everything else fails
GLOBAL_FALLBACK = "https://images.unsplash.com/photo-1532298229144-0ec0c57515c7?auto=format&fit=crop&w=600&h=400&q=80"

# Initializing cloudscraper for fetching AliExpress pages
scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

def get_hash(brand, model):
    key = f"{brand.strip().upper()}_{model.strip().upper()}"
    return hashlib.md5(key.encode('utf-8')).hexdigest()[:12]

def is_valid_image(content):
    if len(content) < 3000:
        return False
    head = content[:12]
    return (
        head[:3] == b"\xff\xd8\xff"
        or head[:4] == b"\x89PNG"
        or head[:4] == b"RIFF"
        or head[:6] in (b"GIF87a", b"GIF89a")
    )

def search_ddg_lite(query):
    url = "https://lite.duckduckgo.com/lite/"
    data = {"q": query}
    try:
        r = requests.post(url, data=data, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            links = []
            for a in soup.find_all("a", href=True):
                href = a["href"]
                # Look for direct aliexpress item URLs
                if "aliexpress.com/item/" in href:
                    # Clean the URL
                    clean_link = href
                    if "/item/" in clean_link:
                        # Extract the base item URL up to .html
                        m = re.search(r'(https://[a-z\.]*aliexpress\.com/item/\d+\.html)', clean_link)
                        if m:
                            clean_link = m.group(1)
                    links.append(clean_link)
            return links
    except Exception as e:
        print(f"  [DDG Error] Query '{query}': {e}")
    return []

def fetch_aliexpress_image(product_url):
    try:
        r = scraper.get(product_url, headers=HEADERS, timeout=12)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "lxml")
            og = soup.select_one('meta[property="og:image"]') or soup.select_one('meta[name="og:image"]')
            if og and og.get("content"):
                return og.get("content").split('?')[0]
            
            # Fallback selectors
            selectors = [
                '.product-gallery img',
                '.magnifier-image',
                'img.product-image',
                'meta[property="twitter:image"]',
            ]
            for sel in selectors:
                el = soup.select_one(sel)
                if el and el.get("src"):
                    src = el.get("src")
                    if src.startswith("//"): src = "https:" + src
                    return src.split('?')[0]
    except Exception as e:
        print(f"  [HTML Error] URL '{product_url}': {e}")
    return None

def process_product(template):
    brand = template["brand"]
    model = template["model"]
    p_type = template["type"]
    key = f"{brand} {model}".strip()
    img_hash = get_hash(brand, model)
    filename = f"ali_{img_hash}.jpg"
    local_path = f"assets/bikes/{filename}"
    filepath = os.path.join(ASSETS_DIR, filename)

    print(f"[*] Processing: {key} ({p_type})")

    # Search query
    query = f"{brand} {model} site:aliexpress.com/item"
    links = search_ddg_lite(query)

    direct_url = None
    image_url = None

    if links:
        direct_url = links[0]
        print(f"  [Found Link] {key} -> {direct_url}")
        
        # Now fetch the image from AliExpress page
        image_url = fetch_aliexpress_image(direct_url)
        if image_url:
            print(f"  [Found Image] {key} -> {image_url}")
        else:
            print(f"  [Image Warning] Could not extract image from page for {key}, using fallback search")
    else:
        print(f"  [Link Warning] No direct link found for {key}")

    # Fallback search URL if direct link not found
    if not direct_url:
        # Create a clean modern search URL
        safe_query = urllib.parse.quote(f"{brand} {model} {p_type}".strip())
        direct_url = f"https://www.aliexpress.com/w/wholesale-product.html?SearchText={safe_query}"

    # Download image if found, otherwise keep fallback
    downloaded = False
    if image_url:
        try:
            r = scraper.get(image_url, headers=HEADERS, timeout=12)
            if r.status_code == 200 and is_valid_image(r.content):
                with open(filepath, "wb") as f:
                    f.write(r.content)
                downloaded = True
                print(f"  [Image OK] Saved local image for {key}")
        except Exception as e:
            print(f"  [Download Error] Failed to download {image_url}: {e}")

    # If download failed, copy from local accessories pool or unsplash fallback
    if not downloaded:
        print(f"  [Fallback Image] Assigning fallback image for {key}")
        # We will let the repair script assign correct local pool image
        local_path = None 

    return key, {
        "brand": brand,
        "model": model,
        "url": direct_url,
        "image_url": image_url,
        "local_image": local_path
    }

def main():
    print("=" * 60)
    print("ALIEXPRESS DYNAMIC PRODUCT DATA ENRICHER")
    print("=" * 60)

    # Load cache if exists
    cache = {}
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                cache = json.load(f)
            print(f"Loaded {len(cache)} cached items.")
        except Exception:
            pass

    to_process = []
    for t in PRODUCT_TEMPLATES:
        key = f"{t['brand']} {t['model']}".strip()
        # Only process if not in cache or missing direct item link/image
        if key in cache and cache[key].get("url") and "aliexpress.com/item/" in cache[key].get("url") and cache[key].get("image_url"):
            # Verify if local image exists
            local_img = cache[key].get("local_image")
            if local_img and os.path.exists(os.path.join(FRONTED_DIR, local_img)):
                continue
        to_process.append(t)

    print(f"Products to query: {len(to_process)} / {len(PRODUCT_TEMPLATES)}")

    if to_process:
        # Use 4 workers to query DDG Lite nicely
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(process_product, t): t for t in to_process}
            for future in as_completed(futures):
                key, result = future.result()
                cache[key] = result
                # Write cache incrementally
                with open(CACHE_PATH, "w", encoding="utf-8") as f:
                    json.dump(cache, f, ensure_ascii=False, indent=2)
                # Small sleep to be polite
                time.sleep(0.5)

    print("\n[+] Finished enrichment process. All items verified/cached.")
    print(f"Total cache entries: {len(cache)}")

if __name__ == "__main__":
    main()
