import json
import os
import re
import sqlite3
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "backend" / "database" / "bicitodo.db"
FRONTEND_DIR = BASE_DIR / "fronted"

UNSUITABLE_IMAGE_MARKERS = (
    "images.unsplash.com",
    "via.placeholder",
    "bike_0.jpg",
    "acc_0.jpg",
    "part_0.jpg",
)

TYPE_RULES = {
    "ciclocomputadores": {
        "types": {"soportes", "otros accesorios", "entrenamiento", "seguridad"},
        "keywords": {"ciclocomputador", "computador", "gps", "garmin", "wahoo", "bryton", "magene", "edge"},
    },
    "sensores": {
        "types": {"otros accesorios", "entrenamiento", "seguridad"},
        "keywords": {"sensor", "cadencia", "velocidad", "pulso", "cardiaca", "cardíaca", "banda", "hrm", "monitor"},
    },
    "radares": {
        "types": {"luces", "seguridad", "otros accesorios"},
        "keywords": {"radar", "trasera", "luz trasera", "nt201", "blinder", "cobber"},
    },
    "luces": {
        "types": {"luces", "seguridad"},
        "keywords": {"luz", "luces", "linterna", "blinder", "ravemen", "cobber", "delantera", "trasera"},
    },
    "bolsos": {
        "types": {"transporte", "fundas", "otros accesorios", "parrillas"},
        "keywords": {"bolso", "bolsa", "alforja", "sillin", "sillín", "cuadro", "manubrio", "mochila", "frame", "tube"},
    },
    "herramientas": {
        "types": {"herramientas", "mantencion", "otros accesorios"},
        "keywords": {"herramienta", "multiherramienta", "llave", "extractor", "torque", "cadena", "calibre", "tool"},
    },
    "bombas": {
        "types": {"inflado", "mantencion", "otros accesorios"},
        "keywords": {"bomba", "inflador", "co2", "aire", "compresor", "psi"},
    },
    "tpu": {
        "types": {"neumaticos y camaras", "otros repuestos"},
        "keywords": {"camara", "cámara", "tpu", "tubeless", "valvula", "válvula", "cinta", "tubo"},
    },
    "componentes": {
        "types": {"transmision", "direccion y cockpit", "pedales", "frenos", "motor y caja", "pernos y adaptadores"},
        "keywords": {
            "monoplato", "biela", "bielas", "stem", "tee", "manubrio", "tija", "cassette",
            "transmision", "transmisión", "maneta", "cambio", "plato", "cadena", "eje",
        },
    },
    "ruedas": {
        "types": {"ruedas"},
        "keywords": {"rueda", "ruedas", "wheel", "llanta", "maza", "carbono", "perfil"},
    },
    "sillines": {
        "types": {"sillin y asiento"},
        "keywords": {"sillin", "sillín", "asiento", "saddle", "gel"},
    },
    "lentes": {
        "types": {"vestuario", "proteccion", "otros accesorios"},
        "keywords": {"lente", "lentes", "gafa", "gafas", "anteojo", "fotocromático", "fotocromatico", "polarizado"},
    },
    "ropa": {
        "types": {"vestuario", "calzado", "proteccion"},
        "keywords": {"tricota", "jersey", "calza", "bib", "short", "guante", "chaqueta", "manga", "ropa", "vestuario"},
    },
    "soportes": {
        "types": {"soportes", "otros accesorios"},
        "keywords": {"soporte", "mount", "holder", "telefono", "telÃ©fono", "garmin", "wahoo", "bryton", "manubrio", "silicona"},
    },
}

TYPE_RULES["soportes"]["keywords"] = {
    "soporte", "mount", "holder", "telefono", "celular",
    "garmin", "wahoo", "bryton", "manubrio", "silicona",
}


def clean_text(value):
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", text).strip().lower()


def image_is_usable(image):
    if not image or not isinstance(image, str):
        return False
    low = image.lower()
    if any(marker in low for marker in UNSUITABLE_IMAGE_MARKERS):
        return False
    if not image.startswith("assets/"):
        return False
    return (FRONTEND_DIR / image).exists()


def row_text(row):
    parts = [row["brand"], row["model"], row["type"], row["category"]]
    return clean_text(" ".join(str(p or "") for p in parts))


