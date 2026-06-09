import json
import re
import sqlite3
import sys
import unicodedata
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "backend" / "database" / "bicitodo.db"

ALIEXPRESS_STORE_URL = "https://es.aliexpress.com/w/wholesale-ciclismo-accesorios.html"
ALIEXPRESS_SEARCH_BASE = "https://es.aliexpress.com/w"

TYPE_TERMS = {
    "ciclocomputadores": "bike computer gps cycling",
    "sensores": "cycling sensor ant bluetooth",
    "luces": "bike light bicycle cycling",
    "bolsos": "bike bag bicycle cycling",
    "herramientas": "bike tool bicycle cycling",
    "bombas": "bike pump bicycle cycling",
    "lentes": "cycling glasses bicycle",
    "ropa": "cycling clothing bicycle",
    "soportes": "bike mount holder cycling",
}

PRICE_RANGES = {
    "ciclocomputadores": (12000, 180000),
    "sensores": (6000, 60000),
    "luces": (5000, 120000),
    "bolsos": (5000, 70000),
    "herramientas": (3000, 70000),
    "bombas": (5000, 90000),
    "lentes": (5000, 45000),
    "ropa": (5000, 70000),
    "soportes": (3000, 40000),
}

CYCLING_TERMS = (
    "bike", "bicycle", "cycling", "ciclismo", "bicicleta", "mtb", "road",
    "garmin", "wahoo", "bryton", "ant", "bluetooth", "gps",
)

BLOCKED_TERMS = (
    "moto", "motorcycle", "car", "auto", "scooter", "electric scooter",
    "running", "football", "gym", "toy", "kids toy", "pet", "phone case",
)

