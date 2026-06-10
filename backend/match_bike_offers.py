import argparse
import json
import re
import sqlite3
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "backend" / "database" / "bicitodo.db"
REPORT_PATH = BASE_DIR / "scratch" / "bike_offer_match_report.json"

STOPWORDS = {
    "bicicleta", "bicicletas", "bike", "bici", "mountain", "mtb", "ruta",
    "road", "gravel", "urbana", "hibrida", "hibrido", "unisex", "hombre",
    "mujer", "aro", "color", "modelo", "mod", "talla", "cuadro",
    "shimano", "sram", "freno", "frenos", "hidraulico", "hidraulica",
    "disco", "mecanico", "mecanica", "aluminio", "carbono", "acero",
}

COLOR_WORDS = {
    "negro", "negra", "blanco", "blanca", "gris", "rojo", "roja", "azul",
    "verde", "naranjo", "naranja", "plateado", "plateada", "amarillo",
    "amarilla", "rosado", "rosada", "morado", "morada", "cafe", "turquesa",
    "celeste", "purpura", "violeta", "burdeo",
}

MODEL_STOPWORDS = STOPWORDS | COLOR_WORDS | {
    "oferta", "nuevo", "nueva", "version", "chile", "adulto", "adultos",
    "nino", "nina", "speed", "velocidades", "vel", "rin", "pulgada",
    "pulgadas", "bicicleteria",
}

TYPE_ALIASES = {
    "ruta": {"ruta", "road", "700c", "sinclair", "tarmac", "allez", "domane", "emonda"},
    "gravel": {"gravel", "diverge", "checkpoint", "gravelx", "gravel-x", "sileno"},
    "mtb": {"mtb", "mountain", "marlin", "rockhopper", "spark", "scale", "w790", "w860"},
    "urbana": {"urbana", "city", "hibrida", "hibrido", "commuter", "paseo"},
    "infantil": {"infantil", "nino", "nina", "junior", "kids", "aro12", "aro16", "aro20"},
    "electrica": {"electrica", "electrico", "ebike", "e-bike"},
}

FAMILY_PATTERNS = {
    "trek": [
        ("speed concept", ("speed concept",)),
        ("checkpoint", ("checkpoint",)),
        ("madone", ("madone",)),
        ("emonda", ("emonda",)),
        ("domane", ("domane",)),
        ("marlin", ("marlin",)),
        ("precaliber", ("precaliber",)),
        ("dual sport", ("dual sport",)),
        ("fuel ex", ("fuel ex", "fuel")),
    ],
    "scott": [
        ("spark", ("spark",)),
        ("scale", ("scale",)),
        ("addict", ("addict",)),
        ("foil", ("foil",)),
        ("speedster", ("speedster",)),
        ("aspect", ("aspect",)),
        ("ransom", ("ransom",)),
        ("genius", ("genius",)),
        ("contessa", ("contessa",)),
    ],
    "cannondale": [
        ("supersix evo", ("supersix evo", "super six evo")),
        ("synapse", ("synapse",)),
        ("topstone", ("topstone",)),
        ("superx", ("superx", "super x")),
        ("caad", ("caad",)),
        ("trail", ("trail",)),
    ],
    "specialized": [
        ("tarmac", ("tarmac",)),
        ("roubaix", ("roubaix",)),
        ("diverge", ("diverge",)),
        ("rockhopper", ("rockhopper",)),
        ("stumpjumper", ("stumpjumper",)),
        ("epic", ("epic",)),
        ("allez", ("allez",)),
        ("sirrus", ("sirrus",)),
    ],
    "polygon": [
        ("siskiu", ("siskiu",)),
        ("xtrada", ("xtrada",)),
        ("strattos", ("strattos",)),
        ("tambora", ("tambora",)),
        ("relic", ("relic",)),
        ("collosus", ("collosus",)),
        ("cascade", ("cascade",)),
    ],
    "atletis": [
        ("w force", ("w force",)),
        ("x force", ("x force",)),
    ],
    "totem": [
        ("w790", ("w790",)),
        ("w860", ("w860",)),
        ("sinclair", ("sinclair",)),
        ("eagle", ("eagle",)),
    ],
    "oxford": [
        ("emerald", ("emerald",)),
        ("merak", ("merak",)),
        ("aqua", ("aqua",)),
        ("storm", ("storm",)),
    ],
    "satiro": [
        ("sileno", ("sileno",)),
    ],
}

