"""
expand_catalog.py - BiciTodo Catalog Expansion v3.0
Extrae el MÁXIMO de productos (bicicletas, accesorios, repuestos) de las 17 tiendas
y los fusiona con el data.json existente.
"""
import os, sys, json, re, time, hashlib, unicodedata
from collections import defaultdict

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

BASE_DIR   = r"c:\Users\basti\Desktop\bicitodo"
FRONTED    = os.path.join(BASE_DIR, "fronted")
ASSETS     = os.path.join(FRONTED, "assets", "bikes")
DATA_PATH  = os.path.join(FRONTED, "data.json")
os.makedirs(ASSETS, exist_ok=True)

scraper = cloudscraper.create_scraper(
    browser={"browser": "chrome", "platform": "windows", "mobile": False}
)
HDR = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "es-CL,es;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ─── Helpers ─────────────────────────────────────────────────────────────────

def fetch_html(url, timeout=25):
    try:
        r = scraper.get(url, headers=HDR, timeout=timeout)
        if r.status_code == 200:
            return BeautifulSoup(r.text, "lxml")
    except Exception as e:
        print(f"  [WARN] HTML fetch error {url}: {e}")
    return None

def fetch_json(url, timeout=20):
    try:
        r = scraper.get(url, headers=HDR, timeout=timeout)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"  [WARN] JSON fetch error {url}: {e}")
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

def get_ext(url):
    if not url: return "jpg"
    m = re.search(r'\.(jpg|jpeg|png|webp|gif)', url.lower().split("?")[0])
    return m.group(1) if m else "jpg"

def make_id(text):
    return hashlib.md5(text.encode()).hexdigest()[:12]

def download_image(img_url, filename):
    if not img_url: return None
    path = os.path.join(ASSETS, filename)
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return f"assets/bikes/{filename}"
    try:
        r = scraper.get(img_url, headers=HDR, timeout=12)
        if r.status_code == 200 and len(r.content) > 1000:
            with open(path, "wb") as f:
                f.write(r.content)
            return f"assets/bikes/{filename}"
    except Exception:
        pass
    return None

# ─── Classification ───────────────────────────────────────────────────────────

ACC_KW = [
    "casco","cascos","luz ","luces","guante","guantes","bombin","bolso","bolsos",
    "alforja","portabotella","caramayola","caramagiola","candado","lentes","antiparras",
    "mochila","campanilla","timbre","rodillo","chaleco","zapatilla","zapatillas",
    "cubresillon","tapabarros","guardabarros","jersey","rodillera","rodilleras",
    "manopla","pantalon ciclismo","ropa ciclismo","kit ciclismo","banano","espejo",
    "reflectante","portabicicleta","soporte ","rack ","carro trasero","botella ",
    "bidon","short ciclismo","shorts ciclismo","polera ciclismo","calcetin",
    "grasa ","lubricante","limpiador","cleaner","aceite ","herramienta","llave ",
    "multiherramienta","protector","cinta manubrio","chaqueta","cortaviento","jacket",
    "vest ciclismo","ciclocomputador","gps ","mat ","cepillo","brush","cleaning kit",
    "care kit","taller","servicio bici","colgador","barra de aprendizaje","smart bar",
    "botas ciclismo","sillin ","sillín ","sillines","sella","asiento bici",
    "portaequipaje","espejo retrovisor","porta casco","antirrobo","traba ",
    "inflador","bombín"
]
REP_KW = [
    "pedal ","pedales","cadena ","cadenas","biela","bielas","piñon","pinon","volante libre",
    "neumatico","neumático","llanta ","llantas","camara de aire","cámara de aire",
    "horquilla","horquillas","freno ","frenos","manubrio","manubrios","puño ","puños",
    "rotor ","rotores","disco de freno","maneta","dirección","maza ","mazas",
    "eje ","ejes","sellante","valvula","parche","reparacion","cuadro ","cuadros",
    "desviador","shifter","shifters","jeringa ","antipinchazo","suspension ","suspensiones",
    "tubo ","tubos","pastilla ","pastillas","cassette ","casete","tee ","potencia ","potencias",
    "rayo ","rayos","rueda ","juego de ruedas","collarin","abrazadera","espaciador",
    "separador","perno ","tornillo ","tuerca ","pressfit"," bb ","bottom bracket",
    "corona ","plato ","cazoleta","liquido freno","líquido freno","frameset",
    "cable freno","cable cambio","funda cable","buje ","bujes","juego pedalier"
]
BIKE_KW = [
    "bicicleta","bicycle","bici ","bike ","mtb","mountain bike","ruta ","gravel",
    "trail ","enduro","downhill","bmx","ebike","e-bike","e bike","electrica",
    "urbana ","urbanas","city bike","infantil ","infantiles","fatbike","fat bike",
    "fixie","tracklocross","precaliber","marlin ","roscoe","procaliber","slash ",
    "fuel ex","domane","emonda","madone","defy ","tcr ","propel ","siskiu",
    "stumpjumper","diverge","crux ","checkpoint","remedy ","powerfly",
    "riverside","rc 500","rc 120","r 500","hibrida","híbrida","hibrido",
    "trekking","cruiser","paseo "
]

def classify(name, price=None):
    n = remove_accents(name.lower())
    for kw in ACC_KW:
        if kw in n: return "accesorios"
    for kw in REP_KW:
        if kw in n: return "repuestos"
    for kw in BIKE_KW:
        if kw in n: return "bicicletas"
    if price and price < 25000: return "repuestos"
    if price and price < 80000: return "accesorios"
    return "bicicletas"

