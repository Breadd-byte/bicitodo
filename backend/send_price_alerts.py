import os
import sqlite3
import json
from supabase import create_client, Client
from services.notifier import enviar_alerta_precio

# Configuration
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database", "bicitodo.db")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "TU_SUPABASE_URL_AQUÍ")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "TU_SUPABASE_KEY_AQUÍ")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def main():
    print("=" * 60)
    print("[send_price_alerts] INICIANDO DESPACHADOR DE ALERTAS DE SUPABASE & BREVO")
    print("=" * 60)
    
    if SUPABASE_URL == "TU_SUPABASE_URL_AQUÍ" or SUPABASE_KEY == "TU_SUPABASE_KEY_AQUÍ":
        print("[ERROR] Supabase URL o Key no configurados en las variables de entorno.")
        print("Asegúrate de exportar SUPABASE_URL y SUPABASE_KEY en tu terminal o sistema.")
        return

    # 1. Initialize Supabase
    try:
        supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("[Supabase] Conectado exitosamente.")
    except Exception as e:
        print(f"[Supabase] Error al conectar: {e}")
        return

    # 2. Fetch all active alerts from Supabase
    try:
        response = supabase_client.table("alertas").select("*").execute()
        alertas = response.data
        print(f"[Supabase] Se obtuvieron {len(alertas)} alertas activas desde la nube.")
    except Exception as e:
        print(f"[Supabase] Error al obtener alertas: {e}")
        return

    if not alertas:
        print("No hay alertas activas registradas en la base de datos de Supabase. Finalizando.")
        return

    # 3. Connect to local SQLite DB
    conn = get_db_connection()
    cursor = conn.cursor()

    notified_count = 0
    errors_count = 0

    print("\nProcesando alertas...")
    for idx, alerta in enumerate(alertas, start=1):
        alerta_id = alerta["id"]
        email = alerta["email_usuario"]
        prod_id = alerta["id_producto"]
        precio_limite = alerta["precio_actual"]
        
        print(f"\n[{idx}/{len(alertas)}] Alerta ID: {alerta_id} | Usuario: {email} | Producto ID: {prod_id}")
        
        # Get local product details
        cursor.execute("SELECT brand, model FROM products WHERE id = ?", (prod_id,))
        prod_row = cursor.fetchone()
        if not prod_row:
            print(f"  [ADVERTENCIA] Producto ID {prod_id} no encontrado en la base de datos local SQLite. Saltando.")
            continue
            
        nombre_producto = f"{prod_row['brand']} {prod_row['model']}"
        
        # Get cheapest offer from local SQLite store_products
        cursor.execute("""
            SELECT price_normal, url, price_card
            FROM store_products
            WHERE product_id = ?
            ORDER BY price_normal ASC
            LIMIT 1
        """, (prod_id,))
        offer_row = cursor.fetchone()
        
        if not offer_row:
            print(f"  [ADVERTENCIA] No hay ofertas activas locales para el producto ID {prod_id}. Saltando.")
            continue
            
        precio_actual = offer_row["price_normal"]
        url_producto = offer_row["url"]
        precio_antiguo = offer_row["price_card"] or int(precio_actual * 1.15) # Fallback si no tiene precio anterior

        print(f"  Precio límite usuario: ${precio_limite:,}")
        print(f"  Precio actual tienda:  ${precio_actual:,}")
        
        # 4. Check price drop condition
        if precio_actual <= precio_limite:
            print(f"  [BAJA DE PRECIO DETECTADA] ¡Enviando alerta a {email}!")
            
            # Send email using our notifier service (Brevo API)
            success = enviar_alerta_precio(
                email_usuario=email,
                nombre_producto=nombre_producto,
                precio_antiguo=int(precio_antiguo),
                precio_nuevo=int(precio_actual),
                url_producto=url_producto
            )
            
            if success:
                notified_count += 1
                # Opcional: Eliminar la alerta en Supabase para no enviar repetidos, o dejarla activa
                # Para un flujo habitual de un solo aviso, se suele eliminar:
                try:
                    supabase_client.table("alertas").delete().eq("id", alerta_id).execute()
                    print(f"  [Supabase] Alerta ID {alerta_id} eliminada tras notificación exitosa.")
                except Exception as e:
                    print(f"  [ADVERTENCIA] No se pudo eliminar la alerta {alerta_id} de Supabase: {e}")
            else:
                errors_count += 1
        else:
            print("  El precio actual aún no alcanza el objetivo del usuario.")

    conn.close()
    
    print("\n" + "=" * 60)
    print(f"[send_price_alerts] COMPLETO!")
    print(f"  - Alertas notificadas con éxito: {notified_count}")
    print(f"  - Errores de envío: {errors_count}")
    print("=" * 60)

if __name__ == "__main__":
    main()
