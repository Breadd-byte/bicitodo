"""
refresh_images.py - Re-descarga las imagenes de cada producto desde su URL de tienda.
Usa la API JSON de Shopify para tiendas Shopify (rapido y confiable).
Para otras tiendas, hace scraping del HTML del producto.
Actualiza data.json con las imagenes correctas.
"""
import os, sys, json, re, time, shutil
os.environ['PYTHONIOENCODING'] = 'utf-8'
try: sys.stdout.reconfigure(encoding='utf-8')
except: pass

try:
    import cloudscraper
    from bs4 import BeautifulSoup
except ImportError:
    os.system("pip install cloudscraper beautifulsoup4 lxml -q")
    import cloudscraper
    from bs4 import BeautifulSoup

BASE_DIR = r"c:\Users\basti\Desktop\bicitodo"
FRONTED_DIR = os.path.join(BASE_DIR, "fronted")
ASSETS_DIR = os.path.join(FRONTED_DIR, "assets", "bikes")

scraper = cloudscraper.create_scraper(
    browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "es-CL,es;q=0.9",
}

FALLBACK_IMG = "https://images.unsplash.com/photo-1571068316344-75bc76f77890?auto=format&fit=crop&w=600&h=400&q=80"

def get_ext(url):
    if not url: return "jpg"
    m = re.search(r'\.(jpg|jpeg|png|webp|gif)', url.lower().split("?")[0])
    return m.group(1) if m else "jpg"

def download_image_fresh(img_url, filepath):
    """Descarga siempre, sin importar si el archivo existe."""
    if not img_url or img_url.startswith("https://images.unsplash"):
        return False
    try:
        r = scraper.get(img_url, headers=HEADERS, timeout=15)
        if r.status_code == 200 and len(r.content) > 3000:
            # Verificar que sea imagen real (magic bytes)
            magic = r.content[:4]
            is_img = (
                magic[:3] == b'\xff\xd8\xff' or   # JPEG
                magic[:4] == b'\x89PNG' or          # PNG
                magic[:4] == b'RIFF' or             # WEBP
                magic[:6] in (b'GIF87a', b'GIF89a') # GIF
            )
            if is_img:
                with open(filepath, 'wb') as f:
                    f.write(r.content)
                return True
    except Exception as e:
        pass
    return False

def get_shopify_image(product_url):
    """Para tiendas Shopify: usa la API JSON del producto para obtener la imagen principal."""
    try:
        # Convertir URL de producto a JSON API
        # https://fauconbikes.cl/products/bicicleta-mtb → https://fauconbikes.cl/products/bicicleta-mtb.json
        json_url = product_url.rstrip('/') + '.json'
        r = scraper.get(json_url, headers=HEADERS, timeout=12)
        if r.status_code == 200:
            data = r.json()
            images = data.get('product', {}).get('images', [])
            if images:
                src = images[0].get('src', '')
                return src.split('?')[0] if src else None
    except Exception:
        pass
    return None

def get_html_image(product_url):
    """Para tiendas HTML: scraping de la imagen principal del producto."""
    try:
        r = scraper.get(product_url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, 'lxml')
        # Intentar diferentes selectores para imagen principal
        selectors = [
            # Open Graph (mas confiable)
            ('meta[property="og:image"]', 'content'),
            ('meta[name="og:image"]', 'content'),
            # Shopify / Magento / Jumpseller producto
            ('.product-main-image img', 'src'),
            ('.product__media img', 'src'),
            ('.product-image img', 'src'),
            ('.product-img img', 'src'),
            ('#product-image img', 'src'),
            ('.product-gallery img', 'src'),
            ('img.product-image-photo', 'src'),
            # Decathlon
            ('img.product-image', 'src'),
            ('picture img', 'src'),
        ]
        for selector, attr in selectors:
            el = soup.select_one(selector)
            if el:
                val = el.get(attr, '')
                if val and ('placeholder' not in val.lower()) and len(val) > 10:
                    if val.startswith('//'): val = 'https:' + val
                    return val.split('?')[0]
    except Exception:
        pass
    return None

# ---- MAIN ----
d = json.load(open(os.path.join(FRONTED_DIR, 'data.json'), encoding='utf-8'))
bikes = d['bicicletas']
print(f"Total bicicletas: {len(bikes)}")
print("Refrescando imagenes...\n")

SHOPIFY_DOMAINS = ['fauconbikes.cl', 'satirobikes.cl', 'www.dsbikes.cl', 'bikeplus.cl', 'copenhague.cl']

updated = 0
failed = 0
skipped = 0

for idx, bike in enumerate(bikes):
    offer = bike['offers'][0]
    product_url = offer.get('url', '')
    store_key = offer.get('storeKey', '')
    
    # Nombre de archivo basado en ID
    old_img_path = bike.get('image', '')
    ext_guess = get_ext(old_img_path)
    new_filename = f"bike_{bike['id']}.{ext_guess}"
    new_filepath = os.path.join(ASSETS_DIR, new_filename)
    
    # Obtener URL de imagen desde la tienda
    img_url = None
    
    if product_url and product_url.startswith('http'):
        domain = re.sub(r'https?://', '', product_url).split('/')[0]
        
        if any(sd in domain for sd in SHOPIFY_DOMAINS):
            # Tienda Shopify: usar API JSON (mas rapido)
            img_url = get_shopify_image(product_url)
        else:
            # Otras tiendas: scraping HTML
            img_url = get_html_image(product_url)
    
    if not img_url:
        # Sin URL de imagen, mantener lo que hay
        skipped += 1
        if (idx + 1) % 50 == 0:
            print(f"  [{idx+1}/{len(bikes)}] {updated} actualizadas, {failed} fallidas, {skipped} sin URL")
        continue
    
    # Determinar extension correcta
    ext = get_ext(img_url)
    new_filename = f"bike_{bike['id']}.{ext}"
    new_filepath = os.path.join(ASSETS_DIR, new_filename)
    local_path = f"assets/bikes/{new_filename}"
    
    # Descargar imagen fresca
    ok = download_image_fresh(img_url, new_filepath)
    
    if ok:
        bike['image'] = local_path
        updated += 1
    else:
        failed += 1
    
    if (idx + 1) % 25 == 0:
        print(f"  [{idx+1}/{len(bikes)}] {updated} actualizadas, {failed} fallidas, {skipped} sin URL")
    
    time.sleep(0.15)  # Gentil con los servidores

# Guardar data.json actualizado
with open(os.path.join(FRONTED_DIR, 'data.json'), 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)

print(f"\nFinalizado!")
print(f"  Imagenes actualizadas: {updated}")
print(f"  Fallidas: {failed}")
print(f"  Sin URL (sin cambio): {skipped}")
print(f"  data.json guardado.")
