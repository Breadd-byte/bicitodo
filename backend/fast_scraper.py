"""
fast_scraper.py - BiciTodo Market Scraper v2.0
Extrae bicicletas de 15 tiendas chilenas usando cloudscraper + BeautifulSoup.
Genera data.json listo para el frontend.
"""
import os, sys, json, re, time, urllib.request, unicodedata

# Forzar UTF-8 en Windows
os.environ['PYTHONIOENCODING'] = 'utf-8'
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

try:
    import cloudscraper
    from bs4 import BeautifulSoup
except ImportError:
    os.system("pip install cloudscraper beautifulsoup4 lxml -q")
    import cloudscraper
    from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTED_DIR = os.path.join(BASE_DIR, "fronted")
ASSETS_DIR = os.path.join(FRONTED_DIR, "assets", "bikes")
os.makedirs(ASSETS_DIR, exist_ok=True)

scraper = cloudscraper.create_scraper(
    browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "es-CL,es;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# -------------------------------------------------------
# HELPERS
# -------------------------------------------------------
def fetch_html(url, timeout=20):
    try:
        r = scraper.get(url, headers=HEADERS, timeout=timeout)
        if r.status_code == 200:
            return BeautifulSoup(r.text, "lxml")
    except Exception as e:
        print(f"  [WARN] Error fetching {url}: {e}")
    return None

def fetch_json(url, timeout=15):
    try:
        r = scraper.get(url, headers=HEADERS, timeout=timeout)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"  [WARN] Error fetching JSON {url}: {e}")
    return None

def clean_price(text):
    if not text: return None
    nums = re.sub(r'[^\d]', '', str(text))
    return int(nums) if nums else None

def clean_text(text):
    if not text: return ""
    return re.sub(r'\s+', ' ', str(text)).strip()

def remove_accents(text):
    nfkd = unicodedata.normalize('NFKD', str(text))
    return ''.join(c for c in nfkd if not unicodedata.combining(c))

def categorize(name):
    n = remove_accents(name.lower())
    if any(k in n for k in ["electrica", "electrico", "ebike", "e-bike", "e bike"]): return "electrica"
    if any(k in n for k in ["fixie", "fix ", "pista", "tracklocross", "chromoly", "city bike", "paseo", "crucero", "klunker"]):
        return "ruta"
    if any(k in n for k in ["gravel", "ruta", "road", "700c", "endurance", "cicloturismo"]): return "ruta"
    if any(k in n for k in ["urbana", "city", "commuter", "hibrida", "paseo"]): return "urbana"
    if any(k in n for k in ["infantil", "nino", "junior", "kids", " 16\"", " 20\"", "sin pedales", "ruedas de entrenamiento"]):
        return "infantil"
    if any(k in n for k in ["bmx", "freestyle", "dirt"]): return "mtb"
    return "mtb"

def extract_wheel(name):
    n = name.lower()
    for pat, val in [('700c', '700c'), (r'\b29\b', '29'), (r'\b27\.5\b', '27.5'), (r'\b26\b', '26'), (r'\b24\b', '24'), (r'\b20\b', '20'), (r'\b16\b', '16')]:
        if re.search(pat, n): return val
    if any(k in n for k in ["gravel", "ruta", "road", "fixie", "fixed", "singlespeed", "carrera", "pista"]):
        return "700c"
    return "29"

def extract_frame(name):
    n = name.lower()
    if any(k in n for k in ["carbon", "carbono"]): return "Carbono"
    if any(k in n for k in ["acero", "steel", "chromoly", "cromo"]): return "Acero"
    return "Aluminio"

ACCESSORY_KW = [
    # Ropa y accesorios de ciclista
    "bib short", "bib ", "bib-", "jersey", "maillot", "culotte",
    "tricota", "camiseta", "calza ", "guante", "calcetines",
    # Partes y componentes
    "casco ", "rodillera", "cargador usb", "rotor ",
    "camara de aire", "sillin ", "manillar",
    "bolsa cuadro", "bolso cuadro", "bolso manubrio", "bolso frontal", "bolso trasero",
    "luz delantera", "luz trasera", "aceite ", "bombin", "inflador",
    "candado", "caramayola", "portabotella", "alforja", "zapatilla",
    "lentes ", "gafas", "maza delantera", "maza trasera", "bieleta ",
    "marco cuadro", "horquilla ", "llanta ", "rayos ", "cassette ",
    "pastillas de freno", "timbre", "cubremochila", "zapatillas",
    "mochila hidratacion", "botella para", "parrilla para", "portamochila",
    "pedal stamp", "pedal spank", "shimano sh-", "shimano ce-",
    # Soportes y racks - NO son bicicletas
    "porta bicicleta", "portabicicleta", "soporte bicicleta",
    "soporte para bici", "soporte de pared", "rack de bicicleta",
    "enlace bieleta", "canasto para",
]

