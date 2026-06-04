import json
import re
import unicodedata
from collections import OrderedDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "fronted" / "data.json"

BIKE_TYPES = {"mtb", "ruta", "gravel", "fixie", "urbana", "hibrida", "infantil", "electrica"}

ACCESSORY_KEYWORDS = [
    "porta bicicleta", "portabicicleta", "porta-bicicleta", "porta ", "soporte bicicleta",
    "casco", "helmet", "guante", "glove", "jersey", "polera", "chaqueta",
    "calza", "short", "pantalon", "pantalón", "calcetin", "calcetín",
    "zapatilla", "zapato", "lente", "gafa", "mochila", "bolso", "banano",
    "caramayola", "bidon", "bidón", "botella", "portabotella", "candado",
    "luz", "luces", "bombin", "bombín", "inflador", "rodillera", "codera",
    "protector", "proteccion", "protección", "limpiador", "lubricante",
    "aceite", "sellante", "muc-off", "herramienta", "kit", "bolsa",
    "alforja", "parrilla", "cinta reflectante", "espejo", "candado",
    "gps", "antirrobo", "anti robo", "soporte",
    "silla", "mascota", "correa",
    "tapabarro", "tapabarros",
    "antiparra", "rampa", "silicona", "liquido limpieza", "liquido de limpieza",
    "spray", "mantenimiento", "desengras", "detergente", "pasta ensamblaje",
    "maleta", "cinta de arrastre", "asiento", "jofa", "puno", "puño",
    "punos", "puños", "grasa", "caramagiola",
    "parrilla", "cobertor", "funda", "servicio taller", "collarin",
    "abrazadera", "rodillo",
]

PART_KEYWORDS = [
    "cuadro", "marco", "frameset", "horquilla", "neumatico", "neumático", "neuma", "neumas", "tubeless",
    "cubierta", "camara", "cámara", "cadena", "cassette", "groupset", "grupo ", "pinon", "pinones", "piñon", "piñón",
    "biela", "plato", "volante", "corona", "chainring", "pedal", "freno", "caliper", "disco",
    "rotor", "pastilla", "patin", "patines", "zapata", "zapatas", "cambio trasero", "desviador", "shifter", "manilla",
    "manubrio", "tee ", "tee-", "tija", "dropper", "sillin", "sillín", "asiento", "collarin", "abrazadera", "puno", "puño", "punos", "puños", "grip", "maza",
    "llanta", "rayo", "valvula", "válvula", "eje pasante", "eje delantero", "eje trasero", "adaptador", "cazoleta",
    "bottom bracket", "pressfit", "eje motor", "roldana", "pata de cambio", "puntera", "postiza",
    "suspension", "amortiguador", "shock", "perno", "pernos",
    "rueda", "motor de bicicleta", "motor ", "sellante",
    "enlace", "bieleta",
]

BIKE_MODEL_KEYWORDS = [
    "bicicleta", " e-bike", " ebike", "mountain bike", "road bike",
    "gravel bike", "rockhopper", "stumpjumper", "epic", "chisel", "diverge",
    "tarmac", "allez", "roubaix", "aethos", "spark", "scale", "ransom",
    "status 170", "p.4", "p.2 trail",
    "addict", "foil", "aspect", "marlin", "domane", "emonda", "émonda",
    "madone", "slash", "fuel ex", "procaliber", "precaliber", "speed concept",
    "orbea", "orca", "alma", "occam", "terra", "cervelo", "cérvelo",
    "pinarello", "dogma", "bianchi", "oltre", "cannondale", "supersix",
    "synapse", "santa cruz", "nomad", "bronson", "riverside", "triban",
    "rockrider", "btwin", "van rysel", "marin ", "norco ", "giant ",
]


def norm_text(value):
    value = (value or "").lower()
    value = value.replace("á", "a").replace("é", "e").replace("í", "i")
    value = value.replace("ó", "o").replace("ú", "u").replace("ñ", "n").replace("ń", "n")
    value = "".join(ch for ch in unicodedata.normalize("NFD", value) if unicodedata.category(ch) != "Mn")
    return re.sub(r"\s+", " ", value).strip()


def best_price(product):
    prices = [offer.get("price") for offer in product.get("offers", []) if isinstance(offer.get("price"), int)]
    return min(prices) if prices else 0