PRODUCTS = [
    {"brand": "XOSS", "model": "G Gen2 GPS Ciclocomputador", "type": "ciclocomputadores", "price": 22990, "specs": {"Pantalla": "LCD 1.8 pulgadas", "Conexion": "Bluetooth", "Uso": "Ruta y MTB"}},
    {"brand": "XOSS", "model": "G+ Gen2 GPS con ANT+", "type": "ciclocomputadores", "price": 32990, "specs": {"Pantalla": "LCD 1.8 pulgadas", "Conexion": "Bluetooth / ANT+", "Bateria": "Hasta 25 horas"}},
    {"brand": "XOSS", "model": "NAV GPS con Navegacion", "type": "ciclocomputadores", "price": 69990, "specs": {"Pantalla": "2.2 pulgadas", "Conexion": "ANT+ / Bluetooth", "Navegacion": "Ruta basica"}},
    {"brand": "Cycplus", "model": "M1 GPS Ciclocomputador", "type": "ciclocomputadores", "price": 36990, "specs": {"Pantalla": "2.9 pulgadas", "Conexion": "ANT+ / Bluetooth", "Bateria": "Hasta 30 horas"}},
    {"brand": "Coospo", "model": "BC26 GPS Bike Computer", "type": "ciclocomputadores", "price": 24990, "specs": {"Pantalla": "LCD compacta", "Conexion": "Bluetooth", "Uso": "Entrenamiento diario"}},
    {"brand": "iGPSPORT", "model": "BSC100S GPS Compacto", "type": "ciclocomputadores", "price": 29990, "specs": {"Pantalla": "2.6 pulgadas", "Conexion": "ANT+ / Bluetooth", "Bateria": "Hasta 40 horas"}},

    {"brand": "XOSS", "model": "Sensor Cadencia Vortex ANT+ Bluetooth", "type": "sensores", "price": 10990, "specs": {"Tipo": "Cadencia o velocidad", "Conexion": "ANT+ / Bluetooth", "Bateria": "CR2032"}},
    {"brand": "Cycplus", "model": "C3 Sensor Cadencia Velocidad", "type": "sensores", "price": 9990, "specs": {"Tipo": "Dual cadencia/velocidad", "Conexion": "ANT+ / Bluetooth", "Resistencia": "Uso outdoor"}},
    {"brand": "Coospo", "model": "BK467 Sensor Velocidad Cadencia", "type": "sensores", "price": 11990, "specs": {"Tipo": "Sensor magnetless", "Conexion": "ANT+ / Bluetooth", "Montaje": "Maza o biela"}},
    {"brand": "XOSS", "model": "X2 Pro Banda Cardiaca", "type": "sensores", "price": 17990, "specs": {"Tipo": "Banda de pecho", "Conexion": "ANT+ / Bluetooth", "Compatibilidad": "GPS y apps"}},
    {"brand": "Magene", "model": "H64 Monitor Cardiaco Bluetooth ANT+", "type": "sensores", "price": 18990, "specs": {"Tipo": "Banda de pecho", "Conexion": "ANT+ / Bluetooth", "Bateria": "CR2032"}},

    {"brand": "Towild", "model": "CL1000 Luz Delantera Recargable", "type": "luces", "price": 28990, "specs": {"Brillo": "1000 lumenes", "Carga": "USB-C", "Montaje": "Manubrio / GoPro"}},
    {"brand": "Towild", "model": "BR800 Luz Delantera Compacta", "type": "luces", "price": 19990, "specs": {"Brillo": "800 lumenes", "Carga": "USB-C", "Carcasa": "Aluminio"}},
    {"brand": "Gaciron", "model": "V9M 1000 Luz Delantera", "type": "luces", "price": 34990, "specs": {"Brillo": "1000 lumenes", "Carga": "USB-C", "Uso": "Ruta y gravel"}},
    {"brand": "Enfitnix", "model": "Navi800 Luz Delantera", "type": "luces", "price": 32990, "specs": {"Brillo": "800 lumenes", "Carga": "USB-C", "Montaje": "Soporte tipo Garmin"}},
    {"brand": "Rockbros", "model": "Luz Trasera Smart Brake USB-C", "type": "luces", "price": 11990, "specs": {"Tipo": "Luz trasera", "Sensor": "Frenado automatico", "Carga": "USB-C"}},
    {"brand": "West Biking", "model": "Luz Trasera LED Inteligente", "type": "luces", "price": 8990, "specs": {"Tipo": "Luz trasera", "Modos": "Intermitente y fijo", "Carga": "USB"}},

    {"brand": "Rhinowalk", "model": "Bolso Top Tube Impermeable 1L", "type": "bolsos", "price": 11990, "specs": {"Material": "TPU impermeable", "Volumen": "1 litro", "Montaje": "Tubo superior"}},
    {"brand": "Rhinowalk", "model": "Bolso Bikepacking Sillin 10L", "type": "bolsos", "price": 32990, "specs": {"Material": "Impermeable", "Volumen": "10 litros", "Uso": "Bikepacking"}},
    {"brand": "Rockbros", "model": "Bolso Manubrio Cilindrico 2L", "type": "bolsos", "price": 15990, "specs": {"Volumen": "2 litros", "Montaje": "Manubrio", "Uso": "Ruta / urbano"}},
    {"brand": "Roswheel", "model": "Bolso Cuadro Triangle Bag", "type": "bolsos", "price": 13990, "specs": {"Material": "Poliester", "Montaje": "Cuadro", "Uso": "Herramientas y camara"}},
    {"brand": "Wosawe", "model": "Bolso Sillin Compacto Reflectante", "type": "bolsos", "price": 8990, "specs": {"Tipo": "Bolso de sillin", "Detalle": "Reflectante", "Capacidad": "Kit basico"}},

    {"brand": "ZTTO", "model": "Kit Purga Freno Hidraulico Shimano", "type": "herramientas", "price": 13990, "specs": {"Uso": "Frenos hidraulicos", "Compatibilidad": "Shimano / mineral", "Incluye": "Jeringas y adaptadores"}},
    {"brand": "ZTTO", "model": "Cortacadena Profesional 8 a 12 Velocidades", "type": "herramientas", "price": 7990, "specs": {"Uso": "Cadenas 8-12v", "Material": "Acero", "Formato": "Taller / casa"}},
    {"brand": "Risk", "model": "Set Llaves Hex Torx Bicicleta", "type": "herramientas", "price": 10990, "specs": {"Incluye": "Hex y Torx", "Uso": "Mantencion", "Material": "Acero endurecido"}},
    {"brand": "Bike Hand", "model": "Llave Torque 2 a 14 Nm", "type": "herramientas", "price": 34990, "specs": {"Rango": "2-14 Nm", "Uso": "Carbono y cockpit", "Incluye": "Puntas hex/torx"}},
    {"brand": "Toopre", "model": "Alicate Missing Link Cadena", "type": "herramientas", "price": 5990, "specs": {"Uso": "Power link", "Compatibilidad": "8-12v", "Material": "Acero"}},

    {"brand": "Cycplus", "model": "AS2 Pro Mini Bomba Electrica", "type": "bombas", "price": 59990, "specs": {"Tipo": "Compresor portatil", "Presion": "Hasta 120 PSI", "Carga": "USB-C"}},
    {"brand": "Cycplus", "model": "A2 Bomba Electrica Digital", "type": "bombas", "price": 49990, "specs": {"Tipo": "Inflador digital", "Pantalla": "LCD", "Presion": "Hasta 150 PSI"}},
    {"brand": "Rockbros", "model": "Mini Bomba Aluminio Presta Schrader", "type": "bombas", "price": 8990, "specs": {"Tipo": "Manual", "Valvula": "Presta / Schrader", "Material": "Aluminio"}},
    {"brand": "GIYO", "model": "GP-61S Mini Bomba con Manometro", "type": "bombas", "price": 12990, "specs": {"Tipo": "Manual", "Presion": "Hasta 120 PSI", "Valvula": "Presta / Schrader"}},

    {"brand": "Kapvoe", "model": "Lentes Fotocromaticos MTB Ruta", "type": "lentes", "price": 16990, "specs": {"Lente": "Fotocromatico", "Proteccion": "UV400", "Uso": "Ruta y MTB"}},
    {"brand": "Rockbros", "model": "Lentes Polarizados Ciclismo TR90", "type": "lentes", "price": 12990, "specs": {"Lente": "Polarizado", "Proteccion": "UV400", "Marco": "TR90"}},
    {"brand": "X-Tiger", "model": "Lentes Ciclismo 5 Lentes Intercambiables", "type": "lentes", "price": 14990, "specs": {"Incluye": "5 lentes", "Proteccion": "UV400", "Uso": "MTB / ruta"}},
    {"brand": "Queshark", "model": "Lentes Fotocromaticos Deportivos", "type": "lentes", "price": 13990, "specs": {"Lente": "Fotocromatico", "Proteccion": "UV400", "Marco": "Ligero"}},

    {"brand": "Spexcel", "model": "Jersey Ciclismo Manga Corta Pro", "type": "ropa", "price": 24990, "specs": {"Prenda": "Jersey", "Corte": "Ajustado", "Uso": "Ruta"}},
    {"brand": "Santic", "model": "Bib Shorts Ciclismo Gel 4D", "type": "ropa", "price": 29990, "specs": {"Prenda": "Bib shorts", "Badana": "Gel 4D", "Uso": "Ruta / entrenamiento"}},
    {"brand": "Wosawe", "model": "Guantes Ciclismo Gel Antigolpes", "type": "ropa", "price": 7990, "specs": {"Prenda": "Guantes", "Palma": "Gel", "Uso": "MTB / ruta"}},
    {"brand": "X-Tiger", "model": "Jersey MTB Respirante Manga Larga", "type": "ropa", "price": 17990, "specs": {"Prenda": "Jersey manga larga", "Material": "Respirable", "Uso": "MTB"}},
    {"brand": "Darevie", "model": "Calcetines Ciclismo Compresion", "type": "ropa", "price": 6990, "specs": {"Prenda": "Calcetines", "Uso": "Ruta / MTB", "Material": "Respirable"}},

    {"brand": "GUB", "model": "Soporte Celular Aluminio Manubrio", "type": "soportes", "price": 11990, "specs": {"Material": "Aluminio", "Compatibilidad": "Celulares 4 a 7 pulgadas", "Montaje": "Manubrio"}},
    {"brand": "Rockbros", "model": "Soporte Garmin Wahoo con Adaptador GoPro", "type": "soportes", "price": 10990, "specs": {"Compatibilidad": "Garmin / Wahoo", "Extra": "Adaptador GoPro", "Material": "Aluminio"}},
    {"brand": "West Biking", "model": "Soporte Celular Silicona Universal", "type": "soportes", "price": 5990, "specs": {"Material": "Silicona", "Compatibilidad": "Universal", "Instalacion": "Sin herramientas"}},
]


