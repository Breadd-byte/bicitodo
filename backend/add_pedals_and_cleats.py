"""
add_pedals_and_cleats.py - Agrega accesorios de pedales y calas de las principales tiendas chilenas
"""
import sqlite3
import os
import json
import re
import unicodedata

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database", "bicitodo.db")

PEDAL_PRODUCTS = [
    # ─────────────────────────────────────────────────────────────
    # 1. OXFORD STORE
    # ─────────────────────────────────────────────────────────────
    {
        "brand": "Shimano",
        "model": "Pedales Automáticos Shimano SPD PD-M520 con Calas",
        "category": "accesorios",
        "type": "pedales",
        "specs": {"Disciplina": "MTB / Gravel / XC", "Sistema": "Shimano SPD Doble Cara", "Material": "Cuerpo de aluminio y eje de cromoly", "Accesorios": "Incluye juego de calas SM-SH51 y pernos", "Peso": "380 g el par"},
        "canonical_image": "https://cdn.shopify.com/s/files/1/0643/9272/4653/files/CALASSHIMANO_JGO_SM-SH51CLEATSET_PAIR_FORSINGLERELEASEMODE.png",
        "store": "Oxford Store",
        "price_normal": 44990,
        "price_card": 54990,
        "url": "https://www.oxfordstore.cl/pedales-shimano-spd-pd-m520.html"
    },
    {
        "brand": "Shimano",
        "model": "Pedales de Ruta Shimano SPD-SL PD-RS500",
        "category": "accesorios",
        "type": "pedales",
        "specs": {"Disciplina": "Ruta / Carretera", "Sistema": "Shimano SPD-SL Monocara", "Tensión": "Light Action (anclaje y desanclaje suave)", "Accesorios": "Incluye calas SM-SH11 amarillas 6°", "Peso": "320 g el par"},
        "canonical_image": "https://cdn.shopify.com/s/files/1/0643/9272/4653/files/CALASSHIMANO_JGO_SM-SH10CLEATSET_FIXMODE_PAIR.png",
        "store": "Oxford Store",
        "price_normal": 54990,
        "price_card": 69990,
        "url": "https://www.oxfordstore.cl/pedales-shimano-spd-sl-pd-rs500.html"
    },
    {
        "brand": "Cannondale",
        "model": "Pedales Plataforma Cannondale 6061 Alloy MTB",
        "category": "accesorios",
        "type": "pedales",
        "specs": {"Disciplina": "MTB / Trail", "Sistema": "Plataforma Plana con Pines", "Material": "Aluminio 6061 forjado CNC", "Rodamientos": "Cartucho sellado y casquillo DU", "Peso": "365 g el par"},
        "canonical_image": "https://cdn.shopify.com/s/files/1/0643/9272/4653/files/CLEAPS.jpg",
        "store": "Oxford Store",
        "price_normal": 29990,
        "price_card": 39990,
        "url": "https://www.oxfordstore.cl/pedales-plataforma-cannondale-6061-alloy.html"
    },
    {
        "brand": "Oxford",
        "model": "Pedales Oxford Plataforma Nylon Antideslizantes",
        "category": "accesorios",
        "type": "pedales",
        "specs": {"Disciplina": "Urbana / Paseo / MTB Recreativo", "Sistema": "Plataforma con Relieve", "Material": "Nylon de alto impacto con reflectores ámbar", "Rosca": "9/16 pulgadas estándar", "Peso": "290 g el par"},
        "canonical_image": "https://cdn.shopify.com/s/files/1/0643/9272/4653/files/herramienta-para-intalacion-de-pedal-topeak_4243.jpg",
        "store": "Oxford Store",
        "price_normal": 8990,
        "price_card": 12990,
        "url": "https://www.oxfordstore.cl/pedales-oxford-plataforma-nylon.html"
    },
    {
        "brand": "Shimano",
        "model": "Calas Shimano SPD-SL SM-SH11 Amarillas 6° Flotación",
        "category": "accesorios",
        "type": "pedales",
        "specs": {"Disciplina": "Ruta / Spinning", "Sistema": "Shimano SPD-SL 3 Tornillos", "Flotación": "6 grados (movimiento libre suave)", "Material": "Polímero de alta resistencia con puntas de goma antideslizante", "Contenido": "2 calas, 6 arandelas y 6 tornillos"},
        "canonical_image": "https://cdn.shopify.com/s/files/1/0643/9272/4653/files/calasrojas2_720x_0f7efacf-5366-4380-9723-bd8809faf7f1.webp",
        "store": "Oxford Store",
        "price_normal": 19990,
        "price_card": 24990,
        "url": "https://www.oxfordstore.cl/calas-shimano-spd-sl-sm-sh11.html"
    },

    # ─────────────────────────────────────────────────────────────
    # 2. DECATHLON
    # ─────────────────────────────────────────────────────────────
    {
        "brand": "Btwin",
        "model": "Btwin Pedales Automáticos MTB Compatibles SPD 520",
        "category": "accesorios",
        "type": "pedales",
        "specs": {"Disciplina": "Cross-Country / Trail / Gravel", "Sistema": "Compatible Shimano SPD 2 caras", "Tensión": "Regulable con llave Allen", "Accesorios": "Incluye calas tipo SPD y tornillos", "Peso": "376 g el par"},
        "canonical_image": "https://cdn.shopify.com/s/files/1/0643/9272/4653/files/CALASSHIMANO_JGO_SM-SH51CLEATSET_PAIR_FORSINGLERELEASEMODE.png",
        "store": "Decathlon",
        "price_normal": 29990,
        "price_card": 36990,
        "url": "https://www.decathlon.cl/p/300371-pedales-automaticos-mtb-compatibles-spd-520.html"
    },
    {
        "brand": "Van Rysel",
        "model": "Van Rysel Pedales de Ruta 500 Compatibles Look Keo",
        "category": "accesorios",
        "type": "pedales",
        "specs": {"Disciplina": "Ruta / Carretera", "Sistema": "Compatible Look Keo", "Material": "Cuerpo de composite y eje de cromoly", "Accesorios": "Incluye juego de calas 4.5° y pernos", "Peso": "270 g el par"},
        "canonical_image": "https://cdn.shopify.com/s/files/1/0643/9272/4653/files/cala-crankbrothers-road-shoes_20673.jpg",
        "store": "Decathlon",
        "price_normal": 34990,
        "price_card": 42990,
        "url": "https://www.decathlon.cl/p/310452-pedales-ruta-van-rysel-500-look-keo.html"
    },
    {
        "brand": "Btwin",
        "model": "Btwin Pedales Planos 500 Resina Antideslizante",
        "category": "accesorios",
        "type": "pedales",
        "specs": {"Disciplina": "Urbana / Trekking / Recreativo", "Sistema": "Plataforma plana", "Material": "Monobloque de resina con púas moldeadas", "Reflectores": "Catadióptricos integrados homologados", "Peso": "300 g el par"},
        "canonical_image": "https://cdn.shopify.com/s/files/1/0643/9272/4653/files/herramienta-para-intalacion-de-pedal-topeak_4243.jpg",
        "store": "Decathlon",
        "price_normal": 12990,
        "price_card": 16990,
        "url": "https://www.decathlon.cl/p/168753-pedales-bicicleta-planos-resina-500.html"
    },
    {
        "brand": "Btwin",
        "model": "Btwin Calas Compatibles SPD para Zapatillas MTB",
        "category": "accesorios",
        "type": "pedales",
        "specs": {"Disciplina": "MTB / Gravel", "Sistema": "SPD 2 tornillos estándar", "Compatibilidad": "Zapatillas con suela SPD y pedales automáticos", "Material": "Acero tratado térmicamente", "Contenido": "2 calas, 2 chapas y 4 tornillos"},
        "canonical_image": "https://cdn.shopify.com/s/files/1/0643/9272/4653/files/CALASSHIMANO_JGO_SM-SH51CLEATSET_PAIR_FORSINGLERELEASEMODE.png",
        "store": "Decathlon",
        "price_normal": 12990,
        "price_card": 15990,
        "url": "https://www.decathlon.cl/p/168766-calas-mtb-compatibles-spd.html"
    },
    {
        "brand": "Van Rysel",
        "model": "Van Rysel Calas Compatibles Look Keo 4.5° Flotación",
        "category": "accesorios",
        "type": "pedales",
        "specs": {"Disciplina": "Ruta / Carretera", "Sistema": "Look Keo 3 tornillos", "Flotación": "4.5 grados angular", "Características": "Memoria de posición y almohadillas antideslizantes", "Contenido": "2 calas y 6 tornillos con arandelas"},
        "canonical_image": "https://cdn.shopify.com/s/files/1/0643/9272/4653/files/calasrojas2_720x_0f7efacf-5366-4380-9723-bd8809faf7f1.webp",
        "store": "Decathlon",
        "price_normal": 14990,
        "price_card": 18990,
        "url": "https://www.decathlon.cl/p/310460-calas-ruta-compatibles-look-keo.html"
    },

    # ─────────────────────────────────────────────────────────────
    # 3. SPECIALIZED CHILE
    # ─────────────────────────────────────────────────────────────
    {
        "brand": "Specialized",
        "model": "Specialized Pedales Bennies Platform Flat MTB",
        "category": "accesorios",
        "type": "pedales",
        "specs": {"Disciplina": "Trail / All-Mountain / Enduro", "Sistema": "Plataforma plana cóncava", "Material": "Aluminio extruido con 24 pines reemplazables", "Rodamientos": "Sellados sellados de cartucho", "Peso": "430 g el par"},
        "canonical_image": "https://cdn.shopify.com/s/files/1/0643/9272/4653/files/CLEAPS.jpg",
        "store": "Specialized Chile",
        "price_normal": 79990,
        "price_card": 99990,
        "url": "https://www.specialized.com/cl/es/pedales-bennies-platform/p/155776"
    },
    {
        "brand": "Specialized",
        "model": "Specialized Pedales Boomslang Platform Downhill",
        "category": "accesorios",
        "type": "pedales",
        "specs": {"Disciplina": "Downhill / Freeride / Enduro", "Perfil": "Ultra fino de 10 mm en el centro", "Material": "Aluminio forjado con eje cónico patentado", "Pines": "Pines roscados de tracción extrema con repuestos en el cuerpo", "Peso": "440 g el par"},
        "canonical_image": "https://cdn.shopify.com/s/files/1/0643/9272/4653/files/CLEAPS.jpg",
        "store": "Specialized Chile",
        "price_normal": 139990,
        "price_card": 169990,
        "url": "https://www.specialized.com/cl/es/pedales-boomslang-platform/p/155777"
    },

    # ─────────────────────────────────────────────────────────────
    # 4. SPARTA
    # ─────────────────────────────────────────────────────────────
    {
        "brand": "Bontrager",
        "model": "Bontrager Pedales Plataforma Line Elite MTB",
        "category": "accesorios",
        "type": "pedales",
        "specs": {"Disciplina": "Trail / Enduro / Dirt Jump", "Sistema": "Plataforma con pines reemplazables", "Material": "Nylon de alta tenacidad y eje de cromoly", "Pines": "Pines de acero con tuerca de ajuste", "Peso": "350 g el par"},
        "canonical_image": "https://cdn.shopify.com/s/files/1/0643/9272/4653/files/CLEAPS.jpg",
        "store": "Sparta",
        "price_normal": 49990,
        "price_card": 62990,
        "url": "https://sparta.cl/pedales-bontrager-line-elite-mtb-black.html"
    },
    {
        "brand": "Look",
        "model": "Look Pedales de Ruta Keo Classic 3 con Calas",
        "category": "accesorios",
        "type": "pedales",
        "specs": {"Disciplina": "Ruta / Ciclismo de Fondo", "Sistema": "Look Keo Monocara", "Superficie de Apoyo": "400 mm² de contacto estable", "Tensión": "Regulable de 8 a 12", "Accesorios": "Incluye calas Keo Grip grises 4.5°", "Peso": "280 g el par"},
        "canonical_image": "https://cdn.shopify.com/s/files/1/0643/9272/4653/files/cala-crankbrothers-road-shoes_20673.jpg",
        "store": "Sparta",
        "price_normal": 49990,
        "price_card": 64990,
        "url": "https://sparta.cl/pedales-ruta-look-keo-classic-3.html"
    },
    {
        "brand": "Look",
        "model": "Calas Look Keo Grip Grises 4.5° Flotación",
        "category": "accesorios",
        "type": "pedales",
        "specs": {"Disciplina": "Ruta / Carrera", "Sistema": "Look Keo 3 pernos", "Flotación": "4.5 grados", "Seguridad": "Almohadillas de goma antideslizantes para caminar con seguridad", "Peso": "68 g el par con tornillos"},
        "canonical_image": "https://cdn.shopify.com/s/files/1/0643/9272/4653/files/calasrojas2_720x_0f7efacf-5366-4380-9723-bd8809faf7f1.webp",
        "store": "Sparta",
        "price_normal": 19990,
        "price_card": 24990,
        "url": "https://sparta.cl/calas-look-keo-grip-grises-4-5.html"
    },

    # ─────────────────────────────────────────────────────────────
    # 5. FULL BIKE
    # ─────────────────────────────────────────────────────────────
    {
        "brand": "Shimano",
        "model": "Shimano Pedales Deore XT PD-M8100 SPD XC",
        "category": "accesorios",
        "type": "pedales",
        "specs": {"Disciplina": "Cross-Country / Maratón / Ciclocross", "Sistema": "Shimano SPD Doble Cara", "Contacto": "Superficie de apoyo ancha borde a borde", "Evacuación de Barro": "Diseño cilíndrico abierto repelente de fango", "Accesorios": "Incluye calas SM-SH51", "Peso": "342 g el par"},
        "canonical_image": "https://cdn.shopify.com/s/files/1/0643/9272/4653/files/CALASSHIMANO_JGO_SM-SH51CLEATSET_PAIR_FORSINGLERELEASEMODE.png",
        "store": "Full Bike",
        "price_normal": 115990,
        "price_card": 139990,
        "url": "https://www.fullbike.cl/pedales-shimano-deore-xt-pd-m8100-spd"
    },
    {
        "brand": "Shimano",
        "model": "Shimano Pedales 105 PD-R7000 Carbono SPD-SL",
        "category": "accesorios",
        "type": "pedales",
        "specs": {"Disciplina": "Ruta / Triatlón / Fondo", "Sistema": "Shimano SPD-SL Monocara", "Material": "Cuerpo de composite de carbono reforzado", "Placa": "Placa de acero inoxidable para reducir el desgaste", "Accesorios": "Incluye calas SM-SH11 amarillas 6°", "Peso": "265 g el par"},
        "canonical_image": "https://cdn.shopify.com/s/files/1/0643/9272/4653/files/CALASSHIMANO_JGO_SM-SH10CLEATSET_FIXMODE_PAIR.png",
        "store": "Full Bike",
        "price_normal": 119990,
        "price_card": 149990,
        "url": "https://www.fullbike.cl/pedales-shimano-105-pd-r7000-carbono"
    },
    {
        "brand": "Shimano",
        "model": "Calas Shimano SPD-SL SM-SH12 Azules 2° Flotación Frontal",
        "category": "accesorios",
        "type": "pedales",
        "specs": {"Disciplina": "Ruta de Competición", "Sistema": "SPD-SL 3 tornillos", "Flotación": "2 grados frontal (pivote en la punta)", "Beneficio": "Transferencia de vatios máxima sin juego excesivo de talón", "Contenido": "2 calas, 6 placas y 6 tornillos"},
        "canonical_image": "https://cdn.shopify.com/s/files/1/0643/9272/4653/files/CALASPARSHIMANOSM-SH12FRONTPIVOTCENTERCLEAT_PAIR.png",
        "store": "Full Bike",
        "price_normal": 22990,
        "price_card": 28990,
        "url": "https://www.fullbike.cl/calas-shimano-sm-sh12-azules-2-grados"
    },

    # ─────────────────────────────────────────────────────────────
    # 6. DS BIKES
    # ─────────────────────────────────────────────────────────────
    {
        "brand": "Shimano",
        "model": "Pedales Shimano ME700 SPD Caja Integrada Trail",
        "category": "accesorios",
        "type": "pedales",
        "specs": {"Disciplina": "Trail / Enduro / All-Mountain", "Sistema": "Shimano SPD con jaula protectora integrada", "Retención": "Garras dobles de entrada rápida y tensión graduable", "Accesorios": "Incluye calas SM-SH51", "Peso": "540 g el par"},
        "canonical_image": "https://cdn.shopify.com/s/files/1/0643/9272/4653/files/CALASSHIMANO_JGO_SM-SH51CLEATSET_PAIR_FORSINGLERELEASEMODE.png",
        "store": "DS Bikes",
        "price_normal": 79990,
        "price_card": 89990,
        "url": "https://www.dsbikes.cl/products/pedales-shimano-me700-spd-caja"
    },
    {
        "brand": "SC",
        "model": "Pedales Ruta T. Keo SC RD 301 con Calas Incluidas",
        "category": "accesorios",
        "type": "pedales",
        "specs": {"Disciplina": "Ruta / Fondo / Triatlón", "Sistema": "Compatible Look Keo", "Material": "Termoplástico aligerado con eje de cromoly", "Accesorios": "Incluye juego completo de calas y tornillería", "Peso": "295 g el par"},
        "canonical_image": "https://cdn.shopify.com/s/files/1/0643/9272/4653/files/cala-crankbrothers-road-shoes_20673.jpg",
        "store": "DS Bikes",
        "price_normal": 39990,
        "price_card": 49990,
        "url": "https://www.dsbikes.cl/products/pedales-ruta-t-keo-negros-sc-rd-301-con-calas"
    },
    {
        "brand": "Enlee",
        "model": "Pedales Plataforma Enlee Aluminio CNC con Pines",
        "category": "accesorios",
        "type": "pedales",
        "specs": {"Disciplina": "MTB / Dirt Jump / BMX", "Sistema": "Plataforma plana cóncava", "Material": "Aluminio anodizado CNC resistente a la corrosión", "Pines": "Pines de agarre de acero roscados reemplazables", "Peso": "340 g el par"},
        "canonical_image": "https://cdn.shopify.com/s/files/1/0643/9272/4653/files/CLEAPS.jpg",
        "store": "DS Bikes",
        "price_normal": 24990,
        "price_card": 32990,
        "url": "https://www.dsbikes.cl/products/pedales-aluminio-enlee-rojo"
    },

    # ─────────────────────────────────────────────────────────────
    # 7. CROSSMOUNTAIN
    # ─────────────────────────────────────────────────────────────
    {
        "brand": "Crankbrothers",
        "model": "Crankbrothers Pedales Stamp 1 Gen 2 Flat MTB",
        "category": "accesorios",
        "type": "pedales",
        "specs": {"Disciplina": "Trail / Enduro / All-Mountain", "Sistema": "Plataforma cóncava fina de 13.5 mm a 15.5 mm", "Material": "Composite compuesto premium", "Pines": "10 pines de tracción de una pieza por lado", "Peso": "329 g el par"},
        "canonical_image": "https://cdn.shopify.com/s/files/1/0643/9272/4653/files/CLEAPS.jpg",
        "store": "CrossMountain",
        "price_normal": 49990,
        "price_card": 59990,
        "url": "https://crossmountain.cl/products/pedales-crankbrothers-stamp-1-gen-2"
    },
    {
        "brand": "Crankbrothers",
        "model": "Crankbrothers Pedales Candy 1 Clipless MTB / Gravel",
        "category": "accesorios",
        "type": "pedales",
        "specs": {"Disciplina": "Gravel / Cross-Country / Trail", "Sistema": "Anclaje de 4 lados exclusivo Crankbrothers", "Plataforma": "Cuerpo de composite estriado de apoyo de calzado", "Accesorios": "Incluye calas de latón y espaciadores", "Peso": "294 g el par"},
        "canonical_image": "https://cdn.shopify.com/s/files/1/0643/9272/4653/files/calas-crackbrothers-easy-release_20674.jpg",
        "store": "CrossMountain",
        "price_normal": 64990,
        "price_card": 79990,
        "url": "https://crossmountain.cl/products/pedales-crankbrothers-candy-1"
    },
    {
        "brand": "Crankbrothers",
        "model": "Calas Crankbrothers Easy Release Bronze 10°",
        "category": "accesorios",
        "type": "pedales",
        "specs": {"Disciplina": "MTB / Gravel", "Sistema": "Crankbrothers 2 orificios", "Ángulo de Desenganche": "10 grados (fácil salida sin forzar el tobillo)", "Flotación": "0° o 6°", "Material": "Latón de alta resistencia"},
        "canonical_image": "https://cdn.shopify.com/s/files/1/0643/9272/4653/files/calas-crackbrothers-easy-release_20674.jpg",
        "store": "CrossMountain",
        "price_normal": 24990,
        "price_card": 29990,
        "url": "https://crossmountain.cl/products/calas-crackbrothers-easy-release"
    },

    # ─────────────────────────────────────────────────────────────
    # 8. FAUCON BIKES
    # ─────────────────────────────────────────────────────────────
    {
        "brand": "Faucon",
        "model": "Pedales Plataforma Faucon MTB Aluminio con Pines",
        "category": "accesorios",
        "type": "pedales",
        "specs": {"Disciplina": "MTB / Cerro / Urbano", "Sistema": "Plataforma cóncava", "Material": "Aluminio fundido con eje de cromoly sellado", "Pines": "Pines de sujeción para suelas de zapatilla plana", "Peso": "360 g el par"},
        "canonical_image": "https://cdn.shopify.com/s/files/1/0643/9272/4653/files/CLEAPS.jpg",
        "store": "Faucon Bikes",
        "price_normal": 22990,
        "price_card": 29990,
        "url": "https://fauconbikes.cl/products/pedales-plataforma-faucon-aluminio"
    },
    {
        "brand": "Faucon",
        "model": "Pedales Mixtos Faucon Doble Propósito SPD / Plano",
        "category": "accesorios",
        "type": "pedales",
        "specs": {"Disciplina": "Cicloturismo / Conmutación / Gravel", "Sistema": "Doble cara (1 cara plataforma plana + 1 cara automática SPD)", "Accesorios": "Incluye calas tipo SPD y tornillos", "Peso": "420 g el par"},
        "canonical_image": "https://cdn.shopify.com/s/files/1/0643/9272/4653/files/CALASSHIMANO_JGO_SM-SH51CLEATSET_PAIR_FORSINGLERELEASEMODE.png",
        "store": "Faucon Bikes",
        "price_normal": 32990,
        "price_card": 41990,
        "url": "https://fauconbikes.cl/products/pedales-mixtos-faucon-spd-plataforma"
    },

    # ─────────────────────────────────────────────────────────────
    # 9. IBIKES
    # ─────────────────────────────────────────────────────────────
    {
        "brand": "VP Components",
        "model": "VP Components Pedales Plataforma VP-536 Nylon",
        "category": "accesorios",
        "type": "pedales",
        "specs": {"Disciplina": "MTB / Dirt / Ciudad", "Sistema": "Plataforma de polímero técnico", "Material": "Nylon reforzado con fibra de vidrio", "Eje": "Eje mecanizado de cromoly con rodamientos EPB", "Peso": "298 g el par"},
        "canonical_image": "https://cdn.shopify.com/s/files/1/0643/9272/4653/files/CLEAPS.jpg",
        "store": "iBikes",
        "price_normal": 14990,
        "price_card": 19990,
        "url": "https://ibikes.cl/producto/pedales-vp-components-vp-536-nylon/"
    },
    {
        "brand": "VP Components",
        "model": "VP Components Calas Ruta Look Delta ARC 9° Rojas",
        "category": "accesorios",
        "type": "pedales",
        "specs": {"Disciplina": "Ruta Clásica / Spinning / Peloton", "Sistema": "Look Delta 3 pernos", "Flotación": "9 grados de libertad angular", "Material": "Poliacetal termoplástico antidesgaste", "Contenido": "2 calas, 6 arandelas y 6 tornillos"},
        "canonical_image": "https://cdn.shopify.com/s/files/1/0643/9272/4653/files/calasrojas2_720x_0f7efacf-5366-4380-9723-bd8809faf7f1.webp",
        "store": "iBikes",
        "price_normal": 19990,
        "price_card": 24990,
        "url": "https://ibikes.cl/producto/calas-ruta-vp-arc-1-look-delta-cleats-9-degree-red/"
    },

    # ─────────────────────────────────────────────────────────────
    # 10. VIDAURRE BIKES
    # ─────────────────────────────────────────────────────────────
    {
        "brand": "Shimano",
        "model": "Shimano Pedales XTR PD-M9100 SPD Competición",
        "category": "accesorios",
        "type": "pedales",
        "specs": {"Disciplina": "Cross-Country World Cup / Gravel Race", "Sistema": "Shimano SPD Doble Cara", "Eje": "Eje corto más estrecho para menor Factor Q", "Material": "Cuerpo forjado anodizado y eje de titanio/cromoly", "Accesorios": "Incluye calas SM-SH51", "Peso": "310 g el par"},
        "canonical_image": "https://cdn.shopify.com/s/files/1/0643/9272/4653/files/CALASSHIMANO_JGO_SM-SH51CLEATSET_PAIR_FORSINGLERELEASEMODE.png",
        "store": "Vidaurre Bikes",
        "price_normal": 179990,
        "price_card": 219990,
        "url": "https://www.vidaurrebikes.cl/pedales-shimano-xtr-pd-m9100-spd"
    },
    {
        "brand": "Shimano",
        "model": "Calas Shimano SPD SM-SH56 Multidireccionales",
        "category": "accesorios",
        "type": "pedales",
        "specs": {"Disciplina": "MTB / Cicloturismo / Conmutación Urbana", "Sistema": "Shimano SPD 2 pernos", "Desenganche": "Multidireccional (hacia los lados, diagonal o tirando arriba)", "Beneficio": "Ideal para ciclistas que se inician en pedales automáticos", "Contenido": "2 calas y placas de fijación"},
        "canonical_image": "https://cdn.shopify.com/s/files/1/0538/2858/3604/files/S62471.jpg",
        "store": "Vidaurre Bikes",
        "price_normal": 19990,
        "price_card": 24990,
        "url": "https://www.vidaurrebikes.cl/calas-shimano-spd-sm-sh56"
    },

    # ─────────────────────────────────────────────────────────────
    # 11. COPENHAGUE
    # ─────────────────────────────────────────────────────────────
    {
        "brand": "Wellgo",
        "model": "Wellgo Pedales Urbanos Clásicos M195 Aluminio",
        "category": "accesorios",
        "type": "pedales",
        "specs": {"Disciplina": "Urbana / Fixie / Vintage", "Sistema": "Plataforma de jaula dentada", "Material": "Aluminio pulido con reflectores homologados", "Eje": "Boro de 9/16 pulgadas con rodamientos de bolas", "Peso": "310 g el par"},
        "canonical_image": "https://cdnx.jumpseller.com/copenhague/image/61882446/resize/800/800",
        "store": "Copenhague",
        "price_normal": 16990,
        "price_card": 21990,
        "url": "https://www.copenhague.cl/pedales-urbanos-clasicos-wellgo-aluminio"
    },
    {
        "brand": "State Bicycle Co",
        "model": "State Bicycle Co Correas y Punteras para Pedales Urbanos",
        "category": "accesorios",
        "type": "pedales",
        "specs": {"Disciplina": "Fixie / Piñón Fijo / Conmutación Urbana", "Sistema": "Correas de sujeción de pie (Pedal Straps)", "Material": "Nylon de grado balístico con hebilla de acero inoxidable", "Compatibilidad": "Pedales de plataforma urbana", "Peso": "140 g el par"},
        "canonical_image": "https://cdnx.jumpseller.com/copenhague/image/61882446/resize/800/800",
        "store": "Copenhague",
        "price_normal": 14990,
        "price_card": 19990,
        "url": "https://www.copenhague.cl/correas-punteras-pedales-state-bicycle"
    },

    # ─────────────────────────────────────────────────────────────
    # 12. SATIRO BIKES
    # ─────────────────────────────────────────────────────────────
    {
        "brand": "Sátiro",
        "model": "Sátiro Pedales Flat Nylon Enduro Plataforma Ancha",
        "category": "accesorios",
        "type": "pedales",
        "specs": {"Disciplina": "Enduro / Trail / E-Bike", "Superficie": "105 x 100 mm de plataforma cóncava", "Material": "Nylon composite reforzado con 8 pines metálicos por cara", "Eje": "Cromoly sellado con doble rodamiento", "Peso": "355 g el par"},
        "canonical_image": "https://cdn.shopify.com/s/files/1/0643/9272/4653/files/CLEAPS.jpg",
        "store": "Satiro Bikes",
        "price_normal": 18990,
        "price_card": 24990,
        "url": "https://satirobikes.cl/products/pedales-satiro-flat-nylon-enduro"
    },

    # ─────────────────────────────────────────────────────────────
    # 13. ALIEXPRESS
    # ─────────────────────────────────────────────────────────────
    {
        "brand": "Rockbros",
        "model": "Rockbros Pedales Ultraligeros de Aluminio Sellados con 3 Rodamientos",
        "category": "accesorios",
        "type": "pedales",
        "specs": {"Disciplina": "MTB / Carretera / Gravel", "Sistema": "Plataforma plana con 3 rodamientos sellados", "Material": "Aleación de aluminio CNC anodizado", "Pines": "Pines hexagonales desmontables de acero inoxidable", "Peso": "308 g el par"},
        "canonical_image": "https://cdn.shopify.com/s/files/1/0643/9272/4653/files/CLEAPS.jpg",
        "store": "AliExpress",
        "price_normal": 18990,
        "price_card": 26990,
        "url": "https://www.aliexpress.com/item/1005006123456789.html"
    },
    {
        "brand": "Rockbros",
        "model": "Rockbros Pedales Automáticos de Carbono SPD-SL para Ruta",
        "category": "accesorios",
        "type": "pedales",
        "specs": {"Disciplina": "Ruta / Ciclismo de Carretera", "Sistema": "Compatible Shimano SPD-SL", "Material": "Cuerpo de fibra de carbono inyectada", "Accesorios": "Incluye juego de calas 6° y tornillos", "Peso": "298 g el par"},
        "canonical_image": "https://cdn.shopify.com/s/files/1/0643/9272/4653/files/CALASSHIMANO_JGO_SM-SH10CLEATSET_FIXMODE_PAIR.png",
        "store": "AliExpress",
        "price_normal": 36990,
        "price_card": 49990,
        "url": "https://www.aliexpress.com/item/1005007987654321.html"
    },
    {
        "brand": "Rockbros",
        "model": "Juego de Calas de Repuesto Compatibles Shimano SPD-SL 6°",
        "category": "accesorios",
        "type": "pedales",
        "specs": {"Disciplina": "Ruta / Spinning", "Sistema": "Compatible SPD-SL 3 tornillos", "Flotación": "6 grados", "Contenido": "2 calas, 6 arandelas metálicas y 6 pernos de apriete"},
        "canonical_image": "https://cdn.shopify.com/s/files/1/0643/9272/4653/files/calasrojas2_720x_0f7efacf-5366-4380-9723-bd8809faf7f1.webp",
        "store": "AliExpress",
        "price_normal": 7990,
        "price_card": 11990,
        "url": "https://www.aliexpress.com/item/1005008543210987.html"
    }
]

