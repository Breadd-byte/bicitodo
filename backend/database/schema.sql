-- BiciTodo SQLite Schema — Actualizado v2.0
-- Refleja la estructura real de bicitodo.db usada por api.py
-- NOTA: Este proyecto usa SQLite (no PostgreSQL). El schema original tenía sintaxis PG incorrecta.

-- 1. Stores Table
CREATE TABLE IF NOT EXISTS stores (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name  TEXT UNIQUE NOT NULL,
    url   TEXT,
    last_scrape TEXT -- ISO 8601 timestamp string
);

-- 2. Products Table (Canonical/Normalized products)
-- Cada fila representa un producto único sin importar en cuántas tiendas aparezca.
CREATE TABLE IF NOT EXISTS products (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    brand            TEXT,
    model            TEXT NOT NULL,
    category         TEXT,           -- 'bicicletas' | 'accesorios' | 'repuestos'
    type             TEXT,           -- 'mtb' | 'ruta' | 'gravel' | 'fixie' | 'urbana' | 'hibrida' | 'infantil' | 'electrica'
    wheel_size       TEXT,           -- '26' | '27.5' | '29' | '700c' | etc.
    frame_type       TEXT,           -- Material del cuadro: 'aluminio' | 'carbono' | 'acero'
    specs            TEXT,           -- JSON serializado con especificaciones técnicas completas
    canonical_image  TEXT,           -- URL de imagen de alta calidad representativa del producto
    normalized_name  TEXT UNIQUE,    -- Nombre normalizado para matching y búsquedas
    is_international INTEGER DEFAULT 0, -- 1 = AliExpress/Internacional, 0 = Tienda local chilena
    rating           REAL DEFAULT 4.5,  -- Calificación promedio (0.0 – 5.0)
    sales_count      INTEGER DEFAULT 0, -- Número de ventas registradas
    review_count     INTEGER DEFAULT 0, -- Número de reseñas
    discount_percent INTEGER DEFAULT 0  -- Porcentaje de descuento calculado
);

-- 3. Store Products Table (Ofertas específicas por tienda)
-- Cada fila es una oferta de un producto en una tienda concreta.
CREATE TABLE IF NOT EXISTS store_products (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id   INTEGER REFERENCES products(id) ON DELETE CASCADE,
    store_id     INTEGER REFERENCES stores(id) ON DELETE CASCADE,
    sku          TEXT,
    url          TEXT NOT NULL,
    image_url    TEXT,
    price_normal INTEGER,            -- Precio actual de venta
    price_card   INTEGER,            -- Precio tachado / precio antes del descuento
    stock        INTEGER DEFAULT 1,  -- 1 = con stock, 0 = sin stock
    last_updated TEXT DEFAULT (datetime('now')), -- ISO 8601
    UNIQUE(store_id, sku)
);

-- 4. Price History Table (Para gráficos de evolución de precios)
CREATE TABLE IF NOT EXISTS price_history (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    store_product_id INTEGER REFERENCES store_products(id) ON DELETE CASCADE,
    price            INTEGER NOT NULL,
    timestamp        TEXT DEFAULT (datetime('now')) -- ISO 8601
);

-- ============================================================
-- ÍNDICES DE RENDIMIENTO
-- Cubren los filtros más usados en /api/productos
-- ============================================================

-- Filtros principales de catálogo
CREATE INDEX IF NOT EXISTS idx_products_category    ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_brand       ON products(brand);
CREATE INDEX IF NOT EXISTS idx_products_type        ON products(type);
CREATE INDEX IF NOT EXISTS idx_products_wheel_size  ON products(wheel_size);
CREATE INDEX IF NOT EXISTS idx_products_intl        ON products(is_international);

-- Filtros de calidad y ordenamiento
CREATE INDEX IF NOT EXISTS idx_products_rating      ON products(rating);
CREATE INDEX IF NOT EXISTS idx_products_sales       ON products(sales_count);
CREATE INDEX IF NOT EXISTS idx_products_discount    ON products(discount_percent);

-- Precios en store_products (usado en JOINs y ORDER BY)
CREATE INDEX IF NOT EXISTS idx_store_products_price    ON store_products(price_normal);
CREATE INDEX IF NOT EXISTS idx_store_products_product  ON store_products(product_id);
CREATE INDEX IF NOT EXISTS idx_store_products_store    ON store_products(store_id);

-- Historial de precios
CREATE INDEX IF NOT EXISTS idx_price_history_store_product ON price_history(store_product_id);
