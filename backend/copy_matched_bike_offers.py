import argparse
import json
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "backend" / "database" / "bicitodo.db"
REPORT_PATH = BASE_DIR / "scratch" / "bike_offer_match_report.json"
BACKUP_DIR = BASE_DIR / "backups"


def backup_db():
    BACKUP_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = BACKUP_DIR / f"bicitodo_before_offer_copy_{stamp}.db"
    shutil.copy2(DB_PATH, target)
    return target


def load_source_offers(conn, product_ids):
    placeholders = ",".join("?" for _ in product_ids)
    rows = conn.execute(
        f"""
        SELECT product_id, store_id, url, image_url, price_normal, price_card, stock
        FROM store_products
        WHERE product_id IN ({placeholders})
        ORDER BY price_normal ASC
        """,
        product_ids,
    ).fetchall()

    best_by_store = {}
    for row in rows:
        if row["store_id"] not in best_by_store:
            best_by_store[row["store_id"]] = dict(row)
    return list(best_by_store.values())


def copy_group_offers(conn, group, apply=False):
    inserted = []
    product_ids = group["product_ids"]
    source_offers = load_source_offers(conn, product_ids)

    for target_product_id in product_ids:
        existing_stores = {
            row["store_id"]
            for row in conn.execute(
                "SELECT store_id FROM store_products WHERE product_id = ?",
                (target_product_id,),
            ).fetchall()
        }

        for offer in source_offers:
            if offer["store_id"] in existing_stores:
                continue

            payload = {
                "target_product_id": target_product_id,
                "source_product_id": offer["product_id"],
                "store_id": offer["store_id"],
                "url": offer["url"],
                "price_normal": offer["price_normal"],
            }

            if apply:
                cursor = conn.execute(
                    """
                    INSERT INTO store_products
                        (product_id, store_id, url, image_url, price_normal, price_card, stock)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        target_product_id,
                        offer["store_id"],
                        offer["url"],
                        offer["image_url"],
                        offer["price_normal"],
                        offer["price_card"],
                        offer["stock"] if offer["stock"] is not None else 1,
                    ),
                )
                conn.execute(
                    "INSERT INTO price_history (store_product_id, price) VALUES (?, ?)",
                    (cursor.lastrowid, offer["price_normal"]),
                )
                payload["new_offer_id"] = cursor.lastrowid

            inserted.append(payload)

    return inserted


def main():
    parser = argparse.ArgumentParser(description="Copia ofertas entre bicicletas estrictamente matcheadas.")
    parser.add_argument("--apply", action="store_true", help="Aplica los cambios. Sin esto solo reporta.")
    parser.add_argument("--report", default=str(REPORT_PATH))
    args = parser.parse_args()

    report = json.loads(Path(args.report).read_text(encoding="utf-8"))
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    backup_path = None
    if args.apply:
        backup_path = backup_db()

    planned = []
    for group in report.get("groups", []):
        planned.extend(copy_group_offers(conn, group, apply=args.apply))

    if args.apply:
        conn.commit()
    conn.close()

    result = {
        "mode": "apply" if args.apply else "dry-run",
        "backup": str(backup_path) if backup_path else None,
        "groups": len(report.get("groups", [])),
        "offers_to_copy": len(planned),
        "offers": planned,
    }
    print(json.dumps({k: result[k] for k in ("mode", "backup", "groups", "offers_to_copy")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
