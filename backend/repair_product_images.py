import argparse
import hashlib
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse

try:
    import cloudscraper
    from bs4 import BeautifulSoup
except ImportError as exc:
    raise SystemExit("Missing dependencies: cloudscraper and beautifulsoup4 are required") from exc

BASE_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = BASE_DIR / "fronted"
DATA_PATH = FRONTEND_DIR / "data.json"
ASSETS_DIR = FRONTEND_DIR / "assets" / "bikes"
REPORT_PATH = BASE_DIR / "scratch" / "image_repair_report.json"

ASSETS_DIR.mkdir(parents=True, exist_ok=True)
REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "es-CL,es;q=0.9,en-US;q=0.8,en;q=0.7",
}

UNTRUSTED_IMAGE_MARKERS = (
    "images.unsplash.com",
    "bike_0.",
    "acc_0.",
    "part_0.",
    "placeholder",
    "no-image",
    "sin-imagen",
)

SHOPIFY_HOST_MARKERS = (
    "fauconbikes.cl",
    "satirobikes.cl",
    "bikeplus.cl",
    "dsbikes.cl",
    "crossmountain.cl",
)

scraper = cloudscraper.create_scraper(browser={"browser": "chrome", "platform": "windows", "mobile": False})


def clean_url(url):
    if not url or not isinstance(url, str):
        return ""
    url = url.strip()
    if url.startswith("//"):
        url = "https:" + url
    return url


def is_http_url(url):
    return clean_url(url).startswith(("http://", "https://"))


def is_untrusted_image_url(url):
    url = (url or "").lower()
    return not url or any(marker in url for marker in UNTRUSTED_IMAGE_MARKERS)


def local_file_ok(image_path):
    if not image_path or not str(image_path).startswith("assets/"):
        return False
    full_path = FRONTEND_DIR / image_path
    return full_path.exists() and full_path.stat().st_size > 1000


def needs_repair(category, product, force=False):
    if force:
        return True
    image = product.get("image", "")
    if not image:
        return True

    # Category prefix mismatch check
    if category == "accesorios" and ("bike_" in image or "part_" in image):
        return True
    if category == "repuestos" and ("bike_" in image or "acc_" in image):
        return True
    if category == "bicicletas" and ("acc_" in image or "part_" in image):
        return True

    if is_untrusted_image_url(image):
        return True
    if image.startswith("assets/") and not local_file_ok(image):
        return True
    if image.startswith("http"):
        return True
    if image.startswith("http") and is_untrusted_image_url(image):
        return True

    # Mismatched hash verification (re-download if filename doesn't contain expected hash)
    if image.startswith("assets/"):
        import os
        basename = os.path.basename(image)
        name_no_ext = os.path.splitext(basename)[0]
        h_brand_model = hashlib.md5(f"{product.get('brand', '').strip().upper()}_{product.get('model', '').strip().upper()}".encode('utf-8')).hexdigest()[:12]
        h_product = product_hash(product)
        if h_brand_model not in name_no_ext and h_product not in name_no_ext:
            return True

    return False


def image_ext_from_url(url, content_type=""):
    haystack = f"{urlparse(url).path.lower()} {content_type.lower()}"
    if "webp" in haystack:
        return "webp"
    if "png" in haystack:
        return "png"
    if "gif" in haystack:
        return "gif"
    if "jpeg" in haystack or "jpg" in haystack:
        return "jpg"
    return "jpg"


def is_valid_image(content):
    if len(content) < 1000:
        return False
    head = content[:12]
    return (
        head[:3] == b"\xff\xd8\xff"
        or head[:4] == b"\x89PNG"
        or head[:4] == b"RIFF"
        or head[:6] in (b"GIF87a", b"GIF89a")
    )


def product_hash(product):
    key = f"{product.get('id', '')}-{product.get('brand', '')}-{product.get('model', '')}"
    return hashlib.md5(key.encode("utf-8")).hexdigest()[:12]


def category_prefix(category):
    return {"bicicletas": "bike", "accesorios": "acc", "repuestos": "part"}.get(category, "prod")


def fetch_shopify_image(product_url):
    json_url = clean_url(product_url).rstrip("/") + ".json"
    try:
        response = scraper.get(json_url, headers=HEADERS, timeout=12)
        if response.status_code != 200:
            return ""
        product_data = response.json().get("product", {})
        images = product_data.get("images") or []
        if images:
            return clean_url(images[0].get("src", "")).split("?")[0]
    except Exception:
        return ""
    return ""


def fetch_html_image(product_url):
    try:
        response = scraper.get(product_url, headers=HEADERS, timeout=14)
        if response.status_code != 200 or not response.text:
            return ""
        soup = BeautifulSoup(response.text, "lxml")
        selectors = [
            ('meta[property="og:image"]', "content"),
            ('meta[name="og:image"]', "content"),
            ('meta[property="twitter:image"]', "content"),
            ('meta[name="twitter:image"]', "content"),
            (".product-main-image img", "src"),
            (".product__media img", "src"),
            (".product-gallery img", "src"),
            ("img.product-image-photo", "src"),
            ("picture img", "src"),
        ]
        for selector, attr in selectors:
            el = soup.select_one(selector)
            if not el:
                continue
            value = clean_url(el.get(attr, ""))
            if is_http_url(value) and not is_untrusted_image_url(value):
                return value.split("?")[0]
    except Exception:
        return ""
    return ""