def split_concatenated_price(value):
    if not isinstance(value, int) or value <= 30000000:
        return value, None
    digits = str(value)
    candidates = []
    for idx in range(4, len(digits) - 3):
        left = int(digits[:idx])
        right = int(digits[idx:])
        if 3000 <= left <= 30000000 and 3000 <= right <= 30000000 and right >= left and right / max(left, 1) <= 2.5:
            candidates.append((left, right))
    if not candidates:
        return value, None
    return min(candidates, key=lambda pair: (len(str(pair[0])), pair[1] - pair[0]))


def normalize_offer_prices(product):
    for offer in product.get("offers", []):
        price, old_price = split_concatenated_price(offer.get("price"))
        if old_price:
            offer["price"] = price
            offer["oldPrice"] = old_price


def contains_any(text, keywords):
    return any(keyword in text for keyword in keywords)


def is_complete_bicycle(product):
    text = norm_text(f"{product.get('brand', '')} {product.get('model', '')} {product.get('type', '')}")
    model_text = norm_text(product.get("model", ""))
    price = best_price(product)
    complete_bike_phrase = (
        model_text.startswith("bicicleta ")
        or model_text.startswith("pack bicicleta ")
        or model_text.startswith("bicicleta balance ")
        or model_text.startswith("bicicleta sin pedales ")
    )

    if model_text.startswith("cuadro ") or model_text.startswith("marco ") or "frameset" in model_text:
        return False

    if contains_any(text, PART_KEYWORDS) and not complete_bike_phrase:
        return False

    if contains_any(text, ACCESSORY_KEYWORDS):
        if not complete_bike_phrase:
            return False
        if "porta bicicleta" in text or "portabicicleta" in text or "soporte bicicleta" in text:
            return False

    if re.search(r"\bbicicleta\b", text):
        return True

    if contains_any(text, BIKE_MODEL_KEYWORDS) and price >= 90000:
        return True

    return product.get("type") in BIKE_TYPES and price >= 90000 and not contains_any(text, ACCESSORY_KEYWORDS + PART_KEYWORDS)


def classify_bike_type(product):
    text = norm_text(f"{product.get('brand', '')} {product.get('model', '')}")
    if any(k in text for k in ["electrica", "electric", "e-bike", "ebike"]):
        return "electrica"
    if any(k in text for k in ["infantil", "nino", "nina", "kids", "runride", "hotwalk", "precaliber", "aro 12", "aro 16", "aro 20", "aro 24"]):
        return "infantil"
    if any(k in text for k in ["gravel", "cyclocross", "ciclocross", "diverge", "terra"]):
        return "gravel"
    if any(k in text for k in ["fixie", "single speed", "single-speed", "pista"]):
        return "fixie"
    if any(k in text for k in ["hibrida", "hybrid", "riverside"]):
        return "hibrida"
    if any(k in text for k in ["urbana", "urban", "city", "paseo"]):
        return "urbana"
    if any(k in text for k in ["ruta", "road", "triathlon", "triatlon", "addict", "tarmac", "allez", "roubaix", "aethos", "domane", "emonda", "madone", "orca", "dogma", "oltre", "specialissima", "supersix", "synapse", "propel", "tcr advanced", "van rysel", "triban"]):
        return "ruta"
    return "mtb"