def categorize_bike(name):
    n = remove_accents(name.lower())
    if any(k in n for k in ["electrica","electrico","ebike","e-bike","e bike","turbo ","powerfly"]): return "electrica"
    if any(k in n for k in ["downhill","enduro","trail ","slash ","remedy ","session ","stumpjumper"]): return "mtb"
    if any(k in n for k in ["gravel","ruta ","road","700c","domane","emonda","madone","defy ","tcr ","propel ","crux ","checkpoint","diverge"]): return "ruta"
    if any(k in n for k in ["urbana","city","commuter","hibrida","hibrido","trekking","crosser","riverside"]): return "urbana"
    if any(k in n for k in ["infantil","junior","kids","nino"," 16"," 20"," 12","sin pedales","ruedas de entrenamiento","precaliber ","marlin 1 ","marlin 2 "]): return "infantil"
    if any(k in n for k in ["bmx","freestyle","dirt","street"]): return "bmx"
    if any(k in n for k in ["fatbike","fat bike","fat-bike"]): return "mtb"
    return "mtb"

def extract_wheel(name):
    n = name.lower()
    for pat, val in [('700c','700c'), (r'\b29\b','29'), (r'\b27\.5\b','27.5'), (r'\b26\b','26'), (r'\b24\b','24'), (r'\b20\b','20'), (r'\b16\b','16'), (r'\b14\b','14'), (r'\b12\b','12')]:
        if re.search(pat, n): return val
    if any(k in n for k in ["gravel", "ruta", "road", "fixie", "fixed", "singlespeed", "carrera", "pista"]):
        return "700c"
    return "29"

def extract_frame(name):
    n = name.lower()
    if any(k in n for k in ["carbon","carbono"]): return "Carbono"
    if any(k in n for k in ["acero","steel","chromoly","cromo"]): return "Acero"
    return "Aluminio"

# ─── SHOPIFY UNIVERSAL (max pages) ───────────────────────────────────────────

def scrape_shopify_all(store_name, store_key, domain, collections, max_pages=20):
    """Extrae TODO (bicicletas + accesorios + repuestos) de un Shopify."""
    items = []
    seen_handles = set()
    for collection in collections:
        for page in range(1, max_pages + 1):
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
                if not title:
                    continue
                vendor = p.get("vendor", store_name)
                prod_url = f"{domain}/products/{handle}"
                variants = p.get("variants", [{}])
                price = None
                old_price = None
                for v in variants:
                    price = clean_price(v.get("price"))
                    compare = clean_price(v.get("compare_at_price"))
                    if price:
                        if compare and compare > price:
                            old_price = compare
                        break
                images = p.get("images", [])
                img_url = None
                if images:
                    raw = images[0].get("src", "")
                    img_url = raw.split("?")[0] if raw else None
                if price:
                    cat = classify(title, price)
                    items.append({
                        "name": title, "brand": vendor, "price_normal": price,
                        "price_card": old_price, "url": prod_url, "image_url": img_url,
                        "store": store_name, "store_key": store_key, "category": cat
                    })
        time.sleep(0.3)
    print(f"  [OK] {store_name}: {len(items)} productos")
    return items

# ─── Individual store scrapers ────────────────────────────────────────────────

def scrape_crossmountain():
    """CrossMountain: Shopify - TODOS los productos"""
    domain = "https://crossmountain.cl"
    collections = [
        "bicicletas", "bicicletas-de-montana", "bicicletas-de-ruta", "bicicletas-electricas",
        "bicicletas-urbanas", "bicicletas-infantiles", "bicicletas-bmx",
        "cascos", "guantes", "luces", "candados", "bolsos-y-mochilas",
        "pedales", "cadenas", "frenos", "manubrios", "horquillas",
        "sillines", "ruedas", "neumaticos", "camaras", "accesorios",
        "repuestos", "componentes", "ropa-ciclismo", "herramientas",
        "tubeless", "lubricantes", "limpieza"
    ]
    return scrape_shopify_all("CrossMountain", "crossmountain", domain, collections)

def scrape_faucon():
    """Faucon Bikes: Shopify - TODOS los productos"""
    domain = "https://fauconbikes.cl"
    collections = [
        "bicicletas-1", "mountain-bike", "ruta", "bicicletas-de-gravel",
        "bicicletas-electricas", "urbanas", "infantiles", "bmx",
        "accesorios", "cascos", "luces", "candados", "bolsos",
        "repuestos", "componentes", "pedales", "cadenas", "frenos",
        "neumaticos", "camaras", "sillines", "manubrios"
    ]
    return scrape_shopify_all("Faucon Bikes", "faucon", domain, collections)

def scrape_ibikes():
    """iBikes: Shopify - TODOS los productos"""
    domain = "https://ibikes.cl"
    collections = [
        "bicicletas", "mountain-bike", "bicicletas-de-ruta", "bicicletas-electricas",
        "bicicletas-urbanas", "bicicletas-infantiles", "bicicletas-gravel", "bmx",
        "accesorios", "cascos", "luces", "candados", "bolsos", "mochilas",
        "guantes", "lentes", "ropa-ciclismo",
        "repuestos", "componentes", "pedales", "cadenas", "frenos", "horquillas",
        "sillines", "manubrios", "ruedas", "neumaticos", "camaras",
        "herramientas", "lubricantes", "limpieza", "portabicicletas"
    ]
    return scrape_shopify_all("iBikes", "ibikes", domain, collections)

def scrape_satiro():
    """Satiro Bikes: Shopify - TODOS los productos"""
    domain = "https://satirobikes.cl"
    collections = [
        "bicicletas", "mountain-bike", "ruta", "urbanas", "electricas", "infantiles",
        "accesorios", "cascos", "luces", "repuestos", "componentes", "pedales",
        "cadenas", "neumaticos", "camaras", "sillines", "manubrios", "herramientas"
    ]
    return scrape_shopify_all("Satiro Bikes", "satiro", domain, collections)

def scrape_bikeplus():
    """BikePlus: Shopify"""
    domain = "https://bikeplus.cl"
    collections = [
        "bicicletas", "bicicletas-de-montana", "bicicletas-de-ruta", "electricas",
        "urbanas", "infantiles", "accesorios", "cascos", "repuestos", "componentes",
        "pedales", "cadenas", "neumaticos", "camaras", "luces"
    ]
    return scrape_shopify_all("BikePlus", "bikeplus", domain, collections)

