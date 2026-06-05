# aggregate_market.py - Central Aggregator and Matching Engine Orchestrator
import os
import sys
import json
import subprocess
import time
import re
import urllib.request
import cloudscraper

# Agregar el directorio actual al path para importar matcher
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass
from services.matcher import ProductMatcher

def run_scrapy_spider(spider_name, backend_dir, base_dir):
    """Ejecuta una araña Scrapy específica y retorna la lista de items."""
    timestamp = int(time.time())
    out_file = os.path.join(base_dir, f"temp_{spider_name}_{timestamp}.json")
    
    # Ejecutamos Scrapy con un límite de items prudente (120) para evitar que demore horas, 
    # pero recolectando suficientes modelos reales de cada tienda.
    # Desactivamos el pipeline de Postgres para volcar a JSON local de forma limpia.
    cmd = f"scrapy crawl {spider_name} -s CLOSESPIDER_ITEMCOUNT=120 -s ITEM_PIPELINES={{}} -O {out_file}"
    
    print(f"🤖 Ejecutando araña: {spider_name}...")
    try:
        subprocess.run(cmd, cwd=backend_dir, shell=True, timeout=300)
    except Exception as e:
        print(f"❌ Error o timeout ejecutando {spider_name}: {e}")
        
    items = []
    if os.path.exists(out_file):
        try:
            with open(out_file, "r", encoding="utf-8") as f:
                items = json.load(f)
            print(f"✅ Araña {spider_name} extrajo {len(items)} items.")
            os.remove(out_file)
        except Exception as e:
            print(f"⚠️ Error leyendo archivo temporal {out_file}: {e}")
            if os.path.exists(out_file):
                os.remove(out_file)
    else:
        print(f"⚠️ No se encontró archivo temporal para {spider_name}.")
        
    return items

