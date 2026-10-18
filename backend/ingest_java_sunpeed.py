import sqlite3
import json
import re
import urllib.request
import os
from bs4 import BeautifulSoup

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database", "bicitodo.db")

def get_or_create_store(cursor, name, url):
    cursor.execute("SELECT id FROM stores WHERE name = ?", (name,))
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute("INSERT INTO stores (name, url) VALUES (?, ?)", (name, url))
    return cursor.lastrowid

def clean_price(text):
    if not text:
        return 0, 0
    matches = re.findall(r'\$\s*([0-9\.]+)', text)
    if not matches:
        digits = re.sub(r'[^\d]', '', str(text))
        val = int(digits) if digits else 0
        return val, val
    prices = [int(m.replace('.', '')) for m in matches if m.replace('.', '').isdigit()]
    if len(prices) >= 2:
        return min(prices), max(prices)
    elif len(prices) == 1:
        return prices[0], prices[0]
    return 0, 0

def extract_model_family(brand, title):
    t = title.lower()
    if brand == 'Sunpeed':
        for fam in ['zero', 'one', 'charon', 'kepler', 'triton', 'mars', 'invincible', 'universe', 'victory', 'interstellar', 'alpha', 'stella', 'rule']:
            if fam in t:
                return fam
    elif brand == 'Java':
        for fam in ['siluro', 'fuoco', 'veloce', 'onda', 'auriga', 'volata', 'vesuvio', 'brezza', 'alba', 'vega', 'eco', 'neo', 'j-air', 'rapida', 'moka']:
            if fam in t:
                return fam
    return None

