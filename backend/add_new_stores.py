"""
add_new_stores.py v1.0
Agrega 4 nuevas tiendas al data.json:
  1. CrossMountain.cl  - Shopify (accesorios + repuestos + bicicletas)
  2. Copenhague.cl     - Shopify via colecciones (accesorios + bicicletas)
  3. FullBike.cl       - Jumpseller HTML scraping (bicicletas + accesorios)
  4. VidaurreBikes.cl  - PrestaShop HTML scraping (bicicletas)
"""
import os, sys, json, re, time, hashlib
import cloudscraper
from bs4 import BeautifulSoup

os.environ['PYTHONIOENCODING'] = 'utf-8'
try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

BASE_DIR   = r"c:\Users\basti\Desktop\bicitodo"
FRONTED    = os.path.join(BASE_DIR, "fronted")
ASSETS     = os.path.join(FRONTED, "assets", "bikes")
DATA_PATH  = os.path.join(FRONTED, "data.json")
os.makedirs(ASSETS, exist_ok=True)

scraper = cloudscraper.create_scraper(browser={"browser":"chrome","platform":"windows","mobile":False})
HDR = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# ─── Category keyword maps ────────────────────────────────────────────
ACC_KW  = ["casco","cascos","luz","luces","guante","guantes","bombin","bombines",
            "bolso","bolsos","alforja","alforjas","portabotella","portabotellas",
            "caramagiola","caramagiolas","candado","candados","lentes","antiparras",
            "mochila","mochilas","campanilla","timbre","rodillo","rodillos",
            "chaleco","chalecos","zapatilla","zapatillas","cubresillon","cubresillones",
            "tapabarros","tapabarro","guardabarros","guardabarro","jersey","jerseys",
            "rodillera","rodilleras","manopla","manoplas","sillin","sillines","sillín",
            "sillines","antipinchazo_acc","pantalon ciclismo","camisa ciclismo","ropa ciclismo",
            "kit ciclismo","banano","bananos","espejo","espejos","reflectante","reflectantes",
            "portabicicleta","portabicicletas","soporte","soportes","rack","racks",
            "carro","carros","botella","botellas","caramayola","caramayolas","bidon","bidones",
            "short","shorts","pantalon","pantalones","pants","ropa","vestuario","calcetines",
            "calcetin","polera","poleras","grasa","grasas","lubricante","lubricantes",
            "limpiador","limpiadores","cleaner","concentrado","concentrados","aceite","aceites",
            "herramienta","herramientas","llave","llaves","extractor","extractores",
            "multiherramienta","multiherramientas","protector","protectores","kit de proteccion",
            "cinta","cintas","chaqueta","chaquetas","cortaviento","cortavientos","jacket","jackets",
            "vest","vests","gps","ciclocomputador","mat","work mat","detailing","cepillo",
            "brush","care kit","essentials kit","cleaning kit","taller","servicio","colgador",
            "solo bike","shotgun","silla","jofa","barra de aprendizaje","smart bar","boots",
            "botas","mac ride","lube","clean protect","ultimate kit","detailing brush"]
REP_KW  = ["pedal","pedales","cadena","cadenas","biela","bielas","piñon","piñones",
            "pinon","pinones","volante","volantes","neumatico","neumaticos","neum",
            "llanta","llantas","camara","camaras","cámara","cámaras","horquilla",
            "horquillas","freno","frenos","manubrio","manubrios","puño","puños","puno",
            "punos","rotor","rotores","disco","discos","maneta","manetas","direccion",
            "direcciones","maza","mazas","eje","ejes","sellante","sellantes","valvula",
            "valvulas","parche","parches","reparacion","reparaciones","cuadro","cuadros",
            "desviador","desviadores","shifter","shifters","jeringa","jeringas",
            "antipinchazo","antipinchazos","suspension","suspensiones","repuesto",
            "repuestos","tubo","tubos","neumático","neumáticos","cinta tubular",
            "cintas tubulares","repuestos suspension","pines","pino","pinos","pastilla",
            "pastillas","cassette","cassettes","casete","casetes","tee","tees","potencia",
            "potencias","rayo","rayos","rueda","ruedas","juego de ruedas","collarin",
            "collarín","abrazadera","abrazaderas","juego de direccion","juego de dirección",
            "espaciador","espaciadores","separador","separadores","perno","pernos",
            "tornillo","tornillos","tuerca","tuercas","pressfit","bb","bottom bracket",
            "motor bsa","motor ceramic","frameset","frame set","corona","plato",
            "cazoleta","liquido","líquido","tubular"]