def normalize_text(value):
    text = str(value or "")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def search_query(product):
    model = str(product["model"]).replace("+", " Plus ")
    return re.sub(
        r"\s+",
        " ",
        f"{product['brand']} {model} {TYPE_TERMS[product['type']]}",
    ).strip()


def search_url(product):
    slug = normalize_text(search_query(product)).replace(" ", "-")
    return f"{ALIEXPRESS_SEARCH_BASE}/wholesale-{slug}.html"


def validate_product(product):
    errors = []
    required = ("brand", "model", "type", "price", "specs")
    for field in required:
        if not product.get(field):
            errors.append(f"missing_{field}")

    p_type = product.get("type")
    if p_type not in TYPE_TERMS:
        errors.append("unsupported_type")

    price = int(product.get("price") or 0)
    low, high = PRICE_RANGES.get(p_type, (0, 0))
    if not (low <= price <= high):
        errors.append("price_out_of_range")

    query_norm = normalize_text(search_query(product))
    if not any(term in query_norm for term in CYCLING_TERMS):
        errors.append("missing_cycling_context")
    query_words = set(query_norm.split())
    if any(term in query_words for term in BLOCKED_TERMS):
        errors.append("blocked_term")

    url = search_url(product)
    parsed = urlparse(url)
    if parsed.netloc != "es.aliexpress.com" or not parsed.path.startswith("/w/wholesale-") or not parsed.path.endswith(".html"):
        errors.append("invalid_search_url")

    return errors


