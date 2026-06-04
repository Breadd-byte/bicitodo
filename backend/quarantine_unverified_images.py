import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = BASE_DIR / "fronted"
DATA_PATH = FRONTEND_DIR / "data.json"
QUARANTINE_PATH = BASE_DIR / "scratch" / "quarantined_unverified_images.json"

BAD_MARKERS = (
    "images.unsplash.com",
    "bike_0.",
    "acc_0.",
    "part_0.",
    "placeholder",
    "no-image",
)


def has_verified_image(product):
    image = product.get("image", "")
    if not image or any(marker in image.lower() for marker in BAD_MARKERS):
        return False
    if image.startswith("assets/"):
        path = FRONTEND_DIR / image
        return path.exists() and path.stat().st_size > 1000
    return image.startswith(("http://", "https://")) and not any(marker in image.lower() for marker in BAD_MARKERS)


def main():
    with DATA_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    quarantined = []
    for category in ("bicicletas", "accesorios", "repuestos"):
        kept = []
        for product in data.get(category, []):
            if has_verified_image(product):
                kept.append(product)
            else:
                item = dict(product)
                item["_quarantine_reason"] = "unverified_or_placeholder_image"
                item["_original_category"] = category
                quarantined.append(item)
        data[category] = kept

    with DATA_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    with QUARANTINE_PATH.open("w", encoding="utf-8") as f:
        json.dump(quarantined, f, ensure_ascii=False, indent=2)

    print("Quarantine complete")
    print("Visible:", {category: len(data.get(category, [])) for category in ("bicicletas", "accesorios", "repuestos")})
    print("Quarantined:", len(quarantined))
    for product in quarantined[:20]:
        print(f"- {product.get('_original_category')} #{product.get('id')}: {product.get('brand')} {product.get('model')} [{product.get('image')}]")


if __name__ == "__main__":
    main()