BIKE_KW = ["bicicleta","bicicletas","bicycle","bicycles","bike","bikes","mtb","ruta","gravel",
            "trail","enduro","downhill","bmx","electrica","electricas","ebike","ebikes",
            "urban","urbana","urbanas","infantil","infantiles","fatbike"]

def classify_by_text(text):
    t = text.lower()
    # Check accessories and spare parts first with word boundaries to avoid greedy matches on "bike", "bicicleta", "mtb", etc.
    for k in ACC_KW:
        if re.search(r'\b' + re.escape(k) + r'\b', t): return "accesorios"
    for k in REP_KW:
        if re.search(r'\b' + re.escape(k) + r'\b', t): return "repuestos"
    for k in BIKE_KW:
        if re.search(r'\b' + re.escape(k) + r'\b', t): return "bicicletas"
    
    # Substring match fallback as absolute last resort
    for k in ACC_KW:
        if k in t: return "accesorios"
    for k in REP_KW:
        if k in t: return "repuestos"
    for k in BIKE_KW:
        if k in t: return "bicicletas"
    return None



def clean_price(s):
    if not s: return 0
    digits = re.sub(r"[^\d]","",str(s))
    try: return int(digits) if digits else 0
    except: return 0

def md5_id(brand, model):
    key = f"{brand.strip().upper()}_{model.strip().upper()}"
    return hashlib.md5(key.encode()).hexdigest()[:12]

def numeric_id(store_key, brand, model):
    return abs(hash(f"{store_key}_{brand}_{model}")) % (10**9)

def download_img(url, filepath):
    try:
        clean = url.split("?")[0]
        r = scraper.get(clean, headers=HDR, timeout=12)
        if r.status_code == 200 and len(r.content) > 1000:
            with open(filepath, "wb") as f: f.write(r.content)
            return True
    except: pass
    return False

def get_ext(url):
    m = re.search(r"\.(jpg|jpeg|png|webp|gif)", (url or "").lower().split("?")[0])
    return m.group(1) if m else "jpg"

def save_img_and_path(img_url, prefix, brand, model):
    h   = md5_id(brand, model)
    ext = get_ext(img_url)
    fp  = os.path.join(ASSETS, f"{prefix}_{h}.{ext}")
    lp  = f"assets/bikes/{prefix}_{h}.{ext}"
    if img_url and not os.path.exists(fp):
        if download_img(img_url, fp):
            print(f"    ✅ {prefix}_{h}.{ext}")
        else:
            return img_url   # CDN fallback
    elif not img_url:
        return "assets/bikes/bike_0.jpg"
    return lp

def classify_bike_type(title):
    t = title.lower()
    if any(k in t for k in ["fixie", "pista", "single-speed", "singlespeed", "tracklocross", "fijo y libre"]):
        return "fixie"
    if any(k in t for k in ["electrica", "e-bike", "ebike", "electric"]):
        return "electrica"
    if any(k in t for k in ["infantil", "niño", "niña", "kids", "juvenil", "chicos", "contessa 16", "riprock"]):
        return "infantil"
    if any(k in t for k in ["mtb", "mountain", "montaña", "trail", "enduro", "downhill", "xc", "spark", "scale", "ransom"]):
        return "mtb"
    if any(k in t for k in ["gravel", "allroad", "all-road", "cyclo", "cyclocross", "ciclocross"]):
        return "gravel"
    if any(k in t for k in ["hibrida", "híbrida", "hybrid"]):
        return "hibrida"
    if any(k in t for k in ["ruta", "road", "triatlon", "carrera", "addict", "foil", "strela", "eternity"]):
        return "ruta"
    if any(k in t for k in ["urbana", "urban", "paseo", "city"]):
        return "urbana"
    return "ruta"  # fallback