def score_candidate(target_type, product_text, candidate):
    rules = TYPE_RULES[target_type]
    score = 0
    candidate_type = clean_text(candidate["type"])
    candidate_text = candidate["text"]

    if candidate_type in rules["types"]:
        score += 35

    for keyword in rules["keywords"]:
        if has_keyword(candidate_text, keyword):
            score += 12
        if has_keyword(product_text, keyword) and has_keyword(candidate_text, keyword):
            score += 25

    # Small preference for real product photos over huge PNG composites.
    try:
        size = (FRONTEND_DIR / candidate["image"]).stat().st_size
        if 8_000 <= size <= 500_000:
            score += 4
    except OSError:
        pass

    return score


def build_image_pools(cur):
    rows = cur.execute(
        """
        SELECT id, brand, model, category, type, specs, canonical_image
        FROM products
        WHERE COALESCE(is_international, 0) = 0
          AND category IN ('accesorios', 'repuestos')
          AND canonical_image IS NOT NULL
          AND canonical_image != ''
        """
    ).fetchall()

    candidates = []
    for row in rows:
        image = row["canonical_image"]
        if not image_is_usable(image):
            continue
        candidate = dict(row)
        candidate["image"] = image
        candidate["text"] = row_text(row)
        candidates.append(candidate)

    pools = {}
    for target_type in TYPE_RULES:
        scored = []
        probe_text = " ".join(TYPE_RULES[target_type]["keywords"])
        for candidate in candidates:
            score = score_candidate(target_type, probe_text, candidate)
            if score > 0:
                scored.append((score, candidate["id"], candidate["image"], candidate))

        scored.sort(key=lambda item: (-item[0], item[1]))
        unique = []
        seen = set()
        for score, _, image, candidate in scored:
            if image in seen:
                continue
            seen.add(image)
            unique.append({"score": score, "image": image, "text": candidate["text"], "type": candidate["type"]})
            if len(unique) >= 250:
                break
        pools[target_type] = unique

    return pools


def choose_image(product, pools):
    p_type = clean_text(product["type"])
    pool = pools.get(p_type) or []
    if not pool:
        return None

    text = clean_text(f"{product['brand']} {product['model']} {product['type']}")
    product_keywords = specific_keywords_for_product(p_type, text)
    strict_pool = strict_candidates_for_product(p_type, text, pool)
    if strict_pool:
        # If we have a strict sub-type pool, all of them are highly correct.
        # We take up to 8 of them to ensure the best possible variety and return.
        top = strict_pool[:8]
        return top[int(product["id"]) % len(top)]["image"]

    specific_pool = [
        candidate for candidate in pool
        if not product_keywords or any(keyword in candidate["text"] for keyword in product_keywords)
    ]
    if specific_pool:
        pool = specific_pool

    scored = []
    for idx, candidate in enumerate(pool):
        score = candidate["score"]
        for keyword in TYPE_RULES.get(p_type, {}).get("keywords", set()):
            if keyword in text and keyword in candidate["text"]:
                score += 30
        for keyword in product_keywords:
            if keyword in candidate["text"]:
                score += 80
        scored.append((score, idx, candidate["image"]))

    scored.sort(key=lambda item: (-item[0], item[1]))
    if not scored:
        return None
    
    # Filter candidates with a score of at least 70% of the maximum score, up to 8, to ensure both correctness and variety
    max_score = scored[0][0]
    top_candidates = [c for c in scored if c[0] >= max_score * 0.70]
    top = top_candidates[:8]
    return top[int(product["id"]) % len(top)][2]