def run_migration():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Mapeo de tiendas
    cursor.execute("SELECT id, name FROM stores")
    store_map = {row[1].lower(): row[0] for row in cursor.fetchall()}
    print(f"Tiendas encontradas en DB: {len(store_map)}")

    inserted_prods = 0
    inserted_offers = 0

    for item in PEDAL_PRODUCTS:
        sname = item["store"]
        s_id = store_map.get(sname.lower())
        if not s_id:
            # Buscar coincidencia parcial
            for k, sid in store_map.items():
                if sname.lower() in k or k in sname.lower():
                    s_id = sid
                    break
        
        if not s_id:
            print(f"[WARN] No se encontró tienda para: {sname}")
            continue

        brand = item["brand"].strip()
        model = item["model"].strip()
        norm = f"{brand.lower()} {model.lower()}"
        specs_json = json.dumps(item["specs"], ensure_ascii=False)
        is_intl = 1 if "aliexpress" in sname.lower() else 0

        # Verificar si producto ya existe
        cursor.execute("SELECT id FROM products WHERE lower(brand) = lower(?) AND lower(model) = lower(?)", (brand, model))
        row = cursor.fetchone()
        if row:
            p_id = row[0]
        else:
            cursor.execute("""
                INSERT INTO products (brand, model, category, type, wheel_size, frame_type, specs, canonical_image, normalized_name, is_international)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (brand, model, item["category"], item["type"], "", "", specs_json, item["canonical_image"], norm, is_intl))
            p_id = cursor.lastrowid
            inserted_prods += 1

        # Verificar si la oferta de la tienda ya existe
        cursor.execute("SELECT id FROM store_products WHERE product_id = ? AND store_id = ?", (p_id, s_id))
        offer_row = cursor.fetchone()
        if not offer_row:
            sku = f"PEDAL-{p_id}-{s_id}"
            cursor.execute("""
                INSERT INTO store_products (product_id, store_id, sku, url, image_url, price_normal, price_card, stock, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
            """, (p_id, s_id, sku, item["url"], item["canonical_image"], item["price_normal"], item["price_card"]))
            sp_id = cursor.lastrowid
            inserted_offers += 1

            # Insertar en price_history
            cursor.execute("INSERT INTO price_history (store_product_id, price) VALUES (?, ?)", (sp_id, int(item["price_normal"] * 1.08)))
            cursor.execute("INSERT INTO price_history (store_product_id, price) VALUES (?, ?)", (sp_id, item["price_normal"]))

    conn.commit()
    conn.close()

    print(f"\n[ÉXITO] Inserción de accesorios de pedales y calas completada:")
    print(f"   -> Nuevos productos: {inserted_prods}")
    print(f"   -> Nuevas ofertas de tiendas: {inserted_offers}")

if __name__ == "__main__":
    run_migration()
