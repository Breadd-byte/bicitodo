"""
refresh_prices.py - Re-verifica precios reales de cada oferta contra la web de la tienda.

Estrategia por plataforma:
  * Shopify (Faucon, CrossMountain, DS Bikes, Satiro, Bike New Sport, Trip Helmets):
      GET <url>.js  -> precio exacto, precio anterior (compare_at) y disponibilidad.
  * Resto (Copenhague/Jumpseller, BlueBike/Woo, Java/Bsale, Sparta, Full Bike, Oxford...):
      HTML -> JSON-LD Product.offers / meta product:price:amount.
  * 404 / 410            -> producto ya no existe  -> stock = 0
  * 403 / timeout / sin precio -> NO se toca (queda marcado como no verificado)

Cada cambio de precio real se registra en price_history.

Uso:
  python refresh_prices.py                 # todas las tiendas
  python refresh_prices.py --store Faucon  # solo tiendas cuyo nombre contiene 'Faucon'
  python refresh_prices.py --dry-run       # no guarda nada, solo reporta
  python refresh_prices.py --limit 50      # prueba rapida
"""
import argparse
import html as html_lib
import json
import os
import re
import sqlite3
import ssl
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database", "bicitodo.db")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-CL,es;q=0.9",
}
SHOPIFY_DOMAINS = {"fauconbikes.cl", "crossmountain.cl", "dsbikes.cl", "satirobikes.cl",
                   "bikenewsport.cl", "triphelmets.com"}
SKIP_DOMAINS = {"aliexpress.com", "es.aliexpress.com", "decathlon.cl", "ibikes.cl",
                "specialized.com"}  # bloquean (403) o renderizan precio con JS
# Bsale publica en JSON-LD el precio NETO (sin IVA) cuando tiene decimales
BSALE_DOMAINS = {"javabikes.cl"}
IVA = 1.19

_ctx = ssl.create_default_context()
_domain_locks = defaultdict(threading.Lock)
_domain_last = defaultdict(float)
MIN_INTERVAL = 0.35  # segundos entre requests al mismo dominio


class Gone(Exception):
    pass


def domain_of(url):
    d = urllib.parse.urlparse(url).netloc.lower()
    return d[4:] if d.startswith("www.") else d


def http_get(url, timeout=15):
    dom = domain_of(url)
    with _domain_locks[dom]:
        wait = MIN_INTERVAL - (time.time() - _domain_last[dom])
        if wait > 0:
            time.sleep(wait)
        _domain_last[dom] = time.time()
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_ctx) as r:
            return r.geturl(), r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        if e.code in (404, 410):
            raise Gone(str(e.code))
        raise


# ----------------------------------------------------------------- extractors
def from_shopify(url):
    parsed = urllib.parse.urlparse(url)
    variant_id = urllib.parse.parse_qs(parsed.query).get("variant", [None])[0]
    base = f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}"
    final_url, body = http_get(base + ".js")
    if "/products/" not in final_url:  # redirige al home/colección => no existe
        raise Gone("redirect")
    d = json.loads(body)
    variants = d.get("variants") or []
    v = None
    if variant_id:
        v = next((x for x in variants if str(x.get("id")) == str(variant_id)), None)
    if v is None:
        avail = [x for x in variants if x.get("available")] or variants
        v = min(avail, key=lambda x: x.get("price") or 0) if avail else None
    price = (v or d).get("price") or d.get("price")
    compare = (v or d).get("compare_at_price") or d.get("compare_at_price")
    return {
        "price": int(round(price / 100)) if price else None,
        "compare": int(round(compare / 100)) if compare else None,
        "available": bool(d.get("available")),
    }


def _to_int_price(val):
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    if re.fullmatch(r"\d+(\.\d+)?", s):
        return float(s)
    s = s.replace("$", "").replace(" ", "")
    if re.fullmatch(r"\d{1,3}(\.\d{3})+(,\d+)?", s):  # 1.234.567,00 formato CL
        return float(s.replace(".", "").replace(",", "."))
    if re.fullmatch(r"\d+,\d+", s):
        return float(s.replace(",", "."))
    return None


def _walk_ld(obj, out):
    if isinstance(obj, list):
        for o in obj:
            _walk_ld(o, out)
    elif isinstance(obj, dict):
        t = obj.get("@type")
        types = t if isinstance(t, list) else [t]
        if "Product" in types or "ProductGroup" in types:
            out.append(obj)
        for k in ("@graph", "hasVariant", "mainEntity"):
            if k in obj:
                _walk_ld(obj[k], out)