def scrape_dsbikes():
    """DS Bikes: Shopify"""
    domain = "https://www.dsbikes.cl"
    collections = [
        "bicicletas", "mountain-bike", "ruta", "urbanas", "electricas",
        "accesorios", "repuestos", "componentes", "pedales", "cadenas",
        "frenos", "neumaticos", "camaras", "cascos", "luces"
    ]
    return scrape_shopify_all("DS Bikes", "dsbikes", domain, collections)

def scrape_copenhague():
    """Copenhague: HTML scraping completo"""
    items = []
    domain = "https://www.copenhague.cl"
    # Copenhague tiene categorías separadas
    category_paths = [
        "/bicicletas", "/bicicletas-de-montana", "/bicicletas-de-ruta",
        "/bicicletas-electricas", "/bicicletas-urbanas", "/bicicletas-infantiles",
        "/accesorios", "/cascos", "/luces", "/candados", "/bolsos",
        "/repuestos", "/componentes", "/pedales", "/neumaticos"
    ]
    seen = set()
    for path in category_paths:
        url = domain + path
        for _ in range(10):
            soup = fetch_html(url)
            if not soup: break
            products = soup.select(".product-block, .item.product, .product-item")
            if not products: break
            for p in products:
                name_el = p.select_one(".product-block__name, h3 a, .name a, .title a, h2 a")
                price_el = p.select_one(".product-block__price, .price, .current-price")
                old_el   = p.select_one(".product-block__compare-price, .compare-price, .old-price")
                img_el   = p.select_one("img")
                a_el     = p.select_one("a")
                if not name_el: continue
                name = clean_text(name_el.get_text())
                if not name or name in seen: continue
                seen.add(name)
                price = clean_price(price_el.get_text() if price_el else None)
                old_price = clean_price(old_el.get_text() if old_el else None)
                img = (img_el.get("src") or img_el.get("data-src")) if img_el else None
                href = a_el.get("href") if a_el else None
                if href and not href.startswith("http"): href = domain + href
                if name and price:
                    cat = classify(name + " " + path, price)
                    items.append({
                        "name": name, "brand": "Copenhague", "price_normal": price,
                        "price_card": old_price if old_price and old_price > price else None,
                        "url": href, "image_url": img,
                        "store": "Copenhague", "store_key": "copenhague", "category": cat
                    })
            nxt = soup.select_one("li.next a, a[rel='next'], .pagination .next a")
            if not nxt: break
            nh = nxt.get("href", "")
            url = nh if nh.startswith("http") else domain + nh
        time.sleep(0.5)
    print(f"  [OK] Copenhague: {len(items)} productos")
    return items

def scrape_fullbike():
    """Full Bike: Jumpseller HTML"""
    items = []
    domain = "https://fullbike.cl"
    category_paths = [
        "/bicicletas", "/bicicletas-de-montana", "/bicicletas-de-ruta",
        "/bicicletas-electricas", "/bicicletas-urbanas", "/bicicletas-infantiles",
        "/accesorios", "/cascos", "/luces", "/repuestos", "/componentes",
        "/pedales", "/neumaticos-y-camaras", "/cadenas", "/frenos", "/sillines",
        "/manubrios-y-potencias", "/ropa-ciclismo"
    ]
    seen = set()
    for path in category_paths:
        url = domain + path
        for _ in range(10):
            soup = fetch_html(url)
            if not soup: break
            products = soup.select(".product-item, .product, .item")
            if not products: break
            for p in products:
                name_el = p.select_one("h2 a, h3 a, .product-name a, .title a")
                price_el = p.select_one(".price, .product-price")
                old_el   = p.select_one(".compare-price, .old-price, .original-price")
                img_el   = p.select_one("img")
                a_el     = p.select_one("a")
                if not name_el: continue
                name = clean_text(name_el.get_text())
                if not name or name in seen: continue
                seen.add(name)
                price = clean_price(price_el.get_text() if price_el else None)
                old_price = clean_price(old_el.get_text() if old_el else None)
                img = (img_el.get("src") or img_el.get("data-src")) if img_el else None
                href = a_el.get("href") if a_el else None
                if href and not href.startswith("http"): href = domain + href
                if name and price:
                    cat = classify(name + " " + path, price)
                    items.append({
                        "name": name, "brand": "Full Bike", "price_normal": price,
                        "price_card": old_price if old_price and old_price > price else None,
                        "url": href, "image_url": img,
                        "store": "Full Bike", "store_key": "fullbike", "category": cat
                    })
            nxt = soup.select_one("a[rel='next'], .pagination-next, .next a")
            if not nxt: break
            nh = nxt.get("href", "")
            url = nh if nh.startswith("http") else domain + nh
        time.sleep(0.5)
    print(f"  [OK] Full Bike: {len(items)} productos")
    return items

