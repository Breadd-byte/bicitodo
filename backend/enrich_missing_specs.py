import importlib.util
import json
import os
import sqlite3
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "fronted" / "data.json"
DB_PATH = BASE_DIR / "backend" / "database" / "bicitodo.db"
GENERATOR_PATH = BASE_DIR / "backend" / "generate_bicycle_specs.py"


def load_bike_generator():
    spec = importlib.util.spec_from_file_location("bike_spec_generator", GENERATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def safe_specs(raw):
    if isinstance(raw, dict):
        return {str(k): v for k, v in raw.items() if str(k).strip() and str(v).strip()}
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except Exception:
        return {}
    if not isinstance(parsed, dict):
        return {}
    return {str(k): v for k, v in parsed.items() if str(k).strip() and str(v).strip()}


def generate_accessory_specs(brand, model):
    model_lower = str(model or "").lower()
    brand_upper = str(brand or "Generica").strip().upper()
    
    # 1. Helmet (Casco)
    if any(x in model_lower for x in ["casco", "helm", "helmet"]):
        return {
            "Tipo": "Casco de Ciclismo / Protección",
            "Material": "Poliestireno expandido (EPS) de alta densidad con carcasa de policarbonato (In-Mold)",
            "Ajuste": "Sistema de ruedecilla micrométrica de ajuste occipital y correas regulables",
            "Ventilación": "Canales de flujo de aire integrados para disipación de calor",
            "Certificación": "Certificación de seguridad internacional CE EN1078"
        }
    # 2. Lights (Luces)
    elif any(x in model_lower for x in ["luz", "luces", "foco", "led", "linterna", "faro", "vioo"]):
        return {
            "Tipo": "Luz LED de Ciclismo de Alta Visibilidad",
            "Potencia": "Hasta 150 Lúmenes (delantera) / 50 Lúmenes (trasera) según modo",
            "Batería": "Batería recargable mediante USB (cable de carga incluido)",
            "Autonomía": "Hasta 8 horas en modo intermitente / 4 horas en modo de brillo continuo",
            "Resistencia": "Resistente a salpicaduras de agua y lluvia moderada (IPX4)"
        }
    # 3. Lock (Candado)
    elif any(x in model_lower for x in ["candado", "u-lock", "traba", "cadena de seguridad", "cable de seguridad"]):
        return {
            "Tipo": "Sistema Antirrobo de Alta Seguridad",
            "Material": "Grillete de acero endurecido macizo con recubrimiento de vinilo protector",
            "Mecanismo": "Cierre de doble pasador giratorio a prueba de ganzúas",
            "Accesorios": "Incluye soporte de montaje al cuadro de la bicicleta y 2 llaves codificadas"
        }
    # 4. Pump (Bombin / Inflador)
    elif any(x in model_lower for x in ["bombin", "bombín", "inflador", "infladora", "bomba de aire"]):
        return {
            "Tipo": "Inflador de Alta Presión de Ciclismo",
            "Presión Máxima": "Hasta 120 PSI / 8.3 Bar de inflado rápido",
            "Compatibilidad": "Cabezal de conexión universal compatible con válvulas Presta (delgada) y Schrader (gruesa)",
            "Material": "Cuerpo de aluminio anodizado ligero o acero reforzado"
        }
    # 5. Bag (Bolso / Alforja / Mochila)
    elif any(x in model_lower for x in ["bolso", "bolsa", "alforja", "mochila", "banano", "cartera"]):
        return {
            "Tipo": "Bolso de Transporte / Alforja de Ciclismo",
            "Material": "Poliéster encerado ripstop altamente resistente a la fricción y lluvia",
            "Montaje": "Correas de velcro ajustables de alta sujeción para fijar al sillín, manillar o cuadro",
            "Capacidad": "Compartimento optimizado para multiherramienta, cámara de repuesto y parches"
        }
    # 6. Bottle cage (Portabotella / Portacaramañola)
    elif any(x in model_lower for x in ["portabotella", "portabotellas", "portacaramañola", "portacaramñola"]):
        return {
            "Tipo": "Portabotella / Portacaramañola de Ciclismo",
            "Material": "Aluminio fundido ultra-ligero y flexible o policarbonato reforzado",
            "Peso": "Entre 30g y 45g de peso ultraligero",
            "Fijación": "Compatible con pernos estándar de fijación en cuadros de bicicleta"
        }
    # Fallback
    return {
        "Categoría": "Accesorio de Ciclismo Premium",
        "Compatibilidad": "Universal para todo tipo de bicicletas (MTB, Ruta, Urbana, Gravel)",
        "Material": "Materiales de alta durabilidad y resistencia al desgaste en exteriores",
        "Diseño": "Diseño ergonómico y aerodinámico optimizado para deportistas"
    }

def generate_part_specs(brand, model):
    model_lower = str(model or "").lower()
    brand_upper = str(brand or "Generica").strip().upper()
    
    # 1. Tires (Neumáticos)
    if any(x in model_lower for x in ["neumatico", "neumático", "coraza", "cubierta", "maxxis", "tubeless"]):
        # Extract size
        size = "Universal"
        import re
        m29 = re.search(r'29(?:\s*x\s*\d+(?:\.\d+)?)?', model_lower)
        m27 = re.search(r'27\.5(?:\s*x\s*\d+(?:\.\d+)?)?', model_lower)
        m26 = re.search(r'26(?:\s*x\s*\d+(?:\.\d+)?)?', model_lower)
        m700 = re.search(r'700\s*x\s*\d+c?', model_lower)
        if m29: size = "29\""
        elif m27: size = "27.5\""
        elif m26: size = "26\""
        elif m700: size = m700.group(0).upper()
        
        return {
            "Tipo": "Neumático / Cubierta de Ciclismo de Alto Rendimiento",
            "Medida": size,
            "Compuesto": "Compuesto de goma optimizado para tracción, baja resistencia al rodado y durabilidad",
            "Estructura": "Tubeless Ready (TR) o aro de alambre tradicional según versión",
            "Protección": "Refuerzo lateral contra cortes y pinchazos en flancos"
        }
    # 2. Chains (Cadenas)
    elif any(x in model_lower for x in ["cadena", "cadenas"]):
        speed = "Universal"
        for sp in ["12v", "12 v", "11v", "11 v", "10v", "10 v", "9v", "9 v", "8v", "8 v", "7v", "7 v", "6v", "6 v"]:
            if sp in model_lower:
                speed = sp.replace(" ", "").upper()
                break
        return {
            "Tipo": "Cadena de Transmisión de Alta Precisión",
            "Velocidades": speed,
            "Eslabones": "116 a 126 eslabones reforzados",
            "Conector": "Incluye pin de conexión rápida o eslabón rápido (Quick-Link / PowerLock)",
            "Tratamiento": "Recubrimiento niquelado o cromado de alta resistencia a la corrosión"
        }
    # 3. Cassette (Cassette / Piñón)
    elif any(x in model_lower for x in ["cassette", "casete", "piñon", "piñón", "corona", "volante"]):
        speed = "Universal"
        for sp in ["12v", "12 v", "11v", "11 v", "10v", "10 v", "9v", "9 v", "8v", "8 v", "7v", "7 v", "6v", "6 v"]:
            if sp in model_lower:
                speed = sp.replace(" ", "").upper()
                break
        return {
            "Tipo": "Cassette / Piñón de Transmisión",
            "Velocidades": speed,
            "Material": "Corona de acero cromado de alta resistencia al torque",
            "Compatibilidad": "Núcleo estándar HG Shimano/SRAM o MicroSpline/XD según versión",
            "Rampas": "Perfil de dientes perfilado (Hyperglide/X-Glide) para cambios fluidos y precisos"
        }
    # 4. Pedals (Pedales)
    elif any(x in model_lower for x in ["pedales", "pedal"]):
        pedal_type = "Plataforma"
        if any(x in model_lower for x in ["automatico", "automático", "spd", "clip", "cleats"]):
            pedal_type = "Automático (SPD / Keo)"
        return {
            "Tipo": f"Pedales de Ciclismo tipo {pedal_type}",
            "Material": "Cuerpo de resina reforzada, aluminio extruido o aleación ligera",
            "Eje": "Eje de acero Chromoly de alta resistencia mecanizado en CNC",
            "Rodamientos": "Cartucho de rodamientos sellados de libre mantenimiento",
            "Características": "Tracción antideslizante con pines de agarre o sistema de tensión ajustable"
        }
    # 5. Grips / Tape (Puños / Cinta)
    elif any(x in model_lower for x in ["puño", "puños", "grip", "grips", "cinta manillar", "cinta de manillar"]):
        return {
            "Tipo": "Puños / Cinta de Manillar de Alta Absorción",
            "Material": "Goma kraton de doble densidad, espuma de silicona o poliuretano antideslizante",
            "Espesor": "2.5 mm a 3.0 mm de espesor para excelente amortiguación de vibraciones",
            "Montaje": "Sistema de bloqueo Lock-On de aluminio o adhesivo trasero de gel"
        }
    # 6. Inner Tubes (Cámaras)
    elif any(x in model_lower for x in ["camara", "cámara"]):
        valve = "Universal"
        if "presta" in model_lower: valve = "Presta (delgada)"
        elif "auto" in model_lower or "schrader" in model_lower: valve = "Schrader / Auto (gruesa)"
        return {
            "Tipo": "Cámara de Aire / Tubo Interior",
            "Material": "Caucho butilo de alta elasticidad y retención de aire hermética",
            "Válvula": valve,
            "Espesor de pared": "0.9 mm optimizado para balance entre peso y resistencia a pinchazos"
        }
    # Fallback
    return {
        "Categoría": "Componente / Repuesto de Transmisión Premium",
        "Compatibilidad": "Estándar compatible con componentes del mismo rango e indexación",
        "Material": "Aleación metálica de alta resistencia mecánica y resistencia al desgaste",
        "Recomendación": "Se recomienda la instalación por personal calificado o con herramientas de precisión"
    }

def specs_are_incomplete(specs):
    return len(safe_specs(specs)) < 3


def best_price_from_offers(product, fallback=300000):
    prices = []
    for offer in product.get("offers", []) or []:
        try:
            price = int(offer.get("price") or 0)
        except Exception:
            price = 0
        if price > 0:
            prices.append(price)
    return min(prices) if prices else fallback


def generated_bike_specs(generator, product, price):
    brand = product.get("brand") or "Generica"
    model = product.get("model") or ""
    current_type = product.get("type") or "mtb"
    current_wheel = product.get("wheelSize") or product.get("wheel_size") or "29"
    frame_type = product.get("frameType") or product.get("frame_type") or "Aluminio"
    bike_type, wheel = generator.correct_bike_type_and_wheel(model, current_type, current_wheel)
    specs = generator.generate_specs_for_bike(brand, model, bike_type, wheel, frame_type, price)
    return bike_type, wheel, specs


def enrich_data_json(generator):
    with DATA_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    updated = 0
    # 1. Bicicletas
    for product in data.get("bicicletas", []):
        if not specs_are_incomplete(product.get("fullSpecs")):
            continue
        bike_type, wheel, specs = generated_bike_specs(generator, product, best_price_from_offers(product))
        product["type"] = bike_type
        product["wheelSize"] = wheel
        product["fullSpecs"] = specs
        product["specs"] = f"{product.get('brand', '').strip()} • {product.get('model', '').strip()}".strip(" •")
        updated += 1

    # 2. Accesorios
    for product in data.get("accesorios", []):
        if not specs_are_incomplete(product.get("fullSpecs")):
            continue
        specs = generate_accessory_specs(product.get("brand"), product.get("model"))
        product["fullSpecs"] = specs
        product["specs"] = f"{product.get('brand', '').strip()} • {product.get('model', '').strip()}".strip(" •")
        updated += 1

    # 3. Repuestos
    for product in data.get("repuestos", []):
        if not specs_are_incomplete(product.get("fullSpecs")):
            continue
        specs = generate_part_specs(product.get("brand"), product.get("model"))
        product["fullSpecs"] = specs
        product["specs"] = f"{product.get('brand', '').strip()} • {product.get('model', '').strip()}".strip(" •")
        updated += 1

    if updated:
        with DATA_PATH.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    return updated


def enrich_database(generator):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    updated = 0
    rows = cur.execute(
        """
        SELECT 
            p.id, 
            p.brand, 
            p.model, 
            p.category, 
            p.type, 
            p.wheel_size, 
            p.frame_type, 
            p.specs,
            MIN(sp.price_normal) AS best_price
        FROM products p
        LEFT JOIN store_products sp ON sp.product_id = p.id
        GROUP BY p.id
        """
    ).fetchall()

    for row in rows:
        if not specs_are_incomplete(row["specs"]):
            continue

        cat = row["category"]
        if cat == "bicicletas":
            product = {
                "brand": row["brand"],
                "model": row["model"],
                "type": row["type"],
                "wheelSize": row["wheel_size"],
                "frameType": row["frame_type"],
            }
            price = int(row["best_price"] or 300000)
            bike_type, wheel, specs = generated_bike_specs(generator, product, price)
            cur.execute(
                """
                UPDATE products
                SET specs = ?, type = ?, wheel_size = ?
                WHERE id = ?
                """,
                (json.dumps(specs, ensure_ascii=False), bike_type, wheel, row["id"]),
            )
        elif cat == "accesorios":
            specs = generate_accessory_specs(row["brand"], row["model"])
            cur.execute(
                """
                UPDATE products
                SET specs = ?
                WHERE id = ?
                """,
                (json.dumps(specs, ensure_ascii=False), row["id"]),
            )
        elif cat == "repuestos":
            specs = generate_part_specs(row["brand"], row["model"])
            cur.execute(
                """
                UPDATE products
                SET specs = ?
                WHERE id = ?
                """,
                (json.dumps(specs, ensure_ascii=False), row["id"]),
            )
        updated += 1

    conn.commit()
    conn.close()
    return updated


def audit_database():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    report = {}
    for category in ("bicicletas", "accesorios", "repuestos"):
        total = cur.execute("SELECT COUNT(*) FROM products WHERE category = ?", (category,)).fetchone()[0]
        incomplete = 0
        for row in cur.execute("SELECT specs FROM products WHERE category = ?", (category,)):
            if specs_are_incomplete(row["specs"]):
                incomplete += 1
        report[category] = {"total": total, "incomplete": incomplete}
    conn.close()
    return report


def main():
    if not DATA_PATH.exists():
        raise FileNotFoundError(DATA_PATH)
    if not DB_PATH.exists():
        raise FileNotFoundError(DB_PATH)

    generator = load_bike_generator()
    json_updated = enrich_data_json(generator)
    db_updated = enrich_database(generator)
    print(json.dumps({
        "data_json_updated": json_updated,
        "database_updated": db_updated,
        "database_audit": audit_database(),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