# Palabras que CONFIRMAN que es una bicicleta
BIKE_KW = [
    "bicicleta", "bike ", "mtb", "mountain bike", "bici ", "ebike",
    "e-bike", "gravel", "fixie", "tracklocross",
    "precaliber", "marlin", "roscoe",
    "procaliber", "slash ", "fuel ex", "domane", "emonda", "madone",
    "defy ", "tcr ", "propel ", "liv langma", "liv avail", "liv tempt",
    "trance ", "anthem ", "attain ", "siskiu",
    "marin ", "kona ", "orbea ", "specialized",
    "giant ", "merida ", "cannondale ", "trek ", "scott ", "focus ",
    "cube ", "ghost ", "stumpjumper",
    "enduro ", "epic ", "turbo ", "diverge", "crux ",
    "checkpoint", "session ", "rize ", "remedy ", "powerfly",
    "nicasio", "san quentin", "headlands",
    "bobcat", "ragnar", "nilo ", "max 7",
    "riverside", "edr cf", "edr ", "rc 500", "rc 120",
    "r 500", "hybride", "hibrida", "hibrido",
]

def is_bike(name):
    nl = remove_accents(name.lower())
    return any(kw in nl for kw in BIKE_KW)

def is_accessory(name, price):
    if price and price < 29000: return True
    nl = remove_accents(name.lower())
    if any(kw in nl for kw in ACCESSORY_KW): return True
    # Para tiendas mixtas (Sparta, Faucon): si no tiene palabra clave de bici, descartar
    return False

def download_image(img_url, filename):
    if not img_url: return None
    path = os.path.join(ASSETS_DIR, filename)
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return f"assets/bikes/{filename}"
    try:
        r = scraper.get(img_url, headers=HEADERS, timeout=12)
        if r.status_code == 200 and len(r.content) > 1000:
            with open(path, "wb") as f:
                f.write(r.content)
            return f"assets/bikes/{filename}"
    except Exception:
        pass
    return None

def get_ext(url):
    if not url: return "jpg"
    m = re.search(r'\.(jpg|jpeg|png|webp|gif)', url.lower().split("?")[0])
    return m.group(1) if m else "jpg"

# -------------------------------------------------------
# SHOPIFY UNIVERSAL (API /products.json)
# Funciona para: Satiro, Faucon, BikePlus, DS Bikes, y mas
# -------------------------------------------------------
def scrape_shopify_api(store_name, store_key, domain, collections, max_pages=8):
    """
    Usa SIEMPRE el endpoint de coleccion especifica para no traer TODO el catalogo.
    Ejemplo: /collections/bicicletas/products.json
    """
    items = []
    seen_handles = set()
    for collection in collections:
        for page in range(1, max_pages + 1):
            # SIEMPRE usar coleccion especifica, nunca el endpoint global
            url = f"{domain}/collections/{collection}/products.json?limit=250&page={page}"
            data = fetch_json(url)
            if not data:
                break
            products = data.get("products", [])
            if not products:
                break
            for p in products:
                handle = p.get("handle", "")
                if handle in seen_handles:
                    continue
                seen_handles.add(handle)
                title = p.get("title", "")
                if not title: continue
                # Filtro estricto: debe ser una bicicleta
                product_type = p.get("product_type", "").lower()
                is_bike_type = "bicicleta" in product_type or "bike" in product_type or "bicycle" in product_type
                if not is_bike_type and not is_bike(title):
                    continue
                vendor = p.get("vendor", store_name)
                prod_url = f"{domain}/products/{handle}"
                variants = p.get("variants", [{}])
                price = None
                for v in variants:
                    price = clean_price(v.get("price"))
                    if price: break
                images = p.get("images", [])
                img_url = None
                if images:
                    raw = images[0].get("src", "")
                    img_url = raw.split("?")[0] if raw else None
                if price and not is_accessory(title, price):
                    items.append({
                        "name": title, "brand": vendor, "price_normal": price,
                        "url": prod_url, "image_url": img_url,
                        "store": store_name, "store_key": store_key
                    })
    print(f"  [OK] {store_name}: {len(items)} bicicletas")
    return items

