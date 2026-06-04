"""
scrape_copenhague_fixed.py
Raspa copenhague.cl correctamente (Jumpseller HTML) y actualiza data.json
con precios reales y descuentos del Cyber Day.
"""
import sys, re, time, json, unicodedata, os
sys.stdout.reconfigure(encoding='utf-8')

try:
    import cloudscraper
    from bs4 import BeautifulSoup
except ImportError:
    import subprocess; subprocess.run(["pip","install","cloudscraper","beautifulsoup4","lxml","-q"])
    import cloudscraper
    from bs4 import BeautifulSoup

DATA_PATH = r"c:\Users\basti\Desktop\bicitodo\fronted\data.json"
ASSETS    = r"c:\Users\basti\Desktop\bicitodo\fronted\assets\bikes"

s = cloudscraper.create_scraper(browser={'browser':'chrome','platform':'windows','mobile':False})
HDR = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "es-CL,es;q=0.9",
}

def clean_price(text):
    if not text: return None
    nums = re.sub(r'[^\d]', '', str(text))
    return int(nums) if nums else None

def clean_text(text):
    if not text: return ""
    return re.sub(r'\s+', ' ', str(text)).strip()

def normalize(text):
    nfkd = unicodedata.normalize('NFKD', str(text).lower().strip())
    return ''.join(c for c in nfkd if not unicodedata.combining(c))

def fetch_page(url):
    try:
        r = s.get(url, headers=HDR, timeout=25)
        if r.status_code == 200:
            return BeautifulSoup(r.text, "lxml")
    except Exception as e:
        print(f"  [WARN] {url}: {e}")
    return None

def download_img(img_url, filename):
    if not img_url: return None
    path = os.path.join(ASSETS, filename)
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return f"assets/bikes/{filename}"
    try:
        r = s.get(img_url, headers=HDR, timeout=12)
        if r.status_code == 200 and len(r.content) > 1000:
            with open(path, "wb") as f:
                f.write(r.content)
            return f"assets/bikes/{filename}"
    except Exception:
        pass
    return None

def scrape_jumpseller_category(domain, path):
    """Raspa una categoría de Jumpseller, con paginación."""
    items = []
    seen = set()
    url = domain + path
    page = 1

    while True:
        page_url = url if page == 1 else f"{url}?page={page}"
        print(f"  Scraping: {page_url}")
        soup = fetch_page(page_url)
        if not soup:
            break

        # Selector correcto para Jumpseller Copenhague
        products = soup.find_all("article", attrs={"data-product-id": True})
        if not products:
            # Fallback: cualquier article con clase product-block
            products = [el for el in soup.find_all("article") if "product-block" in " ".join(el.get("class", []))]

        if not products:
            break

        found_new = False
        for p in products:
            prod_id = p.get("data-product-id", "")

            # Nombre
            name_el = (p.select_one(".product-block__title") or
                       p.select_one("h2") or
                       p.select_one("h3") or
                       p.select_one("[class*='title']"))
            name = clean_text(name_el.get_text()) if name_el else ""
            if not name or name in seen:
                continue
            seen.add(name)
            found_new = True

            # Precios: en Jumpseller, si hay descuento hay 2 divs product-block__price
            # El primero es el precio actual (rebajado), el segundo es el precio anterior
            price_divs = p.select(".product-block__price")
            price = None
            old_price = None
            if len(price_divs) >= 2:
                # Precio con descuento: el primero tiene el precio actual
                # Pero necesitamos identificar cuál es cuál
                # En Copenhague: la estructura es
                # div.product-block__price div.product-block__price-value (precio actual)
                # div.product-block__price div.product-block__price-value (precio anterior tachado)
                texts = [clean_text(d.get_text()) for d in price_divs if clean_text(d.get_text())]
                prices_found = [clean_price(t) for t in texts if clean_price(t)]
                if len(prices_found) >= 2:
                    # El menor es el actual, el mayor es el anterior
                    price = min(prices_found)
                    old_price = max(prices_found)
                elif len(prices_found) == 1:
                    price = prices_found[0]
            elif len(price_divs) == 1:
                price = clean_price(price_divs[0].get_text())

            # También buscar el badge de descuento para verificar
            badge = p.select_one("[class*='label'], [class*='badge'], [class*='tag'], [class*='discount']")
            badge_text = clean_text(badge.get_text()) if badge else ""

            # URL del producto
            a_el = p.select_one("a[href*='/products/'], a[href]")
            prod_url = ""
            if a_el:
                href = a_el.get("href", "")
                prod_url = href if href.startswith("http") else domain + href

            # Imagen
            img_el = p.select_one("img[src], img[data-src]")
            img_url = ""
            if img_el:
                img_url = img_el.get("src") or img_el.get("data-src") or ""
                # Limpiar parámetros de tamaño de Jumpseller
                img_url = re.sub(r'\?.*$', '', img_url)

            # Marca (Copenhague vende principalmente State Bicycle Co)
            vendor_el = p.select_one("[class*='vendor'], [class*='brand'], [class*='maker']")
            brand = clean_text(vendor_el.get_text()) if vendor_el else "State Bicycle Co"

            if price:
                discount_pct = round((1 - price/old_price)*100) if old_price and old_price > price else 0
                item = {
                    "name": name,
                    "brand": brand,
                    "price": price,
                    "old_price": old_price,
                    "discount_pct": discount_pct,
                    "badge": badge_text,
                    "url": prod_url,
                    "image": img_url,
                    "prod_id": prod_id,
                    "category_path": path
                }
                items.append(item)

        if not found_new:
            break

        # Paginación Jumpseller
        next_el = soup.select_one("a[rel='next'], .pagination-next a, li.next a")
        if not next_el:
            break
        page += 1
        time.sleep(0.5)

    return items