def normalize_brand_name(b):
    if not b:
        return "Genérica"
    b_clean = str(b).strip()
    if not b_clean:
        return "Genérica"
    
    canonical = {
        "sram": "SRAM",
        "abus": "ABUS",
        "ybn": "YBN",
        "met": "MET",
        "ht components": "HT Components",
        "vp components": "VP Components",
        "sdg components": "SDG Components",
        "muc-off": "Muc-Off",
        "rockshox": "RockShox",
        "thinkrider": "ThinkRider",
        "sunrace": "SunRace",
        "suntour": "SR Suntour",
        "disney": "Disney",
        "best": "Best",
        "merida": "Merida",
        "scott": "Scott",
        "silverback": "Silverback",
        "upland": "Upland",
        "bell": "Bell",
        "beto": "Beto",
        "blackburn": "Blackburn",
        "crankbrothers": "Crankbrothers",
        "evoc": "Evoc",
        "fidlock": "Fidlock",
        "fizik": "Fizik",
        "fox": "Fox",
        "giro": "Giro",
        "giyo": "Giyo",
        "knog": "Knog",
        "kugan": "Kugan",
        "leatt": "Leatt",
        "lezyne": "Lezyne",
        "northwave": "Northwave",
        "ravemen": "Ravemen",
        "topeak": "Topeak",
        "yakima": "Yakima",
        "continental": "Continental",
        "deity": "Deity",
        "kenda": "Kenda",
        "magura": "Magura",
        "marzocchi": "Marzocchi",
        "maxxis": "Maxxis",
        "prologo": "Prologo",
        "renthal": "Renthal",
        "schwalbe": "Schwalbe",
        "shimano": "Shimano",
        "spank": "Spank",
        "sugek": "Sugek",
        "viking": "Viking",
        "weinmann": "Weinmann",
        "weldtite": "Weldtite"
    }
    
    lower = b_clean.lower()
    if lower in canonical:
        return canonical[lower]
        
    if b_clean.isupper():
        return b_clean.title()
        
    words = b_clean.split()
    title_words = []
    for w in words:
        if w.lower() in ["de", "para", "y", "and"]:
            title_words.append(w.lower())
        else:
            title_words.append(w.capitalize())
    return " ".join(title_words)

def make_entry(brand, model, cat, spec_label, price, old_price,
               store, store_key, url, img_url):
    brand = normalize_brand_name(brand)
    prefix = {"bicicletas":"bike","accesorios":"acc","repuestos":"part"}[cat]
    local  = save_img_and_path(img_url, prefix, brand, model)
    hist   = [int(price*1.15),int(price*1.1),int(price*1.05),price,price,price]
    
    prod_type = cat
    if cat == "bicicletas":
        prod_type = classify_bike_type(model)
        
    return {
        "brand": brand,
        "model": model,
        "type":  prod_type,
        "wheelSize":  "",
        "frameType":  "",
        "specs":      spec_label,
        "original_img_url": img_url or "",
        "fullSpecs": {
            "Categoría": spec_label,
            "Marca": brand,
            "Tienda": store,
        },
        "offers": [{
            "store": store, "storeKey": store_key,
            "price": price,
            "oldPrice": old_price if old_price and old_price > price else None,
            "url": url, "imageUrl": img_url or ""
        }],
        "id":      numeric_id(store_key, brand, model),
        "image":   local,
        "history": hist,
    }

# ══════════════════════════════════════════════════════════════════════
# SOURCE 1 – CROSSMOUNTAIN.CL  (Shopify, 250+ productos de accesorios)
# ══════════════════════════════════════════════════════════════════════
CROSS_ACC_TYPES = {
    "LUCES","ANTIPARRAS","CASCOS ABIERTOS MTB","CASCOS RUTA/XC","GUANTES",
    "MICA ANTIPARRAS","SILLINES","ZAPATILLAS FIJACION MTB","JERSEY HOMBRE BICICLETA",
    "JERSEY MUJER BICICLETA","ROPA CICLISMO","RODILLERAS","MANOPLAS","BANANOS",
    "PORTA BIDONES","BIDONES","CAMPANAS","ESPEJOS","REFLECTANTES",
}
CROSS_REP_TYPES = {
    "NEUMATICOS 29","NEUMATICOS 27.5","NEUMATICOS 26",
    "REPUESTOS SUSPENSION","CINTA TUBULAR","PINOS BICICLETA","CÁMARAS BICICLETA",
    "CAMARAS BICICLETA","FRENOS","CADENAS","PEDALES","MANUBRIOS","PUÑOS BICICLETA",
    "LLANTAS","FRENOS HIDRAULICOS","REPUESTOS FRENOS","PIÑONES","CASETES",
}
CROSS_BIKE_TYPES = {
    "MTB","MOUNTAIN BIKE","RUTA","GRAVEL","BICICLETAS","BICICLETA","E-BIKE",
    "BICICLETAS ELECTRICAS","BIKES",
}

