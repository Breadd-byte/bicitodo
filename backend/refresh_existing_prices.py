"""
Refresh current prices for existing store_products rows.

This script updates prices in SQLite by URL without rebuilding the catalog.
It is intended for cron/maintenance runs where the product catalog should stay
stable but store prices and last_updated timestamps need to be refreshed.
"""
import argparse
import json
import os
import re
import shutil
import sqlite3
import sys
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

try:
    import cloudscraper
    from bs4 import BeautifulSoup
except ImportError as exc:
    raise SystemExit("Missing dependency: pip install cloudscraper beautifulsoup4 lxml") from exc

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "backend", "database", "bicitodo.db")
BACKUPS_DIR = os.path.join(BASE_DIR, "backups")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json;q=0.8,*/*;q=0.7",
    "Accept-Language": "es-CL,es;q=0.9,en-US;q=0.8",
}

SHOPIFY_STORES = {
    "crossmountain": "https://crossmountain.cl",
    "faucon bikes": "https://fauconbikes.cl",
    "ibikes": "https://ibikes.cl",
    "ds bikes": "https://www.dsbikes.cl",
    "satiro bikes": "https://satirobikes.cl",
}

SKIP_STORES = {"aliexpress"}


def make_scraper():
    return cloudscraper.create_scraper(browser={"browser": "chrome", "platform": "windows", "mobile": False})


def clean_price(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value) if value > 0 else None

    text = str(value).strip().replace("\xa0", " ")
    if not text:
        return None

    numeric = text.replace(" ", "")
    if re.fullmatch(r"\d+(?:\.\d{1,2})?", numeric):
        return int(float(numeric))

    if "," in text and re.search(r",\d{1,2}\b", text):
        text = text.rsplit(",", 1)[0]

    nums = re.sub(r"[^\d]", "", text)
    if not nums:
        return None
    price = int(nums)
    return price if price > 0 else None


def normalize_url(url):
    parsed = urllib.parse.urlparse(str(url or "").strip())
    if not parsed.netloc:
        return ""
    netloc = parsed.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    path = re.sub(r"/+$", "", parsed.path.lower())
    return f"{netloc}{path}"


def canonical_store_name(store_name):
    return " ".join(str(store_name or "").lower().split())


def backup_database():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(DB_PATH)
    os.makedirs(BACKUPS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(BACKUPS_DIR, f"bicitodo_before_price_refresh_{timestamp}.db")
    shutil.copy2(DB_PATH, dest)
    return dest


def load_offers(args):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    where = ["sp.url IS NOT NULL", "sp.url != ''", "sp.url != '#'"]
    params = []

    if args.stores:
        placeholders = ",".join("?" for _ in args.stores)
        where.append(f"LOWER(s.name) IN ({placeholders})")
        params.extend(name.lower() for name in args.stores)

    if args.only_stale_days is not None:
        where.append("date(sp.last_updated) <= date('now', ?)")
        params.append(f"-{int(args.only_stale_days)} days")

    query = f"""
        SELECT
            sp.id,
            sp.url,
            sp.price_normal,
            sp.price_card,
            sp.last_updated,
            s.name AS store_name,
            p.category,
            p.brand,
            p.model
        FROM store_products sp
        JOIN stores s ON s.id = sp.store_id
        JOIN products p ON p.id = sp.product_id
        WHERE {" AND ".join(where)}
        ORDER BY s.name, sp.id
    """
    rows = [dict(row) for row in cursor.execute(query, params).fetchall()]
    conn.close()

    if args.limit:
        rows = rows[: args.limit]
    return rows


def shopify_catalog(domain, max_pages=80):
    scraper = make_scraper()
    prices = {}
    for page in range(1, max_pages + 1):
        url = f"{domain.rstrip('/')}/products.json?limit=250&page={page}"
        try:
            response = scraper.get(url, headers=HEADERS, timeout=20)
            if response.status_code != 200:
                break
            products = response.json().get("products", [])
        except Exception as exc:
            print(f"[WARN] Shopify fetch failed for {url}: {exc}")
            break

        if not products:
            break

        for product in products:
            handle = product.get("handle")
            if not handle:
                continue
            variants = product.get("variants") or []
            candidate_prices = []
            candidate_compares = []
            for variant in variants:
                price = clean_price(variant.get("price"))
                compare = clean_price(variant.get("compare_at_price"))
                if price:
                    candidate_prices.append(price)
                    if compare and compare > price:
                        candidate_compares.append(compare)
            if not candidate_prices:
                continue
            current = min(candidate_prices)
            old_price = max(candidate_compares) if candidate_compares else None
            product_url = f"{domain.rstrip('/')}/products/{handle}"
            prices[normalize_url(product_url)] = (current, old_price)

        if len(products) < 250:
            break
        time.sleep(0.25)
    return prices


def walk_json(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_json(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_json(child)


def price_from_json_ld(soup):
    prices = []
    for script in soup.select('script[type="application/ld+json"]'):
        raw = script.string or script.get_text()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except Exception:
            continue
        for node in walk_json(data):
            node_type = str(node.get("@type", "")).lower()
            if "offer" not in node_type and not {"price", "lowPrice", "highPrice"} & set(node.keys()):
                continue
            for key in ("price", "lowPrice", "highPrice"):
                price = clean_price(node.get(key))
                if price:
                    prices.append(price)
    return min(prices) if prices else None


def price_from_meta(soup):
    selectors = [
        'meta[property="product:price:amount"]',
        'meta[property="og:price:amount"]',
        'meta[name="twitter:data1"]',
        'meta[itemprop="price"]',
    ]
    for selector in selectors:
        tag = soup.select_one(selector)
        price = clean_price(tag.get("content") if tag else None)
        if price:
            return price
    return None


def old_price_from_html(soup, current_price):
    selectors = [
        ".price-old",
        ".old-price",
        ".price--old",
        ".compare-at-price",
        ".was-price",
        ".product-price-old",
        "del",
        "s",
    ]
    candidates = []
    for selector in selectors:
        for tag in soup.select(selector):
            price = clean_price(tag.get_text(" ", strip=True))
            if price and price > current_price:
                candidates.append(price)
    return max(candidates) if candidates else None


def price_from_visible_html(soup):
    selectors = [
        "[data-price]",
        "[data-product-price]",
        ".price_amount",
        ".price-amount",
        ".current-price",
        ".product-price",
        ".product__price",
        ".product-block__price",
        ".price-wrapper .price",
        ".price .money",
        ".money",
        "span.price",
        "[class*=price]",
    ]
    candidates = []
    for selector in selectors:
        for tag in soup.select(selector)[:12]:
            raw = tag.get("data-price") or tag.get("data-product-price") or tag.get_text(" ", strip=True)
            price = clean_price(raw)
            if price and price >= 500:
                candidates.append(price)
        if candidates:
            return min(candidates)
    return None


def fetch_page_price(offer):
    scraper = make_scraper()
    try:
        response = scraper.get(offer["url"], headers=HEADERS, timeout=18, allow_redirects=True)
    except Exception as exc:
        return {**offer, "status": "failed", "error": str(exc)}

    if response.status_code in {404, 410}:
        return {**offer, "status": "gone", "price": None, "old_price": None}
    if response.status_code >= 400:
        return {**offer, "status": "failed", "error": f"HTTP {response.status_code}"}

    soup = BeautifulSoup(response.text, "lxml")
    price = price_from_json_ld(soup) or price_from_meta(soup) or price_from_visible_html(soup)
    if not price:
        return {**offer, "status": "failed", "error": "price not found"}

    old_price = old_price_from_html(soup, price)
    return {**offer, "status": "ok", "price": price, "old_price": old_price}


def collect_live_prices(offers, workers):
    by_id = {}
    remaining = []

    for store_name, domain in SHOPIFY_STORES.items():
        store_offers = [offer for offer in offers if canonical_store_name(offer["store_name"]) == store_name]
        if not store_offers:
            continue
        print(f"[>] Fetching Shopify catalog for {store_name}: {len(store_offers)} local offers")
        catalog = shopify_catalog(domain)
        matched = 0
        for offer in store_offers:
            live = catalog.get(normalize_url(offer["url"]))
            if live:
                price, old_price = live
                by_id[offer["id"]] = {**offer, "status": "ok", "price": price, "old_price": old_price}
                matched += 1
            else:
                remaining.append(offer)
        print(f"    Matched {matched}/{len(store_offers)} from catalog")

    shopify_store_names = set(SHOPIFY_STORES)
    for offer in offers:
        if offer["id"] in by_id:
            continue
        store_key = canonical_store_name(offer["store_name"])
        if store_key in shopify_store_names:
            continue
        if store_key in SKIP_STORES:
            by_id[offer["id"]] = {**offer, "status": "skipped", "error": "store skipped"}
            continue
        remaining.append(offer)

    unique_remaining = {offer["id"]: offer for offer in remaining}.values()
    remaining = list(unique_remaining)
    if remaining:
        print(f"[>] Fetching product pages for {len(remaining)} offers")
        with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
            futures = {executor.submit(fetch_page_price, offer): offer for offer in remaining}
            for idx, future in enumerate(as_completed(futures), 1):
                result = future.result()
                by_id[result["id"]] = result
                if idx % 100 == 0:
                    print(f"    Product pages checked: {idx}/{len(remaining)}")

    return [by_id[offer["id"]] for offer in offers if offer["id"] in by_id]


def apply_results(results, dry_run):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    summary = {}
    changed = 0
    refreshed = 0
    failed = 0
    skipped = 0
    gone = 0

    for result in results:
        store = result["store_name"]
        summary.setdefault(store, {"ok": 0, "changed": 0, "failed": 0, "skipped": 0, "gone": 0})
        status = result["status"]

        if status == "skipped":
            skipped += 1
            summary[store]["skipped"] += 1
            continue
        if status == "gone":
            gone += 1
            summary[store]["gone"] += 1
            if not dry_run:
                cursor.execute("UPDATE store_products SET stock = 0, last_updated = datetime('now') WHERE id = ?", (result["id"],))
            continue
        if status != "ok":
            failed += 1
            summary[store]["failed"] += 1
            continue

        old_price = result["old_price"] if result["old_price"] and result["old_price"] > result["price"] else None
        price_changed = result["price"] != result["price_normal"]
        old_price_changed = old_price != result["price_card"]

        refreshed += 1
        summary[store]["ok"] += 1
        if price_changed or old_price_changed:
            changed += 1
            summary[store]["changed"] += 1

        if dry_run:
            continue

        cursor.execute(
            """
            UPDATE store_products
            SET price_normal = ?, price_card = ?, stock = 1, last_updated = datetime('now')
            WHERE id = ?
            """,
            (result["price"], old_price, result["id"]),
        )
        if price_changed:
            cursor.execute(
                "INSERT INTO price_history (store_product_id, price) VALUES (?, ?)",
                (result["id"], result["price"]),
            )

    if not dry_run:
        cursor.execute(
            """
            UPDATE stores
            SET last_scrape = datetime('now')
            WHERE id IN (
                SELECT DISTINCT store_id
                FROM store_products
                WHERE date(last_updated) = date('now')
            )
            """
        )
        conn.commit()
    conn.close()

    return {
        "refreshed": refreshed,
        "changed": changed,
        "failed": failed,
        "skipped": skipped,
        "gone": gone,
        "by_store": summary,
    }


def main():
    parser = argparse.ArgumentParser(description="Refresh existing BiciTodo offer prices in SQLite.")
    parser.add_argument("--dry-run", action="store_true", help="Do not write changes.")
    parser.add_argument("--limit", type=int, default=0, help="Limit offers for testing.")
    parser.add_argument("--workers", type=int, default=8, help="Concurrent product page fetches.")
    parser.add_argument("--stores", nargs="*", help="Restrict to exact store names.")
    parser.add_argument("--only-stale-days", type=int, default=None, help="Only rows older than N days.")
    parser.add_argument("--no-backup", action="store_true", help="Skip DB backup before writing.")
    args = parser.parse_args()

    offers = load_offers(args)
    print(f"[>] Offers selected: {len(offers)}")
    if not offers:
        return

    if not args.dry_run and not args.no_backup:
        backup_path = backup_database()
        print(f"[>] Backup created: {backup_path}")

    started = time.time()
    results = collect_live_prices(offers, args.workers)
    report = apply_results(results, args.dry_run)
    report["seconds"] = round(time.time() - started, 2)
    report["mode"] = "dry-run" if args.dry_run else "apply"

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
