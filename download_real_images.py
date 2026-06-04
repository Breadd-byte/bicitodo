import re
import os
import json
import time
import urllib.request
from duckduckgo_search import DDGS

def get_bike_images():
    assets_dir = "c:/Users/basti/Desktop/bicitodo/fronted/assets/bikes"
    os.makedirs(assets_dir, exist_ok=True)
    
    with open("c:/Users/basti/Desktop/bicitodo/fronted/app.js", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Extraemos id, brand y model
    # pattern: id: 1, brand: 'Oxford', model: 'Everest Aro 29"'
    bikes = re.findall(r"id:\s*(\d+),\s*brand:\s*['\"]([^'\"]+)['\"],\s*model:\s*['\"]([^'\"]+)['\"]", content)
    
    ddgs = DDGS()
    
    for b_id, brand, model in bikes:
        local_path = f"assets/bikes/bike_{b_id}.jpg"
        abs_path = os.path.join(assets_dir, f"bike_{b_id}.jpg")
        
        if os.path.exists(abs_path):
            print(f"Skipping {brand} {model}, already exists.")
            continue
            
        query = f"bicicleta {brand} {model}"
        print(f"Buscando imagen para: {query}")
        
        try:
            results = ddgs.images(query, max_results=3)
            downloaded = False
            for r in results:
                img_url = r.get("image")
                if not img_url: continue
                try:
                    req = urllib.request.Request(img_url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=5) as response, open(abs_path, 'wb') as out_file:
                        out_file.write(response.read())
                    downloaded = True
                    print(f"  -> Descargado: {img_url}")
                    break
                except Exception as e:
                    print(f"  -> Fallo descarga {img_url}: {e}")
            
            if not downloaded:
                print(f"  -> No se pudo descargar imagen para {query}")
        except Exception as e:
            print(f"Error buscando {query}: {e}")
            
        time.sleep(1) # sleep to avoid rate limits

    # Replace URLs in app.js
    import io
    new_content = content
    for b_id, brand, model in bikes:
        # Search for this exact bike block and replace its image
        pattern = r"(id:\s*" + b_id + r",\s*brand:\s*['\"]" + re.escape(brand) + r"['\"],\s*model:\s*['\"]" + re.escape(model) + r"['\"](?:.|\n)*?image:\s*['\"])(http[^'\"]+)(['\"])"
        new_content = re.sub(pattern, r"\g<1>assets/bikes/bike_" + b_id + r".jpg\g<3>", new_content, count=1)
        
    with open("c:/Users/basti/Desktop/bicitodo/fronted/app.js", "w", encoding="utf-8") as f:
        f.write(new_content)
        
    print("Done")

if __name__ == "__main__":
    get_bike_images()