# -------------------------------------------------------
# OXFORD (Magento)
# -------------------------------------------------------
def scrape_oxford():
    items = []
    domain = "https://www.oxfordstore.cl"
    url = f"{domain}/bicicletas.html"
    for _ in range(8):
        soup = fetch_html(url)
        if not soup: break
        for p in soup.select(".product-item-info"):
            name_el = p.select_one(".product-item-link")
            price_el = p.select_one(".price-wrapper .price")
            img_el = p.select_one(".product-image-photo")
            if not name_el: continue
            name = clean_text(name_el.get_text())
            price = clean_price(price_el.get_text() if price_el else None)
            img = img_el.get("src") if img_el else None
            # Quitar parametros de cache de la imagen
            if img and "/cache/" in img:
                img = re.sub(r'/cache/[^/]+/', '/', img)
            href = name_el.get("href", "")
            if name and price and not is_accessory(name, price):
                items.append({
                    "name": name, "brand": "Oxford", "price_normal": price,
                    "url": href, "image_url": img,
                    "store": "Oxford Store", "store_key": "oxford"
                })
        nxt = soup.select_one(".action.next")
        if not nxt or not nxt.get("href"): break
        url = nxt["href"]
    print(f"  [OK] Oxford Store: {len(items)} bicicletas")
    return items

# -------------------------------------------------------
# COPENHAGUE (Jumpseller)
# -------------------------------------------------------
def scrape_copenhague():
    items = []
    domain = "https://www.copenhague.cl"
    url = f"{domain}/bicicletas"
    for _ in range(6):
        soup = fetch_html(url)
        if not soup: break
        products = soup.select(".product-block")
        if not products:
            products = soup.select(".item.product, .product-item")
        if not products: break
        for p in products:
            name_el = p.select_one(".product-block__name, h3 a, .name a, .title a")
            price_el = p.select_one(".product-block__price, .price, .current-price")
            img_el = p.select_one("img")
            a_el = p.select_one("a")
            if not name_el: continue
            name = clean_text(name_el.get_text())
            price = clean_price(price_el.get_text() if price_el else None)
            img = img_el.get("src") or img_el.get("data-src") if img_el else None
            href = a_el.get("href") if a_el else None
            if href and not href.startswith("http"): href = domain + href
            if name and not is_accessory(name, price):
                items.append({
                    "name": name, "brand": "State Bicycle Co", "price_normal": price or 0,
                    "url": href, "image_url": img,
                    "store": "Copenhague", "store_key": "copenhague"
                })
        nxt = soup.select_one("li.next a, a[rel='next'], .pagination .next a")
        if not nxt: break
        nh = nxt.get("href", "")
        url = nh if nh.startswith("http") else domain + nh
    print(f"  [OK] Copenhague: {len(items)} bicicletas")
    return items

# -------------------------------------------------------
# DECATHLON (Oneshop)
# -------------------------------------------------------
def scrape_decathlon():
    items = []
    domain = "https://www.decathlon.cl"
    url = f"{domain}/4786-bicicletas"
    for _ in range(8):
        soup = fetch_html(url)
        if not soup: break
        cards = soup.select("article.product-card")
        if not cards: break
        for p in cards:
            name_el = p.select_one("h2")
            price_el = p.select_one(".price_amount")
            img_el = p.select_one("img")
            a_el = p.select_one("a.js-product-card-link, a")
            brand_el = p.select_one("p.u-typo-body-s")
            if not name_el: continue
            name = clean_text(name_el.get_text())
            price_val = price_el.get("data-value") if price_el else None
            price = clean_price(price_val or (price_el.get_text() if price_el else None))
            img = img_el.get("src") if img_el else None
            href = a_el.get("href") if a_el else None
            if href and not href.startswith("http"): href = domain + href
            brand = clean_text(brand_el.get_text()) if brand_el else "Decathlon"
            if name and price and not is_accessory(name, price):
                items.append({
                    "name": name, "brand": brand, "price_normal": price,
                    "url": href, "image_url": img,
                    "store": "Decathlon", "store_key": "decathlon"
                })
        nxt = soup.select_one("a[data-testid='pagination-next'], .pagination a[rel='next']")
        if not nxt: break
        nh = nxt.get("href", "")
        url = nh if nh.startswith("http") else domain + nh
    print(f"  [OK] Decathlon: {len(items)} bicicletas")
    return items