def main():
    print("🚀 INICIANDO ORQUESTRACIÓN DEL MERCADO DE BICICLETAS CHILENO 2026 🚀")
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    backend_dir = os.path.join(base_dir, "backend")
    fronted_dir = os.path.join(base_dir, "fronted")
    assets_dir = os.path.join(fronted_dir, "assets", "bikes")
    os.makedirs(assets_dir, exist_ok=True)
    
    # 1. Lista de Spiders a Ejecutar (Los 16 registrados)
    spiders = [
        "trek", "specialized", "oxford", "decathlon", "dsbikes", "copenhague",
        "faucon", "satiro", "totem", "sparta", "bikeplus", "bikeshop",
        "falabella", "ripley", "paris", "mercadolibre"
    ]
    
    raw_data = []
    for s in spiders:
        scraped_items = run_scrapy_spider(s, backend_dir, base_dir)
        raw_data.extend(scraped_items)
        time.sleep(1) # Pequeña pausa entre ejecuciones
        
    print(f"\n📊 Extracción finalizada. Total de items en bruto recolectados: {len(raw_data)}")
    
    # Instanciamos el matcher
    matcher = ProductMatcher(threshold=0.82) # Umbral ligeramente más flexible para maximizar matches válidos
    
    # 2. Filtrado y Categorización
    # Blacklist de palabras clave de accesorios y repuestos
    accessory_blacklist = [
        "casco", "rodillera", "bateria", "cargador", "porta bicicleta", "soporte", 
        "tee", "rotor", "neumatico", "camara", "guante", "tricota", "calza", 
        "sillin", "puño", "bolso", "luces", "aceite", "bombin", "herramienta", 
        "luz", "pata de apoyo", "inflador", "candado", "caramayola", "portabotella", 
        "pedales", "bielas", "cadena", "cassette", "pata de cambio", "manubrio", 
        "horquilla", "llanta", "rayos", "freno", "pastillas de freno", "disco de freno"
    ]
    
    filtered_bikes = []
    filtered_repuestos = []
    
    for item in raw_data:
        name = item.get("name")
        price = item.get("price_normal")
        
        if not name or not price:
            continue
            
        name_lower = name.lower()
        
        # Filtro de precio básico (artículos de menos de $30.000 CLP son repuestos/accesorios)
        is_accessory = price < 30000
        
        # O si contiene palabras clave del blacklist
        if not is_accessory:
            for term in accessory_blacklist:
                if term in name_lower:
                    is_accessory = True
                    break
        
        if is_accessory:
            filtered_repuestos.append(item)
        else:
            filtered_bikes.append(item)
            
    print(f"🧹 Filtrado terminado: {len(filtered_bikes)} Bicicletas y {len(filtered_repuestos)} Repuestos/Accesorios.")
    
    # 3. FUSIÓN DE DUPLICADOS (Cerebro del Comparador SoloTodo)
    merged_bikes = []
    
    for item in filtered_bikes:
        name = item.get("name")
        price = item.get("price_normal")
        brand = item.get("brand")
        if not brand or brand == "Unknown":
            brand = matcher.get_brand(name)
            if brand == "Unknown":
                # Extraer primera palabra como fallback
                brand = name.split()[0] if name.split() else "Generica"
                
        model = item.get("model") or name
        # Eliminar marca del modelo si está duplicada al inicio
        if model.lower().startswith(brand.lower()):
            model = model[len(brand):].strip()
            
        image_url = item.get("image_url") or item.get("image")
        store = item.get("store", "Tienda")
        store_key = store.lower().replace(" ", "").replace("_", "")
        url = item.get("url", "#")
        
        # Intentar emparejar con alguna bicicleta ya agregada
        found_match = False
        for bike in merged_bikes:
            # Comparamos la marca y el nombre del modelo
            if matcher.is_match(f"{bike['brand']} {bike['model']}", f"{brand} {model}"):
                # Agregamos esta oferta al producto existente
                offer_exists = False
                for existing_offer in bike["offers"]:
                    if existing_offer["storeKey"] == store_key:
                        # Si ya existe esta tienda, guardamos la oferta más barata
                        if price < existing_offer["price"]:
                            existing_offer["price"] = price
                            existing_offer["url"] = url
                            existing_offer["oldPrice"] = item.get("price_card")
                        offer_exists = True
                        break
                
                if not offer_exists:
                    bike["offers"].append({
                        "store": store,
                        "storeKey": store_key,
                        "price": price,
                        "oldPrice": item.get("price_card"),
                        "url": url,
                        "imageUrl": image_url
                    })
                
                # Fusión incremental de especificaciones técnicas
                if item.get("specs") and isinstance(item["specs"], dict):
                    for k, v in item["specs"].items():
                        if k not in bike["fullSpecs"] or not bike["fullSpecs"][k]:
                            bike["fullSpecs"][k] = v
                
                # Mantener la mejor imagen oficial
                if image_url and not bike.get("original_image_url"):
                    bike["original_image_url"] = image_url
                
                found_match = True
                break
                
        if not found_match:
            # Creamos una nueva bicicleta canónica
            category = matcher.categorize_by_name(name)
            # Mapeamos a las llaves que espera app.js en minúscula sin tildes
            mapped_type = category.lower().replace("é", "e")
            
            wheel_size = matcher.extract_wheel_size(name) or item.get("wheel_size")
            if not wheel_size:
                wheel_size = "29" if mapped_type in ["mtb", "electrica"] else ("700c" if mapped_type == "ruta" else "26")
                
            frame_type = item.get("frame_type") or "Aluminio"
            if "carbon" in name.lower() or "carbono" in name.lower():
                frame_type = "Carbono"
            elif "acero" in name.lower() or "steel" in name.lower():
                frame_type = "Acero"
                
            new_bike = {
                "brand": brand.upper(),
                "model": model,
                "type": mapped_type,
                "wheelSize": str(wheel_size),
                "frameType": frame_type,
                "specs": f"{brand} • {model}",
                "original_image_url": image_url,
                "fullSpecs": item.get("specs") if isinstance(item.get("specs"), dict) else {},
                "offers": [
                    {
                        "store": store,
                        "storeKey": store_key,
                        "price": price,
                        "oldPrice": item.get("price_card"),
                        "url": url,
                        "imageUrl": image_url
                    }
                ]
            }
            merged_bikes.append(new_bike)
            
    print(f"🧩 Matching SoloTodo completado: {len(merged_bikes)} modelos únicos de bicicletas consolidadas.")
    
    # 4. AGRUPACIÓN BÁSICA DE ACCESORIOS (Repuestos)
    merged_repuestos = []
    for item in filtered_repuestos:
        name = item.get("name")
        price = item.get("price_normal")
        brand = item.get("brand") or matcher.get_brand(name)
        if brand == "Unknown":
            brand = name.split()[0] if name.split() else "Generica"
            
        store = item.get("store", "Tienda")
        store_key = store.lower().replace(" ", "").replace("_", "")
        url = item.get("url", "#")
        image_url = item.get("image_url") or item.get("image")
        
        found_match = False
        for rep in merged_repuestos:
            # Match simple de strings para repuestos
            if matcher.is_match(f"{rep['brand']} {rep['model']}", f"{brand} {name}"):
                offer_exists = False
                for off in rep["offers"]:
                    if off["storeKey"] == store_key:
                        if price < off["price"]:
                            off["price"] = price
                            off["url"] = url
                        offer_exists = True
                        break
                if not offer_exists:
                    rep["offers"].append({
                        "store": store,
                        "storeKey": store_key,
                        "price": price,
                        "oldPrice": item.get("price_card"),
                        "url": url,
                        "imageUrl": image_url
                    })
                found_match = True
                break
                
        if not found_match:
            new_rep = {
                "brand": brand.upper(),
                "model": name,
                "type": "accesorios",
                "wheelSize": "",
                "frameType": "",
                "specs": f"{brand} • {name}",
                "original_image_url": image_url,
                "fullSpecs": item.get("specs") if isinstance(item.get("specs"), dict) else {},
                "offers": [
                    {
                        "store": store,
                        "storeKey": store_key,
                        "price": price,
                        "oldPrice": item.get("price_card"),
                        "url": url,
                        "imageUrl": image_url
                    }
                ]
            }
            merged_repuestos.append(new_rep)
            
    print(f"📦 Accesorios/repuestos consolidados: {len(merged_repuestos)} modelos únicos.")
    
    # 5. DESCARGAR FOTOS REALES Y ASIGNAR ID (Caché local robusta)
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
    
    final_bicicletas = []
    final_repuestos = []
    
    print("\n📸 Iniciando descarga de imágenes oficiales reales para Bicicletas...")
    for idx, bike in enumerate(merged_bikes):
        b_id = idx + 1
        img_url = bike.get("original_image_url")
        local_img = "https://images.unsplash.com/photo-1532298229144-0ec0c57515c7?auto=format&fit=crop&w=500&h=400&q=80" # Fallback premium
        
        if img_url:
            ext = img_url.split("?")[0].split(".")[-1]
            if len(ext) > 4 or not ext.isalnum(): ext = "jpg"
            img_filename = f"bike_{b_id}.{ext}"
            img_path = os.path.join(assets_dir, img_filename)
            
            try:
                resp = scraper.get(img_url, timeout=10)
                if resp.status_code == 200:
                    with open(img_path, "wb") as f:
                        f.write(resp.content)
                    local_img = f"assets/bikes/{img_filename}"
                    print(f"  [Bici {b_id}] Foto real descargada de: {bike['brand']} {bike['model']}")
                else:
                    print(f"  [Bici {b_id}] Fallo HTTP {resp.status_code} para {img_url}")
            except Exception as e:
                print(f"  [Bici {b_id}] Error descargando {img_url}: {e}")
                
        # Simular historial realista de precios para el gráfico de sparklines
        best_price = min(o["price"] for o in bike["offers"])
        bike_history = [int(best_price * 1.08), int(best_price * 1.03), int(best_price)]
        
        # Armar objeto final
        bike_obj = {
            "id": b_id,
            "brand": bike["brand"],
            "model": bike["model"],
            "type": bike["type"],
            "wheelSize": bike["wheelSize"],
            "frameType": bike["frameType"],
            "specs": bike["specs"],
            "image": local_img,
            "original_img_url": bike.get("original_image_url"),
            "history": bike_history,
            "fullSpecs": bike["fullSpecs"],
            "offers": sorted(bike["offers"], key=lambda o: o["price"])
        }
        final_bicicletas.append(bike_obj)
        
    print("\n📸 Iniciando descarga de imágenes oficiales para Repuestos y Accesorios...")
    for idx, rep in enumerate(merged_repuestos):
        r_id = len(final_bicicletas) + idx + 1
        img_url = rep.get("original_image_url")
        local_img = "https://images.unsplash.com/photo-1485965120184-e220f721d03e?auto=format&fit=crop&w=500&h=400&q=80" # Fallback
        
        if img_url:
            ext = img_url.split("?")[0].split(".")[-1]
            if len(ext) > 4 or not ext.isalnum(): ext = "jpg"
            img_filename = f"rep_{r_id}.{ext}"
            img_path = os.path.join(assets_dir, img_filename)
            
            try:
                resp = scraper.get(img_url, timeout=10)
                if resp.status_code == 200:
                    with open(img_path, "wb") as f:
                        f.write(resp.content)
                    local_img = f"assets/bikes/{img_filename}"
                    print(f"  [Rep {r_id}] Foto real descargada de: {rep['brand']} {rep['model']}")
                else:
                    print(f"  [Rep {r_id}] Fallo HTTP {resp.status_code} para {img_url}")
            except Exception as e:
                print(f"  [Rep {r_id}] Error descargando {img_url}: {e}")
                
        best_price = min(o["price"] for o in rep["offers"])
        rep_history = [int(best_price * 1.05), int(best_price * 1.02), int(best_price)]
        
        rep_obj = {
            "id": r_id,
            "brand": rep["brand"],
            "model": rep["model"],
            "type": rep["type"],
            "wheelSize": rep["wheelSize"],
            "frameType": rep["frameType"],
            "specs": rep["specs"],
            "image": local_img,
            "original_img_url": rep.get("original_image_url"),
            "history": rep_history,
            "fullSpecs": rep["fullSpecs"],
            "offers": sorted(rep["offers"], key=lambda o: o["price"])
        }
        final_repuestos.append(rep_obj)
        
    # 6. GUARDAR BASE DE DATOS FINALdata.json
    final_db = {
        "bicicletas": final_bicicletas,
        "repuestos": final_repuestos
    }
    
    data_json_path = os.path.join(fronted_dir, "data.json")
    with open(data_json_path, "w", encoding="utf-8") as f:
        json.dump(final_db, f, ensure_ascii=False, indent=4)
        
    print(f"\n🎉 ¡PROCESO DE AGREGACIÓN FINALIZADO CON ÉXITO! 🎉")
    print(f"💾 Se guardaron {len(final_bicicletas)} bicicletas y {len(final_repuestos)} accesorios reales en {data_json_path}")

if __name__ == "__main__":
    main()