def specific_keywords_for_product(target_type, product_text):
    checks = {
        "componentes": [
            (("cassette",), {"cassette", "piñon", "piñón", "piñones"}),
            (("monoplato", "plato"), {"monoplato", "plato"}),
            (("biela", "bielas"), {"biela", "bielas", "crank"}),
            (("stem", "tee"), {"stem", "tee", "potencia"}),
            (("manubrio",), {"manubrio", "handlebar"}),
            (("tija", "tubo de asiento"), {"tija", "asiento"}),
            (("maneta", "manetas", "transmisión", "transmision", "desviador", "desviadores"), {"transmision", "transmisión", "cambio", "desviador", "maneta", "shifter"}),
        ],
        "tpu": [
            (("camara", "cámara"), {"camara", "cámara", "tpu"}),
            (("valvula", "válvula"), {"valvula", "válvula"}),
            (("tubeless", "cinta"), {"tubeless", "cinta", "sellante"}),
        ],
        "ropa": [
            (("tricota", "jersey", "manga"), {"tricota", "jersey", "polera", "camiseta", "manga"}),
            (("chaqueta",), {"chaqueta", "cortaviento"}),
            (("bib", "calza", "short"), {"bib", "calza", "short"}),
            (("guante", "guantes"), {"guante", "guantes"}),
        ],
        "bolsos": [
            (("sillin", "sillín"), {"bolso", "sillin", "sillín"}),
            (("cuadro", "frame"), {"bolso", "cuadro", "frame"}),
            (("manubrio", "handlebar"), {"bolso", "manubrio", "handlebar"}),
            (("telefono", "teléfono"), {"bolso", "telefono", "teléfono"}),
        ],
        "ciclocomputadores": [
            (("garmin", "edge"), {"garmin", "edge", "gps", "ciclocomputador", "computador"}),
            (("magene",), {"magene", "gps", "ciclocomputador", "computador"}),
            (("igpsport", "igps"), {"igpsport", "igps", "gps", "ciclocomputador", "computador"}),
            (("gps", "ciclocomputador", "computer"), {"gps", "ciclocomputador", "computador"}),
        ],
        "sensores": [
            (("cardiaca", "cardíaca", "pulso", "hr"), {"cardiaca", "cardíaca", "pulso", "banda", "monitor"}),
            (("cadencia", "velocidad"), {"sensor", "cadencia", "velocidad"}),
        ],
        "radares": [
            (("radar",), {"radar"}),
            (("luz", "trasera"), {"luz", "trasera"}),
        ],
        "ruedas": [
            (("rueda", "ruedas", "wheel"), {"rueda", "ruedas", "llanta", "maza"}),
        ],
        "sillines": [
            (("sillin", "sillín", "asiento"), {"sillin", "sillín", "asiento", "saddle"}),
        ],
        "bombas": [
            (("bomba", "inflador", "compresor"), {"bomba", "inflador", "co2", "aire", "compresor"}),
        ],
        "lentes": [
            (("lente", "lentes", "gafa", "gafas"), {"lente", "lentes", "gafa", "gafas", "anteojo"}),
        ],
        "luces": [
            (("luz", "luces"), {"luz", "luces", "linterna", "delantera", "trasera"}),
        ],
        "soportes": [
            (("garmin", "wahoo", "bryton"), {"soporte", "mount", "garmin", "wahoo", "bryton"}),
            (("telefono", "telÃ©fono"), {"soporte", "telefono", "telÃ©fono", "holder"}),
            (("manubrio",), {"soporte", "manubrio", "mount"}),
        ],
    }

    for triggers, keywords in checks.get(target_type, []):
        if any(has_keyword(product_text, trigger) for trigger in triggers):
            return keywords
    return set()


def has_keyword(text, keyword):
    if " " in keyword:
        return keyword in text
    return bool(re.search(r"\b" + re.escape(keyword) + r"\b", text))