TIER_TOKENS = {
    "al", "alr", "sl", "slr", "rc", "pro", "team", "comp", "expert",
    "elite", "sport", "axs", "di2", "grx", "ltd", "lefty", "evo", "gen",
    "hi", "mod", "lab71", "disc", "xtr", "deore", "xt", "nx", "sx",
}


def normalize_text(value):
    text = str(value or "")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = text.replace("27,5", "27.5").replace("27 5", "27.5")
    text = re.sub(r"[^a-z0-9.]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def clean_model_tokens(value):
    out = []
    for token in normalize_text(value).split():
        if token in MODEL_STOPWORDS:
            continue
        if token in {"700", "700c", "12", "16", "20", "24", "26", "27.5", "275", "28", "29"}:
            continue
        if len(token) <= 1 and not token.isdigit():
            continue
        out.append(token)
    return out


def extract_wheel(value):
    text = normalize_text(value)
    patterns = [
        r"aro\s*(12|16|20|24|26|27\.5|275|28|29)",
        r"\b(12|16|20|24|26|27\.5|275|28|29)\s*(?:x|\"|pulg|pulgadas)\b",
        r"\b(700c|700)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            wheel = match.group(1)
            if wheel == "275":
                return "27.5"
            if wheel == "700":
                return "700c"
            return wheel
    return ""


def infer_type(row):
    explicit = normalize_text(row["type"])
    haystack = normalize_text(f"{row['brand']} {row['model']} {row['wheel_size']} {row['frame_type']} {row['specs']}")
    if any(word in haystack for word in TYPE_ALIASES["electrica"]):
        return "electrica"
    if any(word in haystack for word in TYPE_ALIASES["gravel"]):
        return "gravel"
    if any(word in haystack for word in TYPE_ALIASES["infantil"]):
        return "infantil"
    for bike_type, words in TYPE_ALIASES.items():
        if explicit == bike_type:
            return bike_type
        if any(word in haystack for word in words):
            return bike_type
    return explicit or "mtb"


def find_family(brand, model_text):
    brand_key = normalize_text(brand)
    text = f" {normalize_text(model_text)} "
    for canonical, aliases in FAMILY_PATTERNS.get(brand_key, []):
        for alias in aliases:
            if f" {normalize_text(alias)} " in text:
                return canonical

    model_tokens = clean_model_tokens(model_text)
    return model_tokens[0] if model_tokens else ""


def extract_variant_tokens(brand, family, model_text):
    brand_tokens = set(clean_model_tokens(brand))
    family_tokens = set(clean_model_tokens(family))
    model_tokens = [token for token in clean_model_tokens(model_text) if token not in brand_tokens]
    variant = []

    for token in model_tokens:
        if token in family_tokens:
            continue
        has_digit = any(ch.isdigit() for ch in token)
        is_short_code = re.fullmatch(r"[a-z]{1,4}", token) is not None
        if has_digit or token in TIER_TOKENS or is_short_code:
            variant.append(token)

    seen = set()
    ordered = []
    for token in variant:
        if token not in seen:
            ordered.append(token)
            seen.add(token)
    return ordered[:6]


def model_signature(row):
    text = f"{row['brand']} {row['model']} {row['wheel_size']} {row['frame_type']} {row['specs']}"
    brand_key = normalize_text(row["brand"])
    family = find_family(row["brand"], row["model"])
    variant = extract_variant_tokens(row["brand"], family, row["model"])
    wheel = row.get("match_wheel") or extract_wheel(text)
    bike_type = row.get("match_type") or infer_type(row)

    if not brand_key or not family or not variant:
        return None

    return {
        "key": "|".join([brand_key, family, bike_type or "", wheel or "", " ".join(variant)]),
        "brand": brand_key,
        "family": family,
        "variant": variant,
        "type": bike_type or "",
        "wheel": wheel or "",
    }


def load_bikes(conn):
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
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
            p.canonical_image,
            sp.id AS offer_id,
            sp.store_id,
            sp.url,
            sp.image_url,
            sp.price_normal,
            sp.price_card,
            s.name AS store
        FROM products p
        JOIN store_products sp ON sp.product_id = p.id
        JOIN stores s ON s.id = sp.store_id
        WHERE p.category = 'bicicletas'
          AND COALESCE(p.is_international, 0) = 0
        ORDER BY p.id
        """
    ).fetchall()

    bikes = []
    for row in rows:
        item = dict(row)
        text = f"{item['brand']} {item['model']} {item['wheel_size']} {item['frame_type']} {item['specs']}"
        item["match_wheel"] = item["wheel_size"] or extract_wheel(text)
        item["match_type"] = infer_type(item)
        item["signature"] = model_signature(item)
        bikes.append(item)
    return bikes


def build_signature_groups(bikes):
    grouped = defaultdict(list)
    skipped = 0
    for bike in bikes:
        signature = bike.get("signature")
        if not signature:
            skipped += 1
            continue
        grouped[signature["key"]].append(bike)

    report_groups = []
    for signature_key, items in grouped.items():
        product_ids = sorted({item["id"] for item in items})
        stores = sorted(set(item["store"] for item in items))
        if len(product_ids) < 2 or len(stores) < 2:
            continue

        cheapest_by_store = {}
        for item in sorted(items, key=lambda row: row["price_normal"] or 10**18):
            cheapest_by_store.setdefault(item["store_id"], item)

        representative = items[0]["signature"]
        report_groups.append({
            "signature": {
                "key": signature_key,
                "brand": representative["brand"],
                "family": representative["family"],
                "variant": representative["variant"],
                "type": representative["type"],
                "wheel": representative["wheel"],
            },
            "product_ids": product_ids,
            "stores": stores,
            "best_price": min(item["price_normal"] for item in items if item["price_normal"]),
            "items": [
                {
                    "id": item["id"],
                    "brand": item["brand"],
                    "model": item["model"],
                    "type": item["type"],
                    "wheel": item["match_wheel"],
                    "store": item["store"],
                    "price": item["price_normal"],
                    "url": item["url"],
                }
                for item in sorted(cheapest_by_store.values(), key=lambda row: (row["price_normal"] or 10**18, row["id"]))
            ],
        })

    report_groups.sort(key=lambda group: (-len(group["stores"]), group["signature"]["brand"], group["signature"]["family"]))
    return report_groups, skipped


def main():
    parser = argparse.ArgumentParser(description="Detecta bicicletas iguales para convertirlas en multiples ofertas.")
    parser.add_argument("--report", default=str(REPORT_PATH))
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    bikes = load_bikes(conn)
    report_groups, skipped_without_signature = build_signature_groups(bikes)

    report = {
        "mode": "strict-signature",
        "bikes_scanned": len({bike["id"] for bike in bikes}),
        "offers_scanned": len(bikes),
        "skipped_without_signature": skipped_without_signature,
        "multi_store_groups": len(report_groups),
        "potential_extra_offers": sum(len(group["stores"]) - 1 for group in report_groups),
        "groups": report_groups,
    }

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        key: report[key]
        for key in (
            "mode",
            "bikes_scanned",
            "offers_scanned",
            "skipped_without_signature",
            "multi_store_groups",
            "potential_extra_offers",
        )
    }, ensure_ascii=False, indent=2))
    print(f"Report written to {report_path}")
    conn.close()


if __name__ == "__main__":
    main()
