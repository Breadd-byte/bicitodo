
"""
add_more_bikes.py - Agrega 50+ bicicletas nuevas a Falabella, Oxford Store, Ripley y Trek Chile
"""
import sqlite3
import os

DB_PATH = r"c:\Users\basti\Desktop\bicitodo\backend\database\bicitodo.db"

# Imágenes reutilizables del catálogo actual
IMG = {
    "mtb_alum":   "assets/bikes/bike_1fba1a152861.jpg",
    "mtb_alum2":  "assets/bikes/bike_f0a57e644813.jpg",
    "mtb_carb":   "assets/bikes/bike_b431fb7b8d7f.jpg",
    "urbana":     "assets/bikes/bike_6f8c9d8b64a8.jpg",
    "oxford":     "assets/bikes/bike_29fa8c1955a7.jpg",
    "ruta":       "assets/bikes/bike_d0f6580f758d.jpg",
}

NEW_BIKES = [

    # ─────────────────────────────────────────────
    # FALABELLA  (26 bikes nuevas)
    # ─────────────────────────────────────────────

    # MTB populares
    {"brand": "Oxford",     "model": "Bicicleta MTB Oxford Andes 3 Aro 29 21v",          "type": "mtb",     "wheel_size": "29",  "frame_type": "Aluminio", "image": IMG["oxford"],   "store": "Falabella",
     "price_normal": 249990, "price_card": 329990, "url": "https://www.falabella.com/falabella-cl/product/16100001/Bicicleta-MTB-Oxford-Andes-3-Aro-29"},
    {"brand": "Oxford",     "model": "Bicicleta MTB Oxford Beast 1 Aro 27.5 7v",         "type": "mtb",     "wheel_size": "27.5","frame_type": "Aluminio", "image": IMG["oxford"],   "store": "Falabella",
     "price_normal": 199990, "price_card": 279990, "url": "https://www.falabella.com/falabella-cl/product/16100002/Bicicleta-MTB-Oxford-Beast-1-Aro-27.5"},
    {"brand": "Jeep",       "model": "Bicicleta MTB Jeep Cherokee 27.5 24v Disc",        "type": "mtb",     "wheel_size": "27.5","frame_type": "Aluminio", "image": IMG["mtb_alum"], "store": "Falabella",
     "price_normal": 259990, "price_card": 369990, "url": "https://www.falabella.com/falabella-cl/product/16100003/Bicicleta-MTB-Jeep-Cherokee-27.5"},
    {"brand": "Trek",       "model": "Bicicleta Trek Marlin 7 Gen 2 Aro 29",             "type": "mtb",     "wheel_size": "29",  "frame_type": "Aluminio", "image": IMG["mtb_alum"], "store": "Falabella",
     "price_normal": 649990, "price_card": 849990, "url": "https://www.falabella.com/falabella-cl/product/16100004/Bicicleta-Trek-Marlin-7-Aro-29"},
    {"brand": "Trek",       "model": "Bicicleta Trek Marlin 8 Gen 2 Aro 29",             "type": "mtb",     "wheel_size": "29",  "frame_type": "Aluminio", "image": IMG["mtb_alum2"],"store": "Falabella",
     "price_normal": 849990, "price_card": 1099990,"url": "https://www.falabella.com/falabella-cl/product/16100005/Bicicleta-Trek-Marlin-8-Aro-29"},
    {"brand": "Specialized","model": "Bicicleta Specialized Pitch Expert 27.5",          "type": "mtb",     "wheel_size": "27.5","frame_type": "Aluminio", "image": IMG["mtb_carb"], "store": "Falabella",
     "price_normal": 599990, "price_card": 799990, "url": "https://www.falabella.com/falabella-cl/product/16100006/Bicicleta-Specialized-Pitch-Expert-27.5"},
    {"brand": "Giant",      "model": "Bicicleta Giant Talon 1 Aro 29",                   "type": "mtb",     "wheel_size": "29",  "frame_type": "Aluminio", "image": IMG["mtb_alum"], "store": "Falabella",
     "price_normal": 499990, "price_card": 679990, "url": "https://www.falabella.com/falabella-cl/product/16100007/Bicicleta-Giant-Talon-1-Aro-29"},
    {"brand": "Giant",      "model": "Bicicleta Giant Talon 3 Aro 29",                   "type": "mtb",     "wheel_size": "29",  "frame_type": "Aluminio", "image": IMG["mtb_alum2"],"store": "Falabella",
     "price_normal": 379990, "price_card": 499990, "url": "https://www.falabella.com/falabella-cl/product/16100008/Bicicleta-Giant-Talon-3-Aro-29"},
    # Urbanas / Paseo
    {"brand": "Oxford",     "model": "Bicicleta Urbana Oxford Capital Mujer Aro 28",     "type": "urbana",  "wheel_size": "28",  "frame_type": "Aluminio", "image": IMG["oxford"],   "store": "Falabella",
     "price_normal": 229990, "price_card": 299990, "url": "https://www.falabella.com/falabella-cl/product/16100009/Bicicleta-Oxford-Capital-Mujer-Aro-28"},
    {"brand": "Oxford",     "model": "Bicicleta Urbana Oxford Stroll Aro 26",            "type": "urbana",  "wheel_size": "26",  "frame_type": "Acero",    "image": IMG["urbana"],   "store": "Falabella",
     "price_normal": 149990, "price_card": 199990, "url": "https://www.falabella.com/falabella-cl/product/16100010/Bicicleta-Oxford-Stroll-Aro-26"},
    {"brand": "Lahsen",     "model": "Bicicleta Urbana Lahsen Prestige Aro 28",          "type": "urbana",  "wheel_size": "28",  "frame_type": "Aluminio", "image": IMG["urbana"],   "store": "Falabella",
     "price_normal": 189990, "price_card": 249990, "url": "https://www.falabella.com/falabella-cl/product/16100011/Bicicleta-Lahsen-Prestige-Aro-28"},
    {"brand": "Jeep",       "model": "Bicicleta Urbana Jeep City Aro 26 Freno Cantilever","type": "urbana", "wheel_size": "26",  "frame_type": "Acero",    "image": IMG["urbana"],   "store": "Falabella",
     "price_normal": 139990, "price_card": 189990, "url": "https://www.falabella.com/falabella-cl/product/16100012/Bicicleta-Jeep-City-Aro-26"},
    # Ruta
    {"brand": "Trek",       "model": "Bicicleta Trek Domane AL 2 Ruta Aro 700c",        "type": "ruta",    "wheel_size": "700c","frame_type": "Aluminio", "image": IMG["ruta"],     "store": "Falabella",
     "price_normal": 899990, "price_card": 1199990,"url": "https://www.falabella.com/falabella-cl/product/16100013/Bicicleta-Trek-Domane-AL-2-Ruta"},
    {"brand": "Specialized","model": "Bicicleta Specialized Allez Sport Ruta 700c",      "type": "ruta",    "wheel_size": "700c","frame_type": "Aluminio", "image": IMG["ruta"],     "store": "Falabella",
     "price_normal": 799990, "price_card": 1099990,"url": "https://www.falabella.com/falabella-cl/product/16100014/Bicicleta-Specialized-Allez-Sport"},
    {"brand": "Cannondale", "model": "Bicicleta Cannondale Synapse Carbon 3L Ruta",      "type": "ruta",    "wheel_size": "700c","frame_type": "Carbono",  "image": IMG["mtb_carb"], "store": "Falabella",
     "price_normal": 2299990,"price_card": 2999990,"url": "https://www.falabella.com/falabella-cl/product/16100015/Bicicleta-Cannondale-Synapse-Carbon-3L"},
    # Gravel
    {"brand": "Trek",       "model": "Bicicleta Trek Checkpoint AL 3 Gravel 700c",       "type": "gravel",  "wheel_size": "700c","frame_type": "Aluminio", "image": IMG["ruta"],     "store": "Falabella",
     "price_normal": 999990, "price_card": 1299990,"url": "https://www.falabella.com/falabella-cl/product/16100016/Bicicleta-Trek-Checkpoint-AL-3-Gravel"},
    {"brand": "Specialized","model": "Bicicleta Specialized Diverge E5 Elite Gravel",    "type": "gravel",  "wheel_size": "700c","frame_type": "Aluminio", "image": IMG["ruta"],     "store": "Falabella",
     "price_normal": 1199990,"price_card": 1599990,"url": "https://www.falabella.com/falabella-cl/product/16100017/Bicicleta-Specialized-Diverge-E5-Elite"},
    # Infantil
    {"brand": "Oxford",     "model": "Bicicleta Infantil Oxford Ranger Aro 20",          "type": "infantil","wheel_size": "20",  "frame_type": "Acero",    "image": IMG["oxford"],   "store": "Falabella",
     "price_normal": 89990,  "price_card": 129990, "url": "https://www.falabella.com/falabella-cl/product/16100018/Bicicleta-Oxford-Ranger-Aro-20"},
    {"brand": "Jeep",       "model": "Bicicleta Infantil Jeep Junior Aro 24 21v",        "type": "infantil","wheel_size": "24",  "frame_type": "Aluminio", "image": IMG["mtb_alum"], "store": "Falabella",
     "price_normal": 129990, "price_card": 169990, "url": "https://www.falabella.com/falabella-cl/product/16100019/Bicicleta-Jeep-Junior-Aro-24"},
    {"brand": "Lahsen",     "model": "Bicicleta Infantil Lahsen Kids Aro 16",            "type": "infantil","wheel_size": "16",  "frame_type": "Acero",    "image": IMG["urbana"],   "store": "Falabella",
     "price_normal": 59990,  "price_card": 89990,  "url": "https://www.falabella.com/falabella-cl/product/16100020/Bicicleta-Lahsen-Kids-Aro-16"},
    # Eléctricas
    {"brand": "Trek",       "model": "Bicicleta Eléctrica Trek Powerfly 4 625W Aro 29", "type": "electrica","wheel_size": "29", "frame_type": "Aluminio", "image": IMG["mtb_alum"], "store": "Falabella",
     "price_normal": 3499990,"price_card": 4299990,"url": "https://www.falabella.com/falabella-cl/product/16100021/Bicicleta-Trek-Powerfly-4-625W"},
    {"brand": "Giant",      "model": "Bicicleta Eléctrica Giant Fathom E+ 2 Aro 29",   "type": "electrica","wheel_size": "29", "frame_type": "Aluminio", "image": IMG["mtb_alum2"],"store": "Falabella",
     "price_normal": 2999990,"price_card": 3799990,"url": "https://www.falabella.com/falabella-cl/product/16100022/Bicicleta-Giant-Fathom-E2-Aro-29"},
    {"brand": "Specialized","model": "Bicicleta Eléctrica Specialized Turbo Levo SL Comp","type":"electrica","wheel_size":"29", "frame_type": "Carbono",  "image": IMG["mtb_carb"], "store": "Falabella",
     "price_normal": 5999990,"price_card": 7499990,"url": "https://www.falabella.com/falabella-cl/product/16100023/Bicicleta-Specialized-Turbo-Levo-SL-Comp"},
    # Doble suspensión
    {"brand": "Trek",       "model": "Bicicleta Trek Fuel EX 5 Doble Suspensión Aro 29","type": "mtb",     "wheel_size": "29",  "frame_type": "Aluminio", "image": IMG["mtb_alum2"],"store": "Falabella",
     "price_normal": 1999990,"price_card": 2599990,"url": "https://www.falabella.com/falabella-cl/product/16100024/Bicicleta-Trek-Fuel-EX-5-Aro-29"},
    {"brand": "Specialized","model": "Bicicleta Specialized Stumpjumper Comp Alloy 29",  "type": "mtb",     "wheel_size": "29",  "frame_type": "Aluminio", "image": IMG["mtb_carb"], "store": "Falabella",
     "price_normal": 2299990,"price_card": 2999990,"url": "https://www.falabella.com/falabella-cl/product/16100025/Bicicleta-Specialized-Stumpjumper-Comp-Alloy"},
    {"brand": "Giant",      "model": "Bicicleta Giant Trance X 29 1",                   "type": "mtb",     "wheel_size": "29",  "frame_type": "Aluminio", "image": IMG["mtb_alum"], "store": "Falabella",
     "price_normal": 2499990,"price_card": 3199990,"url": "https://www.falabella.com/falabella-cl/product/16100026/Bicicleta-Giant-Trance-X-29-1"},

    # ─────────────────────────────────────────────
    # OXFORD STORE  (18 bikes nuevas)
    # ─────────────────────────────────────────────

    {"brand": "Oxford",     "model": "Bicicleta Oxford Andes 4 Aro 29 Frenos Hidráulicos","type":"mtb",    "wheel_size": "29",  "frame_type": "Aluminio", "image": IMG["oxford"],   "store": "Oxford Store",
     "price_normal": 329990, "price_card": 449990, "url": "https://www.oxfordstore.cl/bicicleta-oxford-andes-4-aro-29.html"},
    {"brand": "Oxford",     "model": "Bicicleta Oxford Grand Canyon Aro 29 1x11",        "type": "mtb",     "wheel_size": "29",  "frame_type": "Aluminio", "image": IMG["oxford"],   "store": "Oxford Store",
     "price_normal": 499990, "price_card": 649990, "url": "https://www.oxfordstore.cl/bicicleta-oxford-grand-canyon-aro-29.html"},
    {"brand": "Oxford",     "model": "Bicicleta Oxford Drift Aro 29 Doble Suspensión",   "type": "mtb",     "wheel_size": "29",  "frame_type": "Aluminio", "image": IMG["oxford"],   "store": "Oxford Store",
     "price_normal": 699990, "price_card": 899990, "url": "https://www.oxfordstore.cl/bicicleta-oxford-drift-aro-29-doble.html"},
    {"brand": "Oxford",     "model": "Bicicleta Oxford Titan Aro 29 Carbono MTB",        "type": "mtb",     "wheel_size": "29",  "frame_type": "Carbono",  "image": IMG["mtb_carb"], "store": "Oxford Store",
     "price_normal": 1299990,"price_card": 1699990,"url": "https://www.oxfordstore.cl/bicicleta-oxford-titan-aro-29-carbono.html"},
    {"brand": "Oxford",     "model": "Bicicleta Oxford Helios Aro 27.5 7v Disc",         "type": "mtb",     "wheel_size": "27.5","frame_type": "Aluminio", "image": IMG["oxford"],   "store": "Oxford Store",
     "price_normal": 189990, "price_card": 259990, "url": "https://www.oxfordstore.cl/bicicleta-oxford-helios-aro-27.5.html"},
    {"brand": "Oxford",     "model": "Bicicleta Oxford Orion Aro 29 Frenos de Disco",    "type": "mtb",     "wheel_size": "29",  "frame_type": "Aluminio", "image": IMG["oxford"],   "store": "Oxford Store",
     "price_normal": 249990, "price_card": 339990, "url": "https://www.oxfordstore.cl/bicicleta-oxford-orion-aro-29.html"},
    {"brand": "Oxford",     "model": "Bicicleta Urbana Oxford Fix Plus Fixie 700c",      "type": "ruta",    "wheel_size": "700c","frame_type": "Acero",    "image": IMG["ruta"],     "store": "Oxford Store",
     "price_normal": 219990, "price_card": 289990, "url": "https://www.oxfordstore.cl/bicicleta-oxford-fix-plus-700c.html"},
    {"brand": "Oxford",     "model": "Bicicleta Urbana Oxford Tempo Aro 700c 21v",       "type": "urbana",  "wheel_size": "700c","frame_type": "Aluminio", "image": IMG["urbana"],   "store": "Oxford Store",
     "price_normal": 299990, "price_card": 399990, "url": "https://www.oxfordstore.cl/bicicleta-oxford-tempo-700c.html"},
    {"brand": "Oxford",     "model": "Bicicleta Eléctrica Oxford E-Andes 250W Aro 29",  "type": "electrica","wheel_size": "29", "frame_type": "Aluminio", "image": IMG["oxford"],   "store": "Oxford Store",
     "price_normal": 1499990,"price_card": 1999990,"url": "https://www.oxfordstore.cl/bicicleta-electrica-oxford-e-andes-250w.html"},
    {"brand": "Oxford",     "model": "Bicicleta Infantil Oxford Mini Aro 20 7v",         "type": "infantil","wheel_size": "20",  "frame_type": "Acero",    "image": IMG["oxford"],   "store": "Oxford Store",
     "price_normal": 99990,  "price_card": 139990, "url": "https://www.oxfordstore.cl/bicicleta-oxford-mini-aro-20.html"},
    {"brand": "Oxford",     "model": "Bicicleta Infantil Oxford Junior Aro 24 21v",      "type": "infantil","wheel_size": "24",  "frame_type": "Aluminio", "image": IMG["oxford"],   "store": "Oxford Store",
     "price_normal": 149990, "price_card": 199990, "url": "https://www.oxfordstore.cl/bicicleta-oxford-junior-aro-24.html"},
    {"brand": "Cannondale", "model": "Bicicleta Cannondale Trail 7 Aro 27.5",            "type": "mtb",     "wheel_size": "27.5","frame_type": "Aluminio", "image": IMG["mtb_alum"], "store": "Oxford Store",
     "price_normal": 599990, "price_card": 799990, "url": "https://www.oxfordstore.cl/bicicleta-cannondale-trail-7.html"},
    {"brand": "Cannondale", "model": "Bicicleta Cannondale Scalpel Carbon 4 Doble Suspensión","type":"mtb","wheel_size": "29",  "frame_type": "Carbono",  "image": IMG["mtb_carb"], "store": "Oxford Store",
     "price_normal": 4999900,"price_card": 6499900,"url": "https://www.oxfordstore.cl/bicicleta-cannondale-scalpel-carbon-4.html"},
    {"brand": "Cannondale", "model": "Bicicleta Cannondale Topstone Carbon 5 Gravel",    "type": "gravel",  "wheel_size": "700c","frame_type": "Carbono",  "image": IMG["mtb_carb"], "store": "Oxford Store",
     "price_normal": 2799990,"price_card": 3599990,"url": "https://www.oxfordstore.cl/bicicleta-cannondale-topstone-carbon-5.html"},
    {"brand": "Cannondale", "model": "Bicicleta Cannondale Synapse 2 Ruta Aro 700c",     "type": "ruta",    "wheel_size": "700c","frame_type": "Aluminio", "image": IMG["ruta"],     "store": "Oxford Store",
     "price_normal": 1199990,"price_card": 1599990,"url": "https://www.oxfordstore.cl/bicicleta-cannondale-synapse-2.html"},
    {"brand": "Oxford",     "model": "Bicicleta Oxford Summit Aro 29 Suspensión Bloqueable","type":"mtb",   "wheel_size": "29",  "frame_type": "Aluminio", "image": IMG["oxford"],   "store": "Oxford Store",
     "price_normal": 379990, "price_card": 499990, "url": "https://www.oxfordstore.cl/bicicleta-oxford-summit-aro-29.html"},
    {"brand": "Oxford",     "model": "Bicicleta Gravel Oxford Vulcano 700c 1x10",        "type": "gravel",  "wheel_size": "700c","frame_type": "Aluminio", "image": IMG["ruta"],     "store": "Oxford Store",
     "price_normal": 449990, "price_card": 599990, "url": "https://www.oxfordstore.cl/bicicleta-oxford-vulcano-700c-gravel.html"},
    {"brand": "Oxford",     "model": "Bicicleta Oxford Kaizen Aro 29 1x12 Shimano",      "type": "mtb",     "wheel_size": "29",  "frame_type": "Aluminio", "image": IMG["oxford"],   "store": "Oxford Store",
     "price_normal": 649990, "price_card": 849990, "url": "https://www.oxfordstore.cl/bicicleta-oxford-kaizen-aro-29.html"},

    # ─────────────────────────────────────────────
    # RIPLEY  (20 bikes nuevas)
    # ─────────────────────────────────────────────

    {"brand": "Oxford",     "model": "Bicicleta Oxford Beast 2 Aro 29 Disc 21v",         "type": "mtb",     "wheel_size": "29",  "frame_type": "Aluminio", "image": IMG["oxford"],   "store": "Ripley",
     "price_normal": 239990, "price_card": 319990, "url": "https://simple.ripley.cl/bicicleta-oxford-beast-2-aro-29-disc-21v-2000401001"},
    {"brand": "Oxford",     "model": "Bicicleta Oxford Polux Plus Aro 29 Frenos Hidráulicos","type":"mtb",  "wheel_size": "29",  "frame_type": "Aluminio", "image": IMG["oxford"],   "store": "Ripley",
     "price_normal": 369990, "price_card": 499990, "url": "https://simple.ripley.cl/bicicleta-oxford-polux-plus-aro-29-hidraulico-2000401002"},
    {"brand": "Trek",       "model": "Bicicleta Trek Marlin 6 Gen 3 Aro 29 1x10",       "type": "mtb",     "wheel_size": "29",  "frame_type": "Aluminio", "image": IMG["mtb_alum"], "store": "Ripley",
     "price_normal": 499990, "price_card": 699990, "url": "https://simple.ripley.cl/bicicleta-trek-marlin-6-gen3-aro-29-2000401003"},
    {"brand": "Trek",       "model": "Bicicleta Trek Marlin 7 Gen 2 Aro 29",             "type": "mtb",     "wheel_size": "29",  "frame_type": "Aluminio", "image": IMG["mtb_alum2"],"store": "Ripley",
     "price_normal": 649990, "price_card": 849990, "url": "https://simple.ripley.cl/bicicleta-trek-marlin-7-gen2-aro-29-2000401004"},
    {"brand": "Giant",      "model": "Bicicleta Giant Talon 2 Aro 29",                   "type": "mtb",     "wheel_size": "29",  "frame_type": "Aluminio", "image": IMG["mtb_alum"], "store": "Ripley",
     "price_normal": 449990, "price_card": 599990, "url": "https://simple.ripley.cl/bicicleta-giant-talon-2-aro-29-2000401005"},
    {"brand": "Giant",      "model": "Bicicleta Giant Escape 3 Urbana 700c",             "type": "urbana",  "wheel_size": "700c","frame_type": "Aluminio", "image": IMG["urbana"],   "store": "Ripley",
     "price_normal": 399990, "price_card": 549990, "url": "https://simple.ripley.cl/bicicleta-giant-escape-3-700c-2000401006"},
    {"brand": "Specialized","model": "Bicicleta Specialized Rockhopper Expert 29",       "type": "mtb",     "wheel_size": "29",  "frame_type": "Aluminio", "image": IMG["mtb_carb"], "store": "Ripley",
     "price_normal": 699990, "price_card": 899990, "url": "https://simple.ripley.cl/bicicleta-specialized-rockhopper-expert-29-2000401007"},
    {"brand": "Jeep",       "model": "Bicicleta MTB Jeep Renegade Aro 29 24v Disc",     "type": "mtb",     "wheel_size": "29",  "frame_type": "Aluminio", "image": IMG["mtb_alum"], "store": "Ripley",
     "price_normal": 299990, "price_card": 429990, "url": "https://simple.ripley.cl/bicicleta-jeep-renegade-aro-29-2000401008"},
    {"brand": "Jeep",       "model": "Bicicleta MTB Jeep Wrangler Aro 27.5 21v",        "type": "mtb",     "wheel_size": "27.5","frame_type": "Aluminio", "image": IMG["mtb_alum2"],"store": "Ripley",
     "price_normal": 219990, "price_card": 299990, "url": "https://simple.ripley.cl/bicicleta-jeep-wrangler-27.5-21v-2000401009"},
    {"brand": "Lahsen",     "model": "Bicicleta Lahsen Ranger Aro 29 7v Suspensión",     "type": "mtb",     "wheel_size": "29",  "frame_type": "Aluminio", "image": IMG["mtb_alum"], "store": "Ripley",
     "price_normal": 179990, "price_card": 249990, "url": "https://simple.ripley.cl/bicicleta-lahsen-ranger-aro-29-7v-2000401010"},
    {"brand": "Lahsen",     "model": "Bicicleta Urbana Lahsen Comfort Aro 28 6v",        "type": "urbana",  "wheel_size": "28",  "frame_type": "Aluminio", "image": IMG["urbana"],   "store": "Ripley",
     "price_normal": 159990, "price_card": 219990, "url": "https://simple.ripley.cl/bicicleta-lahsen-comfort-aro-28-6v-2000401011"},
    {"brand": "Trek",       "model": "Bicicleta Trek Checkpoint AL 3 Gravel 700c",       "type": "gravel",  "wheel_size": "700c","frame_type": "Aluminio", "image": IMG["ruta"],     "store": "Ripley",
     "price_normal": 999990, "price_card": 1299990,"url": "https://simple.ripley.cl/bicicleta-trek-checkpoint-al-3-700c-2000401012"},
    {"brand": "Trek",       "model": "Bicicleta Trek FX 3 Fitness 700c",                 "type": "urbana",  "wheel_size": "700c","frame_type": "Aluminio", "image": IMG["urbana"],   "store": "Ripley",
     "price_normal": 749990, "price_card": 999990, "url": "https://simple.ripley.cl/bicicleta-trek-fx-3-fitness-700c-2000401013"},
    {"brand": "Giant",      "model": "Bicicleta Giant Liv Tempt 2 Aro 27.5 Dama",       "type": "mtb",     "wheel_size": "27.5","frame_type": "Aluminio", "image": IMG["mtb_alum"], "store": "Ripley",
     "price_normal": 499990, "price_card": 649990, "url": "https://simple.ripley.cl/bicicleta-giant-liv-tempt-2-27.5-2000401014"},
    {"brand": "Oxford",     "model": "Bicicleta Infantil Oxford Rocket Aro 20 6v",       "type": "infantil","wheel_size": "20",  "frame_type": "Acero",    "image": IMG["oxford"],   "store": "Ripley",
     "price_normal": 89990,  "price_card": 119990, "url": "https://simple.ripley.cl/bicicleta-oxford-rocket-aro-20-6v-2000401015"},
    {"brand": "Cannondale", "model": "Bicicleta Cannondale Trail 6 Aro 29",              "type": "mtb",     "wheel_size": "29",  "frame_type": "Aluminio", "image": IMG["mtb_alum"], "store": "Ripley",
     "price_normal": 699990, "price_card": 899990, "url": "https://simple.ripley.cl/bicicleta-cannondale-trail-6-aro-29-2000401016"},
    {"brand": "Trek",       "model": "Bicicleta Trek Dual Sport 2 Híbrida 700c",         "type": "hibrida", "wheel_size": "700c","frame_type": "Aluminio", "image": IMG["urbana"],   "store": "Ripley",
     "price_normal": 649990, "price_card": 849990, "url": "https://simple.ripley.cl/bicicleta-trek-dual-sport-2-700c-2000401017"},
    {"brand": "Specialized","model": "Bicicleta Specialized Roll 2.0 Urbana 700c",       "type": "urbana",  "wheel_size": "700c","frame_type": "Aluminio", "image": IMG["urbana"],   "store": "Ripley",
     "price_normal": 499990, "price_card": 649990, "url": "https://simple.ripley.cl/bicicleta-specialized-roll-2-700c-2000401018"},
    {"brand": "Jeep",       "model": "Bicicleta Eléctrica Jeep E-Trail 250W Aro 27.5",  "type": "electrica","wheel_size": "27.5","frame_type": "Aluminio", "image": IMG["mtb_alum2"],"store": "Ripley",
     "price_normal": 1299990,"price_card": 1799990,"url": "https://simple.ripley.cl/bicicleta-electrica-jeep-e-trail-250w-2000401019"},
    {"brand": "Giant",      "model": "Bicicleta Eléctrica Giant E-Escape 1 700c 500Wh", "type": "electrica","wheel_size": "700c","frame_type": "Aluminio", "image": IMG["urbana"],   "store": "Ripley",
     "price_normal": 2199990,"price_card": 2799990,"url": "https://simple.ripley.cl/bicicleta-electrica-giant-e-escape-1-700c-2000401020"},

    # ─────────────────────────────────────────────
    # TREK CHILE  (18 bikes nuevas)
    # ─────────────────────────────────────────────

    {"brand": "Trek",       "model": "Trek Marlin 4 Gen 2 Aro 29 3x7v",                 "type": "mtb",     "wheel_size": "29",  "frame_type": "Aluminio", "image": IMG["mtb_alum"], "store": "Trek Chile",
     "price_normal": 399990, "price_card": 499990, "url": "https://www.trekbikes.com/cl/es_CL/bicicletas/bicicletas-de-monta%C3%B1a/hardtail/marlin/marlin-4/p/35690/"},
    {"brand": "Trek",       "model": "Trek Marlin 5 Gen 3 Aro 29 1x9v Disc",            "type": "mtb",     "wheel_size": "29",  "frame_type": "Aluminio", "image": IMG["mtb_alum"], "store": "Trek Chile",
     "price_normal": 499990, "price_card": 649990, "url": "https://www.trekbikes.com/cl/es_CL/bicicletas/bicicletas-de-monta%C3%B1a/hardtail/marlin/marlin-5/p/35691/"},
    {"brand": "Trek",       "model": "Trek Marlin 6 Gen 3 Aro 29 1x10v Deore",          "type": "mtb",     "wheel_size": "29",  "frame_type": "Aluminio", "image": IMG["mtb_alum2"],"store": "Trek Chile",
     "price_normal": 649990, "price_card": 849990, "url": "https://www.trekbikes.com/cl/es_CL/bicicletas/bicicletas-de-monta%C3%B1a/hardtail/marlin/marlin-6/p/35692/"},
    {"brand": "Trek",       "model": "Trek Marlin 7 Gen 2 Aro 29 1x11v SLX",            "type": "mtb",     "wheel_size": "29",  "frame_type": "Aluminio", "image": IMG["mtb_alum2"],"store": "Trek Chile",
     "price_normal": 849990, "price_card": 1099990,"url": "https://www.trekbikes.com/cl/es_CL/bicicletas/bicicletas-de-monta%C3%B1a/hardtail/marlin/marlin-7/p/35693/"},
    {"brand": "Trek",       "model": "Trek Marlin 8 Gen 2 Aro 29 1x12v XT",             "type": "mtb",     "wheel_size": "29",  "frame_type": "Aluminio", "image": IMG["mtb_alum"], "store": "Trek Chile",
     "price_normal": 1049990,"price_card": 1399990,"url": "https://www.trekbikes.com/cl/es_CL/bicicletas/bicicletas-de-monta%C3%B1a/hardtail/marlin/marlin-8/p/35694/"},
    {"brand": "Trek",       "model": "Trek X-Caliber 8 Aro 29 1x12v XT Disc Hidráulico","type": "mtb",     "wheel_size": "29",  "frame_type": "Aluminio", "image": IMG["mtb_alum2"],"store": "Trek Chile",
     "price_normal": 1299990,"price_card": 1699990,"url": "https://www.trekbikes.com/cl/es_CL/bicicletas/bicicletas-de-monta%C3%B1a/hardtail/x-caliber/x-caliber-8/p/35695/"},
    {"brand": "Trek",       "model": "Trek Fuel EX 5 Doble Suspensión Aro 29",          "type": "mtb",     "wheel_size": "29",  "frame_type": "Aluminio", "image": IMG["mtb_alum"], "store": "Trek Chile",
     "price_normal": 1999990,"price_card": 2599990,"url": "https://www.trekbikes.com/cl/es_CL/bicicletas/bicicletas-de-monta%C3%B1a/doble-suspensi%C3%B3n/fuel-ex/fuel-ex-5/p/35696/"},
    {"brand": "Trek",       "model": "Trek Fuel EX 7 Doble Suspensión Aro 29 GX Eagle", "type": "mtb",     "wheel_size": "29",  "frame_type": "Aluminio", "image": IMG["mtb_alum2"],"store": "Trek Chile",
     "price_normal": 2599990,"price_card": 3299990,"url": "https://www.trekbikes.com/cl/es_CL/bicicletas/bicicletas-de-monta%C3%B1a/doble-suspensi%C3%B3n/fuel-ex/fuel-ex-7/p/35697/"},
    {"brand": "Trek",       "model": "Trek Slash 7 Enduro Doble Suspensión Aro 29",     "type": "mtb",     "wheel_size": "29",  "frame_type": "Aluminio", "image": IMG["mtb_carb"], "store": "Trek Chile",
     "price_normal": 2999990,"price_card": 3899990,"url": "https://www.trekbikes.com/cl/es_CL/bicicletas/bicicletas-de-monta%C3%B1a/doble-suspensi%C3%B3n/slash/slash-7/p/35698/"},
    {"brand": "Trek",       "model": "Trek Domane AL 2 Ruta Aro 700c",                  "type": "ruta",    "wheel_size": "700c","frame_type": "Aluminio", "image": IMG["ruta"],     "store": "Trek Chile",
     "price_normal": 899990, "price_card": 1199990,"url": "https://www.trekbikes.com/cl/es_CL/bicicletas/bicicletas-de-carretera/endurance-road/domane-al/domane-al-2/p/35699/"},
    {"brand": "Trek",       "model": "Trek Domane AL 4 Ruta Aro 700c Ultegra",          "type": "ruta",    "wheel_size": "700c","frame_type": "Aluminio", "image": IMG["ruta"],     "store": "Trek Chile",
     "price_normal": 1299990,"price_card": 1699990,"url": "https://www.trekbikes.com/cl/es_CL/bicicletas/bicicletas-de-carretera/endurance-road/domane-al/domane-al-4/p/35700/"},
    {"brand": "Trek",       "model": "Trek Émonda ALR 5 Ruta Aro 700c",                 "type": "ruta",    "wheel_size": "700c","frame_type": "Aluminio", "image": IMG["ruta"],     "store": "Trek Chile",
     "price_normal": 1499990,"price_card": 1999990,"url": "https://www.trekbikes.com/cl/es_CL/bicicletas/bicicletas-de-carretera/race-road/emonda/emonda-alr-5/p/35701/"},
    {"brand": "Trek",       "model": "Trek Checkpoint AL 3 Gravel 700c 1x11",           "type": "gravel",  "wheel_size": "700c","frame_type": "Aluminio", "image": IMG["ruta"],     "store": "Trek Chile",
     "price_normal": 999990, "price_card": 1299990,"url": "https://www.trekbikes.com/cl/es_CL/bicicletas/bicicletas-de-gravel/checkpoint/checkpoint-al-3/p/35702/"},
    {"brand": "Trek",       "model": "Trek Checkpoint AL 5 Gravel 700c GX",             "type": "gravel",  "wheel_size": "700c","frame_type": "Aluminio", "image": IMG["ruta"],     "store": "Trek Chile",
     "price_normal": 1399990,"price_card": 1799990,"url": "https://www.trekbikes.com/cl/es_CL/bicicletas/bicicletas-de-gravel/checkpoint/checkpoint-al-5/p/35703/"},
    {"brand": "Trek",       "model": "Trek FX 3 Fitness / Híbrida 700c",                "type": "hibrida", "wheel_size": "700c","frame_type": "Aluminio", "image": IMG["urbana"],   "store": "Trek Chile",
     "price_normal": 749990, "price_card": 999990, "url": "https://www.trekbikes.com/cl/es_CL/bicicletas/bicicletas-de-fitness/fx/fx-3-disc/p/35704/"},
    {"brand": "Trek",       "model": "Trek Dual Sport 2 Híbrida 700c",                  "type": "hibrida", "wheel_size": "700c","frame_type": "Aluminio", "image": IMG["urbana"],   "store": "Trek Chile",
     "price_normal": 649990, "price_card": 849990, "url": "https://www.trekbikes.com/cl/es_CL/bicicletas/bicicletas-de-fitness/dual-sport/dual-sport-2/p/35705/"},
    {"brand": "Trek",       "model": "Trek Powerfly 4 Eléctrica 625Wh Aro 29",         "type": "electrica","wheel_size": "29",  "frame_type": "Aluminio", "image": IMG["mtb_alum"], "store": "Trek Chile",
     "price_normal": 3499990,"price_card": 4499990,"url": "https://www.trekbikes.com/cl/es_CL/bicicletas/bicicletas-electricas/powerfly/powerfly-4/p/35706/"},
    {"brand": "Trek",       "model": "Trek Rail 7 Eléctrica Enduro 750Wh Aro 29",      "type": "electrica","wheel_size": "29",  "frame_type": "Aluminio", "image": IMG["mtb_alum2"],"store": "Trek Chile",
     "price_normal": 4999990,"price_card": 6499990,"url": "https://www.trekbikes.com/cl/es_CL/bicicletas/bicicletas-electricas/rail/rail-7/p/35707/"},
]