def classify_cross(p_type, title):
    t = (p_type or "").strip().upper()
    
    # Check accessories and spare parts keyword lists first on product_type
    for k in ACC_KW:
        if re.search(r'\b' + re.escape(k) + r'\b', t.lower()): return "accesorios"
    for k in REP_KW:
        if re.search(r'\b' + re.escape(k) + r'\b', t.lower()): return "repuestos"
        
    # Check ACC and REP types first to avoid greedy matching on MTB, RUTA, etc.
    for at in CROSS_ACC_TYPES:
        if at in t: return "accesorios"
    for rt in CROSS_REP_TYPES:
        if rt in t: return "repuestos"
    for bt in CROSS_BIKE_TYPES:
        # Avoid greedy substring matches on generic "BICICLETA" or "BIKE" in "Zapatillas De Bicicleta"
        if bt == t or t in ["BICICLETAS", "BICICLETA", "BIKES", "MTB", "MOUNTAIN BIKE", "E-BIKE"]:
            return "bicicletas"
    # fallback by title
    return classify_by_text(title)


def scrape_crossmountain():
    print("\n🚵 CrossMountain.cl (Shopify)")
    base = "https://crossmountain.cl"
    acc, rep, bikes = [], [], []
    page = 1
    while True:
        r = scraper.get(f"{base}/products.json?limit=250&page={page}", headers=HDR, timeout=15)
        if r.status_code != 200: break
        prods = r.json().get("products", [])
        if not prods: break
        print(f"  Page {page}: {len(prods)} prods")
        for p in prods:
            title   = p.get("title","").strip()
            p_type  = p.get("product_type","").strip()
            vendor  = p.get("vendor","").strip() or "CrossMountain"
            handle  = p.get("handle","")
            url     = f"{base}/products/{handle}"
            img_url = p["images"][0]["src"].split("?")[0] if p.get("images") else ""
            variants = p.get("variants",[])
            if not variants: continue
            price   = clean_price(variants[0].get("price",0))
            cmp     = clean_price(variants[0].get("compare_at_price",0))
            if price < 500: continue
            cat = classify_cross(p_type, title)
            if not cat: continue
            spec = p_type.title() if p_type else cat.title()
            entry = make_entry(vendor, title, cat, spec, price,
                               cmp if cmp > price else None,
                               "CrossMountain","crossmountain", url, img_url)
            if cat == "bicicletas": bikes.append(entry)
            elif cat == "accesorios": acc.append(entry)
            else: rep.append(entry)
        if len(prods) < 250: break
        page += 1
        time.sleep(0.5)
    print(f"  ✅ {len(bikes)} bikes, {len(acc)} acc, {len(rep)} rep")
    return bikes, acc, rep

# ══════════════════════════════════════════════════════════════════════
# SOURCE 2 – COPENHAGUE.CL  (Jumpseller HTML via category crawling)
# ══════════════════════════════════════════════════════════════════════
COPE_CATS = [
    ("/bicicletas",                                  "bicicletas"),
    ("/accesorios-para-ciclistas",                   "accesorios"),
    ("/mochilas-alforjas",                           "accesorios"),
    ("/bolsos-para-ciclistas",                       "accesorios"),
    ("/candados-bicicleta",                          "accesorios"),
    ("/cascos",                                      "accesorios"),
    ("/lentes",                                      "accesorios"),
    ("/complementos/luces",                          "accesorios"),
    ("/reflectantes-2",                              "accesorios"),
    ("/componentes-bicicleta",                       "repuestos"),
    ("/cadenas-para-bicicleta",                      "repuestos"),
    ("/camaras-bicicletas",                          "repuestos"),
    ("/complementos-1/frenos",                       "repuestos"),
    ("/complementos/pedales",                        "repuestos"),
    ("/pinones-cassette",                            "repuestos"),
    ("/complementos/cintas-punos-manubrios-bicicletas","repuestos"),
    ("/ruedas",                                      "repuestos"),
    ("/asientos-1",                                  "repuestos"),
]

