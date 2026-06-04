"""
expand_accesorios_repuestos.py - Expandir accesorios y repuestos v1.0
Fuentes:
  1. Faucon Bikes Shopify API - accesorios y componentes
  2. BikePlus Shopify API - accesorios y componentes
  3. Satiro Bikes Shopify API - accesorios y componentes

Resultado: data.json con muchos más accesorios y repuestos
"""
import os, sys, json, re, time, hashlib
import cloudscraper

os.environ['PYTHONIOENCODING'] = 'utf-8'
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

BASE_DIR = r"c:\Users\basti\Desktop\bicitodo"
FRONTED_DIR = os.path.join(BASE_DIR, "fronted")
ASSETS_DIR = os.path.join(FRONTED_DIR, "assets", "bikes")
os.makedirs(ASSETS_DIR, exist_ok=True)

scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}

# ---- Categorization keywords ----
# Types we classify as ACCESSORIES (non-part cycling gear)
ACC_TYPES = {
    "CASCOS MOUNTAIN BIKE", "CASCOS RUTA", "CASCOS INTEGRALES",
    "PACK DE LUCES", "LUZ DELANTERA", "LUZ TRASERA",
    "GUANTES LARGOS", "GUANTES",
    "BOLSOS", "ALFORJAS", "MOCHILA",
    "BOMBIN DE MANO", "BOMBIN CO2",
    "CANDADO U-LOCK", "CANDADO PLEGABLE", "CANDADO DE CADENA",
    "PORTA BOTELLAS", "BOTELLAS Y CARAMAGIOLAS",
    "LENTES Y ANTIPARRAS",
    "RODILLERAS", "CUBRESILLON", "TAPABARROS",
    "HERRAMIENTAS", "RODILLOS",
    "CAMPANA DE BICICLETA", "ANCLAJE UNIVERSAL",
    "ZAPATILLAS DE MONTANA",
}
# Types we classify as REPUESTOS/COMPONENTS (mechanical parts)
REP_TYPES = {
    "FRENOS HIDRAULICOS", "FRENO",
    "DESVIADOR TRASERO", "DESVIADOR", "SHIFTER",
    "PEDALES ANCLAJE DE MONTANA", "PEDALES DE PLATAFORMA", "PEDALES ANCLAJE DE RUTA", "PEDALES ANCLAJE MIXTO",
    "VOLANTE DE RUTA", "VOLANTE MOUNTAIN BIKE", "VOLANTE",
    "JUEGO DE DIRECCION",
    "LLANTAS",
    "MAZA TRASERA", "MAZAS",
    "DISCOS DE FRENO",
    "PINONES", "PI\u00d1ONES",
    "PINOS",
    "Neum\u00e1tico MTB", "Neum\u00e1tico Gravel", "Neum\u00e1tico XC", "Neum\u00e1tico Enduro / DH",
    "NEUMATICO MTB", "NEUMATICO",
    "CAMARAS",
    "CINTA ANTIPINCHAZO",
    "SELLANTE",
    "VALVULAS",
    "KIT DE REPARACION",
    "PARCHES",
    "EJES PASANTES",
    "HORQUILLAS DE RESORTE",
    "JERINGA",
    "CUADRO",
    "REPUESTO", "Repuesto",
    "PUNO", "PUNGOS", "PU\u00d1OS",
    "PORTA BOTELLAS COMPONENTE",
}

BIKE_TYPES = {
    "RUTERA", "XC", "MOUNTAIN BIKE", "GRAVEL", "TRAIL", "ENDURO", "DOWNHILL",
    "ELECTRICA DOBLE SUSPENSION", "INFANTILES", "BMX / Dirt", "URBANA",
    "CICLOCROSS Y GRAVEL", "TRIATHLON Y CRONO", "TRIATL\u00d3N Y CRONO",
}

def classify(product_type_str):
    t = (product_type_str or '').strip().upper()
    for bt in BIKE_TYPES:
        if bt in t or t in bt:
            return 'bicicletas'
    for at in ACC_TYPES:
        if at.upper() in t or t in at.upper():
            return 'accesorios'
    for rt in REP_TYPES:
        if rt.upper() in t or t in rt.upper():
            return 'repuestos'
    # Default heuristic by keywords in title
    return None

