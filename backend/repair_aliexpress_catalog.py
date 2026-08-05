import ast
import json
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path
from urllib.parse import urlencode

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = BASE_DIR / "backend"
DB_PATH = BACKEND_DIR / "database" / "bicitodo.db"
IMPORTER_PATH = BACKEND_DIR / "import_aliexpress.py"

ALIEXPRESS_SEARCH_BASE = "https://www.aliexpress.com/w/wholesale-product.html"

VARIATION_SUFFIXES = [
    " Pro Bundle",
    " Team Edition",
    " Carbon Series",
    " Stealth Black",
    " X-Edition",
    " Commuter Pack",
    " Limited Color",
    " Custom Pack",
    " Aero Edition",
    " Signature",
    " Advanced",
    " Ultimate",
    " Extreme",
    " Premium",
    " Master",
    " Expert",
    " Sport",
    " Race",
    " Tour",
    " Lite",
    " Plus",
    " Ultra",
    " Evo",
    " Neo",
    " Max",
    " Comp",
    " Pro",
    " Elite",
]

TYPE_SEARCH_TERMS = {
    "ciclocomputadores": "bike computer gps",
    "sensores": "cycling sensor ant bluetooth",
    "radares": "cycling rear radar light",
    "luces": "bike light bicycle",
    "bolsos": "bike bag bicycle",
    "herramientas": "bike tool bicycle",
    "bombas": "bike pump bicycle",
    "tpu": "tpu inner tube tubeless bicycle",
    "componentes": "bike component bicycle",
    "ruedas": "carbon wheelset bicycle",
    "sillines": "bike saddle bicycle",
    "lentes": "cycling glasses",
    "ropa": "cycling clothing",
    "soportes": "bike mount holder",
}

# These were checked from public search results. Everything else is sent to an
# AliExpress search URL instead of a fabricated /item/ page.
VERIFIED_MATCHES = {
    "geoid cc400 gps": {
        "url": "https://www.aliexpress.com/w/wholesale-product.html?SearchText=GEOID+CC400+GPS",
        "image": "https://ae01.alicdn.com/kf/S1832d50b605a4dbd942b4356edbd010bQ.jpeg",
    },
    "geoid cc600 gps smart": {
        "url": "https://www.aliexpress.com/w/wholesale-product.html?SearchText=GEOID+CC600+GPS+Smart",
        "image": "https://ae01.alicdn.com/kf/S50ea8a52d9b940d58ce1dde5fc452cdau.jpg",
    },
    "geoid cc700 pro gps bundle": {
        "url": "https://www.aliexpress.com/w/wholesale-product.html?SearchText=GEOID+CC700+Pro+GPS+Bundle",
        "image": "https://ae01.alicdn.com/kf/S831bb166c930429e9cd7c38812929e91m.jpg?has_lang=1&ver=1",
    },
    "geoid cc700 color gps": {
        "url": "https://www.aliexpress.com/w/wholesale-product.html?SearchText=GEOID+CC700+Color+GPS",
        "image": "https://ae01.alicdn.com/kf/S4880794fe0ec44f0a0996d27ee3ee86bV.jpg",
    },
    "geoid cc500 gps pro": {
        "url": "https://www.aliexpress.com/w/wholesale-product.html?SearchText=GEOID+CC500+GPS+Pro",
        "image": "https://ae01.alicdn.com/kf/S598b704403b24bda917c238050208483n.jpg",
    },
    "cheji bib shorts de ciclismo pro slim fit": {
        "url": "https://www.aliexpress.com/w/wholesale-product.html?SearchText=Cheji+Bib+Shorts+de+Ciclismo+Pro+Slim+Fit",
        "image": "https://ae01.alicdn.com/kf/HTB16qzfPpXXXXbsXXXXq6xXFXXX0/Blue-Cheji-Cycling-Jerseys-and-Bibs-Set-For-Men-Bicycle-Kits-MTB-Jerseys-And-Bibs-Set.jpg",
    },
    "inbike guantes de ciclismo con gel antigolpes cortos": {
        "url": "https://www.aliexpress.com/w/wholesale-product.html?SearchText=Inbike+Guantes+de+Ciclismo+con+Gel+Antigolpes+Cortos",
        "image": "https://ae01.alicdn.com/kf/HTB1DNCuO4TpK1RjSZR0q6zEwXXaZ/INBIKE-Sport-Gloves-Shockproof-Cycling-Gloves-Touch-Screen-GEL-Riding-MTB-Bike-Glove-Motorcycle-Winter-Autumn.jpg_480x480.jpg",
    },
    "magene s3+ sensor de cadencia y velocidad": {
        "url": "https://www.aliexpress.com/w/wholesale-product.html?SearchText=Magene+S3%2B+Sensor+de+Cadencia+y+Velocidad",
        "image": "assets/bikes/acc_e08554081002.jpg",
    },
    "ridenow camara tpu superlight road 700c": {
        "url": "https://www.aliexpress.com/w/wholesale-product.html?SearchText=RideNow+Camara+TPU+Superlight+Road+700c",
        "image": "assets/bikes/part_da4cacc1b8a8.webp",
    },
    "rockbros luz delantera 400lm recargable usb": {
        "url": "https://www.aliexpress.com/w/wholesale-product.html?SearchText=Rockbros+Luz+Delantera+400LM+Recargable+USB",
        "image": "assets/bikes/prod_105484cdf481_1025.webp",
    },
}

