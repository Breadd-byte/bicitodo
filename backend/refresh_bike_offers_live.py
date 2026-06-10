import argparse
import importlib
import json
import sqlite3
import sys
import time
import urllib.parse
from collections import defaultdict
from pathlib import Path

from match_bike_offers import DB_PATH, clean_model_tokens, infer_type, load_bikes, model_signature

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parents[1]
SCRAPER_DIR = BASE_DIR / "backend" / "scrapers" / "bicycles"
LIVE_REPORT_PATH = BASE_DIR / "scratch" / "bike_live_offer_report.json"

STORE_MODULES = [
    ("ibikes", "iBikes"),
    ("satiro", "Satiro Bikes"),
    ("faucon", "Faucon Bikes"),
    ("dsbikes", "DS Bikes"),
    ("crossmountain", "CrossMountain"),
    ("copenhague", "Copenhague"),
    ("fullbike", "Full Bike"),
    ("vidaurre", "Vidaurre Bikes"),
    ("decathlon", "Decathlon"),
    ("oxford", "Oxford Store"),
    ("sparta", "Sparta"),
    ("totem", "Totem Chile"),
    ("trek", "Trek Chile"),
    ("specialized", "Specialized Chile"),
]


def clean_text(value):
    return " ".join(str(value or "").split())


def clean_price(value):
    import re

    nums = re.sub(r"[^\d]", "", str(value or ""))
    return int(nums) if nums else None


def item_to_match_row(item):
    name = clean_text(item.get("name"))
    brand = clean_text(item.get("brand"))
    if not brand or brand.lower() in {"generica", "genérica"}:
        tokens = clean_model_tokens(name)
        brand = tokens[0].title() if tokens else ""

    model = clean_text(item.get("model")) or name
    row = {
        "id": None,
        "brand": brand,
        "model": model,
        "type": clean_text(item.get("type")) or "",
        "wheel_size": clean_text(item.get("wheel_size")) or "",
        "frame_type": clean_text(item.get("frame_type")) or "",
        "specs": json.dumps(item.get("specs") or {}, ensure_ascii=False) if isinstance(item.get("specs"), dict) else "",
        "store": clean_text(item.get("store")),
        "store_id": None,
        "price_normal": clean_price(item.get("price_normal")),
        "price_card": clean_price(item.get("price_card")),
        "url": clean_text(item.get("url")),
        "image_url": clean_text(item.get("image_url")),
    }
    row["match_type"] = infer_type(row)
    row["match_wheel"] = row["wheel_size"]
    row["signature"] = model_signature(row)
    return row


def load_existing_index(conn):
    bikes = load_bikes(conn)
    by_signature = defaultdict(list)
    store_names_by_product = defaultdict(set)
    for bike in bikes:
        signature = bike.get("signature")
        if signature:
            by_signature[signature["key"]].append(bike)
        store_names_by_product[bike["id"]].add(bike["store"].lower())
    return by_signature, store_names_by_product


def get_store_id(conn, store_name, url):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM stores WHERE LOWER(name) = LOWER(?)", (store_name,))
    row = cursor.fetchone()
    if row:
        return row[0]
    parsed = urllib.parse.urlparse(url)
    store_url = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else ""
    cursor.execute("INSERT INTO stores (name, url) VALUES (?, ?)", (store_name, store_url))
    return cursor.lastrowid


def scrape_store(module_key):
    sys.path.insert(0, str(BASE_DIR / "backend"))
    module = importlib.import_module(f"scrapers.bicycles.{module_key}")
    return module.scrape()


def choose_product(existing_rows):
    return sorted(existing_rows, key=lambda row: (row["price_normal"] or 10**18, row["id"]))[0]


def apply_offer(conn, product_id, row):
    cursor = conn.cursor()
    store_id = get_store_id(conn, row["store"], row["url"])
    cursor.execute("SELECT id, price_normal FROM store_products WHERE url = ?", (row["url"],))
    existing_by_url = cursor.fetchone()
    if existing_by_url:
        offer_id, old_price = existing_by_url
        cursor.execute(
            """
            UPDATE store_products
            SET product_id = ?, store_id = ?, image_url = ?, price_normal = ?,
                price_card = ?, stock = 1, last_updated = datetime('now')
            WHERE id = ?
            """,
            (product_id, store_id, row["image_url"], row["price_normal"], row["price_card"], offer_id),
        )
        if old_price != row["price_normal"]:
            cursor.execute("INSERT INTO price_history (store_product_id, price) VALUES (?, ?)", (offer_id, row["price_normal"]))
        return "updated"

    cursor.execute(
        """
        INSERT INTO store_products (product_id, store_id, url, image_url, price_normal, price_card, stock)
        VALUES (?, ?, ?, ?, ?, ?, 1)
        """,
        (product_id, store_id, row["url"], row["image_url"], row["price_normal"], row["price_card"]),
    )
    offer_id = cursor.lastrowid
    cursor.execute("INSERT INTO price_history (store_product_id, price) VALUES (?, ?)", (offer_id, row["price_normal"]))
    return "inserted"


def main():
    parser = argparse.ArgumentParser(description="Refuerza ofertas de bicicletas existentes sin crear productos nuevos.")
    parser.add_argument("--stores", nargs="*", default=[key for key, _ in STORE_MODULES], help="Keys de tiendas a revisar.")
    parser.add_argument("--apply", action="store_true", help="Aplica inserciones/actualizaciones en SQLite.")
    parser.add_argument("--report", default=str(LIVE_REPORT_PATH))
    parser.add_argument("--limit-per-store", type=int, default=0)
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    by_signature, store_names_by_product = load_existing_index(conn)

    summary = []
    matches = []
    actions = {"inserted": 0, "updated": 0}

    for key in args.stores:
        started = time.time()
        try:
            scraped = scrape_store(key)
            if args.limit_per_store:
                scraped = scraped[:args.limit_per_store]
        except Exception as exc:
            summary.append({"store_key": key, "status": "failed", "count": 0, "matched": 0, "error": str(exc)})
            continue

        matched_count = 0
        for item in scraped:
            row = item_to_match_row(item)
            if not row["signature"] or not row["price_normal"] or not row["url"] or not row["store"]:
                continue

            candidates = by_signature.get(row["signature"]["key"], [])
            if not candidates:
                continue

            canonical = choose_product(candidates)
            if row["store"].lower() in store_names_by_product[canonical["id"]]:
                continue

            matched_count += 1
            match = {
                "action": "would_insert" if not args.apply else "pending",
                "product_id": canonical["id"],
                "signature": row["signature"],
                "existing_model": canonical["model"],
                "existing_store": canonical["store"],
                "new_store": row["store"],
                "new_model": row["model"],
                "price": row["price_normal"],
                "url": row["url"],
            }
            if args.apply:
                action = apply_offer(conn, canonical["id"], row)
                actions[action] += 1
                match["action"] = action
                store_names_by_product[canonical["id"]].add(row["store"].lower())
            matches.append(match)

        summary.append({
            "store_key": key,
            "status": "ok",
            "count": len(scraped),
            "matched": matched_count,
            "seconds": round(time.time() - started, 2),
        })
        time.sleep(0.5)

    if args.apply:
        conn.commit()
    conn.close()

    report = {
        "mode": "apply" if args.apply else "dry-run",
        "summary": summary,
        "actions": actions,
        "matches_count": len(matches),
        "matches": matches,
    }

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("mode", "actions", "matches_count")}, ensure_ascii=False, indent=2))
    print(f"Report written to {report_path}")


if __name__ == "__main__":
    main()
