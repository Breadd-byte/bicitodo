import json
from pathlib import Path

from validate_product_urls_fast import normalize_url

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "fronted" / "data.json"
REPORT_PATH = BASE_DIR / "scratch" / "url_validation_report.json"
QUARANTINE_PATH = BASE_DIR / "scratch" / "quarantined_invalid_urls.json"
KEPT_QUARANTINE_PATH = BASE_DIR / "scratch" / "quarantined_confirmed_invalid_urls.json"


def is_confirmed_invalid(validation):
    return validation and validation.get("reason") in {"generic_or_malformed", "redirected_to_search", "http_error"} and validation.get("status") == 404


def main():
    with DATA_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    report = json.load(REPORT_PATH.open(encoding="utf-8")) if REPORT_PATH.exists() else {}
    quarantined = json.load(QUARANTINE_PATH.open(encoding="utf-8")) if QUARANTINE_PATH.exists() else []

    validation_by_url = {item.get("url"): item for item in report.get("invalid_urls", [])}
    restored = []
    confirmed = []

    for product in quarantined:
        offers = product.get("offers", [])
        validations = [validation_by_url.get(offer.get("url")) for offer in offers]
        if validations and all(is_confirmed_invalid(item) for item in validations):
            confirmed.append(product)
            continue

        category = product.get("_original_category") or "accesorios"
        product.pop("_quarantine_reason", None)
        product.pop("_original_category", None)
        for offer in product.get("offers", []):
            offer["url"] = normalize_url(offer.get("url", ""))
        data.setdefault(category, []).append(product)
        restored.append(product)

    for category in ("bicicletas", "accesorios", "repuestos"):
        seen = set()
        unique = []
        for product in data.get(category, []):
            key = product.get("id")
            if key in seen:
                continue
            seen.add(key)
            unique.append(product)
        data[category] = sorted(unique, key=lambda item: item.get("id", 0))

    with DATA_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    with KEPT_QUARANTINE_PATH.open("w", encoding="utf-8") as f:
        json.dump(confirmed, f, ensure_ascii=False, indent=2)

    print("Restore complete")
    print("Restored uncertain products:", len(restored))
    print("Still quarantined confirmed invalid:", len(confirmed))
    print("Visible:", {category: len(data.get(category, [])) for category in ("bicicletas", "accesorios", "repuestos")})
    for product in confirmed:
        print(f"- confirmed invalid {product.get('_original_category')} #{product.get('id')}: {product.get('brand')} {product.get('model')}")


if __name__ == "__main__":
    main()