# -------------------------------------------------------
# FALABELLA (API REST publica)
# -------------------------------------------------------
def scrape_falabella():
    items = []
    categories = ["cat40062", "cat40063", "cat40064", "cat40065", "cat40066"]
    BASE = "https://www.falabella.com.cl/rest/model/falabella/rest/browse/BrowseActor/fetch-product-summary"
    for cat in categories:
        offset = 0
        while True:
            params = f"?Nrpp=50&No={offset}&Nr=AND(product.siteId:FALCL,category.repositoryId:{cat})&Ns=product.isAvailableInStore|1&rankingMechanism=ProductRanking"
            data = fetch_json(BASE + params)
            if not data: break
            results = data.get("results", {})
            records = results.get("records", []) or results.get("products", [])
            if not records: break
            for rec in records:
                attrs = rec.get("attributes", rec)
                name = clean_text(attrs.get("displayName") or attrs.get("product.displayName") or "")
                brand = clean_text(attrs.get("brand") or attrs.get("product.brand") or "Desconocida")
                pid = attrs.get("productId") or attrs.get("product.repositoryId") or ""
                slug = attrs.get("slug") or attrs.get("product.slug") or pid
                prod_url = f"https://www.falabella.com.cl/falabella-cl/product/{pid}/{slug}"
                skus = attrs.get("skus", [])
                price = None
                if isinstance(skus, list) and skus:
                    price = clean_price(str(skus[0].get("price", {}).get("original", "")))
                if not price:
                    price = clean_price(str(attrs.get("price", "")))
                images = attrs.get("images") or attrs.get("product.imageList") or []
                img = None
                if images:
                    img = images[0] if isinstance(images[0], str) else None
                if name and price and not is_accessory(name, price):
                    items.append({
                        "name": name, "brand": brand, "price_normal": price,
                        "url": prod_url, "image_url": img,
                        "store": "Falabella", "store_key": "falabella"
                    })
            total = results.get("totalNumRecs", 0)
            offset += 50
            if offset >= min(total, 300): break
        time.sleep(0.5)
    print(f"  [OK] Falabella: {len(items)} bicicletas")
    return items

# -------------------------------------------------------
# RIPLEY (HTML)
# -------------------------------------------------------
def scrape_ripley():
    items = []
    base = "https://simple.ripley.cl"
    urls = [
        "/bicicletas", "/bicicletas-de-montana",
        "/bicicletas-de-ruta-y-gravel", "/bicicletas-electricas",
        "/bicicletas-infantiles", "/bicicletas-urbanas-e-hibridas",
    ]
    for path in urls:
        soup = fetch_html(base + path)
        if not soup: continue
        for p in soup.select("[class*='ProductItem'], [class*='catalog-product'], .product-item"):
            name_el = p.select_one("[class*='productName'], [class*='product-title'], h2, h3")
            price_el = p.select_one("[class*='price']:not([class*='old']), [class*='Price']")
            img_el = p.select_one("img")
            a_el = p.select_one("a")
            if not name_el: continue
            name = clean_text(name_el.get_text())
            if len(name) < 5: continue
            price = clean_price(price_el.get_text() if price_el else None)
            img = img_el.get("src") or img_el.get("data-src") if img_el else None
            href = a_el.get("href") if a_el else None
            if href and href.startswith("/"): href = base + href
            if name and price and not is_accessory(name, price):
                items.append({
                    "name": name, "brand": "Ripley", "price_normal": price,
                    "url": href, "image_url": img,
                    "store": "Ripley", "store_key": "ripley"
                })
        time.sleep(1)
    print(f"  [OK] Ripley: {len(items)} bicicletas")
    return items