def parse_copenhague_page(html, cat, base):
    soup  = BeautifulSoup(html, "lxml")
    # Jumpseller card elements
    cards = soup.select("article[data-product-id], .product-block__wrapper")
    items = []
    for card in cards:
        name_el = (card.select_one(".product-block__name")
                   or card.select_one("a.product-block__name")
                   or card.select_one("h2") 
                   or card.select_one(".product-name")
                   or card.select_one("a[href]"))
        name = name_el.get_text(strip=True) if name_el else ""
        if not name or len(name) < 2: continue
        
        # Price - extract current and old price safely from Jumpseller card
        money_els = card.select(".theme-money, .money")
        price = 0
        old_price = None
        if money_els:
            price = clean_price(money_els[0].get_text(strip=True))
            if len(money_els) > 1:
                old_price = clean_price(money_els[1].get_text(strip=True))
        else:
            price_el = card.select_one("[class*='price']")
            price = clean_price(price_el.get_text(strip=True)) if price_el else 0
            
        if price < 500: continue
        
        # Image
        img_el = card.select_one("img[src], img[data-src]")
        img_raw = ""
        if img_el:
            img_raw = img_el.get("src") or img_el.get("data-src") or ""
            if img_raw.startswith("//"):
                img_raw = "https:" + img_raw
            elif img_raw.startswith("/"):
                img_raw = base + img_raw
            # Replace resize to get higher resolution
            img_raw = re.sub(r"/resize/\d+/\d+", "/resize/800/800", img_raw).split("?")[0]
            
        # URL
        link_el = card.select_one("a[href]")
        href = link_el["href"] if link_el else ""
        prod_url = base + href if href.startswith("/") else href
        
        brand = "State Bicycle Co"
        spec_label = cat.title()
        
        entry = make_entry(brand, name, cat, spec_label, price, old_price,
                           "Copenhague", "copenhague", prod_url, img_raw)
        items.append(entry)
    return items

def scrape_copenhague():
    print("\n🚲 Copenhague.cl (Jumpseller HTML)")
    base = "https://www.copenhague.cl"
    bikes, acc, rep = [], [], []
    seen_ids = set()

    for path, cat in COPE_CATS:
        print(f"  Scraping {path}...")
        page_url = base + path
        page_num = 0
        while page_url:
            r = scraper.get(page_url, headers=HDR, timeout=12)
            if r.status_code != 200: break
            items = parse_copenhague_page(r.text, cat, base)
            if not items: break
            for item in items:
                if item["id"] not in seen_ids:
                    seen_ids.add(item["id"])
                    if cat == "bicicletas": bikes.append(item)
                    elif cat == "accesorios": acc.append(item)
                    else: rep.append(item)
            page_num += 1
            # get next page using rel="next"
            soup = BeautifulSoup(r.text, "lxml")
            next_el = soup.select_one("a[rel='next'], li.next a, .pagination .next a, a[aria-label*='iguiente']")
            if next_el:
                href = next_el.get("href", "")
                page_url = (base + href) if href.startswith("/") else href
            else:
                break
            time.sleep(0.5)
        print(f"    {path}: {page_num} pages scraped")

    print(f"  ✅ {len(bikes)} bikes, {len(acc)} acc, {len(rep)} rep")
    return bikes, acc, rep

# ══════════════════════════════════════════════════════════════════════
# SOURCE 3 – FULLBIKE.CL  (Jumpseller – HTML paginado)
# ══════════════════════════════════════════════════════════════════════
FULLBIKE_CATS = [
    ("/bicicletas",                          "bicicletas"),
    ("/bicicletas-doble-susp",               "bicicletas"),
    ("/bicicletas-de-gravel/cyclo",          "bicicletas"),
    ("/bicicletas-de-paseo/urbanas",         "bicicletas"),
    ("/bicicletas/bicicletas-de-triatlon",   "bicicletas"),
    ("/bicicletas/bicicletas-electricas",    "bicicletas"),
    ("/bicicletas/bicicletas-infantiles",    "bicicletas"),
    ("/bicicletas/bicicletas-mtb",           "bicicletas"),
    ("/bicicletas/bicicletas-mtb-mujer",     "bicicletas"),
    ("/bicicletas/bicicletas-ruta",          "bicicletas"),
    ("/accesorios",                          "accesorios"),
    ("/repuestos",                           "repuestos"),
    ("/cascos",                              "accesorios"),
    ("/luces",                               "accesorios"),
    ("/protecciones",                        "accesorios"),
    ("/ropa-ciclismo",                       "accesorios"),
    ("/componentes",                         "repuestos"),
]