def scrape_decathlon():
    """Decathlon: HTML scraping todas las categorías"""
    items = []
    domain = "https://www.decathlon.cl"
    # Bicicletas + accesorios + repuestos
    paths = [
        "/4786-bicicletas", "/8613-ciclismo-de-montana",
        "/8617-ciclismo-de-ruta", "/8614-ciclismo-electrico",
        "/8616-ciclismo-urbano", "/11773-bicicletas-infantiles",
        "/6637-cascos-ciclismo", "/6638-guantes-ciclismo",
        "/6640-bolsos-ciclismo", "/10621-luces-ciclismo",
        "/6648-candados-bicicleta", "/6644-neumaticos-bicicleta",
        "/6645-camaras-bicicleta", "/6642-componentes-bicicleta"
    ]
    seen = set()
    for path in paths:
        url = domain + path
        for _ in range(8):
            soup = fetch_html(url)
            if not soup: break
            cards = soup.select("article.product-card, .product-item")
            if not cards: break
            for p in cards:
                name_el  = p.select_one("h2, h3")
                price_el = p.select_one(".price_amount, .price-amount")
                old_el   = p.select_one(".price-compare, .was-price")
                img_el   = p.select_one("img")
                a_el     = p.select_one("a.js-product-card-link, a")
                brand_el = p.select_one("p.u-typo-body-s, .brand")
                if not name_el: continue
                name = clean_text(name_el.get_text())
                if not name or name in seen: continue
                seen.add(name)
                price_val = price_el.get("data-value") if price_el else None
                price = clean_price(price_val or (price_el.get_text() if price_el else None))
                old_price = clean_price(old_el.get_text() if old_el else None)
                img = img_el.get("src") if img_el else None
                href = a_el.get("href") if a_el else None
                if href and not href.startswith("http"): href = domain + href
                brand = clean_text(brand_el.get_text()) if brand_el else "Decathlon"
                if name and price:
                    cat = classify(name + " " + path, price)
                    items.append({
                        "name": name, "brand": brand, "price_normal": price,
                        "price_card": old_price if old_price and old_price > price else None,
                        "url": href, "image_url": img,
                        "store": "Decathlon", "store_key": "decathlon", "category": cat
                    })
            nxt = soup.select_one("a[data-testid='pagination-next'], .pagination a[rel='next']")
            if not nxt: break
            nh = nxt.get("href", "")
            url = nh if nh.startswith("http") else domain + nh
        time.sleep(0.5)
    print(f"  [OK] Decathlon: {len(items)} productos")
    return items

def scrape_oxford():
    """Oxford Store: Magento - bicicletas + accesorios"""
    items = []
    domain = "https://www.oxfordstore.cl"
    paths = [
        "/bicicletas.html", "/bicicletas-de-montana.html",
        "/bicicletas-de-ruta.html", "/bicicletas-electricas.html",
        "/bicicletas-urbanas.html", "/bicicletas-infantiles.html",
        "/accesorios-ciclismo.html", "/casco.html", "/luces.html",
        "/repuestos-bicicleta.html"
    ]
    seen = set()
    for path in paths:
        url = domain + path
        for _ in range(8):
            soup = fetch_html(url)
            if not soup: break
            for p in soup.select(".product-item-info"):
                name_el  = p.select_one(".product-item-link")
                price_el = p.select_one(".price-wrapper .price")
                old_el   = p.select_one(".old-price .price")
                img_el   = p.select_one(".product-image-photo")
                if not name_el: continue
                name = clean_text(name_el.get_text())
                if not name or name in seen: continue
                seen.add(name)
                price = clean_price(price_el.get_text() if price_el else None)
                old_price = clean_price(old_el.get_text() if old_el else None)
                img = img_el.get("src") if img_el else None
                if img and "/cache/" in img:
                    img = re.sub(r'/cache/[^/]+/', '/', img)
                href = name_el.get("href", "")
                if name and price:
                    cat = classify(name + " " + path, price)
                    items.append({
                        "name": name, "brand": "Oxford", "price_normal": price,
                        "price_card": old_price if old_price and old_price > price else None,
                        "url": href, "image_url": img,
                        "store": "Oxford Store", "store_key": "oxford", "category": cat
                    })
            nxt = soup.select_one(".action.next")
            if not nxt or not nxt.get("href"): break
            url = nxt["href"]
        time.sleep(0.5)
    print(f"  [OK] Oxford Store: {len(items)} productos")
    return items

def scrape_sparta():
    """Sparta: Magento - todas categorías"""
    items = []
    domain = "https://sparta.cl"
    paths = [
        "/bicicletas-de-montana", "/bicicletas-de-ruta", "/bicicletas-electricas",
        "/bicicletas-urbanas", "/bicicletas-infantiles", "/bicicletas-bmx",
        "/accesorios-ciclismo", "/cascos-ciclismo", "/luces-bicicleta",
        "/repuestos-bicicleta"
    ]
    seen = set()
    for path in paths:
        url = domain + path
        for _ in range(8):
            soup = fetch_html(url)
            if not soup: break
            prods = soup.select(".product-item-info")
            if not prods: break
            for p in prods:
                name_el  = p.select_one(".product-item-link")
                price_el = p.select_one(".price")
                old_el   = p.select_one(".old-price .price")
                img_el   = p.select_one("img")
                if not name_el: continue
                name = clean_text(name_el.get_text())
                if not name or name in seen: continue
                seen.add(name)
                price = clean_price(price_el.get_text() if price_el else None)
                old_price = clean_price(old_el.get_text() if old_el else None)
                img = img_el.get("src") if img_el else None
                href = name_el.get("href", "")
                if name and price:
                    cat = classify(name + " " + path, price)
                    items.append({
                        "name": name, "brand": "Sparta", "price_normal": price,
                        "price_card": old_price if old_price and old_price > price else None,
                        "url": href, "image_url": img,
                        "store": "Sparta", "store_key": "sparta", "category": cat
                    })
            nxt = soup.select_one(".action.next")
            if not nxt or not nxt.get("href"): break
            url = nxt["href"]
        time.sleep(0.5)
    print(f"  [OK] Sparta: {len(items)} productos")
    return items