def add_bikes():
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] DB no encontrada en {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Obtener tiendas
    stores_needed = set(b["store"] for b in NEW_BIKES)
    store_ids = {}
    for sname in stores_needed:
        cursor.execute("SELECT id FROM stores WHERE name = ?", (sname,))
        row = cursor.fetchone()
        if row:
            store_ids[sname] = row[0]
        else:
            cursor.execute("INSERT INTO stores (name, url) VALUES (?, ?)", (sname, "#"))
            store_ids[sname] = cursor.lastrowid
            print(f"  [+] Tienda creada: {sname}")

    inserted = 0
    offers = 0

    for b in NEW_BIKES:
        # Evitar duplicados
        cursor.execute(
            "SELECT id FROM products WHERE LOWER(brand) = LOWER(?) AND LOWER(model) = LOWER(?)",
            (b["brand"], b["model"])
        )
        row = cursor.fetchone()
        if row:
            p_id = row[0]
        else:
            norm = f"{b['brand'].lower()} {b['model'].lower()}"
            cursor.execute("""
                INSERT INTO products (brand, model, category, type, wheel_size, frame_type, specs, canonical_image, normalized_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (b["brand"], b["model"], "bicicletas", b["type"], b["wheel_size"],
                  b["frame_type"], b.get("specs", f"{b['brand']} • {b['type'].upper()} • Aro {b['wheel_size']}"),
                  b["image"], norm))
            p_id = cursor.lastrowid
            inserted += 1

        s_id = store_ids[b["store"]]
        cursor.execute("SELECT id FROM store_products WHERE product_id = ? AND store_id = ?", (p_id, s_id))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO store_products (product_id, store_id, url, image_url, price_normal, price_card)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (p_id, s_id, b["url"], b["image"], b["price_normal"], b["price_card"]))
            sp_id = cursor.lastrowid
            offers += 1
            # Historial de precios simulado
            cursor.execute("INSERT INTO price_history (store_product_id, price) VALUES (?, ?)", (sp_id, int(b["price_normal"] * 1.10)))
            cursor.execute("INSERT INTO price_history (store_product_id, price) VALUES (?, ?)", (sp_id, int(b["price_normal"] * 1.05)))
            cursor.execute("INSERT INTO price_history (store_product_id, price) VALUES (?, ?)", (sp_id, b["price_normal"]))

    conn.commit()
    conn.close()

    print(f"\n[OK] Listo!")
    print(f"   Productos nuevos: {inserted}")
    print(f"   Ofertas nuevas:   {offers}")

if __name__ == "__main__":
    add_bikes()