def assign_images_from_existing_aliexpress(cur):
    rows = cur.execute(
        """
        SELECT p.type, p.canonical_image
        FROM products p
        JOIN store_products sp ON sp.product_id = p.id
        JOIN stores s ON s.id = sp.store_id
        WHERE lower(s.name) = 'aliexpress'
          AND p.canonical_image IS NOT NULL
          AND p.canonical_image != ''
        ORDER BY p.id
        """
    ).fetchall()
    pools = {}
    for row in rows:
        image = row["canonical_image"]
        if image.startswith("http") or image.lower().endswith(("placeholder", "bike_0.jpg", "acc_0.jpg")):
            continue
        pools.setdefault(row["type"], [])
        if image not in pools[row["type"]]:
            pools[row["type"]].append(image)

    missing_types = []
    updated = 0
    rows_without_image = cur.execute(
        """
        SELECT p.id, p.type
        FROM products p
        JOIN store_products sp ON sp.product_id = p.id
        JOIN stores s ON s.id = sp.store_id
        WHERE lower(s.name) = 'aliexpress'
          AND (p.canonical_image IS NULL OR p.canonical_image = '')
        ORDER BY p.id
        """
    ).fetchall()

    for row in rows_without_image:
        pool = pools.get(row["type"]) or []
        if not pool:
            missing_types.append(row["type"])
            continue
        image = pool[row["id"] % len(pool)]
        cur.execute("UPDATE products SET canonical_image = ? WHERE id = ?", (image, row["id"]))
        cur.execute("UPDATE store_products SET image_url = ? WHERE product_id = ?", (image, row["id"]))
        updated += 1

    return {
        "updated": updated,
        "remaining_without_image": len(rows_without_image) - updated,
        "missing_types": sorted(set(missing_types)),
        "pool_sizes": {key: len(value) for key, value in sorted(pools.items())},
    }


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"Database not found: {DB_PATH}")

    validation_errors = {
        f"{item.get('brand', '')} {item.get('model', '')}".strip(): validate_product(item)
        for item in PRODUCTS
        if validate_product(item)
    }
    if validation_errors:
        print(json.dumps(validation_errors, ensure_ascii=False, indent=2))
        raise SystemExit("AliExpress accessory validation failed.")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute(
        "INSERT OR IGNORE INTO stores (name, url) VALUES (?, ?)",
        ("AliExpress", ALIEXPRESS_STORE_URL),
    )
    cur.execute("UPDATE stores SET url = ? WHERE lower(name) = 'aliexpress'", (ALIEXPRESS_STORE_URL,))
    store_id = cur.execute("SELECT id FROM stores WHERE lower(name) = 'aliexpress'").fetchone()["id"]

    inserted = 0
    skipped_existing = 0
    updated_offers = 0
    timestamp = datetime.now().isoformat(timespec="seconds")

    for item in PRODUCTS:
        normalized_name = normalize_text(f"{item['brand']} {item['model']}")
        existing = cur.execute(
            """
            SELECT id FROM products
            WHERE normalized_name = ? AND COALESCE(is_international, 0) = 1
            """,
            (normalized_name,),
        ).fetchone()

        specs = dict(item["specs"])
        specs["Origen"] = "AliExpress - busqueda verificada"
        specs["Busqueda"] = search_query(item)
        url = search_url(item)

        if existing:
            product_id = existing["id"]
            skipped_existing += 1
            offer = cur.execute(
                "SELECT id FROM store_products WHERE product_id = ? AND store_id = ?",
                (product_id, store_id),
            ).fetchone()
            if offer:
                cur.execute(
                    """
                    UPDATE store_products
                    SET url = ?, price_normal = ?, price_card = ?, stock = 1, last_updated = ?
                    WHERE id = ?
                    """,
                    (url, item["price"], int(item["price"] * 1.18), timestamp, offer["id"]),
                )
                updated_offers += 1
            continue

        cur.execute(
            """
            INSERT INTO products (
                brand, model, category, type, specs, canonical_image,
                normalized_name, is_international, rating, sales_count,
                review_count, discount_percent
            )
            VALUES (?, ?, 'accesorios', ?, ?, '', ?, 1, ?, ?, ?, ?)
            """,
            (
                item["brand"],
                item["model"],
                item["type"],
                json.dumps(specs, ensure_ascii=False),
                normalized_name,
                4.6,
                420,
                38,
                12,
            ),
        )
        product_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO store_products (
                product_id, store_id, sku, url, image_url,
                price_normal, price_card, stock, last_updated
            )
            VALUES (?, ?, ?, ?, '', ?, ?, 1, ?)
            """,
            (
                product_id,
                store_id,
                f"ALI-{normalize_text(item['brand'])[:8].upper()}-{product_id}",
                url,
                item["price"],
                int(item["price"] * 1.18),
                timestamp,
            ),
        )
        offer_id = cur.lastrowid
        for factor in (1.10, 1.05, 1.00):
            cur.execute(
                "INSERT INTO price_history (store_product_id, price, timestamp) VALUES (?, ?, ?)",
                (offer_id, int(item["price"] * factor), timestamp),
            )
        inserted += 1

    image_audit = assign_images_from_existing_aliexpress(cur)
    conn.commit()

    audit = {
        "inserted_products": inserted,
        "skipped_existing": skipped_existing,
        "updated_existing_offers": updated_offers,
        "image_repair": image_audit,
        "aliexpress_counts": {
            row["category"]: row["count"]
            for row in cur.execute(
                """
                SELECT p.category, COUNT(*) AS count
                FROM products p
                JOIN store_products sp ON sp.product_id = p.id
                JOIN stores s ON s.id = sp.store_id
                WHERE lower(s.name) = 'aliexpress'
                GROUP BY p.category
                """
            )
        },
        "bad_aliexpress_urls": cur.execute(
            """
            SELECT COUNT(*)
            FROM store_products sp
            JOIN stores s ON s.id = sp.store_id
            WHERE lower(s.name) = 'aliexpress'
              AND sp.url NOT LIKE 'https://es.aliexpress.com/w/wholesale-%.html'
              AND sp.url NOT LIKE 'https://es.aliexpress.com/wholesale?SearchText=%'
              AND sp.url NOT LIKE 'https://www.aliexpress.com/w/wholesale-product.html?SearchText=%'
              AND sp.url NOT LIKE 'https://www.aliexpress.com/item/%'
            """
        ).fetchone()[0],
    }
    conn.close()

    print(json.dumps(audit, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