def strict_candidates_for_product(target_type, product_text, pool):
    if target_type == "ropa":
        is_gloves = has_keyword(product_text, "guante") or has_keyword(product_text, "glove")
        is_bottom = any(has_keyword(product_text, w) for w in ("calza", "bib", "pantalon", "malla", "short")) and not any(has_keyword(product_text, w) for w in ("manga", "sleeve", "jersey", "tricota", "polera", "camiseta", "chaqueta", "jacket"))
        is_top = any(has_keyword(product_text, w) for w in ("jersey", "tricota", "polera", "camiseta", "chaqueta", "jacket", "manga", "sleeve", "cortaviento", "windbreaker")) or (not is_gloves and not is_bottom)

        strict = []
        for candidate in pool:
            c_text = candidate["text"]
            c_gloves = has_keyword(c_text, "guante") or has_keyword(c_text, "glove")
            c_bottom = any(has_keyword(c_text, w) for w in ("calza", "bib", "pantalon", "malla", "short")) and not any(has_keyword(c_text, w) for w in ("manga", "sleeve", "jersey", "tricota", "polera", "camiseta", "chaqueta", "jacket"))
            c_top = any(has_keyword(c_text, w) for w in ("jersey", "tricota", "polera", "camiseta", "chaqueta", "jacket", "manga", "sleeve", "cortaviento", "windbreaker")) or (not c_gloves and not c_bottom)

            if is_gloves and c_gloves:
                strict.append(candidate)
            elif is_bottom and c_bottom:
                strict.append(candidate)
            elif is_top and c_top:
                strict.append(candidate)
        
        if strict:
            is_long_sleeve = is_top and any(has_keyword(product_text, w) for w in ("larga", "long", "chaqueta", "jacket", "cortaviento"))
            is_short_sleeve = is_top and not is_long_sleeve

            strict_sub = []
            for candidate in strict:
                c_text = candidate["text"]
                c_long_sleeve = any(has_keyword(c_text, w) for w in ("larga", "long", "chaqueta", "jacket", "cortaviento"))
                
                if is_long_sleeve and c_long_sleeve:
                    strict_sub.append(candidate)
                elif is_short_sleeve and not c_long_sleeve:
                    strict_sub.append(candidate)
            
            if strict_sub:
                return strict_sub
            return strict

    if target_type == "componentes" and has_keyword(product_text, "cassette"):
        strict = [
            candidate for candidate in pool
            if has_keyword(candidate["text"], "cassette") and (has_keyword(candidate["text"], "piñon") or has_keyword(candidate["text"], "piñón") or has_keyword(candidate["text"], "pinon"))
        ]
        if strict:
            return strict

    if target_type == "componentes" and has_keyword(product_text, "monoplato"):
        strict = [candidate for candidate in pool if has_keyword(candidate["text"], "monoplato")]
        if strict:
            return strict

    if target_type == "componentes" and (has_keyword(product_text, "biela") or has_keyword(product_text, "bielas")):
        strict = [candidate for candidate in pool if has_keyword(candidate["text"], "biela") or has_keyword(candidate["text"], "bielas")]
        if strict:
            return strict

    if target_type == "componentes" and any(has_keyword(product_text, w) for w in ("tee", "stem", "potencia")):
        strict = [candidate for candidate in pool if any(has_keyword(candidate["text"], w) for w in ("tee", "stem", "potencia"))]
        if strict:
            return strict

    if target_type == "componentes" and any(has_keyword(product_text, w) for w in ("manubrio", "handlebar")) and not any(has_keyword(product_text, w) for w in ("tee", "stem", "potencia")):
        strict = [
            candidate for candidate in pool 
            if any(has_keyword(candidate["text"], w) for w in ("manubrio", "handlebar"))
            and not any(has_keyword(candidate["text"], w) for w in ("tee", "stem", "potencia"))
        ]
        if strict:
            return strict

    if target_type == "componentes" and any(has_keyword(product_text, w) for w in ("tija", "seatpost", "tubo de asiento")):
        strict = [candidate for candidate in pool if any(has_keyword(candidate["text"], w) for w in ("tija", "seatpost", "tubo de asiento", "tubo de sillin", "tubo de sillín"))]
        if strict:
            return strict

    if target_type == "componentes" and any(has_keyword(product_text, w) for w in ("pedal", "pedales")):
        strict = [candidate for candidate in pool if any(has_keyword(candidate["text"], w) for w in ("pedal", "pedales"))]
        if strict:
            return strict

    if target_type == "componentes" and has_keyword(product_text, "cadena"):
        strict = [candidate for candidate in pool if has_keyword(candidate["text"], "cadena")]
        if strict:
            return strict

    if target_type == "componentes" and any(has_keyword(product_text, w) for w in ("freno", "frenos", "brake")):
        strict = [candidate for candidate in pool if any(has_keyword(candidate["text"], w) for w in ("freno", "frenos", "brake"))]
        if strict:
            return strict

    if target_type == "componentes" and any(has_keyword(product_text, w) for w in ("maneta", "shifter", "cambio", "desviador", "pata")):
        strict = [candidate for candidate in pool if any(has_keyword(candidate["text"], w) for w in ("maneta", "shifter", "cambio", "desviador", "pata"))]
        if strict:
            return strict

    if target_type == "tpu":
        is_chamber = any(has_keyword(product_text, w) for w in ("camara", "cámara", "tpu", "tube"))
        is_valve = any(has_keyword(product_text, w) for w in ("valvula", "válvula", "valve"))
        is_tape = any(has_keyword(product_text, w) for w in ("cinta", "tape", "conversión", "conversion"))
        
        if is_chamber:
            strict = [candidate for candidate in pool if any(has_keyword(candidate["text"], w) for w in ("camara", "cámara", "tpu", "tube"))]
            if strict:
                return strict
        elif is_valve:
            strict = [candidate for candidate in pool if any(has_keyword(candidate["text"], w) for w in ("valvula", "válvula", "valve"))]
            if strict:
                return strict
        elif is_tape:
            strict = [candidate for candidate in pool if any(has_keyword(candidate["text"], w) for w in ("cinta", "tape", "conversión", "conversion", "tubeless"))]
            if strict:
                return strict

    if target_type == "ruedas":
        strict = [
            candidate for candidate in pool
            if (has_keyword(candidate["text"], "rueda") or has_keyword(candidate["text"], "ruedas"))
            and not has_keyword(candidate["text"], "bicicleta")
        ]
        if strict:
            return strict

    if target_type == "soportes" and (has_keyword(product_text, "telefono") or has_keyword(product_text, "celular")):
        strict = [
            candidate for candidate in pool
            if has_keyword(candidate["text"], "celular") or has_keyword(candidate["text"], "telefono") or has_keyword(candidate["text"], "porta celular")
        ]
        if strict:
            return strict

    if target_type == "soportes" and any(has_keyword(product_text, key) for key in ("garmin", "wahoo", "bryton")):
        strict = [
            candidate for candidate in pool
            if any(has_keyword(candidate["text"], key) for key in ("garmin", "wahoo", "bryton"))
            and any(has_keyword(candidate["text"], key) for key in ("soporte", "mount", "adaptador", "montaje"))
            and not has_keyword(candidate["text"], "ciclocomputador")
            and not has_keyword(candidate["text"], "computador")
        ]
        if strict:
            return strict

    return []