def acc_or_rep_by_title(title):
    t = title.lower()
    acc_kw = ['casco', 'luz', 'luces', 'guante', 'bombin', 'bolso', 'alforja',
               'portabotella', 'caramagiola', 'candado', 'lentes', 'antiparras',
               'banano', 'mochila', 'campanilla', 'timbre', 'rodillo',
               'chaleco', 'zapatilla', 'cubresillon', 'tapabarros']
    rep_kw = ['pedal', 'cadena', 'biela', 'pinon', 'volante', 'neumatico', 'llanta',
               'camara', 'sillin', 'horquilla', 'freno', 'manubrio', 'puno', 'puños',
               'rotor', 'disco', 'maneta', 'direccion', 'maza', 'eje', 'sellante',
               'valvula', 'parche', 'kit de reparacion', 'cuadro', 'desviador',
               'shifter', 'jeringa', 'antipinchazo', 'CO2']
    for kw in acc_kw:
        if kw in t:
            return 'accesorios'
    for kw in rep_kw:
        if kw in t:
            return 'repuestos'
    return None

def get_hash(brand, model):
    key = f"{brand.strip().upper()}_{model.strip().upper()}"
    return hashlib.md5(key.encode('utf-8')).hexdigest()[:12]

def clean_price(val):
    try: return int(float(str(val)))
    except: return 0

def download_image(img_url, filepath):
    try:
        r = scraper.get(img_url, headers=HEADERS, timeout=12)
        if r.status_code == 200 and len(r.content) > 1000:
            with open(filepath, "wb") as f:
                f.write(r.content)
            return True
    except Exception:
        pass
    return False

def fetch_shopify_products(base_url, store_name):
    """Fetch all products from a Shopify store via the products.json API"""
    products = []
    page = 1
    while True:
        url = f"{base_url}/products.json?limit=250&page={page}"
        try:
            r = scraper.get(url, headers=HEADERS, timeout=15)
            if r.status_code != 200:
                break
            batch = r.json().get('products', [])
            if not batch:
                break
            products.extend(batch)
            print(f"  {store_name}: fetched {len(products)} products so far...")
            if len(batch) < 250:
                break
            page += 1
            time.sleep(0.5)
        except Exception as e:
            print(f"  Error fetching {store_name} page {page}: {e}")
            break
    return products

def make_product_entry(brand, model, cat, product_type_str, price, old_price,
                       store_name, store_key, product_url, img_url, prefix):
    h = get_hash(brand, model)
    ext = 'jpg'
    if img_url:
        m = re.search(r'\.(jpg|jpeg|png|webp|gif)', img_url.lower().split('?')[0])
        if m: ext = m.group(1)
    
    filepath = os.path.join(ASSETS_DIR, f"{prefix}_{h}.{ext}")
    local_img = f"assets/bikes/{prefix}_{h}.{ext}"
    
    # Download image if not already present
    if img_url and not os.path.exists(filepath):
        clean_url = img_url.split('?')[0]
        if download_image(clean_url, filepath):
            print(f"    ✅ Downloaded image: {prefix}_{h}.{ext}")
        else:
            local_img = img_url  # fallback to CDN
    elif not img_url:
        local_img = f"assets/bikes/bike_0.jpg"
    
    # Build specs based on category
    if cat == 'accesorios':
        specs = f"Tipo: {product_type_str.title()}" if product_type_str else "Accesorio de ciclismo"
    else:
        specs = f"Componente: {product_type_str.title()}" if product_type_str else "Repuesto de bicicleta"
    
    # Generate price history
    history_prices = [int(price * 1.15), int(price * 1.1), int(price * 1.05), price, price, price]
    
    return {
        "brand": brand,
        "model": model,
        "type": cat,
        "wheelSize": "",
        "frameType": "",
        "specs": specs,
        "original_img_url": img_url or "",
        "fullSpecs": {
            "Categoría": product_type_str.title() if product_type_str else cat.title(),
            "Marca": brand,
            "Tienda": store_name,
        },
        "offers": [{
            "store": store_name,
            "storeKey": store_key,
            "price": price,
            "oldPrice": old_price if old_price and old_price > price else None,
            "url": product_url,
            "imageUrl": img_url or ""
        }],
        "id": abs(hash(f"{store_key}_{brand}_{model}")) % (10**9),
        "image": local_img,
        "history": history_prices
    }