def classify_non_bike_category(product):
    text = norm_text(f"{product.get('brand', '')} {product.get('model', '')}")
    
    # 1. Componentes específicos que a veces se confunden
    # Asiento/sillín y puños/grips son repuestos, a menos que sean un bolso o funda para ellos
    if contains_any(text, ["sillin", "sillín", "asiento", "puno", "puño", "punos", "puños", "grip"]):
        if contains_any(text, ["bolso", "bolsa", "alforja", "funda", "cobertor", "cubresillin", "cubresillín"]):
            return "accesorios"
        return "repuestos"
        
    # 2. Palabras clave definitivas de accesorios (tienen prioridad)
    definite_accessories = [
        "casco", "helmet", "rodillera", "codera", "antiparra", "gafa", "lente", "jofa", 
        "pechera", "protector", "proteccion", "protección",
        "jersey", "polera", "chaqueta", "calza", "short", "pantalon", "pantalón", 
        "calcetin", "calcetín", "guante", "glove", "poleron", "polerón", "cortaviento", 
        "vestuario", "ropa", "zapatilla", "zapato", "calzado", "manguilla", "perneras",
        "bolso", "bolsa", "mochila", "alforja", "banano", "maleta", "funda", "cobertor",
        "candado", "antirrobo", "anti robo", "seguridad", "traba", "cable de acero",
        "luz", "luces", "foco led", "reflectante", "reflectantes",
        "caramayola", "caramagiola", "bidon", "bidón", "botella", "portabotella", 
        "porta caramagiola", "porta caramayola",
        "portabicicleta", "porta bicicleta", "portabicicletas", "soporte bicicleta", 
        "rodillo", "entrenamiento", "parrilla", "tapabarro", "tapabarros", "rampa", 
        "soporte de celular", "porta celular", "gps", "ciclocomputador", "soporte",
        "herramienta", "kit herramienta", "llave", "multiherramienta", "bombin", 
        "bombín", "inflador", "bomba de aire", "limpiador", "limpieza", "desengras", 
        "detergente", "grasa", "silicona", "spray", "mantenimiento", "pasta ensamblaje", 
        "muc-off", "peaty", "lubricante", "aceite", "sellante"
    ]
    
    # 3. Palabras clave definitivas de repuestos
    definite_parts = [
        "cuadro", "marco", "frameset", "horquilla", "neumatico", "neumático", "neuma",
        "neumas", "cubierta", "camara", "cámara", "cadena", "cassette",
        "groupset", "grupo ", "pinon", "pinones", "piñon", "piñón", "biela", "plato",
        "volante", "corona", "chainring", "pedal", "pedales", "freno", "caliper", "disco", "rotor",
        "pastilla", "patin", "patines", "zapata", "zapatas", "cambio trasero", "desviador",
        "shifter", "manilla", "manubrio", "tee ", "tee-", "stem", "tija", "dropper", 
        "collarin", "abrazadera", "maza", "llanta", "rayo", "valvula", "válvula", "eje pasante",
        "eje delantero", "eje trasero", "cazoleta", "bottom bracket", "pressfit",
        "eje motor", "roldana", "pata de cambio", "puntera", "postiza", "suspension",
        "amortiguador", "shock", "rueda", "ruedas", "motor ", "bieleta", "enlace", "calapies"
    ]

    if contains_any(text, definite_accessories):
        return "accesorios"
        
    if contains_any(text, definite_parts):
        return "repuestos"
        
    return "accesorios"


def classify_accessory_type(product):
    text = norm_text(f"{product.get('brand', '')} {product.get('model', '')}")
    rules = [
        ("cascos", ["casco", "helmet", "jofa"]),
        ("vestuario", ["jersey", "polera", "chaqueta", "calza", "short", "pantalon", "calcetin", "guante", "glove"]),
        ("calzado", ["zapatilla", "zapato", "calzado"]),
        ("proteccion", ["rodillera", "codera", "protector", "proteccion", "antiparra", "lente", "gafa"]),
        ("hidratacion", ["caramayola", "caramagiola", "bidon", "botella", "portabotella", "porta caramagiola"]),
        ("luces", ["luz", "luces", "reflectante"]),
        ("seguridad", ["candado", "antirrobo", "anti robo"]),
        ("transporte", ["portabicicleta", "porta bicicleta", "rampa", "maleta", "bolso", "mochila", "banano", "alforja"]),
        ("herramientas", ["herramienta", "kit herramienta", "llave", "multiherramienta"]),
        ("inflado", ["bombin", "inflador", "bomba", "inflado"]),
        ("mantencion", ["limpiador", "limpieza", "lubricante", "aceite", "sellante", "desengras", "detergente", "grasa", "silicona", "spray", "mantenimiento", "pasta ensamblaje", "muc-off", "peaty"]),
        ("entrenamiento", ["rodillo", "trainer"]),
        ("soportes", ["soporte", "porta celular", "gps"]),
        ("tapabarros", ["tapabarro", "tapabarros"]),
        ("parrillas", ["parrilla"]),
        ("fundas", ["cobertor", "funda"]),
        ("servicios", ["servicio taller", "mantencion taller", "armando bicicleta"]),
    ]
    for label, keywords in rules:
        if contains_any(text, keywords):
            return label
    return "otros accesorios"