def repair_database():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    pools = build_image_pools(cur)
    missing_pools = {key: len(value) for key, value in pools.items() if not value}
    if missing_pools:
        raise RuntimeError(f"No local image candidates for AliExpress types: {missing_pools}")

    ali_rows = cur.execute(
        """
        SELECT p.id, p.brand, p.model, p.type, p.category, p.canonical_image
        FROM products p
        WHERE COALESCE(p.is_international, 0) = 1
        ORDER BY p.id
        """
    ).fetchall()

    updated = 0
    by_type = defaultdict(int)
    for row in ali_rows:
        if row["canonical_image"] and ("assets/bikes/ali_" in row["canonical_image"] or "unsplash.com" in row["canonical_image"] or "alicdn.com" in row["canonical_image"]):
            continue
        image = choose_image(row, pools)
        if not image:
            continue
        if row["canonical_image"] == image:
            continue
        cur.execute("UPDATE products SET canonical_image = ? WHERE id = ?", (image, row["id"]))
        cur.execute("UPDATE store_products SET image_url = ? WHERE product_id = ?", (image, row["id"]))
        updated += 1
        by_type[row["type"]] += 1

    conn.commit()

    remaining_external = cur.execute(
        """
        SELECT COUNT(*)
        FROM products p
        WHERE COALESCE(p.is_international, 0) = 1
          AND (p.canonical_image LIKE 'http%' OR p.canonical_image LIKE '%images.unsplash.com%')
        """
    ).fetchone()[0]

    audit = {
        "updated": updated,
        "total_aliexpress": len(ali_rows),
        "remaining_external_or_unsplash": remaining_external,
        "pool_sizes": {key: len(value) for key, value in pools.items()},
        "updated_by_type": dict(sorted(by_type.items())),
    }
    conn.close()
    return audit


def main():
    print(json.dumps(repair_database(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