def parse_fullbike_page(html, cat, base):
    soup  = BeautifulSoup(html, "lxml")
    cards = soup.select("article[data-product-id]")
    items = []
    for card in cards:
        pid     = card.get("data-product-id","")
        # Name
        name_el = (card.select_one("a.product-block__name")
                   or card.select_one("h2") or card.select_one(".product-name"))
        name    = name_el.get_text(strip=True) if name_el else ""
        if not name: continue
        # Price - extract current and old price safely from Jumpseller card
        money_els = card.select(".theme-money, .money")
        price = 0
        old_price = None
        if money_els:
            price = clean_price(money_els[0].get_text(strip=True))
            if len(money_els) > 1:
                old_price = clean_price(money_els[1].get_text(strip=True))
        else:
            price_el = card.select_one("[class*='price']")
            price = clean_price(price_el.get_text(strip=True)) if price_el else 0
            
        if price < 500: continue
        # Image – Jumpseller puts full URL in data-src or src
        img_el  = card.select_one("img[data-src], img[src]")
        img_raw = ""
        if img_el:
            img_raw = img_el.get("data-src") or img_el.get("src","")
            if img_raw.startswith("//"):
                img_raw = "https:" + img_raw
            elif img_raw.startswith("/"):
                img_raw = base + img_raw
            # Replace resize dimensions to get larger image
            img_raw = re.sub(r"/resize/\d+/\d+", "/resize/800/800", img_raw).split("?")[0]
        # URL
        link_el = card.select_one("a[href]")
        prod_url = base + link_el["href"] if link_el and link_el.get("href","").startswith("/") else ""

        # Brand = vendor field in data attr or first word of name
        vendor_el = card.select_one("[data-brand], [class*=brand]")
        brand = vendor_el.get_text(strip=True) if vendor_el else name.split()[0].title()

        spec_label = cat.title()
        entry = make_entry(brand, name, cat, spec_label, price, old_price,
                           "Full Bike", "fullbike", prod_url, img_raw)
        items.append(entry)
    return items

def get_fullbike_next_page(html, current_page):
    soup = BeautifulSoup(html, "lxml")
    next_el = soup.select_one("a[rel=next], .pagination__next a, a[aria-label='Siguiente']")
    if next_el and next_el.get("href"):
        return next_el["href"]
    return None

def scrape_fullbike():
    print("\n🔧 FullBike.cl (Jumpseller HTML)")
    base = "https://www.fullbike.cl"
    bikes, acc, rep = [], [], []
    seen_ids = set()

    for path, cat in FULLBIKE_CATS:
        print(f"  Scraping {path}...")
        page_url = base + path
        page_num = 0
        while page_url:
            r = scraper.get(page_url, headers=HDR, timeout=12)
            if r.status_code != 200: break
            items = parse_fullbike_page(r.text, cat, base)
            for item in items:
                if item["id"] not in seen_ids:
                    seen_ids.add(item["id"])
                    if cat == "bicicletas": bikes.append(item)
                    elif cat == "accesorios": acc.append(item)
                    else: rep.append(item)
            page_num += 1
            # next page
            soup = BeautifulSoup(r.text, "lxml")
            next_el = soup.select_one("a[rel='next'], .pagination a[aria-label*='iguiente']")
            if next_el:
                href = next_el.get("href","")
                page_url = (base + href) if href.startswith("/") else href
            else:
                break
            time.sleep(0.5)
        print(f"    {path}: {page_num} pages scraped")

    print(f"  ✅ {len(bikes)} bikes, {len(acc)} acc, {len(rep)} rep")
    return bikes, acc, rep

# ══════════════════════════════════════════════════════════════════════
# SOURCE 4 – VIDAURREBIKES.CL  (PrestaShop Custom)
# ══════════════════════════════════════════════════════════════════════
VIDAURRE_CATS = [
    ("/2630/listado/bicicletas",  "bicicletas"),
    ("/2630/listado/accesorios",  "accesorios"),
    ("/2630/listado/componentes", "repuestos"),
    ("/2630/listado/cascos",      "accesorios"),
    ("/2630/listado/guantes",     "accesorios"),
    ("/2630/listado/neumaticos",  "repuestos"),
    ("/2630/listado/pedales",     "repuestos"),
]