def scrape_bikeshop():
    """Bikeshop: Magento - todas categorías"""
    items = []
    domain = "https://www.bikeshop.cl"
    paths = [
        "/bicicletas", "/bicicletas-de-montana", "/bicicletas-de-ruta",
        "/bicicletas-electricas", "/bicicletas-urbanas", "/bicicletas-infantiles",
        "/accesorios-bicicleta", "/repuestos-bicicleta", "/cascos"
    ]
    seen = set()
    for path in paths:
        url = domain + path
        for _ in range(8):
            soup = fetch_html(url)
            if not soup: break
            prods = soup.select(".product-item-info, .item.product")
            if not prods: break
            for p in prods:
                name_el  = p.select_one(".product-item-link, .product-name")
                price_el = p.select_one(".price")
                old_el   = p.select_one(".old-price .price")
                img_el   = p.select_one("img")
                if not name_el: continue
                name = clean_text(name_el.get_text())
                if not name or name in seen: continue
                seen.add(name)
                price = clean_price(price_el.get_text() if price_el else None)
                old_price = clean_price(old_el.get_text() if old_el else None)
                img = img_el.get("src") if img_el else None
                href = name_el.get("href", "")
                if name and price:
                    cat = classify(name + " " + path, price)
                    items.append({
                        "name": name, "brand": "Bikeshop", "price_normal": price,
                        "price_card": old_price if old_price and old_price > price else None,
                        "url": href, "image_url": img,
                        "store": "Bikeshop", "store_key": "bikeshop", "category": cat
                    })
            nxt = soup.select_one(".action.next, a.next")
            if not nxt or not nxt.get("href"): break
            url = nxt["href"]
        time.sleep(0.5)
    print(f"  [OK] Bikeshop: {len(items)} productos")
    return items

def scrape_totem():
    """Totem Bikes: HTML"""
    items = []
    domain = "https://totem.cl"
    paths = [
        "/bicicletas", "/bicicletas-de-montana", "/bicicletas-de-ruta",
        "/bicicletas-electricas", "/bicicletas-urbanas",
        "/accesorios", "/repuestos"
    ]
    seen = set()
    for path in paths:
        url = domain + path
        for _ in range(8):
            soup = fetch_html(url)
            if not soup: break
            prods = soup.select(".product-item-info, .product-item, li.product")
            if not prods: break
            for p in prods:
                name_el  = p.select_one(".product-item-link, h2 a, h3 a")
                price_el = p.select_one(".price")
                old_el   = p.select_one(".old-price .price")
                img_el   = p.select_one("img")
                if not name_el: continue
                name = clean_text(name_el.get_text())
                if not name or name in seen: continue
                seen.add(name)
                price = clean_price(price_el.get_text() if price_el else None)
                old_price = clean_price(old_el.get_text() if old_el else None)
                img = (img_el.get("src") or img_el.get("data-src")) if img_el else None
                href = name_el.get("href", "")
                if href and href.startswith("/"): href = domain + href
                if name and price:
                    cat = classify(name + " " + path, price)
                    items.append({
                        "name": name, "brand": "Totem", "price_normal": price,
                        "price_card": old_price if old_price and old_price > price else None,
                        "url": href, "image_url": img,
                        "store": "Totem Chile", "store_key": "totem", "category": cat
                    })
            nxt = soup.select_one(".action.next, .pagination__next, a[rel='next']")
            if not nxt or not nxt.get("href"): break
            nh = nxt["href"]
            url = nh if nh.startswith("http") else domain + nh
        time.sleep(0.5)
    print(f"  [OK] Totem Chile: {len(items)} productos")
    return items

def scrape_falabella():
    """Falabella: API REST - bicicletas + accesorios ciclismo"""
    items = []
    categories = [
        ("cat40062", "bicicletas"), ("cat40063", "bicicletas"),
        ("cat40064", "bicicletas"), ("cat40065", "bicicletas"),
        ("cat40066", "bicicletas"), ("cat4006401", "bicicletas"),
        # Accesorios ciclismo
        ("cat40067", "accesorios"), ("cat40068", "accesorios"),
    ]
    BASE = "https://www.falabella.com.cl/rest/model/falabella/rest/browse/BrowseActor/fetch-product-summary"
    seen = set()
    for cat_id, cat_type in categories:
        offset = 0
        while True:
            params = f"?Nrpp=50&No={offset}&Nr=AND(product.siteId:FALCL,category.repositoryId:{cat_id})&Ns=product.isAvailableInStore|1&rankingMechanism=ProductRanking"
            data = fetch_json(BASE + params)
            if not data: break
            results = data.get("results", {})
            records = results.get("records", []) or results.get("products", [])
            if not records: break
            for rec in records:
                attrs = rec.get("attributes", rec)
                name = clean_text(attrs.get("displayName") or attrs.get("product.displayName") or "")
                if not name or name in seen: continue
                seen.add(name)
                brand = clean_text(attrs.get("brand") or attrs.get("product.brand") or "Desconocida")
                pid = attrs.get("productId") or attrs.get("product.repositoryId") or ""
                slug = attrs.get("slug") or attrs.get("product.slug") or pid
                prod_url = f"https://www.falabella.com.cl/falabella-cl/product/{pid}/{slug}"
                skus = attrs.get("skus", [])
                price = old_price = None
                if isinstance(skus, list) and skus:
                    price_data = skus[0].get("price", {})
                    price = clean_price(str(price_data.get("original", "")))
                    old_price = clean_price(str(price_data.get("compare", "") or ""))
                if not price:
                    price = clean_price(str(attrs.get("price", "")))
                images = attrs.get("images") or attrs.get("product.imageList") or []
                img = None
                if images:
                    img = images[0] if isinstance(images[0], str) else None
                if name and price:
                    cat = classify(name, price)
                    items.append({
                        "name": name, "brand": brand, "price_normal": price,
                        "price_card": old_price if old_price and old_price > price else None,
                        "url": prod_url, "image_url": img,
                        "store": "Falabella", "store_key": "falabella", "category": cat
                    })
            total = results.get("totalNumRecs", 0)
            offset += 50
            if offset >= min(total, 500): break
        time.sleep(0.5)
    print(f"  [OK] Falabella: {len(items)} productos")
    return items

