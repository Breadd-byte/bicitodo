import sqlite3
import re
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database", "bicitodo.db")

def repair_brands():
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}")
        return
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    rows = cursor.execute("SELECT id, brand, model FROM products WHERE brand IN ('Genérica', 'Generica')").fetchall()
    
    print(f"Checking {len(rows)} products for brand repair...")
    repaired = 0
    
    known_brands = [
        "Scott", "Trek", "Specialized", "Giant", "Van Rysel", 
        "Knog", "Rockbros", "Slime", "Vittoria", "Pirelli", 
        "Maxxis", "Continental", "Chaoyang", "Arisun", "Eclat", 
        "Shimano", "SRAM", "Bontrager", "Oxford", "State Bicycle Co"
    ]
    
    for r in rows:
        row_id = r["id"]
        brand = r["brand"]
        model = r["model"]
        
        matched_brand = None
        for kb in known_brands:
            if re.search(r'\b' + re.escape(kb) + r'\b', model, re.IGNORECASE):
                matched_brand = kb
                break
                
        if matched_brand:
            # Clean model name
            # Remove "Bicicleta" (case insensitive, full word)
            cleaned_model = re.sub(r'\bBicicleta\b', '', model, flags=re.IGNORECASE)
            # Remove the matched brand name (case insensitive, full word)
            cleaned_model = re.sub(r'\b' + re.escape(matched_brand) + r'\b', '', cleaned_model, flags=re.IGNORECASE)
            # Clean extra spaces
            cleaned_model = re.sub(r'\s+', ' ', cleaned_model).strip()
            
            # Brand stored in upper case in database (e.g. SCOTT)
            brand_upper = matched_brand.upper()
            normalized_name = f"{brand_upper.lower()} {cleaned_model.lower()}"
            
            print(f"Repaired ID {row_id}: '{brand}' + '{model}' -> '{brand_upper}' + '{cleaned_model}'")
            
            cursor.execute(
                "UPDATE products SET brand = ?, model = ?, normalized_name = ? WHERE id = ?",
                (brand_upper, cleaned_model, normalized_name, row_id)
            )
            repaired += 1
            
    conn.commit()
    conn.close()
    print(f"Total repaired brand products: {repaired}")

if __name__ == "__main__":
    repair_brands()