def process_shopify_store(base_url, store_name, store_key):
    """Process a Shopify store and return (acc_list, rep_list)"""
    print(f"\n🛒 Processing {store_name}...")
    raw_products = fetch_shopify_products(base_url, store_name)
    print(f"  Total products fetched: {len(raw_products)}")
    
    accesorios = []
    repuestos = []
    skipped_bikes = 0
    
    for p in raw_products:
        title = p.get('title', '').strip()
        p_type = p.get('product_type', '').strip()
        vendor = p.get('vendor', '').strip() or store_name
        
        # Get image
        img_url = None
        if p.get('images'):
            img_url = p['images'][0].get('src', '').split('?')[0]
        
        # Get price
        variants = p.get('variants', [])
        if not variants:
            continue
        
        price = clean_price(variants[0].get('price', 0))
        compare_price = clean_price(variants[0].get('compare_at_price', 0))
        old_price = compare_price if compare_price > price else None
        
        if price < 500:  # Skip free/invalid items
            continue
        
        # Product URL
        handle = p.get('handle', '')
        product_url = f"{base_url}/products/{handle}" if handle else base_url
        
        # Classify
        cat = classify(p_type)
        if cat is None:
            cat = acc_or_rep_by_title(title)
        if cat == 'bicicletas' or cat is None:
            skipped_bikes += 1
            continue
        
        prefix = 'acc' if cat == 'accesorios' else 'part'
        entry = make_product_entry(vendor, title, cat, p_type, price, old_price,
                                   store_name, store_key, product_url, img_url, prefix)
        
        if cat == 'accesorios':
            accesorios.append(entry)
        else:
            repuestos.append(entry)
    
    print(f"  ✅ {len(accesorios)} accesorios, {len(repuestos)} repuestos, {skipped_bikes} bikes/others skipped")
    return accesorios, repuestos

def main():
    print("🚀 EXPANDING ACCESORIOS & REPUESTOS FROM MULTIPLE STORES 🚀")
    print("=" * 60)
    
    data_path = os.path.join(FRONTED_DIR, "data.json")
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    bikes = data.get("bicicletas", [])
    print(f"Loaded {len(bikes)} existing bikes.")
    
    all_accesorios = []
    all_repuestos = []
    
    # === SOURCE 1: FAUCON BIKES ===
    acc1, rep1 = process_shopify_store(
        "https://fauconbikes.cl", "Faucon Bikes", "faucon"
    )
    all_accesorios.extend(acc1)
    all_repuestos.extend(rep1)
    
    # === SOURCE 2: BIKEPLUS ===
    acc2, rep2 = process_shopify_store(
        "https://bikeplus.cl", "BikePlus", "bikeplus"
    )
    all_accesorios.extend(acc2)
    all_repuestos.extend(rep2)
    
    # === SOURCE 3: SATIRO BIKES ===
    acc3, rep3 = process_shopify_store(
        "https://satirobikes.cl", "Satiro Bikes", "satiro"
    )
    all_accesorios.extend(acc3)
    all_repuestos.extend(rep3)
    
    # Remove duplicates by ID
    seen_acc_ids = set()
    unique_acc = []
    for item in all_accesorios:
        if item['id'] not in seen_acc_ids:
            seen_acc_ids.add(item['id'])
            unique_acc.append(item)
    
    seen_rep_ids = set()
    unique_rep = []
    for item in all_repuestos:
        if item['id'] not in seen_rep_ids:
            seen_rep_ids.add(item['id'])
            unique_rep.append(item)
    
    print(f"\n{'='*60}")
    print(f"📊 FINAL RESULTS:")
    print(f"   Bicicletas: {len(bikes)}")
    print(f"   Accesorios: {len(unique_acc)} (was {len(data.get('accesorios',[]))})")
    print(f"   Repuestos:  {len(unique_rep)} (was {len(data.get('repuestos',[]))})")
    
    # Save updated data
    data["accesorios"] = unique_acc
    data["repuestos"] = unique_rep
    
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ data.json updated successfully!")
    print(f"   File: {data_path}")

if __name__ == "__main__":
    main()