def classify_part_type(product):
    text = norm_text(f"{product.get('brand', '')} {product.get('model', '')}")
    rules = [
        ("neumaticos y camaras", ["neumatico", "cubierta", "camara", "tubeless", "valvula"]),
        ("transmision", ["cadena", "cassette", "groupset", "grupo ", "pinon", "piñon", "biela", "plato", "volante", "corona", "chainring", "cambio trasero", "desviador", "shifter", "roldana", "pata de cambio"]),
        ("frenos", ["freno", "caliper", "disco", "rotor", "pastilla", "patin", "patines", "zapata", "zapatas", "brake"]),
        ("ruedas", ["rueda", "ruedas", "llanta", "maza", "rayo"]),
        ("direccion y cockpit", ["manubrio", "tee ", "tee-", "stem", "direccion", "espaciador", "grip", "puno", "puño"]),
        ("sillin y asiento", ["sillin", "sillín", "asiento", "tija", "dropper", "collarin", "abrazadera"]),
        ("cuadros y horquillas", ["cuadro", "marco", "frameset", "horquilla"]),
        ("motor y caja", ["motor", "bottom bracket", "pressfit", "cazoleta", "eje motor", "bb86", "bsa ", "dub", "t47"]),
        ("suspension", ["suspension", "amortiguador", "shock", "bieleta", "enlace"]),
        ("pedales", ["pedal", "pedales"]),
        ("pernos y adaptadores", ["eje pasante", "eje delantero", "eje trasero", "puntera", "postiza", "adaptador", "perno", "espaciador", "conos"]),
        ("mantencion", ["cepillo", "sellante", "lubricante", "grasa", "limpiador", "muc-off"]),
    ]
    for label, keywords in rules:
        if contains_any(text, keywords):
            return label
    return "otros repuestos"


def product_key(product):
    name = norm_text(f"{product.get('brand', '')} {product.get('model', '')}")
    stores = "|".join(sorted(norm_text(o.get("storeKey") or o.get("store")) for o in product.get("offers", [])))
    return f"{name}|{stores}"


def merge_product(existing, incoming):
    seen = {
        (
            norm_text(o.get("storeKey") or o.get("store")),
            norm_text(o.get("url")),
            o.get("price"),
        )
        for o in existing.get("offers", [])
    }
    for offer in incoming.get("offers", []):
        key = (norm_text(offer.get("storeKey") or offer.get("store")), norm_text(offer.get("url")), offer.get("price"))
        if key not in seen:
            existing.setdefault("offers", []).append(offer)
            seen.add(key)

    if not existing.get("image") and incoming.get("image"):
        existing["image"] = incoming["image"]
    if len(incoming.get("history", [])) > len(existing.get("history", [])):
        existing["history"] = incoming["history"]
    return existing


def main():
    with DATA_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    original_counts = {cat: len(data.get(cat, [])) for cat in ("bicicletas", "accesorios", "repuestos")}
    buckets = {"bicicletas": OrderedDict(), "accesorios": OrderedDict(), "repuestos": OrderedDict()}
    moved = 0
    duplicates = 0

    for original_category in ("bicicletas", "accesorios", "repuestos"):
        for product in data.get(original_category, []):
            normalize_offer_prices(product)
            if is_complete_bicycle(product):
                category = "bicicletas"
                product["type"] = classify_bike_type(product)
            else:
                category = classify_non_bike_category(product)
                product["type"] = classify_part_type(product) if category == "repuestos" else classify_accessory_type(product)

            if category != original_category:
                moved += 1

            key = product_key(product)
            if key in buckets[category]:
                merge_product(buckets[category][key], product)
                duplicates += 1
            else:
                buckets[category][key] = product

    cleaned = {cat: list(items.values()) for cat, items in buckets.items()}
    next_id = 1
    for cat in ("bicicletas", "accesorios", "repuestos"):
        for product in cleaned[cat]:
            product["id"] = next_id
            next_id += 1

    with DATA_PATH.open("w", encoding="utf-8") as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)

    print("Catalog repair complete")
    print("Original:", original_counts)
    print("Cleaned:", {cat: len(cleaned[cat]) for cat in cleaned})
    print("Moved:", moved)
    print("Duplicates merged:", duplicates)


if __name__ == "__main__":
    main()