def fetch_product_page_image(product):
    offers = sorted(product.get("offers", []), key=lambda offer: offer.get("price") or 10**18)
    for offer in offers:
        product_url = clean_url(offer.get("url", ""))
        if not is_http_url(product_url):
            continue
        host = urlparse(product_url).netloc.lower()
        image_url = ""
        if any(marker in host for marker in SHOPIFY_HOST_MARKERS):
            image_url = fetch_shopify_image(product_url)
        if not image_url:
            image_url = fetch_html_image(product_url)
        if image_url:
            return image_url
    return ""


def image_candidates(product):
    candidates = []
    original = clean_url(product.get("original_img_url", ""))
    if is_http_url(original) and not is_untrusted_image_url(original):
        candidates.append(("original_img_url", original))

    offers = sorted(product.get("offers", []), key=lambda offer: offer.get("price") or 10**18)
    for offer in offers:
        image_url = clean_url(offer.get("imageUrl", ""))
        if is_http_url(image_url) and not is_untrusted_image_url(image_url):
            candidates.append((f"offer:{offer.get('storeKey') or offer.get('store')}", image_url))

    seen = set()
    unique = []
    for source, url in candidates:
        key = url.lower()
        if key not in seen:
            unique.append((source, url))
            seen.add(key)
    return unique


def download_image(url, category, product):
    try:
        response = scraper.get(url, headers=HEADERS, timeout=16)
        if response.status_code != 200 or not is_valid_image(response.content):
            return "", 0
        ext = image_ext_from_url(url, response.headers.get("content-type", ""))
        filename = f"{category_prefix(category)}_real_{product.get('id')}_{product_hash(product)}.{ext}"
        file_path = ASSETS_DIR / filename
        file_path.write_bytes(response.content)
        return f"assets/bikes/{filename}", len(response.content)
    except Exception:
        return "", 0


def repair_one(category, product, force=False):
    old_image = product.get("image", "")
    if not needs_repair(category, product, force=force):
        return product, {
            "id": product.get("id"),
            "category": category,
            "status": "kept",
            "image": old_image,
        }

    candidates = image_candidates(product)
    if not candidates:
        page_image = fetch_product_page_image(product)
        if page_image:
            candidates.append(("product_page", page_image))

    for source, candidate in candidates:
        local_path, size = download_image(candidate, category, product)
        if not local_path:
            continue
        product["image"] = local_path
        product["original_img_url"] = candidate
        for offer in product.get("offers", []):
            if not is_http_url(offer.get("imageUrl", "")) or is_untrusted_image_url(offer.get("imageUrl", "")):
                offer["imageUrl"] = candidate
        return product, {
            "id": product.get("id"),
            "category": category,
            "status": "updated",
            "source": source,
            "old_image": old_image,
            "new_image": local_path,
            "remote": candidate,
            "bytes": size,
            "model": product.get("model", ""),
        }

    return product, {
        "id": product.get("id"),
        "category": category,
        "status": "failed",
        "old_image": old_image,
        "model": product.get("model", ""),
        "offers": [offer.get("url") for offer in product.get("offers", [])],
    }


def audit(data):
    stats = {}
    for category in ("bicicletas", "accesorios", "repuestos"):
        products = data.get(category, [])
        stats[category] = {
            "total": len(products),
            "needs_repair": sum(1 for product in products if needs_repair(category, product)),
            "missing_local": sum(
                1 for product in products
                if str(product.get("image", "")).startswith("assets/") and not local_file_ok(product.get("image", ""))
            ),
            "external_or_placeholder": sum(1 for product in products if is_untrusted_image_url(product.get("image", ""))),
            "has_remote_candidate": sum(1 for product in products if image_candidates(product)),
        }
    return stats


def main():
    parser = argparse.ArgumentParser(description="Repair product images from real store image URLs.")
    parser.add_argument("--force", action="store_true", help="Re-download all product images, not only suspicious ones.")
    parser.add_argument("--workers", type=int, default=14)
    parser.add_argument("--limit", type=int, default=0, help="Optional cap for testing.")
    args = parser.parse_args()

    with DATA_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    before = audit(data)
    print("Image audit before:")
    print(json.dumps(before, ensure_ascii=False, indent=2))

    tasks = []
    for category in ("bicicletas", "accesorios", "repuestos"):
        for idx, product in enumerate(data.get(category, [])):
            if args.force or needs_repair(category, product):
                tasks.append((category, idx, product))

    if args.limit:
        tasks = tasks[:args.limit]

    print(f"Products queued for image repair: {len(tasks)}")
    started = time.time()
    results = []

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_map = {
            executor.submit(repair_one, category, product, args.force): (category, idx)
            for category, idx, product in tasks
        }
        for processed, future in enumerate(as_completed(future_map), start=1):
            category, idx = future_map[future]
            product, result = future.result()
            data[category][idx] = product
            results.append(result)
            if processed % 50 == 0 or result["status"] == "failed":
                counts = {status: sum(1 for r in results if r["status"] == status) for status in ("updated", "kept", "failed")}
                print(f"[{processed}/{len(tasks)}] {counts}")

    with DATA_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    after = audit(data)
    report = {
        "before": before,
        "after": after,
        "results": results,
        "elapsed_seconds": round(time.time() - started, 2),
    }
    with REPORT_PATH.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("Image audit after:")
    print(json.dumps(after, ensure_ascii=False, indent=2))
    print(f"Report written to {REPORT_PATH}")


if __name__ == "__main__":
    main()