def scrape_ripley():
    """Ripley: HTML - bicicletas + accesorios"""
    items = []
    base = "https://simple.ripley.cl"
    paths = [
        "/bicicletas", "/bicicletas-de-montana",
        "/bicicletas-de-ruta-y-gravel", "/bicicletas-electricas",
        "/bicicletas-infantiles", "/bicicletas-urbanas-e-hibridas",
        "/accesorios-ciclismo", "/cascos-ciclismo", "/candados-bicicleta"
    ]
    seen = set()
    for path in paths:
        soup = fetch_html(base + path)
        if not soup: continue
        for p in soup.select("[class*='ProductItem'], [class*='catalog-product'], .product-item"):
            name_el  = p.select_one("[class*='productName'], [class*='product-title'], h2, h3")
            price_el = p.select_one("[class*='price']:not([class*='old']), [class*='Price']")
            old_el   = p.select_one("[class*='oldPrice'], [class*='old-price']")
            img_el   = p.select_one("img")
            a_el     = p.select_one("a")
            if not name_el: continue
            name = clean_text(name_el.get_text())
            if not name or len(name) < 5 or name in seen: continue
            seen.add(name)
            price = clean_price(price_el.get_text() if price_el else None)
            old_price = clean_price(old_el.get_text() if old_el else None)
            img = (img_el.get("src") or img_el.get("data-src")) if img_el else None
            href = a_el.get("href") if a_el else None
            if href and href.startswith("/"): href = base + href
            if name and price:
                cat = classify(name + " " + path, price)
                items.append({
                    "name": name, "brand": "Ripley", "price_normal": price,
                    "price_card": old_price if old_price and old_price > price else None,
                    "url": href, "image_url": img,
                    "store": "Ripley", "store_key": "ripley", "category": cat
                })
        time.sleep(1)
    print(f"  [OK] Ripley: {len(items)} productos")
    return items

def scrape_paris():
    """Paris: HTML - bicicletas + accesorios"""
    items = []
    base = "https://www.paris.cl"
    paths = [
        "/bicicletas", "/bicicletas-de-montana", "/bicicletas-electricas",
        "/bicicletas-urbanas", "/bicicletas-infantiles", "/bicicletas-de-ruta",
        "/accesorios-ciclismo", "/cascos-ciclismo"
    ]
    seen = set()
    for path in paths:
        soup = fetch_html(base + path)
        if not soup: continue
        for p in soup.select("[class*='product'], article.item"):
            name_el  = p.select_one("[class*='name'], [class*='title'], h2, h3")
            price_el = p.select_one("[class*='price']:not([class*='old'])")
            old_el   = p.select_one("[class*='old-price'], [class*='strike']")
            img_el   = p.select_one("img")
            a_el     = p.select_one("a")
            if not name_el: continue
            name = clean_text(name_el.get_text())
            if not name or len(name) < 5 or name in seen: continue
            seen.add(name)
            price = clean_price(price_el.get_text() if price_el else None)
            old_price = clean_price(old_el.get_text() if old_el else None)
            img = (img_el.get("src") or img_el.get("data-src")) if img_el else None
            href = a_el.get("href") if a_el else None
            if href and href.startswith("/"): href = base + href
            if name and price:
                cat = classify(name + " " + path, price)
                items.append({
                    "name": name, "brand": "Paris", "price_normal": price,
                    "price_card": old_price if old_price and old_price > price else None,
                    "url": href, "image_url": img,
                    "store": "Paris", "store_key": "paris", "category": cat
                })
        time.sleep(1)
    print(f"  [OK] Paris: {len(items)} productos")
    return items

def scrape_trek():
    """Trek Chile: HTML"""
    items = []
    domain = "https://www.trek.cl"
    paths = [
        "/c/bicicletas", "/c/mountain-bikes", "/c/road-bikes",
        "/c/electric-bikes", "/c/gravel-bikes", "/c/kids-bikes",
        "/c/urban-bikes", "/c/accessories", "/c/helmets", "/c/apparel"
    ]
    seen = set()
    for path in paths:
        url = domain + path
        for _ in range(5):
            soup = fetch_html(url)
            if not soup: break
            for p in soup.select("[class*='ProductCard'], [class*='product-card'], .product-item"):
                name_el  = p.select_one("h2, h3, [class*='name'], [class*='title']")
                price_el = p.select_one("[class*='price'], [class*='Price']")
                img_el   = p.select_one("img")
                a_el     = p.select_one("a")
                if not name_el: continue
                name = clean_text(name_el.get_text())
                if not name or len(name) < 3 or name in seen: continue
                seen.add(name)
                price = clean_price(price_el.get_text() if price_el else None)
                img = (img_el.get("src") or img_el.get("data-src")) if img_el else None
                href = a_el.get("href") if a_el else None
                if href and href.startswith("/"): href = domain + href
                if name and price:
                    cat = classify(name + " " + path, price)
                    items.append({
                        "name": name, "brand": "Trek", "price_normal": price,
                        "price_card": None, "url": href, "image_url": img,
                        "store": "Trek Chile", "store_key": "trek", "category": cat
                    })
            nxt = soup.select_one("a[aria-label='Next page'], .pagination-next")
            if not nxt: break
            nh = nxt.get("href", "")
            url = nh if nh.startswith("http") else domain + nh
        time.sleep(1)
    print(f"  [OK] Trek Chile: {len(items)} productos")
    return items

def scrape_specialized():
    """Specialized Chile: HTML"""
    items = []
    domain = "https://www.specialized.com/cl/es"
    paths = [
        "/c/bikes", "/c/mountain", "/c/road", "/c/electric",
        "/c/urban", "/c/kids", "/c/helmets-accessories"
    ]
    seen = set()
    for path in paths:
        url = domain + path
        soup = fetch_html(url)
        if not soup: continue
        for p in soup.select("[class*='ProductCard'], [class*='product-card'], [class*='product-tile']"):
            name_el  = p.select_one("h2, h3, [class*='name'], [class*='title']")
            price_el = p.select_one("[class*='price'], [class*='Price']")
            img_el   = p.select_one("img")
            a_el     = p.select_one("a")
            if not name_el: continue
            name = clean_text(name_el.get_text())
            if not name or name in seen: continue
            seen.add(name)
            price = clean_price(price_el.get_text() if price_el else None)
            img = (img_el.get("src") or img_el.get("data-src")) if img_el else None
            href = a_el.get("href") if a_el else None
            if href and href.startswith("/"): href = "https://www.specialized.com" + href
            if name and price:
                cat = classify(name + " " + path, price)
                items.append({
                    "name": name, "brand": "Specialized", "price_normal": price,
                    "price_card": None, "url": href, "image_url": img,
                    "store": "Specialized Chile", "store_key": "specialized", "category": cat
                })
        time.sleep(1)
    print(f"  [OK] Specialized Chile: {len(items)} productos")
    return items

