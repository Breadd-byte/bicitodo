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
    for product in data.get("bicicletas", []):
        if not specs_are_incomplete(product.get("fullSpecs")):
            continue

        bike_type, wheel, specs = generated_bike_specs(generator, product, best_price_from_offers(product))
        product["type"] = bike_type
        product["wheelSize"] = wheel
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
        WHERE p.category = 'bicicletas'
        GROUP BY p.id
        """
    ).fetchall()

    for row in rows:
        if not specs_are_incomplete(row["specs"]):
            continue

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
