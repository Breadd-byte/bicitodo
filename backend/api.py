# api.py - Dynamic High-Performance FastAPI Backend for BiciTodo
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
import sqlite3
import json
import os
from collections import defaultdict

app = FastAPI(
    title="BiciTodo API",
    description="API dinámica y de alto rendimiento para el comparador de precios de ciclismo en Chile",
    version="1.0.0"
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Permite solicitudes desde cualquier origen para desarrollo local
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database", "bicitodo.db")

# Configuración de Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL", "TU_SUPABASE_URL_AQUÍ")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "TU_SUPABASE_KEY_AQUÍ")

# Cliente Supabase
supabase_client: Client = None
if SUPABASE_URL != "TU_SUPABASE_URL_AQUÍ" and SUPABASE_KEY != "TU_SUPABASE_KEY_AQUÍ":
    try:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("[Supabase] Conectado exitosamente en la API.")
    except Exception as e:
        print(f"[Supabase] Error de conexión: {e}")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def build_product_summary(row, full_specs):
    parts = []
    product_type = row["type"]
    frame_type = row["frame_type"]
    wheel_size = row["wheel_size"]

    if product_type:
        parts.append(str(product_type).title())
    if frame_type:
        parts.append(str(frame_type))
    if wheel_size:
        wheel_label = str(wheel_size)
        parts.append(wheel_label if wheel_label.lower().startswith("aro") else f"Aro {wheel_label}")

    if not parts and full_specs:
        for key in ("Transmision", "Transmisión", "Cuadro", "Horquilla"):
            value = full_specs.get(key)
            if value:
                parts.append(str(value))
            if len(parts) >= 2:
                break

    if not parts:
        parts.append(f"{row['brand']} {row['model']}")

    return " • ".join(parts[:3])

def normalize_store_key(store_name):
    key = (store_name or "").lower().replace(" ", "").replace("_", "").replace("-", "")
    aliases = {
        "oxfordstore": "oxford",
        "trekchile": "trek",
        "specializedchile": "specialized",
        "totemchile": "totem",
        "fauconbikes": "faucon",
        "satirobikes": "satiro",
        "dsbikes": "dsbikes",
        "vidaurrebikes": "vidaurre",
        "mercadolibre": "mercadolibre",
        "aliexpress": "aliexpress",
        "bikeplus": "bikeplus",
        "bikeshop": "bikeshop",
        "fullbike": "fullbike",
    }
    return aliases.get(key, key)

@app.get("/api/stats")
async def get_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        counts = {}
        for category in ("bicicletas", "accesorios", "repuestos"):
            cursor.execute("SELECT COUNT(*) as total FROM products WHERE category = ?", (category,))
            counts[category] = cursor.fetchone()["total"]
        cursor.execute("SELECT COUNT(*) as total FROM stores")
        counts["tiendas"] = cursor.fetchone()["total"]
        return counts
    finally:
        conn.close()

@app.get("/api/productos")
async def get_productos(
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(20, ge=1, le=100, description="Productos por página"),
    tienda: str = Query(None, description="Filtrar por tienda o lista de tiendas (separadas por coma)"),
    categoria: str = Query(None, description="Filtrar por categoría (bicicletas, accesorios, repuestos)"),
    search: str = Query(None, description="Término de búsqueda"),
    price_min: int = Query(None, description="Precio mínimo"),
    price_max: int = Query(None, description="Precio máximo"),
    brand: str = Query(None, description="Filtrar por marca o lista de marcas (separadas por coma)"),
    tipo: str = Query(None, description="Filtrar por tipo/subcategoria o lista de tipos (separados por coma)"),
    aro: str = Query(None, description="Filtrar por tamano de aro o lista de aros (separados por coma)"),
    sort_by: str = Query("relevant", description="Ordenamiento: relevant, price-asc, price-desc, discount, stores"),
    discount_min: int = Query(None, description="Descuento mínimo en porcentaje"),
    internacional: bool = Query(None, description="Filtrar por internacional (AliExpress)"),
    quick_filter: str = Query(None, description="Filtro rápido de AliExpress: bestseller, toprated, trends, value")
):
    """
    Endpoint de búsqueda y paginación dinámico de alto rendimiento.
    - Soporta múltiples filtros dinámicos (tienda, marca, precio, búsqueda por texto).
    - Implementa mezcla equitativa (Fair Mix) de tiendas en el Home mediante ROW_NUMBER() si no hay filtros activos.
    - Soporta ordenamiento por relevancia, precio y mayor descuento.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Construcción dinámica de filtros WHERE
        where_clauses = []
        where_params = []
        
        # Filtro de categoría
        if categoria:
            where_clauses.append("p.category = ?")
            where_params.append(categoria)
            
        # Filtro de tiendas (soporta múltiples separadas por coma)
        if tienda:
            stores_list = [t.strip().lower().replace(" ", "").replace("_", "") for t in tienda.split(",")]
            placeholders = ",".join("?" for _ in stores_list)
            # En la base de datos limpiamos el nombre para comparar con storeKey
            where_clauses.append(f"LOWER(REPLACE(REPLACE(s.name, ' ', ''), '_', '')) IN ({placeholders})")
            where_params.extend(stores_list)
            
        # Filtro de marcas (soporta múltiples separadas por coma)
        if brand:
            brands_list = [b.strip().lower() for b in brand.split(",")]
            placeholders = ",".join("?" for _ in brands_list)
            where_clauses.append(f"LOWER(p.brand) IN ({placeholders})")
            where_params.extend(brands_list)

        # Filtro de tipo/subcategoria
        if tipo:
            types_list = [t.strip().lower() for t in tipo.split(",") if t.strip()]
            if types_list:
                placeholders = ",".join("?" for _ in types_list)
                where_clauses.append(f"LOWER(p.type) IN ({placeholders})")
                where_params.extend(types_list)

        # Filtro de aro para bicicletas
        if aro:
            wheel_list = [w.strip().lower() for w in aro.split(",") if w.strip()]
            if wheel_list:
                placeholders = ",".join("?" for _ in wheel_list)
                where_clauses.append(f"LOWER(COALESCE(p.wheel_size, '')) IN ({placeholders})")
                where_params.extend(wheel_list)
            
        # Filtro de rango de precio
        if price_min is not None:
            where_clauses.append("pco.price_normal >= ?")
            where_params.append(price_min)
        if price_max is not None:
            where_clauses.append("pco.price_normal <= ?")
            where_params.append(price_max)
            
        # Filtro de búsqueda por texto (búsqueda de marca o modelo)
        if search:
            search_query = f"%{search.lower()}%"
            where_clauses.append("(LOWER(p.brand) LIKE ? OR LOWER(p.model) LIKE ?)")
            where_params.extend([search_query, search_query])

        # Filtro de descuento mínimo
        if discount_min is not None:
            where_clauses.append("pco.price_card IS NOT NULL AND pco.price_card > 0 AND ((CAST(pco.price_card AS REAL) - pco.price_normal) / pco.price_card) * 100 >= ?")
            where_params.append(discount_min)

        # Filtro de internacionalidad (AliExpress vs Tiendas Locales)
        if internacional is True:
            where_clauses.append("p.is_international = 1")
        else:
            where_clauses.append("p.is_international = 0")

        # Filtro rápido para AliExpress
        if quick_filter:
            if quick_filter == "bestseller":
                where_clauses.append("p.sales_count >= 1000")
            elif quick_filter == "toprated":
                where_clauses.append("p.rating >= 4.8")
            elif quick_filter == "trends":
                where_clauses.append("p.sales_count >= 500 AND p.discount_percent >= 25")
            elif quick_filter == "value":
                where_clauses.append("p.rating >= 4.7 AND pco.price_normal <= 100000")

        # Determinar si hay filtros activos
        has_filters = 1 if (categoria or tienda or brand or tipo or aro or price_min is not None or price_max is not None or search or discount_min is not None or internacional is True or quick_filter) else 0

        # Cláusula WHERE final
        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        # Ordenamiento dinámico
        order_sql = "ORDER BY rn, store_id"
        if sort_by == "price-asc":
            order_sql = "ORDER BY price_normal ASC"
        elif sort_by == "price-desc":
            order_sql = "ORDER BY price_normal DESC"
        elif sort_by == "discount":
            order_sql = "ORDER BY (CAST(price_card AS REAL) - price_normal) / price_card DESC"
        elif sort_by == "stores":
            order_sql = "ORDER BY offer_count DESC, price_normal ASC"
        elif sort_by == "sales":
            order_sql = "ORDER BY sales_count DESC"
        elif sort_by == "rating":
            order_sql = "ORDER BY rating DESC"

        # 1. Query para contar total de resultados
        count_query = f"""
        WITH ProductCheapestOffer AS (
            SELECT 
                sp.product_id,
                sp.store_id,
                sp.price_normal,
                sp.price_card,
                ROW_NUMBER() OVER (PARTITION BY sp.product_id ORDER BY sp.price_normal ASC) as price_rn
            FROM store_products sp
        ),
        RankedProducts AS (
            SELECT 
                p.id,
                pco.store_id,
                ROW_NUMBER() OVER (PARTITION BY pco.store_id ORDER BY p.id DESC) as rn
            FROM products p
            JOIN ProductCheapestOffer pco ON p.id = pco.product_id AND pco.price_rn = 1
            JOIN stores s ON pco.store_id = s.id
            {where_sql}
        )
        SELECT COUNT(*) as total FROM RankedProducts
        WHERE ({has_filters} = 1 OR rn <= 5);
        """
        cursor.execute(count_query, where_params)
        total_products = cursor.fetchone()["total"]
        
        total_pages = max(1, (total_products + limit - 1) // limit)
        if page > total_pages:
            page = total_pages
            
        offset = (page - 1) * limit

        # 2. Query principal para obtener productos paginados
        main_query = f"""
        WITH ProductCheapestOffer AS (
            SELECT 
                sp.product_id,
                sp.store_id,
                sp.price_normal,
                sp.price_card,
                ROW_NUMBER() OVER (PARTITION BY sp.product_id ORDER BY sp.price_normal ASC) as price_rn
            FROM store_products sp
        ),
        RankedProducts AS (
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
                p.rating,
                p.sales_count,
                p.review_count,
                p.discount_percent,
                p.is_international,
                pco.store_id,
                pco.price_normal,
                pco.price_card,
                (SELECT COUNT(*) FROM store_products spc WHERE spc.product_id = p.id) as offer_count,
                ROW_NUMBER() OVER (PARTITION BY pco.store_id ORDER BY p.id DESC) as rn
            FROM products p
            JOIN ProductCheapestOffer pco ON p.id = pco.product_id AND pco.price_rn = 1
            JOIN stores s ON pco.store_id = s.id
            {where_sql}
        )
        SELECT id, brand, model, category, type, wheel_size, frame_type, specs, canonical_image, rating, sales_count, review_count, discount_percent, is_international
        FROM RankedProducts
        WHERE ({has_filters} = 1 OR rn <= 5)
        {order_sql}
        LIMIT ? OFFSET ?;
        """
        # Añadir limit y offset a los parámetros
        main_params = list(where_params)
        main_params.extend([limit, offset])
        
        cursor.execute(main_query, main_params)
        products_rows = cursor.fetchall()
        
        if not products_rows:
            return {"productos": [], "total_pages": total_pages, "current_page": page, "total_count": 0}

        # 3. Obtener las ofertas de todas las tiendas para los productos seleccionados en la página
        product_ids = [row["id"] for row in products_rows]
        placeholders = ",".join("?" for _ in product_ids)
        
        offers_query = f"""
        SELECT 
            sp.product_id,
            sp.price_normal,
            sp.price_card,
            sp.url,
            sp.image_url,
            s.name as store_name,
            s.id as store_id
        FROM store_products sp
        JOIN stores s ON sp.store_id = s.id
        WHERE sp.product_id IN ({placeholders})
        ORDER BY sp.price_normal ASC;
        """
        cursor.execute(offers_query, product_ids)
        offers_rows = cursor.fetchall()
        
        offers_by_product = defaultdict(list)
        for o in offers_rows:
            store_key = normalize_store_key(o["store_name"])
            offers_by_product[o["product_id"]].append({
                "store": o["store_name"],
                "storeKey": store_key,
                "price": o["price_normal"],
                "oldPrice": o["price_card"],
                "url": o["url"],
                "imageUrl": o["image_url"]
            })

        # 4. Obtener los historiales de precios para los productos de la página
        history_query = f"""
        SELECT 
            sp.product_id,
            ph.price
        FROM price_history ph
        JOIN store_products sp ON ph.store_product_id = sp.id
        WHERE sp.product_id IN ({placeholders})
        ORDER BY ph.timestamp ASC;
        """
        cursor.execute(history_query, product_ids)
        history_rows = cursor.fetchall()
        
        history_by_product = defaultdict(list)
        for h in history_rows:
            history_by_product[h["product_id"]].append(h["price"])

        # 5. Construir la lista final de productos en el formato del frontend
        productos_list = []
        for row in products_rows:
            pid = row["id"]
            p_offers = offers_by_product[pid]
            p_history = history_by_product[pid]
            
            if not p_history and p_offers:
                best_price = p_offers[0]["price"]
                p_history = [int(best_price * 1.08), int(best_price * 1.04), best_price]
                
            p_history = p_history[-6:]
            
            try:
                full_specs = json.loads(row["specs"]) if row["specs"] else {}
            except Exception:
                full_specs = {}

            product_obj = {
                "id": pid,
                "brand": row["brand"],
                "model": row["model"],
                "category": row["category"],
                "type": row["type"],
                "wheelSize": row["wheel_size"] or "",
                "frameType": row["frame_type"] or "",
                "specs": build_product_summary(row, full_specs),
                "image": row["canonical_image"],
                "history": p_history,
                "fullSpecs": full_specs,
                "offers": p_offers,
                "isInternational": bool(row["is_international"]),
                "rating": row["rating"] or 4.5,
                "sales_count": row["sales_count"] or 100,
                "review_count": row["review_count"] or 15,
                "discount_percent": row["discount_percent"] or 0
            }
            productos_list.append(product_obj)

        # Get brand counts for the active category (to keep filter panel accurate)
        brand_counts = {}
        is_intl_val = 1 if internacional is True else 0
        if categoria:
            cursor.execute("SELECT brand, COUNT(*) as cnt FROM products WHERE category = ? AND is_international = ? GROUP BY brand", (categoria, is_intl_val))
            for r in cursor.fetchall():
                if r["brand"]:
                    brand_counts[r["brand"]] = r["cnt"]

        # Get subcategory/type counts
        type_counts = {}
        if categoria:
            cursor.execute("SELECT type, COUNT(*) as cnt FROM products WHERE category = ? AND is_international = ? GROUP BY type", (categoria, is_intl_val))
            for r in cursor.fetchall():
                if r["type"]:
                    type_counts[r["type"]] = r["cnt"]

        return {
            "productos": productos_list,
            "total_pages": total_pages,
            "current_page": page,
            "total_count": total_products,
            "brands": brand_counts,
            "types": type_counts
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")
    finally:
        conn.close()

class AlertaSchema(BaseModel):
    email_usuario: str
    id_producto: int
    precio_actual: int

@app.post("/api/crear-alerta")
async def crear_alerta(alerta: AlertaSchema):
    if not supabase_client:
        raise HTTPException(
            status_code=503, 
            detail="El servicio de alertas en la nube (Supabase) no está configurado."
        )
    try:
        data = {
            "email_usuario": alerta.email_usuario,
            "id_producto": alerta.id_producto,
            "precio_actual": alerta.precio_actual
        }
        response = supabase_client.table("alertas").insert(data).execute()
        return {"status": "success", "message": "Alerta registrada correctamente", "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al registrar alerta en Supabase: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    # Iniciar servidor local de prueba en el puerto 8000
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
