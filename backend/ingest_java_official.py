"""
ingest_java_official.py - Scraper oficial para bicicletas Java en Chile (javabikes.cl)
Ingesta el catalogo completo de Java con:
- Precios reales de venta y precios tachados/oferta
- Tipos: ruta, gravel, mtb, urbana, plegable, triatlon
- Imagenes oficiales y enlaces verificados
"""
import urllib.request
import ssl
import re
import sqlite3
import os
from bs4 import BeautifulSoup

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database", "bicitodo.db")
ctx = ssl.create_default_context()
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36'
}

def clean_prices(text):
    if not text:
        return 0, None
    matches = re.findall(r'\$\s*([0-9\.]+)', text)
    if not matches:
        digits = re.sub(r'[^\d]', '', str(text))
        v = int(digits) if digits else 0
        return v, None
    vals = [int(m.replace('.', '')) for m in matches if m.replace('.', '').isdigit()]
    if len(vals) >= 2:
        # Usually format is $ 1.249.000 $ 1.124.100 -> regular, normal
        reg = max(vals)
        norm = min(vals)
        return norm, (reg if reg > norm else None)
    elif len(vals) == 1:
        return vals[0], None
    return 0, None

def get_or_create_store(cur, name, url):
    cur.execute("SELECT id FROM stores WHERE name = ?", (name,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute("INSERT INTO stores (name, url) VALUES (?, ?)", (name, url))
    return cur.lastrowid

def run():
    print("=== INGESTANDO BICICLETAS JAVA OFICIALES (javabikes.cl) ===")
    collections = {
        'carretera': 'ruta',
        'gravel': 'gravel',
        'mtb': 'mtb',
        'urbanas': 'urbana',
        'plegables': 'plegable',
        'triatlon-o-contra-reloj': 'triatlon'
    }

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    store_id = get_or_create_store(cur, 'Java Bikes Chile', 'https://www.javabikes.cl')

    non_bikes = ['radar', 'gps', 'ciclocomputador', 'luz', 'acople', 'ruedas', 'tija', 'horquilla', 'manubrio', 'porta', 'casco', 'polera', 'guante', 'sillin']

    new_prods = 0
    new_offers = 0
    updated_offers = 0

    for col, btype in collections.items():
        url = f'https://www.javabikes.cl/collection/{col}'
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
                soup = BeautifulSoup(r.read().decode('utf-8', errors='replace'), 'html.parser')
                cards = soup.find_all(['div', 'article'], class_=re.compile(r'product|item', re.I))
                for card in cards:
                    name_el = card.find(class_=re.compile(r'name|title', re.I))
                    price_el = card.find(class_=re.compile(r'price', re.I))
                    a_el = card.find('a', href=True)
                    img_el = card.find('img')
                    if not (name_el and price_el and a_el):
                        continue

                    title = name_el.get_text(strip=True)
                    price_text = price_el.get_text(strip=True)
                    href = a_el['href']
                    if not href.startswith('http'):
                        href = 'https://www.javabikes.cl' + href

                    img = img_el.get('src', '') if img_el else ''

                    p_norm, p_card = clean_prices(price_text)
                    if p_norm < 150000 or any(nb in title.lower() for nb in non_bikes):
                        continue

                    wheel = '700c' if btype in ['ruta', 'gravel', 'triatlon'] else ('20' if btype == 'plegable' else '29')
                    frame = 'Fibra de Carbono' if any(c in title.lower() for c in ['carbon', 'di2', 'vesuvio', 'fuoco', 'volata', 'j-air']) else 'Aluminio'

                    model_name = f"Bicicleta Java {title}" if "java" not in title.lower() else f"Bicicleta {title}"
                    norm_name = re.sub(r'\s+', ' ', model_name.lower()).strip()
                    specs = f"Java • {btype.upper()} • Aro {wheel} • Cuadro {frame}"

                    cur.execute("SELECT id FROM products WHERE category = 'bicicletas' AND brand = 'Java' AND normalized_name = ?", (norm_name,))
                    prod_row = cur.fetchone()
                    if not prod_row:
                        cur.execute("""
                            INSERT INTO products (brand, model, category, type, wheel_size, frame_type, specs, canonical_image, normalized_name, is_international)
                            VALUES ('Java', ?, 'bicicletas', ?, ?, ?, ?, ?, ?, 0)
                        """, (model_name, btype, wheel, frame, specs, img, norm_name))
                        prod_id = cur.lastrowid
                        new_prods += 1
                    else:
                        prod_id = prod_row[0]

                    cur.execute("SELECT id, price_normal FROM store_products WHERE url = ?", (href,))
                    sp_row = cur.fetchone()
                    if sp_row:
                        cur.execute("""
                            UPDATE store_products 
                            SET price_normal = ?, price_card = ?, stock = 1, image_url = COALESCE(NULLIF(?, ''), image_url), last_updated = CURRENT_TIMESTAMP
                            WHERE id = ?
                        """, (p_norm, p_card, img, sp_row[0]))
                        if sp_row[1] != p_norm:
                            cur.execute("INSERT INTO price_history (store_product_id, price) VALUES (?, ?)", (sp_row[0], p_norm))
                        updated_offers += 1
                    else:
                        cur.execute("""
                            INSERT INTO store_products (product_id, store_id, url, image_url, price_normal, price_card, stock, last_updated)
                            VALUES (?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
                        """, (prod_id, store_id, href, img, p_norm, p_card))
                        new_sp_id = cur.lastrowid
                        cur.execute("INSERT INTO price_history (store_product_id, price) VALUES (?, ?)", (new_sp_id, p_norm))
                        new_offers += 1

                    print(f"  [OK] {model_name} -> ${p_norm:,} (Ref: ${p_card or p_norm:,})")
        except Exception as e:
            print(f"Error colección {col}: {e}")

    conn.commit()
    conn.close()

    print("\n=== RESUMEN JAVA ===")
    print(f"Productos nuevos: {new_prods}")
    print(f"Ofertas nuevas: {new_offers}")
    print(f"Ofertas actualizadas: {updated_offers}")

if __name__ == '__main__':
    run()