LOCAL_IMAGE_OVERRIDES = {
    "rockbros soporte de manubrio para garmin wahoo bryton": "assets/bikes/acc_fec7a6ceebc0.png",
    "rockbros soporte metalico de telefono para manubrio": "assets/bikes/prod_da6361e7f58a_955.jpg",
    "west biking soporte de silicona elastica de telefono": "assets/bikes/part_ibikes_822876395.jpg",
}


def normalize_text(value):
    text = str(value or "")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def load_templates():
    text = IMPORTER_PATH.read_text(encoding="utf-8")
    module = ast.parse(text)
    templates = []
    for node in module.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "PRODUCT_TEMPLATES" for target in node.targets):
            continue
        templates = ast.literal_eval(node.value)
        break

    by_brand = {}
    for item in templates:
        by_brand.setdefault(normalize_text(item["brand"]), []).append(item)

    for brand_templates in by_brand.values():
        brand_templates.sort(key=lambda item: len(item["model"]), reverse=True)
    return by_brand


def match_template(row, templates_by_brand):
    brand_key = normalize_text(row["brand"])
    model = row["model"] or ""
    model_norm = normalize_text(model)

    for template in templates_by_brand.get(brand_key, []):
        base_norm = normalize_text(template["model"])
        if model_norm == base_norm:
            return template
        if not model_norm.startswith(base_norm + " "):
            continue

        suffix_norm = normalize_text(model[len(template["model"]):])
        known_suffixes = {normalize_text(suffix) for suffix in VARIATION_SUFFIXES}
        if suffix_norm in known_suffixes:
            return template

    return {
        "brand": row["brand"],
        "model": row["model"],
        "type": row["type"],
        "category": row["category"],
    }


def build_query(template):
    brand = template.get("brand") or ""
    model = template.get("model") or ""
    p_type = normalize_text(template.get("type"))
    type_terms = TYPE_SEARCH_TERMS.get(p_type, "cycling bicycle")
    return re.sub(r"\s+", " ", f"{brand} {model} {type_terms}").strip()


def build_search_url(query):
    return f"{ALIEXPRESS_SEARCH_BASE}?{urlencode({'SearchText': query})}"


def verified_key(template):
    return normalize_text(f"{template.get('brand', '')} {template.get('model', '')}")


def is_verified_image(url):
    return isinstance(url, str) and "alicdn.com" in url.lower()


def load_verified_matches():
    matches = dict(VERIFIED_MATCHES)
    cache_path = BASE_DIR / "scratch" / "aliexpress_direct_cache.json"
    if cache_path.exists():
        try:
            with cache_path.open("r", encoding="utf-8") as f:
                cache = json.load(f)
            for key, val in cache.items():
                url = val.get("url")
                if url and "aliexpress.com/item/" in url:
                    img = val.get("local_image") or val.get("image_url")
                    if img:
                        matches[normalize_text(key)] = {
                            "url": url,
                            "image": img
                        }
        except Exception as e:
            print(f"Error loading cache in repair catalog: {e}")
    return matches


