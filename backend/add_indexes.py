import sqlite3
import os

DB_PATH = r"c:\Users\basti\Desktop\bicitodo\backend\database\bicitodo.db"

def main():
    print("==================================================")
    print("[>] INICIANDO OPTIMIZACION DE BASE DE DATOS (SQLITE)")
    print("==================================================")
    
    if not os.path.exists(DB_PATH):
        print(f"[x] Base de datos no encontrada en {DB_PATH}")
        return
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Define indexes to create
    indexes = [
        # Indexes on products table
        ("idx_products_category", "products(category)"),
        ("idx_products_is_international", "products(is_international)"),
        ("idx_products_brand", "products(brand)"),
        ("idx_products_type", "products(type)"),
        ("idx_products_normalized_name", "products(normalized_name)"),
        
        # Indexes on store_products table
        ("idx_store_products_product_id", "store_products(product_id)"),
        ("idx_store_products_store_id", "store_products(store_id)"),
        ("idx_store_products_price_normal", "store_products(price_normal)"),
        ("idx_store_products_price_card", "store_products(price_card)"),
        
        # Indexes on price_history table
        ("idx_price_history_store_product_id", "price_history(store_product_id)")
    ]
    
    created_count = 0
    for index_name, target in indexes:
        try:
            print(f"[+] Creando indice {index_name} en {target}...")
            cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {target};")
            created_count += 1
        except Exception as e:
            print(f"  [x] Error al crear {index_name}: {str(e)}")
            
    # Apply vacuum to rebuild database file with indexes
    print("[+] Ejecutando VACUUM para reconstruir y desfragmentar la base de datos...")
    cursor.execute("VACUUM;")
    
    # Run ANALYZE to update SQLite query planner statistics
    print("[+] Ejecutando ANALYZE para actualizar las estadisticas del optimizador...")
    cursor.execute("ANALYZE;")
    
    conn.commit()
    conn.close()
    
    print("\n[+] Base de datos optimizada con éxito.")
    print(f"  - Total indices creados/verificados: {created_count}")
    print("==================================================")

if __name__ == "__main__":
    main()