# -------------------------------------------------------
# PARIS (HTML)
# -------------------------------------------------------
def scrape_paris():
    items = []
    base = "https://www.paris.cl"
    urls = ["/bicicletas", "/bicicletas-de-montana", "/bicicletas-electricas", "/bicicletas-urbanas"]
    for path in urls:
        soup = fetch_html(base + path)
        if not soup: continue
        for p in soup.select("[class*='product'], article.item"):
            name_el = p.select_one("[class*='name'], [class*='title'], h2, h3")
            price_el = p.select_one("[class*='price']:not([class*='old'])")
            img_el = p.select_one("img")
            a_el = p.select_one("a")
            if not name_el: continue
            name = clean_text(name_el.get_text())
            if len(name) < 5: continue
            price = clean_price(price_el.get_text() if price_el else None)
            img = img_el.get("src") or img_el.get("data-src") if img_el else None
            href = a_el.get("href") if a_el else None
            if href and href.startswith("/"): href = base + href
            if name and price and not is_accessory(name, price):
                items.append({
                    "name": name, "brand": "Paris", "price_normal": price,
                    "url": href, "image_url": img,
                    "store": "Paris", "store_key": "paris"
                })
        time.sleep(1)
    print(f"  [OK] Paris: {len(items)} bicicletas")
    return items

# -------------------------------------------------------
# SPARTA (Magento)
# -------------------------------------------------------
def scrape_sparta():
    """
    Sparta.cl es una tienda deportiva general. Las URLs de bicicletas deben filtrar
    estrictamente por nombre para evitar zapatillas, ropa, etc.
    """
    items = []
    domain = "https://sparta.cl"
    paths = ["/bicicletas-de-montana", "/bicicletas-de-ruta", "/bicicletas-electricas", "/bicicletas-urbanas", "/bicicletas-infantiles"]
    for path in paths:
        url = domain + path
        for _ in range(5):
            soup = fetch_html(url)
            if not soup: break
            prods = soup.select(".product-item-info")
            if not prods: break
            for p in prods:
                name_el = p.select_one(".product-item-link")
                price_el = p.select_one(".price")
                img_el = p.select_one("img")
                if not name_el: continue
                name = clean_text(name_el.get_text())
                # FILTRO ESTRICTO: debe ser una bicicleta o marco
                if not is_bike(name):
                    continue
                price = clean_price(price_el.get_text() if price_el else None)
                img = img_el.get("src") if img_el else None
                href = name_el.get("href", "")
                if price and not is_accessory(name, price):
                    items.append({
                        "name": name, "brand": "Sparta", "price_normal": price,
                        "url": href, "image_url": img,
                        "store": "Sparta", "store_key": "sparta"
                    })
            nxt = soup.select_one(".action.next")
            if not nxt or not nxt.get("href"): break
            url = nxt["href"]
        time.sleep(0.5)
    print(f"  [OK] Sparta: {len(items)} bicicletas")
    return items

# -------------------------------------------------------
# TOTEM BIKES (Magento/custom)
# -------------------------------------------------------
def scrape_totem():
    items = []
    domain = "https://totem.cl"
    urls_try = [
        f"{domain}/bicicletas",
        f"{domain}/bicicletas-de-montana",
        f"{domain}/bicicletas-de-ruta",
    ]
    for start_url in urls_try:
        url = start_url
        for _ in range(5):
            soup = fetch_html(url)
            if not soup: break
            prods = soup.select(".product-item-info, .product-item, li.product")
            if not prods: break
            for p in prods:
                name_el = p.select_one(".product-item-link, h2 a, h3 a")
                price_el = p.select_one(".price")
                img_el = p.select_one("img")
                if not name_el: continue
                name = clean_text(name_el.get_text())
                price = clean_price(price_el.get_text() if price_el else None)
                img = img_el.get("src") or img_el.get("data-src") if img_el else None
                href = name_el.get("href", "")
                if href and href.startswith("/"): href = domain + href
                if name and price and not is_accessory(name, price):
                    items.append({
                        "name": name, "brand": "Totem", "price_normal": price,
                        "url": href, "image_url": img,
                        "store": "Totem Chile", "store_key": "totem"
                    })
            nxt = soup.select_one(".action.next, .pagination__next, a[rel='next']")
            if not nxt or not nxt.get("href"): break
            nh = nxt["href"]
            url = nh if nh.startswith("http") else domain + nh
        time.sleep(0.5)
    print(f"  [OK] Totem Chile: {len(items)} bicicletas")
    return items

