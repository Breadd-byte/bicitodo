import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "fronted" / "data.json"
SYNTHETIC_SOURCE = BASE_DIR / "backend" / "enrich_and_perfect_images.py"
QUARANTINE_PATH = BASE_DIR / "scratch" / "quarantined_synthetic_catalog_items.json"


def synthetic_models():
    if not SYNTHETIC_SOURCE.exists():
        return set()
    text = SYNTHETIC_SOURCE.read_text(encoding="utf-8")
    return set(re.findall(r'"model":\s*"([^"]+)"', text))


def has_real_offer_image(product):
    for offer in product.get("offers", []):
        image_url = offer.get("imageUrl")
        if isinstance(image_url, str) and image_url.startswith(("http://", "https://")):
            return True
    return False


def main():
    models = synthetic_models()
    with DATA_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    quarantined = []
    for category in ("bicicletas", "accesorios", "repuestos"):
        kept = []
        for product in data.get(category, []):
            is_synthetic = product.get("model") in models and not has_real_offer_image(product)
            if is_synthetic:
                item = dict(product)
                item["_quarantine_reason"] = "synthetic_catalog_item_without_real_store_image"
                item["_original_category"] = category
                quarantined.append(item)
            else:
                kept.append(product)
        data[category] = kept

    with DATA_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    with QUARANTINE_PATH.open("w", encoding="utf-8") as f:
        json.dump(quarantined, f, ensure_ascii=False, indent=2)

    print("Synthetic quarantine complete")
    print("Visible:", {category: len(data.get(category, [])) for category in ("bicicletas", "accesorios", "repuestos")})
    print("Quarantined:", len(quarantined))
    for product in quarantined:
        print(f"- {product.get('_original_category')} #{product.get('id')}: {product.get('brand')} {product.get('model')}")


if __name__ == "__main__":
    main()