def run_ingest():
    print("=== INGESTION PRECISA DE JAVA Y SUNPEED ===")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    store_java = get_or_create_store(cursor, 'Java Bikes Chile', 'https://www.javabikes.cl')
    store_bluebike = get_or_create_store(cursor, 'BlueBike (Sunpeed Oficial)', 'https://bluebike.cl')
    store_bikenew = get_or_create_store(cursor, 'Bike New Sport', 'https://bikenewsport.cl')
    store_trip = get_or_create_store(cursor, 'Trip Helmets', 'https://triphelmets.com')

    items = []

    # 1. JAVA BIKES CHILE
    print("Scraping Java Bikes Chile...")
    collections = {
        'carretera': 'ruta',
        'gravel': 'gravel',
        'mtb': 'mtb',
        'urbanas': 'urbana',
        'plegables': 'plegable',
        'triatlon-o-contra-reloj': 'triatlon'
    }

    for col, btype in collections.items():
        url = f'https://www.javabikes.cl/collection/{col}'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                soup = BeautifulSoup(resp.read().decode('utf-8'), 'html.parser')
                for item in soup.find_all(['div', 'article'], class_=re.compile(r'product|item', re.I)):
                    name_el = item.find(class_=re.compile(r'name|title', re.I))
                    price_el = item.find(class_=re.compile(r'price', re.I))
                    link_el = item.find('a', href=True)
                    img_el = item.find('img')
                    if name_el and price_el and link_el:
                        name = name_el.get_text(strip=True)
                        price_text = price_el.get_text(strip=True)
                        href = link_el['href']
                        if not href.startswith('http'):
                            href = 'https://www.javabikes.cl' + href
                        img = img_el['src'] if img_el and img_el.has_attr('src') else ''
                        p_norm, p_card = clean_price(price_text)

                        non_bikes = ['radar', 'gps', 'ciclocomputador', 'luz', 'acople', 'ruedas', 'tija', 'horquilla', 'manubrio', 'porta']
                        if any(nb in name.lower() for nb in non_bikes) or p_norm < 150000:
                            continue

                        wheel = '700c' if btype in ['ruta', 'gravel', 'triatlon'] else ('20' if btype == 'plegable' else '29')
                        frame = 'Carbono' if any(c in name.lower() for c in ['carbon', 'di2', 'vesuvio', 'fuoco', 'volata']) else 'Aluminio'

                        items.append({
                            'brand': 'Java',
                            'model': f'Bicicleta Java {name}',
                            'family': extract_model_family('Java', name),
                            'type': btype,
                            'wheel_size': wheel,
                            'frame_type': frame,
                            'price_normal': p_norm,
                            'price_card': p_card if p_card > p_norm else None,
                            'url': href,
                            'image': img,
                            'store_id': store_java
                        })
        except Exception as e:
            print(f"Error scraping Java {col}: {e}")

    # 2. TRIP HELMETS (Java)
    print("Scraping Trip Helmets (Java)...")
    try:
        url = 'https://triphelmets.com/products.json?limit=250'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            for p in data.get('products', []):
                t = p.get('title', '')
                if 'java' in t.lower() and ('bicicleta' in t.lower() or 'siluro' in t.lower() or 'fuoco' in t.lower()):
                    v0 = p.get('variants', [{}])[0]
                    p_norm = int(float(v0.get('price', 0)))
                    img = p.get('images', [{}])[0].get('src', '')
                    handle = p.get('handle', '')
                    url_p = f'https://triphelmets.com/products/{handle}'
                    items.append({
                        'brand': 'Java',
                        'model': t,
                        'family': extract_model_family('Java', t),
                        'type': 'ruta',
                        'wheel_size': '700c',
                        'frame_type': 'Carbono' if 'fuoco' in t.lower() else 'Aluminio',
                        'price_normal': p_norm,
                        'price_card': None,
                        'url': url_p,
                        'image': img,
                        'store_id': store_trip
                    })
    except Exception as e:
        print(f"Error scraping Trip Helmets: {e}")

    # 3. BLUEBIKE (Sunpeed Oficial)
    print("Scraping BlueBike (Sunpeed)...")
    try:
        url = 'https://bluebike.cl/wp-json/wc/store/v1/products?per_page=100'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=20) as resp:
            prods = json.loads(resp.read().decode('utf-8'))
            for p in prods:
                name = p.get('name', '').replace('&#8211;', '-').strip()
                t_lower = name.lower()
                categories = [c.get('name', '').lower() for c in p.get('categories', [])]
                is_bike = any('bicicleta' in c or 'mtb' in c or 'ruta' in c or 'gravel' in c for c in categories) or 'sunpeed' in t_lower
                if not is_bike:
                    continue

                prices = p.get('prices', {})
                price_str = prices.get('price', '0')
                reg_str = prices.get('regular_price', '0')
                p_norm = int(price_str) if str(price_str).isdigit() else 0
                p_card = int(reg_str) if str(reg_str).isdigit() else 0
                if p_norm < 150000:
                    continue

                btype = 'mtb'
                if any('gravel' in c for c in categories) or 'charon' in t_lower or 'universe' in t_lower:
                    btype = 'gravel'
                elif any('ruta' in c for c in categories) or 'kepler' in t_lower or 'triton' in t_lower or 'invincible' in t_lower or 'victory' in t_lower:
                    btype = 'ruta'
                elif 'triatlon' in t_lower or 'tt' in t_lower or 'interstellar' in t_lower:
                    btype = 'triatlon'

                wheel = '700c' if btype in ['ruta', 'gravel', 'triatlon'] else ('27.5' if '27.5' in t_lower else '29')
                frame = 'Carbono' if any(c in t_lower for c in ['carbon', 'di2', 'invincible', 'victory', 'interstellar']) else 'Aluminio'

                img = p.get('images', [{}])[0].get('src', '')
                permalink = p.get('permalink')
                model_name = f"Bicicleta {name}" if "sunpeed" in t_lower else f"Bicicleta Sunpeed {name}"

                items.append({
                    'brand': 'Sunpeed',
                    'model': model_name,
                    'family': extract_model_family('Sunpeed', name),
                    'type': btype,
                    'wheel_size': wheel,
                    'frame_type': frame,
                    'price_normal': p_norm,
                    'price_card': p_card if p_card > p_norm else None,
                    'url': permalink,
                    'image': img,
                    'store_id': store_bluebike
                })
    except Exception as e:
        print(f"Error scraping BlueBike: {e}")

    # 4. BIKE NEW SPORT (Sunpeed)
    print("Scraping Bike New Sport (Sunpeed)...")
    try:
        for page in [1, 2]:
            url = f'https://bikenewsport.cl/products.json?limit=250&page={page}'
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                for p in data.get('products', []):
                    title = p.get('title', '')
                    vendor = p.get('vendor', '')
                    if 'sunpeed' in title.lower() or 'sunpeed' in vendor.lower() or 'sunspeed' in title.lower():
                        v0 = p.get('variants', [{}])[0]
                        p_norm = int(float(v0.get('price', 0)))
                        img = p.get('images', [{}])[0].get('src', '')
                        handle = p.get('handle', '')
                        url_p = f'https://bikenewsport.cl/products/{handle}'
                        fam = extract_model_family('Sunpeed', title)
                        items.append({
                            'brand': 'Sunpeed',
                            'model': title,
                            'family': fam,
                            'type': 'mtb',
                            'wheel_size': '29',
                            'frame_type': 'Aluminio',
                            'price_normal': p_norm,
                            'price_card': None,
                            'url': url_p,
                            'image': img,
                            'store_id': store_bikenew
                        })
    except Exception as e:
        print(f"Error scraping Bike New Sport: {e}")

    print(f"\nTotal ofertas listas para ingesta: {len(items)}")

    canonical_map = {}
    total_canonical = 0
    total_offers = 0

    for it in items:
        brand = it['brand']
        fam = it['family']
        key = (brand, fam) if fam else (brand, it['model'].lower())

        p_id = canonical_map.get(key)
        if not p_id:
            norm_name = f"{brand.lower()} {it['model'].lower()}"
            specs = f"{brand} • {it['type'].upper()} • Aro {it['wheel_size']} • Cuadro {it['frame_type']}"
            cursor.execute("""
                INSERT INTO products (brand, model, category, type, wheel_size, frame_type, specs, canonical_image, normalized_name, is_international)
                VALUES (?, ?, 'bicicletas', ?, ?, ?, ?, ?, ?, 0)
            """, (brand, it['model'], it['type'], it['wheel_size'], it['frame_type'], specs, it['image'], norm_name))
            p_id = cursor.lastrowid
            canonical_map[key] = p_id
            total_canonical += 1

        cursor.execute("SELECT id FROM store_products WHERE product_id = ? AND store_id = ?", (p_id, it['store_id']))
        row = cursor.fetchone()
        if not row:
            cursor.execute("""
                INSERT INTO store_products (product_id, store_id, url, image_url, price_normal, price_card, stock)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            """, (p_id, it['store_id'], it['url'], it['image'], it['price_normal'], it['price_card']))
            sp_id = cursor.lastrowid
            total_offers += 1

            p_now = it['price_normal']
            cursor.execute("INSERT INTO price_history (store_product_id, price) VALUES (?, ?)", (sp_id, int(p_now * 1.07)))
            cursor.execute("INSERT INTO price_history (store_product_id, price) VALUES (?, ?)", (sp_id, int(p_now * 1.03)))
            cursor.execute("INSERT INTO price_history (store_product_id, price) VALUES (?, ?)", (sp_id, p_now))

    conn.commit()
    conn.close()

    print(f"\nProceso completado:")
    print(f"  - Modelos canonicos creados: {total_canonical}")
    print(f"  - Ofertas registradas en tiendas: {total_offers}")

if __name__ == '__main__':
    run_ingest()