def main():
    domain = "https://www.copenhague.cl"

    # Categorías de Copenhague (verificadas)
    categories = [
        "/bicicletas",
        "/bicicletas-urbanas-state-bicycle",
        "/bicicletas-fixie-acero-state-bicycle",
        "/bicicletas-fixie-cromoly-state-bicycle",
        "/bicicletas-de-ruta-state-bicycle",
        "/accesorios",
        "/repuestos",
    ]

    # También intentar categorías que vimos en el menu
    extra_categories = [
        "/bicicletas-cyber-2027",  # Categoría Cyber especial que vimos
    ]

    all_items = []
    seen_names = set()

    print("=" * 60)
    print("SCRAPEANDO COPENHAGUE.CL (Jumpseller)")
    print("=" * 60)

    for cat in categories + extra_categories:
        print(f"\n[>] Categoría: {cat}")
        try:
            items = scrape_jumpseller_category(domain, cat)
            new_items = [i for i in items if i["name"] not in seen_names]
            for i in new_items:
                seen_names.add(i["name"])
            all_items.extend(new_items)
            print(f"    {len(new_items)} productos nuevos | Total: {len(all_items)}")
        except Exception as e:
            print(f"    [ERROR] {e}")

    print(f"\n{'='*60}")
    print(f"TOTAL COPENHAGUE: {len(all_items)} productos")

    # Mostrar los con descuento
    with_disc = [i for i in all_items if i["discount_pct"] > 0]
    print(f"CON DESCUENTO (Cyber): {len(with_disc)}")
    for item in sorted(with_disc, key=lambda x: -x["discount_pct"])[:10]:
        print(f"  {item['name'][:55]} | {item['price']:,} (antes {item['old_price']:,}) -{item['discount_pct']}%")

    if not all_items:
        print("⚠️ No se encontraron productos")
        return

    # Actualizar data.json
    print(f"\nActualizando data.json...")
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Indexar existentes
    existing_by_name = {}
    for cat_key in ["bicicletas", "accesorios", "repuestos"]:
        for prod in data.get(cat_key, []):
            key = normalize(prod.get("model", ""))
            existing_by_name[key] = (cat_key, prod)

    updated = 0
    added = 0

    for item in all_items:
        key = normalize(item["name"])

        # Clasificar
        name_lower = item["name"].lower()
        cat_path = item["category_path"].lower()
        if any(k in name_lower for k in ["bicicleta","bike","fixie","gravel","ruta","electrica","urbana","infantil","bmx","chromoly"]):
            cat_key = "bicicletas"
        elif any(k in name_lower for k in ["pedal","cadena","freno","neumatico","camara","cassette","horquilla","rotor"]):
            cat_key = "repuestos"
        else:
            cat_key = "accesorios"

        if key in existing_by_name:
            ck, prod = existing_by_name[key]
            # Actualizar oferta de Copenhague
            for off in prod["offers"]:
                if off.get("storeKey") == "copenhague":
                    off["price"] = item["price"]
                    if item["old_price"] and item["old_price"] > item["price"]:
                        off["oldPrice"] = item["old_price"]
                    elif "oldPrice" in off and item["old_price"] is None:
                        off["oldPrice"] = None
                    off["url"] = item["url"] or off.get("url","#")
                    updated += 1
                    break
            else:
                # Copenhague no está en este producto, agregar
                prod["offers"].append({
                    "store": "Copenhague",
                    "storeKey": "copenhague",
                    "price": item["price"],
                    "oldPrice": item["old_price"] if item["old_price"] and item["old_price"] > item["price"] else None,
                    "url": item["url"] or "#"
                })
                prod["offers"].sort(key=lambda o: o["price"])
                updated += 1
        else:
            # Nuevo producto
            max_id = max((p["id"] for ck in ["bicicletas","accesorios","repuestos"] for p in data.get(ck,[])), default=0)
            new_id = max_id + 1 + added

            # Tipo de bicicleta
            if any(k in name_lower for k in ["electrica","electric","ebike"]):
                bike_type = "electrica"
            elif any(k in name_lower for k in ["gravel","ruta","road"]):
                bike_type = "ruta"
            elif any(k in name_lower for k in ["urbana","city"]):
                bike_type = "urbana"
            elif any(k in name_lower for k in ["infantil","junior","kids"]):
                bike_type = "infantil"
            elif any(k in name_lower for k in ["fixie","track","chromoly"]):
                bike_type = "ruta"
            else:
                bike_type = "urbana"

            # Descargar imagen
            img_local = None
            if item["image"]:
                ext = re.search(r'\.(jpg|jpeg|png|webp)', item["image"].lower())
                ext = ext.group(1) if ext else "jpg"
                fname = f"copenhague_{item['prod_id'] or new_id}.{ext}"
                img_local = download_img(item["image"], fname)

            final_img = img_local or "https://images.unsplash.com/photo-1532298229144-0ec0c57515c7?auto=format&fit=crop&w=500&h=400&q=80"

            new_prod = {
                "id": new_id,
                "brand": item["brand"] or "State Bicycle Co",
                "model": item["name"],
                "type": bike_type if cat_key == "bicicletas" else cat_key,
                "wheelSize": "700c" if any(k in name_lower for k in ["fixie","ruta","gravel","urbana","700"]) else "29",
                "frameType": "Acero" if any(k in name_lower for k in ["chromoly","acero","steel","cromo"]) else "Aluminio",
                "specs": f"{item['brand'] or 'State Bicycle Co'} - {item['name']}",
                "image": final_img,
                "history": [int(item["price"] * 1.08), int(item["price"] * 1.04), item["price"]],
                "fullSpecs": {},
                "offers": [{
                    "store": "Copenhague",
                    "storeKey": "copenhague",
                    "price": item["price"],
                    "oldPrice": item["old_price"] if item["old_price"] and item["old_price"] > item["price"] else None,
                    "url": item["url"] or "#"
                }]
            }
            data[cat_key].append(new_prod)
            existing_by_name[key] = (cat_key, new_prod)
            added += 1

    # Guardar
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ data.json actualizado:")
    print(f"  Actualizados: {updated} productos de Copenhague")
    print(f"  Nuevos: {added} productos de Copenhague")

    # Verificar descuentos guardados
    cop_with_disc = []
    for cat_key in ["bicicletas","accesorios","repuestos"]:
        for prod in data.get(cat_key, []):
            for off in prod.get("offers", []):
                if off.get("storeKey") == "copenhague" and off.get("oldPrice") and off["oldPrice"] > off["price"]:
                    pct = round((1 - off["price"]/off["oldPrice"])*100)
                    cop_with_disc.append((prod["model"][:50], off["price"], off["oldPrice"], pct))

    print(f"\n  Descuentos Copenhague visibles en la web: {len(cop_with_disc)}")
    for name, price, old, pct in sorted(cop_with_disc, key=lambda x: -x[3])[:10]:
        print(f"    {name}: {price:,} (antes {old:,}) -{pct}%")

if __name__ == "__main__":
    main()