def scrape_mercadolibre():
    """MercadoLibre: API pública - bicicletas + accesorios"""
    items = []
    # Bicicletas + accesorios de ciclismo en Chile
    categories = [
        ("MLC1500", "bicicletas"),    # Bicicletas
        ("MLC1501", "bicicletas"),    # MTB
        ("MLC1502", "bicicletas"),    # Ruta
        ("MLC1503", "accesorios"),    # Accesorios ciclismo
        ("MLC1504", "repuestos"),     # Repuestos bicicleta
    ]
    seen = set()
    for cat_id, cat_type in categories:
        for offset in range(0, 500, 50):
            url = f"https://api.mercadolibre.com/sites/MLC/search?category={cat_id}&limit=50&offset={offset}"
            data = fetch_json(url)
            if not data: break
            results = data.get("results", [])
            if not results: break
            for r in results:
                name = r.get("title", "")
                if not name or name in seen: continue
                seen.add(name)
                price = int(r.get("price", 0) or 0)
                if price < 1000: continue
                old_price = int(r.get("original_price", 0) or 0)
                brand_attrs = [a for a in r.get("attributes", []) if a.get("id") == "BRAND"]
                brand = brand_attrs[0].get("value_name", "Generica") if brand_attrs else "Generica"
                permalink = r.get("permalink", "#")
                thumbnail = r.get("thumbnail", "").replace("-I.", "-O.")
                cat = classify(name, price)
                items.append({
                    "name": name, "brand": brand, "price_normal": price,
                    "price_card": old_price if old_price > price else None,
                    "url": permalink, "image_url": thumbnail,
                    "store": "MercadoLibre", "store_key": "mercadolibre", "category": cat
                })
            time.sleep(0.3)
            if len(results) < 50: break
    print(f"  [OK] MercadoLibre: {len(items)} productos")
    return items

def scrape_vidaurre():
    """Vidaurre Bikes: HTML scraping"""
    items = []
    domain = "https://vidaurrebikes.cl"
    paths = ["/bicicletas", "/accesorios", "/repuestos"]
    seen = set()
    for path in paths:
        url = domain + path
        for _ in range(8):
            soup = fetch_html(url)
            if not soup: break
            prods = soup.select(".product-item, .product, .item, [class*='product']")
            if not prods: break
            for p in prods:
                name_el  = p.select_one("h2 a, h3 a, .product-name a, .name a")
                price_el = p.select_one(".price, .current-price")
                old_el   = p.select_one(".old-price, .compare-price")
                img_el   = p.select_one("img")
                a_el     = p.select_one("a")
                if not name_el: continue
                name = clean_text(name_el.get_text())
                if not name or name in seen: continue
                seen.add(name)
                price = clean_price(price_el.get_text() if price_el else None)
                old_price = clean_price(old_el.get_text() if old_el else None)
                img = (img_el.get("src") or img_el.get("data-src")) if img_el else None
                href = a_el.get("href") if a_el else None
                if href and not href.startswith("http"): href = domain + href
                if name and price:
                    cat = classify(name + " " + path, price)
                    items.append({
                        "name": name, "brand": "Vidaurre", "price_normal": price,
                        "price_card": old_price if old_price and old_price > price else None,
                        "url": href, "image_url": img,
                        "store": "Vidaurre Bikes", "store_key": "vidaurre", "category": cat
                    })
            nxt = soup.select_one("a[rel='next'], .pagination-next, .next a")
            if not nxt: break
            nh = nxt.get("href", "")
            url = nh if nh.startswith("http") else domain + nh
        time.sleep(0.5)
    print(f"  [OK] Vidaurre Bikes: {len(items)} productos")
    return items

# ─── Build product object ─────────────────────────────────────────────────────

FALLBACK_IMG = {
    "bicicletas": "https://images.unsplash.com/photo-1571068316344-75bc76f77890?auto=format&fit=crop&w=600&h=400&q=80",
    "accesorios": "https://images.unsplash.com/photo-1485965120184-e220f721d03e?auto=format&fit=crop&w=600&h=400&q=80",
    "repuestos":  "https://images.unsplash.com/photo-1573467965706-5c5e4d44c4e5?auto=format&fit=crop&w=600&h=400&q=80",
}

def build_product(idx, item, category):
    """Construye el objeto compatible con data.json a partir de un item scraped."""
    price = item.get("price_normal") or 0
    old_price = item.get("price_card")
    name = item["name"]
    brand = clean_text(item.get("brand") or "Generica").title()
    img_url = item.get("image_url")
    store = item["store"]
    store_key = item.get("store_key", store.lower().replace(" ", ""))

    # Intenta descargar imagen
    if img_url:
        ext = get_ext(img_url)
        filename = f"prod_{make_id(name + store)}_{idx}.{ext}"
        local_img = download_image(img_url, filename)
    else:
        local_img = None
    final_img = local_img or FALLBACK_IMG.get(category, FALLBACK_IMG["bicicletas"])

    history = [int(price * 1.08), int(price * 1.04), price]

    obj = {
        "id": idx,
        "brand": brand,
        "model": name,
        "type": categorize_bike(name) if category == "bicicletas" else category,
        "wheelSize": extract_wheel(name) if category == "bicicletas" else "",
        "frameType": extract_frame(name) if category == "bicicletas" else "",
        "specs": f"{brand} - {name}",
        "image": final_img,
        "history": history,
        "fullSpecs": {},
        "offers": [{
            "store": store,
            "storeKey": store_key,
            "price": price,
            "oldPrice": old_price if old_price and old_price > price else None,
            "url": item.get("url", "#")
        }]
    }
    return obj