def repair_database(db_path=DB_PATH):
    templates_by_brand = load_templates()
    verified_matches_dynamic = load_verified_matches()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    rows = cur.execute(
        """
        SELECT
            p.id,
            p.brand,
            p.model,
            p.category,
            p.type,
            p.canonical_image,
            sp.id AS offer_id,
            sp.url,
            sp.image_url
        FROM products p
        JOIN store_products sp ON sp.product_id = p.id
        JOIN stores s ON s.id = sp.store_id
        WHERE COALESCE(p.is_international, 0) = 1
          AND LOWER(s.name) = 'aliexpress'
        ORDER BY p.id
        """
    ).fetchall()

    updated_urls = 0
    verified_images = 0
    search_urls = 0
    direct_urls = 0
    verified_product_ids = set()
    local_image_overrides = 0

    for row in rows:
        # Conservative policy: never invent a product/image association from
        # a search result. Existing direct item pages stay active; every other
        # offer remains stored but quarantined until a verified direct listing
        # and its matching image are supplied.
        current_url = str(row["url"] or "").lower()
        if "aliexpress." in current_url and "/item/" in current_url:
            cur.execute("UPDATE store_products SET stock = 1 WHERE id = ?", (row["offer_id"],))
            direct_urls += 1
        else:
            cur.execute("UPDATE store_products SET stock = 0 WHERE id = ?", (row["offer_id"],))
            search_urls += 1
        continue

        template = match_template(row, templates_by_brand)
        exact_template_match = (
            normalize_text(row["brand"]) == normalize_text(template.get("brand"))
            and normalize_text(row["model"]) == normalize_text(template.get("model"))
        )
        match = verified_matches_dynamic.get(verified_key(template)) if exact_template_match else None

        if match:
            target_url = match["url"]
            target_image = match["image"]
            direct_urls += 1
            if row["canonical_image"] != target_image:
                cur.execute("UPDATE products SET canonical_image = ? WHERE id = ?", (target_image, row["id"]))
            if row["image_url"] != target_image:
                cur.execute("UPDATE store_products SET image_url = ? WHERE id = ?", (target_image, row["offer_id"]))
            verified_images += 1
            verified_product_ids.add(row["id"])
        else:
            target_url = build_search_url(build_query(template))
            search_urls += 1
            target_image = LOCAL_IMAGE_OVERRIDES.get(verified_key(template))
            if target_image:
                if row["canonical_image"] != target_image:
                    cur.execute("UPDATE products SET canonical_image = ? WHERE id = ?", (target_image, row["id"]))
                if row["image_url"] != target_image:
                    cur.execute("UPDATE store_products SET image_url = ? WHERE id = ?", (target_image, row["offer_id"]))
                local_image_overrides += 1

        if row["url"] != target_url:
            cur.execute("UPDATE store_products SET url = ? WHERE id = ?", (target_url, row["offer_id"]))
            updated_urls += 1

    conn.commit()

    fake_item_urls = cur.execute(
        """
        SELECT COUNT(*)
        FROM store_products sp
        JOIN products p ON p.id = sp.product_id
        JOIN stores s ON s.id = sp.store_id
        WHERE COALESCE(p.is_international, 0) = 1
          AND LOWER(s.name) = 'aliexpress'
          AND sp.url LIKE '%/item/1005001234%'
        """
    ).fetchone()[0]

    audit = {
        "international_offers": len(rows),
        "updated_urls": updated_urls,
        "search_urls": search_urls,
        "direct_verified_urls": direct_urls,
        "verified_image_rows": verified_images,
        "verified_image_products": len(verified_product_ids),
        "local_image_overrides": local_image_overrides,
        "remaining_fake_item_urls": fake_item_urls,
    }
    conn.close()
    return audit


def main():
    print(json.dumps(repair_database(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