def from_html(url):
    final_url, page = http_get(url)
    final_path = urllib.parse.urlparse(final_url).path.rstrip("/")
    orig_path = urllib.parse.urlparse(url).path.rstrip("/")
    if final_path in ("", "/"):
        raise Gone("redirect-home")
    if final_path != orig_path and re.search(r"/(collections?|categoria|category|catalog)\b", final_path):
        raise Gone("redirect-collection")

    prices, available = [], None
    products = []
    for block in re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', page, re.S | re.I):
        try:
            _walk_ld(json.loads(html_lib.unescape(block.strip())), products)
        except Exception:  # noqa: BLE001
            continue
    for prod in products:
        offers = prod.get("offers") or []
        offers = offers if isinstance(offers, list) else [offers]
        for off in offers:
            if not isinstance(off, dict):
                continue
            for key in ("price", "lowPrice"):
                p = _to_int_price(off.get(key))
                if p:
                    prices.append(p)
            av = str(off.get("availability", "")).lower()
            if av:
                in_stock = "instock" in av or "preorder" in av
                available = in_stock if available is None else (available or in_stock)

    if not prices:
        m = re.search(r'product:price:amount"\s+content="([0-9\.,]+)"', page) or \
            re.search(r'itemprop="price"\s+content="([0-9\.,]+)"', page)
        if m:
            p = _to_int_price(m.group(1))
            if p:
                prices.append(p)

    if not prices:
        return None

    dom = domain_of(url)
    if dom in BSALE_DOMAINS:
        gross = [p for p in prices if p == int(p)]
        price = min(gross) if gross else min(prices) * IVA
    else:
        price = min(prices)

    compare = None
    m = re.search(r'(?:compare|regular|old|before|tachado)[^>]{0,80}>\s*\$\s*([0-9\.]{4,})', page, re.I)
    if m:
        c = _to_int_price(m.group(1))
        if c and c > price:
            compare = int(round(c))

    return {"price": int(round(price)), "compare": compare,
            "available": True if available is None else available}


def check_offer(url):
    dom = domain_of(url)
    if any(dom == s or dom.endswith("." + s) for s in SKIP_DOMAINS):
        return "skip", None
    if "/search" in url or "wholesale" in url or "/collections/" in url:
        return "bad_url", None
    try:
        data = from_shopify(url) if dom in SHOPIFY_DOMAINS else from_html(url)
    except Gone:
        return "gone", None
    except Exception as e:  # noqa: BLE001
        return "error", str(e)[:60]
    if not data or not data.get("price"):
        return "no_price", None
    return "ok", data


# ----------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", help="Filtra tiendas por nombre (contiene)")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    conn = sqlite3.connect(DB_PATH, timeout=30)
    cur = conn.cursor()
    q = """SELECT sp.id, sp.url, sp.price_normal, sp.price_card, sp.stock, s.name
           FROM store_products sp JOIN stores s ON s.id = sp.store_id
           WHERE sp.url LIKE 'http%'"""
    params = []
    if args.store:
        q += " AND LOWER(s.name) LIKE ?"
        params.append(f"%{args.store.lower()}%")
    q += " ORDER BY s.name"
    if args.limit:
        q += f" LIMIT {int(args.limit)}"
    rows = cur.execute(q, params).fetchall()
    print(f"Verificando {len(rows)} ofertas con {args.workers} hilos...\n")

    stats = defaultdict(Counter)
    changes = []
    big_changes = []
    t0 = time.time()

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(check_offer, r[1]): r for r in rows}
        for i, fut in enumerate(as_completed(futs), 1):
            sp_id, url, old_price, old_card, old_stock, store = futs[fut]
            status, data = fut.result()
            stats[store][status] += 1
            if status == "ok":
                new_price, new_card = data["price"], data["compare"]
                if new_card and new_card <= new_price:
                    new_card = None
                new_stock = 1 if data["available"] else 0
                if new_price != old_price:
                    stats[store]["price_changed"] += 1
                    diff = (new_price - old_price) / old_price if old_price else 1
                    if abs(diff) > 0.4:
                        big_changes.append((store, old_price, new_price, url))
                changes.append(("ok", sp_id, new_price, new_card, new_stock, old_price))
            elif status == "gone":
                changes.append(("gone", sp_id, None, None, 0, old_price))
            if i % 250 == 0:
                print(f"  {i}/{len(rows)}  ({time.time() - t0:.0f}s)")

    if not args.dry_run:
        for kind, sp_id, price, card, stock, old_price in changes:
            if kind == "ok":
                cur.execute("""UPDATE store_products SET price_normal=?, price_card=?, stock=?,
                               last_updated=CURRENT_TIMESTAMP WHERE id=?""", (price, card, stock, sp_id))
                if price != old_price:
                    cur.execute("INSERT INTO price_history (store_product_id, price) VALUES (?, ?)",
                                (sp_id, price))
            else:
                cur.execute("UPDATE store_products SET stock=0, last_updated=CURRENT_TIMESTAMP WHERE id=?",
                            (sp_id,))
        conn.commit()
    conn.close()

    print(f"\n{'Tienda':<28}{'ok':>6}{'cambio$':>9}{'gone':>6}{'sinPrecio':>10}{'error':>7}{'skip':>6}")
    tot = Counter()
    for store, c in sorted(stats.items()):
        tot.update(c)
        print(f"{store:<28}{c['ok']:>6}{c['price_changed']:>9}{c['gone']:>6}{c['no_price']:>10}"
              f"{c['error']:>7}{c['skip'] + c['bad_url']:>6}")
    print(f"{'TOTAL':<28}{tot['ok']:>6}{tot['price_changed']:>9}{tot['gone']:>6}{tot['no_price']:>10}"
          f"{tot['error']:>7}{tot['skip'] + tot['bad_url']:>6}")
    if big_changes:
        print(f"\nCambios > 40% (revisar): {len(big_changes)}")
        for b in big_changes[:15]:
            print("  ", b)
    print(("\n[DRY-RUN] nada guardado." if args.dry_run else "\nCambios guardados.") +
          f"  Tiempo: {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