# ─── Merge with existing data ─────────────────────────────────────────────────

def normalize_key(name):
    """Clave de deduplicación: nombre normalizado sin acentos, minúsculas."""
    return remove_accents(name.lower().strip())

def merge_into(existing_list, new_items, category):
    """
    Fusiona new_items en existing_list.
    Si el producto ya existe (por nombre normalizado), agrega la oferta.
    Si es nuevo, agrega el producto completo.
    """
    existing_keys = {}
    for prod in existing_list:
        key = normalize_key(prod.get("model", ""))
        existing_keys[key] = prod

    added = 0
    updated = 0
    for item in new_items:
        key = normalize_key(item["name"])
        if key in existing_keys:
            # Agregar/actualizar oferta en producto existente
            prod = existing_keys[key]
            store_key = item.get("store_key", "")
            offer_exists = False
            for off in prod["offers"]:
                if off["storeKey"] == store_key:
                    # Si el precio es mejor, actualizar
                    if item["price_normal"] and item["price_normal"] < off["price"]:
                        off["price"] = item["price_normal"]
                        off["url"] = item.get("url", "#")
                    if item.get("price_card") and item["price_card"] > off["price"]:
                        off["oldPrice"] = item["price_card"]
                    offer_exists = True
                    break
            if not offer_exists and item.get("price_normal"):
                prod["offers"].append({
                    "store": item["store"],
                    "storeKey": store_key,
                    "price": item["price_normal"],
                    "oldPrice": item.get("price_card"),
                    "url": item.get("url", "#")
                })
                prod["offers"].sort(key=lambda o: o["price"])
                updated += 1
        else:
            if not item.get("price_normal"):
                continue
            # Nuevo producto
            new_idx = len(existing_list) + 1
            obj = build_product(new_idx, item, category)
            existing_list.append(obj)
            existing_keys[key] = obj
            added += 1
    return added, updated

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("\nBICITODO - CATALOG EXPANSION v3.0")
    print("=" * 60)

    # Cargar data.json existente
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"Cargado data.json existente:")
        print(f"  Bicicletas: {len(data.get('bicicletas', []))}")
        print(f"  Accesorios: {len(data.get('accesorios', []))}")
        print(f"  Repuestos:  {len(data.get('repuestos', []))}")
    else:
        data = {"bicicletas": [], "accesorios": [], "repuestos": []}

    # Definir scrapers
    scraper_tasks = [
        ("CrossMountain",      scrape_crossmountain),
        ("Faucon Bikes",       scrape_faucon),
        ("iBikes",             scrape_ibikes),
        ("Satiro Bikes",       scrape_satiro),
        ("BikePlus",           scrape_bikeplus),
        ("DS Bikes",           scrape_dsbikes),
        ("Copenhague",         scrape_copenhague),
        ("Full Bike",          scrape_fullbike),
        ("Decathlon",          scrape_decathlon),
        ("Oxford Store",       scrape_oxford),
        ("Sparta",             scrape_sparta),
        ("Bikeshop",           scrape_bikeshop),
        ("Totem Chile",        scrape_totem),
        ("Falabella",          scrape_falabella),
        ("Ripley",             scrape_ripley),
        ("Paris",              scrape_paris),
        ("Trek Chile",         scrape_trek),
        ("Specialized Chile",  scrape_specialized),
        ("MercadoLibre",       scrape_mercadolibre),
        ("Vidaurre Bikes",     scrape_vidaurre),
    ]

    all_raw = []
    for store_name, fn in scraper_tasks:
        print(f"\n[>] Scraping {store_name}...")
        try:
            items = fn()
            all_raw.extend(items)
            print(f"    Acumulado: {len(all_raw)} items")
        except Exception as e:
            print(f"    [ERROR] {store_name}: {e}")

    print(f"\n{'='*60}")
    print(f"TOTAL ITEMS EXTRAIDOS: {len(all_raw)}")

    # Clasificar por categoría
    by_cat = {"bicicletas": [], "accesorios": [], "repuestos": []}
    for item in all_raw:
        cat = item.get("category") or classify(item["name"], item.get("price_normal"))
        if cat not in by_cat:
            cat = "accesorios"
        by_cat[cat].append(item)

    print(f"\nClasificación:")
    for cat, items in by_cat.items():
        print(f"  {cat}: {len(items)}")

    # Fusionar con data.json
    print(f"\nFusionando con catálogo existente...")
    for cat in ["bicicletas", "accesorios", "repuestos"]:
        added, updated = merge_into(data[cat], by_cat[cat], cat)
        print(f"  {cat}: +{added} nuevos, {updated} actualizados con nueva tienda")

    # Re-numerar IDs
    all_products = data["bicicletas"] + data["accesorios"] + data["repuestos"]
    for i, p in enumerate(all_products, 1):
        p["id"] = i

    # Guardar
    print(f"\nGuardando data.json...")
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"RESULTADO FINAL:")
    print(f"  Bicicletas: {len(data['bicicletas'])}")
    print(f"  Accesorios: {len(data.get('accesorios', []))}")
    print(f"  Repuestos:  {len(data['repuestos'])}")
    total = len(data['bicicletas']) + len(data.get('accesorios', [])) + len(data['repuestos'])
    print(f"  TOTAL: {total} productos")

    # Resumen por tienda
    store_cnt = defaultdict(int)
    for p in all_products:
        for o in p.get("offers", []):
            store_cnt[o["store"]] += 1
    print(f"\nProductos por tienda:")
    for s, cnt in sorted(store_cnt.items(), key=lambda x: -x[1]):
        print(f"  {s}: {cnt}")

if __name__ == "__main__":
    main()
