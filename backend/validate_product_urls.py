import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse

try:
    import cloudscraper
except ImportError as exc:
    raise SystemExit("Missing dependency: cloudscraper") from exc

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "fronted" / "data.json"
REPORT_PATH = BASE_DIR / "scratch" / "url_validation_report.json"
QUARANTINE_PATH = BASE_DIR / "scratch" / "quarantined_invalid_urls.json"

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

BAD_URL_MARKERS = (
    "/search",
    "search?",
    "buscar?",
    "catalogsearch",
    "listado.mercadolibre",
)

scraper = cloudscraper.create_scraper(browser={"browser": "chrome", "platform": "windows", "mobile": False})


def normalize_url(url):
    if not isinstance(url, str):
        return ""
    url = url.strip()
    if url.startswith("//"):
        url = "https:" + url
    url = url.replace("https://sparta.cl//", "https://sparta.cl/")
    url = url.replace("https://www.decathlon.cl//", "https://www.decathlon.cl/")
    return url


def structurally_bad(url):
    low = url.lower()
    if not low.startswith(("http://", "https://")):
        return True
    return any(marker in low for marker in BAD_URL_MARKERS)


def validate_url(url, timeout=6):
    url = normalize_url(url)
    if structurally_bad(url):
        return {"url": url, "valid": False, "status": None, "reason": "generic_or_malformed"}

    try:
        response = scraper.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True, stream=True)
        status = response.status_code
        final_url = response.url
        content_type = response.headers.get("content-type", "")
        response.close()

        if 200 <= status < 400:
            final_low = final_url.lower()
            if any(marker in final_low for marker in BAD_URL_MARKERS):
                return {"url": url, "valid": False, "status": status, "final_url": final_url, "reason": "redirected_to_search"}
            return {"url": url, "valid": True, "status": status, "final_url": final_url, "content_type": content_type}

        # 401/403 can be bot protection on a real product page; keep them but report.
        if status in (401, 403, 429):
            return {"url": url, "valid": True, "status": status, "final_url": final_url, "reason": "protected_but_reachable"}

        return {"url": url, "valid": False, "status": status, "final_url": final_url, "reason": "http_error"}
    except Exception as exc:
        return {"url": url, "valid": False, "status": None, "reason": type(exc).__name__}


def main():
    parser = argparse.ArgumentParser(description="Validate and remove broken product offer URLs.")
    parser.add_argument("--workers", type=int, default=18)
    parser.add_argument("--timeout", type=int, default=6)
    parser.add_argument("--apply", action="store_true", help="Remove invalid offers and quarantine products with no valid offers.")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    with DATA_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    all_urls = {}
    refs = []
    for category in ("bicicletas", "accesorios", "repuestos"):
        for product in data.get(category, []):
            for offer in product.get("offers", []):
                url = normalize_url(offer.get("url"))
                offer["url"] = url
                all_urls[url] = None
                refs.append((category, product.get("id"), url))

    urls = list(all_urls.keys())
    if args.limit:
        urls = urls[:args.limit]

    print(f"Validating {len(urls)} unique URLs ({len(refs)} offer references).", flush=True)
    results = {}
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_map = {executor.submit(validate_url, url, args.timeout): url for url in urls}
        for idx, future in enumerate(as_completed(future_map), start=1):
            url = future_map[future]
            results[url] = future.result()
            if idx % 100 == 0:
                invalid = sum(1 for r in results.values() if not r["valid"])
                print(f"[{idx}/{len(urls)}] invalid={invalid}", flush=True)

    for url in all_urls:
        if url not in results:
            results[url] = validate_url(url, args.timeout)

    invalid_urls = {url for url, result in results.items() if not result["valid"]}
    protected_urls = [r for r in results.values() if r.get("reason") == "protected_but_reachable"]

    quarantined = []
    removed_offers = []
    if args.apply:
        for category in ("bicicletas", "accesorios", "repuestos"):
            kept_products = []
            for product in data.get(category, []):
                valid_offers = []
                for offer in product.get("offers", []):
                    url = normalize_url(offer.get("url"))
                    if url in invalid_urls:
                        removed_offers.append({
                            "category": category,
                            "product_id": product.get("id"),
                            "model": product.get("model"),
                            "store": offer.get("store"),
                            "url": url,
                            "validation": results.get(url),
                        })
                    else:
                        valid_offers.append(offer)

                if valid_offers:
                    product["offers"] = valid_offers
                    kept_products.append(product)
                else:
                    item = dict(product)
                    item["_quarantine_reason"] = "no_valid_product_url"
                    item["_original_category"] = category
                    quarantined.append(item)
            data[category] = kept_products

        with DATA_PATH.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        with QUARANTINE_PATH.open("w", encoding="utf-8") as f:
            json.dump(quarantined, f, ensure_ascii=False, indent=2)

    report = {
        "total_unique_urls": len(results),
        "invalid_count": len(invalid_urls),
        "protected_but_reachable_count": len(protected_urls),
        "removed_offers": removed_offers,
        "quarantined_products": quarantined,
        "results": results,
    }
    with REPORT_PATH.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("URL validation complete", flush=True)
    print(f"Invalid URLs: {len(invalid_urls)}", flush=True)
    print(f"Protected but reachable: {len(protected_urls)}", flush=True)
    if args.apply:
        print(f"Removed offers: {len(removed_offers)}", flush=True)
        print(f"Quarantined products: {len(quarantined)}", flush=True)
        print("Visible:", {category: len(data.get(category, [])) for category in ("bicicletas", "accesorios", "repuestos")}, flush=True)
    print(f"Report written to {REPORT_PATH}", flush=True)


if __name__ == "__main__":
    main()
