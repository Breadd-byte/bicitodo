import argparse
import json
import ssl
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit, urlunsplit
from urllib.request import Request, urlopen

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
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-CL,es;q=0.9,en-US;q=0.8",
}

BAD_MARKERS = ("/search", "search?", "buscar?", "catalogsearch", "listado.mercadolibre")
PROTECTED_STATUSES = {401, 403, 429}


def normalize_url(url):
    if not isinstance(url, str):
        return ""
    url = url.strip()
    if url.startswith("//"):
        url = "https:" + url
    replacements = {
        "https://sparta.cl//": "https://sparta.cl/",
        "https://www.decathlon.cl//": "https://www.decathlon.cl/",
    }
    for old, new in replacements.items():
        url = url.replace(old, new)
    try:
        parts = urlsplit(url)
        path = quote(parts.path, safe="/:%")
        query = quote(parts.query, safe="=&?/%:+,._-")
        url = urlunsplit((parts.scheme, parts.netloc, path, query, parts.fragment))
    except Exception:
        pass
    return url


def generic_or_malformed(url):
    low = url.lower()
    if not low.startswith(("http://", "https://")):
        return True
    return any(marker in low for marker in BAD_MARKERS)


def validate_url(url, timeout):
    url = normalize_url(url)
    if generic_or_malformed(url):
        return {"url": url, "valid": False, "reason": "generic_or_malformed"}
    try:
        req = Request(url, headers=HEADERS, method="GET")
        context = ssl.create_default_context()
        with urlopen(req, timeout=timeout, context=context) as response:
            status = response.status
            final_url = response.geturl()
            if any(marker in final_url.lower() for marker in BAD_MARKERS):
                return {"url": url, "valid": False, "status": status, "final_url": final_url, "reason": "redirected_to_search"}
            return {"url": url, "valid": 200 <= status < 400, "status": status, "final_url": final_url}
    except HTTPError as exc:
        if exc.code in PROTECTED_STATUSES:
            return {"url": url, "valid": True, "status": exc.code, "reason": "protected_but_reachable"}
        return {"url": url, "valid": False, "status": exc.code, "reason": "http_error"}
    except URLError as exc:
        return {"url": url, "valid": False, "reason": "url_error", "detail": str(exc.reason)}
    except Exception as exc:
        return {"url": url, "valid": False, "reason": type(exc).__name__, "detail": str(exc)}


def confirmed_invalid(result):
    if not result:
        return False
    if result.get("reason") in {"generic_or_malformed", "redirected_to_search"}:
        return True
    return result.get("reason") == "http_error" and result.get("status") == 404


def main():
    parser = argparse.ArgumentParser(description="Fast URL validation with urllib.")
    parser.add_argument("--workers", type=int, default=24)
    parser.add_argument("--timeout", type=int, default=7)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    with DATA_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    urls = []
    for category in ("bicicletas", "accesorios", "repuestos"):
        for product in data.get(category, []):
            for offer in product.get("offers", []):
                offer["url"] = normalize_url(offer.get("url", ""))
                urls.append(offer["url"])

    unique_urls = list(dict.fromkeys(urls))
    if args.limit:
        unique_urls = unique_urls[:args.limit]

    print(f"Validating {len(unique_urls)} unique URLs", flush=True)
    results = {}
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_map = {executor.submit(validate_url, url, args.timeout): url for url in unique_urls}
        for idx, future in enumerate(as_completed(future_map), 1):
            url = future_map[future]
            results[url] = future.result()
            if idx % 100 == 0:
                invalid = sum(1 for item in results.values() if not item.get("valid"))
                print(f"[{idx}/{len(unique_urls)}] invalid={invalid}", flush=True)

    invalid_urls = {url for url, result in results.items() if not result.get("valid")}
    removable_urls = {url for url, result in results.items() if confirmed_invalid(result)}
    removed_offers = []
    quarantined_products = []

    if args.apply:
        for category in ("bicicletas", "accesorios", "repuestos"):
            kept_products = []
            for product in data.get(category, []):
                valid_offers = []
                for offer in product.get("offers", []):
                    url = offer.get("url", "")
                    if url in removable_urls:
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
                    quarantined_products.append(item)
            data[category] = kept_products

        with DATA_PATH.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        with QUARANTINE_PATH.open("w", encoding="utf-8") as f:
            json.dump(quarantined_products, f, ensure_ascii=False, indent=2)

    report = {
        "total_unique_urls": len(results),
        "invalid_count": len(invalid_urls),
        "removable_invalid_count": len(removable_urls),
        "invalid_urls": [results[url] for url in sorted(invalid_urls)],
        "removed_offers": removed_offers,
        "quarantined_products": quarantined_products,
    }
    with REPORT_PATH.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"Invalid URLs: {len(invalid_urls)}", flush=True)
    print(f"Confirmed removable URLs: {len(removable_urls)}", flush=True)
    if args.apply:
        print(f"Removed offers: {len(removed_offers)}", flush=True)
        print(f"Quarantined products: {len(quarantined_products)}", flush=True)
        print("Visible:", {category: len(data.get(category, [])) for category in ("bicicletas", "accesorios", "repuestos")}, flush=True)
    print(f"Report written to {REPORT_PATH}", flush=True)


if __name__ == "__main__":
    main()
