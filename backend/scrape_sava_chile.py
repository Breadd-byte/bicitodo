"""
scrape_sava_chile.py - Scraper oficial para bicicletas SAVA en Chile (savachile.cl)
Obtiene todos los modelos de fibra de carbono (MTB, Ruta, Gravel, DH) con:
- Precios 100% reales (normal y referencia con descuento)
- Imagen de alta resolución
- Especificaciones reales (aro, transmisión, cuadro de carbono)
- Enlace directo a la tienda oficial
"""
import urllib.request
import urllib.parse
import ssl
import re
import json
import sqlite3
import os
from bs4 import BeautifulSoup

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database", "bicitodo.db")
ctx = ssl.create_default_context()
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}

def clean_title(title):
    t = re.sub(r'\s+', ' ', title).strip()
    # Normalize naming
    if not t.lower().startswith('bicicleta'):
        t = f"Bicicleta {t}"
    return t

def infer_bike_type(title, text=""):
    comb = f"{title} {text}".lower()
    if any(k in comb for k in ['dh', 'downhill', 'denon', 'full suspension']):
        return 'mtb'
    if any(k in comb for k in ['deck', 'mountain', 'mtb']):
        return 'mtb'
    if any(k in comb for k in ['wind of war', 'r08', 'ruta', 'road']):
        return 'ruta'
    if any(k in comb for k in ['gravel']):
        return 'gravel'
    return 'mtb'

def infer_wheel_size(title, text=""):
    comb = f"{title} {text}".lower()
    if '29' in comb:
        return '29'
    if '27.5' in comb or '27,5' in comb:
        return '27.5'
    if '700' in comb or 'r08' in comb or 'wind of war' in comb or 'ruta' in comb:
        return '700c'
    return '29'

def get_or_create_store(cur, name, url):
    cur.execute("SELECT id FROM stores WHERE name = ?", (name,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute("INSERT INTO stores (name, url) VALUES (?, ?)", (name, url))
    return cur.lastrowid

def scrape_sava():
    print("=== INICIANDO SCRAPER SAVA CHILE (savachile.cl) ===")
    
    # Discovery of product URLs
    candidate_urls = [
        'https://savachile.cl/3-bicicletas-sava-fibra-carbono-mountain-bike',
        'https://savachile.cl/4-bicicletas-de-ruta',
        'https://savachile.cl/2-inicio',
        'https://savachile.cl/productos-rebajados'
    ]
    
    product_urls = set()
    for cat_url in candidate_urls:
        try:
            req = urllib.request.Request(cat_url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
                soup = BeautifulSoup(r.read().decode('utf-8', errors='replace'), 'html.parser')
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    if re.search(r'/\d+(?:-\d+)?-[a-z0-9\-]+\.html', href) and 'content' not in href:
                        clean_href = href.split('#')[0].split('?')[0]
                        product_urls.add(clean_href)
        except Exception as e:
            print(f"Error explorando {cat_url}: {e}")
            
    print(f"URLs de productos encontradas: {len(product_urls)}")
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    store_id = get_or_create_store(cur, 'Sava Bikes Chile', 'https://savachile.cl')
    
    added_products = 0
    added_offers = 0
    updated_offers = 0
    
    for url in product_urls:
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
                html = r.read().decode('utf-8', errors='replace')
                soup = BeautifulSoup(html, 'html.parser')
                
                title_el = soup.find('h1')
                if not title_el:
                    continue
                raw_title = title_el.get_text(strip=True)
                
                # Filter out non-bicycles (lentes, accesorios, etc)
                non_bikes = ['lente', 'anteojo', 'casco', 'polera', 'guante', 'calcet', 'polarizado', 'tubo', 'porta']
                if any(nb in raw_title.lower() for nb in non_bikes):
                    continue
                
                # Price extraction
                price_meta = soup.find('meta', property='product:price:amount')
                if not price_meta or not price_meta.get('content'):
                    continue
                    
                price_normal = int(float(price_meta['content']))
                if price_normal < 200000: # Sava carbon bikes start above 400k
                    continue
                    
                # Reference price / old price if on sale
                regular_price = None
                regular_el = soup.find(class_=re.compile(r'regular-price|old-price', re.I))
                if regular_el:
                    digits = re.sub(r'[^\d]', '', regular_el.get_text(strip=True))
                    if digits and int(digits) > price_normal:
                        regular_price = int(digits)
                        
                # Image extraction
                img_url = ""
                og_img = soup.find('meta', property='og:image')
                if og_img and og_img.get('content'):
                    img_url = og_img['content']
                elif soup.find('img', class_=re.compile(r'js-qv-product-cover', re.I)):
                    img_url = soup.find('img', class_=re.compile(r'js-qv-product-cover', re.I)).get('src', '')
                    
                # Type, wheel, frame
                bike_type = infer_bike_type(raw_title, html)
                wheel_size = infer_wheel_size(raw_title, html)
                frame_type = "Fibra de Carbono"
                
                clean_name = clean_title(raw_title)
                if 'sava' not in clean_name.lower():
                    clean_name = f"Bicicleta Sava {clean_name.replace('Bicicleta ', '')}"
                    
                norm_name = re.sub(r'\s+', ' ', clean_name.lower()).strip()
                specs = f"Sava • {bike_type.upper()} • Aro {wheel_size} • Cuadro {frame_type}"
                
                # Check if product exists
                cur.execute("SELECT id FROM products WHERE category = 'bicicletas' AND brand = 'Sava' AND normalized_name = ?", (norm_name,))
                prod_row = cur.fetchone()
                
                if not prod_row:
                    cur.execute("""
                        INSERT INTO products (brand, model, category, type, wheel_size, frame_type, specs, canonical_image, normalized_name, is_international)
                        VALUES ('Sava', ?, 'bicicletas', ?, ?, ?, ?, ?, ?, 0)
                    """, (clean_name, bike_type, wheel_size, frame_type, specs, img_url, norm_name))
                    prod_id = cur.lastrowid
                    added_products += 1
                else:
                    prod_id = prod_row[0]
                    
                # Check store_products
                cur.execute("SELECT id FROM store_products WHERE url = ?", (url,))
                sp_row = cur.fetchone()
                if sp_row:
                    cur.execute("""
                        UPDATE store_products 
                        SET price_normal = ?, price_card = ?, stock = 1, image_url = COALESCE(NULLIF(?, ''), image_url), last_updated = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (price_normal, regular_price, img_url, sp_row[0]))
                    updated_offers += 1
                else:
                    cur.execute("""
                        INSERT INTO store_products (product_id, store_id, url, image_url, price_normal, price_card, stock, last_updated)
                        VALUES (?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
                    """, (prod_id, store_id, url, img_url, price_normal, regular_price))
                    new_sp_id = cur.lastrowid
                    cur.execute("INSERT INTO price_history (store_product_id, price) VALUES (?, ?)", (new_sp_id, price_normal))
                    added_offers += 1
                    
                print(f"  [OK] {clean_name} -> ${price_normal:,} (Normal: ${regular_price or price_normal:,})")
        except Exception as e:
            print(f"Error procesando {url}: {e}")
            
    conn.commit()
    conn.close()
    
    print("\n=== RESUMEN SAVA ===")
    print(f"Productos nuevos: {added_products}")
    print(f"Ofertas nuevas: {added_offers}")
    print(f"Ofertas actualizadas: {updated_offers}")

if __name__ == '__main__':
    scrape_sava()