# -------------------------------------------------------
# BIKESHOP.CL (Magento)
# -------------------------------------------------------
def scrape_bikeshop():
    items = []
    domain = "https://www.bikeshop.cl"
    urls = [f"{domain}/bicicletas", f"{domain}/bicicletas-de-montana", f"{domain}/bicicletas-de-ruta"]
    for start_url in urls:
        url = start_url
        for _ in range(5):
            soup = fetch_html(url)
            if not soup: break
            prods = soup.select(".product-item-info, .item.product")
            if not prods: break
            for p in prods:
                name_el = p.select_one(".product-item-link, .product-name")
                price_el = p.select_one(".price")
                img_el = p.select_one("img")
                if not name_el: continue
                name = clean_text(name_el.get_text())
                price = clean_price(price_el.get_text() if price_el else None)
                img = img_el.get("src") if img_el else None
                href = name_el.get("href", "")
                if name and price and not is_accessory(name, price):
                    items.append({
                        "name": name, "brand": "Bikeshop", "price_normal": price,
                        "url": href, "image_url": img,
                        "store": "Bikeshop", "store_key": "bikeshop"
                    })
            nxt = soup.select_one(".action.next, a.next")
            if not nxt or not nxt.get("href"): break
            url = nxt["href"]
        time.sleep(0.5)
    print(f"  [OK] Bikeshop: {len(items)} bicicletas")
    return items

# -------------------------------------------------------
# TREK CHILE
# -------------------------------------------------------
def scrape_trek():
    items = []
    domain = "https://www.trek.cl"
    urls = [
        f"{domain}/c/bicicletas",
        f"{domain}/c/mountain-bikes",
        f"{domain}/c/road-bikes",
        f"{domain}/c/electric-bikes",
    ]
    for url in urls:
        soup = fetch_html(url)
        if not soup: continue
        for p in soup.select("[class*='ProductCard'], [class*='product-card'], .product-item"):
            name_el = p.select_one("h2, h3, [class*='name'], [class*='title']")
            price_el = p.select_one("[class*='price'], [class*='Price']")
            img_el = p.select_one("img")
            a_el = p.select_one("a")
            if not name_el: continue
            name = clean_text(name_el.get_text())
            if len(name) < 3: continue
            price = clean_price(price_el.get_text() if price_el else None)
            img = img_el.get("src") or img_el.get("data-src") if img_el else None
            href = a_el.get("href") if a_el else None
            if href and href.startswith("/"): href = domain + href
            if name and price and not is_accessory(name, price):
                items.append({
                    "name": name, "brand": "Trek", "price_normal": price,
                    "url": href, "image_url": img,
                    "store": "Trek Chile", "store_key": "trek"
                })
        time.sleep(1)
    print(f"  [OK] Trek Chile: {len(items)} bicicletas")
    return items

# -------------------------------------------------------
# MERCADOLIBRE (API publica)
# -------------------------------------------------------
def scrape_mercadolibre():
    """
    MercadoLibre API publica - busca por categoria de bicicletas directamente
    Categoria MLC1500 = Deportes > Ciclismo > Bicicletas
    """
    items = []
    # Usar categoria directa en lugar de busqueda de texto
    cat_urls = [
        "https://api.mercadolibre.com/sites/MLC/search?category=MLC1500&limit=50&offset=0",
        "https://api.mercadolibre.com/sites/MLC/search?category=MLC1500&limit=50&offset=50",
        "https://api.mercadolibre.com/sites/MLC/search?category=MLC1500&limit=50&offset=100",
        "https://api.mercadolibre.com/sites/MLC/search?category=MLC1500&limit=50&offset=150",
        "https://api.mercadolibre.com/sites/MLC/search?category=MLC1500&limit=50&offset=200",
    ]
    for url in cat_urls:
        data = fetch_json(url)
        if not data: continue
        results = data.get("results", [])
        if not results: break
        for r in results:
            price = r.get("price")
            if not price or price < 30000: continue
            name = r.get("title", "")
            if not name or is_accessory(name, price): continue
            if not is_bike(name): continue
            brand_attrs = [a for a in r.get("attributes", []) if a.get("id") == "BRAND"]
            brand = brand_attrs[0].get("value_name", "Generica") if brand_attrs else "Generica"
            permalink = r.get("permalink", "#")
            thumbnail = r.get("thumbnail", "").replace("-I.", "-O.")
            items.append({
                "name": name, "brand": brand, "price_normal": int(price),
                "url": permalink, "image_url": thumbnail,
                "store": "MercadoLibre", "store_key": "mercadolibre"
            })
        time.sleep(0.3)
    print(f"  [OK] MercadoLibre: {len(items)} bicicletas")
    return items