def parse_prestashop_page(html, cat, base):
    soup  = BeautifulSoup(html, "lxml")
    # Custom PrestaShop/Ailoo product card elements
    cards = soup.select("article.product-miniature, .product_list li.ajax_block_product")
    items = []
    for card in cards:
        # Name
        name_el = card.select_one("h3.product-title a, h2.product-name a, h1.product_name, .product-title a, a[class*=name], .product-name a")
        if not name_el:
            name_el = card.find("a", href=lambda h: h and "/producto/" in h)
        name = name_el.get_text(strip=True) if name_el else ""
        if not name or len(name) < 2: continue
        
        prod_url = name_el.get("href","")
        if prod_url.startswith("/"):
            prod_url = base + prod_url
            
        # Price
        price_el = card.select_one(".price, .product-price span, [class*=price]")
        price = clean_price(price_el.get_text(strip=True)) if price_el else 0
        if price < 500: continue
        
        # Image
        img_el = card.find("img")
        img_raw = ""
        if img_el:
            img_raw = img_el.get("src") or img_el.get("data-src") or ""
            if img_raw.startswith("//"):
                img_raw = "https:" + img_raw
            elif img_raw.startswith("/"):
                img_raw = base + img_raw
                
        brand_el = card.select_one(".product-manufacturer, [class*=brand]")
        brand = brand_el.get_text(strip=True) if brand_el else name.split()[0].title()

        entry = make_entry(brand, name, cat, cat.title(), price, None,
                           "Vidaurre Bikes", "vidaurre", prod_url, img_raw)
        items.append(entry)
    return items

def scrape_vidaurre():
    print("\n🏔️  VidaurreBikes.cl (PrestaShop)")
    base = "https://www.vidaurrebikes.cl"
    bikes, acc, rep = [], [], []
    seen_ids = set()

    for path, cat in VIDAURRE_CATS:
        print(f"  Scraping {path}...")
        page = 1
        while page <= 10:
            url = f"{base}{path}?page={page}" if page > 1 else base + path
            r = scraper.get(url, headers=HDR, timeout=12)
            if r.status_code != 200: break
            items = parse_prestashop_page(r.text, cat, base)
            if not items: break
            for item in items:
                if item["id"] not in seen_ids:
                    seen_ids.add(item["id"])
                    if cat == "bicicletas": bikes.append(item)
                    elif cat == "accesorios": acc.append(item)
                    else: rep.append(item)
            page += 1
            time.sleep(0.5)
        print(f"    {path}: {page - 1} pages scraped")

    print(f"  ✅ {len(bikes)} bikes, {len(acc)} acc, {len(rep)} rep")
    return bikes, acc, rep

# ══════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════
def merge_by_id(existing, new_items):
    """Merge new items into existing list, deduplicating by ID."""
    seen = {item["id"] for item in existing}
    added = 0
    for item in new_items:
        if item["id"] not in seen:
            seen.add(item["id"])
            existing.append(item)
            added += 1
    return added

def main():
    print("🚀 ADDING NEW STORES: CrossMountain + Copenhague + FullBike + VidaurreBikes")
    print("=" * 70)

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Current: {len(data['bicicletas'])} bikes | "
          f"{len(data['accesorios'])} acc | {len(data['repuestos'])} rep")

    all_new_bikes, all_new_acc, all_new_rep = [], [], []

    # ── CrossMountain ──
    b, a, r = scrape_crossmountain()
    all_new_bikes += b; all_new_acc += a; all_new_rep += r

    # ── Copenhague ──
    b, a, r = scrape_copenhague()
    all_new_bikes += b; all_new_acc += a; all_new_rep += r

    # ── FullBike ──
    b, a, r = scrape_fullbike()
    all_new_bikes += b; all_new_acc += a; all_new_rep += r

    # ── VidaurreBikes ──
    b, a, r = scrape_vidaurre()
    all_new_bikes += b; all_new_acc += a; all_new_rep += r

    # Merge into data
    ab = merge_by_id(data["bicicletas"],  all_new_bikes)
    aa = merge_by_id(data["accesorios"],  all_new_acc)
    ar = merge_by_id(data["repuestos"],   all_new_rep)

    print("\n" + "=" * 70)
    print(f"📊 FINAL RESULTS:")
    print(f"   Bicicletas: {len(data['bicicletas'])} (+{ab} nuevas)")
    print(f"   Accesorios: {len(data['accesorios'])} (+{aa} nuevas)")
    print(f"   Repuestos:  {len(data['repuestos'])} (+{ar} nuevas)")

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ data.json guardado exitosamente!")

if __name__ == "__main__":
    main()