# -------------------------------------------------------
# MAIN
# -------------------------------------------------------
def main():
    print("\nBICITODO - FAST MARKET SCRAPER 2026")
    print("=" * 50)

    all_bikes = []

    scraper_tasks = [
        ("Oxford Store",    scrape_oxford),
        ("Copenhague",      scrape_copenhague),
        ("Decathlon",       scrape_decathlon),
        ("Falabella",       scrape_falabella),
        ("Ripley",          scrape_ripley),
        ("Paris",           scrape_paris),
        ("Sparta",          scrape_sparta),
        ("Satiro Bikes",    lambda: scrape_shopify_api("Satiro Bikes", "satiro", "https://satirobikes.cl", ["bicicletas", "mountain-bike", "ruta", "urbanas"])),
        ("Totem Chile",     scrape_totem),
        ("Faucon Bikes",    lambda: scrape_shopify_api("Faucon Bikes", "faucon", "https://fauconbikes.cl", ["bicicletas-1", "mountain-bike", "ruta", "bicicletas-de-gravel", "bicicletas-electricas", "urbanas"])),
        ("BikePlus",        lambda: scrape_shopify_api("BikePlus", "bikeplus", "https://bikeplus.cl", ["bicicletas", "bicicletas-de-montana", "bicicletas-de-ruta"])),
        ("Bikeshop",        scrape_bikeshop),
        ("DS Bikes",        lambda: scrape_shopify_api("DS Bikes", "dsbikes", "https://www.dsbikes.cl", ["bicicletas", "mountain-bike", "ruta", "urbanas", "electricas"])),
        ("Trek Chile",      scrape_trek),
        ("MercadoLibre",    scrape_mercadolibre),
    ]

    for store_name, fn in scraper_tasks:
        print(f"\n[>] Scraping {store_name}...")
        try:
            bikes = fn()
            all_bikes.extend(bikes)
            print(f"    Total acumulado: {len(all_bikes)} bicicletas")
        except Exception as e:
            print(f"    [ERROR] {store_name}: {e}")

    print(f"\n{'='*50}")
    print(f"TOTAL BICICLETAS EXTRAIDAS: {len(all_bikes)}")

    # Separar accesorios que se colaron
    bikes_clean = [b for b in all_bikes
                   if not is_accessory(b["name"], b.get("price_normal"))
                   and is_bike(b["name"])]
    print(f"BICICLETAS (despues de filtro estricto): {len(bikes_clean)}")

    # Construir objetos finales con imagen local
    FALLBACK_BIKE = "https://images.unsplash.com/photo-1571068316344-75bc76f77890?auto=format&fit=crop&w=600&h=400&q=80"
    final_bikes = []

    for idx, item in enumerate(bikes_clean):
        b_id = idx + 1
        img_url = item.get("image_url")
        ext = get_ext(img_url)
        filename = f"bike_{b_id}.{ext}"
        local_img = download_image(img_url, filename) or FALLBACK_BIKE

        price = item.get("price_normal") or 150000

        bike_obj = {
            "id": b_id,
            "brand": clean_text(item.get("brand") or "Generica").title(),
            "model": item["name"],
            "type": categorize(item["name"]),
            "wheelSize": extract_wheel(item["name"]),
            "frameType": extract_frame(item["name"]),
            "specs": f"{clean_text(item.get('brand') or 'Generica').title()} - {item['name']}",
            "image": local_img,
            "history": [int(price * 1.08), int(price * 1.04), price],
            "fullSpecs": {},
            "offers": [{
                "store": item["store"],
                "storeKey": item["store_key"],
                "price": price,
                "oldPrice": None,
                "url": item.get("url", "#")
            }]
        }
        final_bikes.append(bike_obj)

        if (idx + 1) % 25 == 0:
            print(f"  Procesadas {idx+1}/{len(bikes_clean)} bicicletas...")

    # Guardar
    data_path = os.path.join(FRONTED_DIR, "data.json")
    output = {"bicicletas": final_bikes, "repuestos": []}
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nFINALIZADO!")
    print(f"Guardadas {len(final_bikes)} bicicletas en {data_path}")

    # Resumen por tienda
    store_counts = {}
    for b in final_bikes:
        for o in b["offers"]:
            s = o["store"]
            store_counts[s] = store_counts.get(s, 0) + 1
    print("\nBicicletas por tienda:")
    for s, cnt in sorted(store_counts.items(), key=lambda x: -x[1]):
        print(f"  {s}: {cnt}")

if __name__ == "__main__":
    main()
