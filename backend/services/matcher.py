# matcher.py - Matching Engine Central v2.0
# Soporta marcas premium, nacionales y genéricas del mercado chileno
import re
import difflib
import unicodedata

class ProductMatcher:
    def __init__(self, threshold=0.85):
        self.threshold = threshold
        
        # ===== MARCAS PREMIUM INTERNACIONALES =====
        self.brands_premium = [
            "Trek", "Specialized", "Giant", "Scott", "Merida", "Cannondale",
            "Kona", "Orbea", "Cube", "Santa Cruz", "Yeti", "Pivot", "Ibis",
            "Rocky Mountain", "Norco", "Intense", "Evil", "Transition",
            "Cervelo", "Pinarello", "Colnago", "BMC", "Factor", "Canyon",
            "Bianchi", "Wilier", "De Rosa", "Look", "Time", "Marin", "Liv",
            "Polygon", "Ridley", "Mondraker", "Devinci", "Fantic", "Patrol",
            "Dominate",
        ]
        
        # ===== MARCAS NACIONALES / RECONOCIDAS EN CHILE =====
        self.brands_nacional = [
            "Oxford", "Sparta", "Faucon", "Sátiro", "Satiro", "Totem",
            "Lahsen", "Benotto", "Topmega", "Kuwahara", "Raleigh",
            "Turbo", "Haro", "GT", "Jeep", "Caloi", "Clifford", "Kross",
            "Twitter", "Trinx", "Sunpeed", "Java", "Battle", "Chillafish",
            "Globber", "State Bicycle Co", "State Bicycle", "Sátiro Bikes",
            "DS Bikes", "Dsbikes",
        ]
        
        # ===== MARCAS RETAIL (Decathlon y otras) =====
        self.brands_retail = [
            "Rockrider", "Btwin", "B'Twin", "Van Rysel", "Triban", "Elops",
            "Oxelo", "Domyos",                        # Decathlon
            "Volcom", "Upland",                        # Otras retail
        ]
        
        # ===== MARCAS DE COMPONENTES =====
        self.brands_componentes = [
            "Shimano", "SRAM", "Campagnolo", "Maxxis", "Schwalbe",
            "Continental", "Michelin", "WTB", "Race Face", "RockShox",
            "Fox", "Manitou", "Marzocchi", "Formula", "Hope", "Magura",
            "TRP", "Tektro", "Hayes", "Avid",
        ]
        
        # Lista completa unificada (para get_brand)
        self.brands = (
            self.brands_premium + self.brands_nacional +
            self.brands_retail + self.brands_componentes
        )
        
        # Alias de normalización (para homologar variantes de escritura)
        self.brand_aliases = {
            "satiro": "Sátiro",
            "b'twin": "Btwin",
            "btwin": "Btwin",
            "aro": "",        # "aro" es ruido en nombres
            "shimano": "Shimano",
        }
        
        # Palabras ruidosas a eliminar en normalización
        self.noise_words = [
            "bicicleta", "bici", "aros", "pulgadas", "modelo",
            "temporada", "2026", "2025", "2024", "2023",
            "nueva", "nuevo", "color", "negro", "blanco", "rojo", "azul",
            "mountain", "bike", "bicycle",
        ]

    def remove_accents(self, text):
        """Elimina acentos: á→a, é→e, ú→u, ñ→n, etc."""
        nfkd_form = unicodedata.normalize('NFKD', text)
        return ''.join([c for c in nfkd_form if not unicodedata.combining(c)])

    def normalize(self, text):
        """Normalización robusta: minúsculas, sin acentos, sin ruido."""
        if not text:
            return ""
        text = text.lower()
        text = self.remove_accents(text)
        text = re.sub(r'[^a-z0-9 ]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remover palabras ruidosas
        for n in self.noise_words:
            text = re.sub(r'\b' + re.escape(n) + r'\b', '', text)
        
        return re.sub(r'\s+', ' ', text).strip()

    def get_brand(self, text):
        """Detecta la marca en un texto de nombre de producto."""
        text_normalized = self.remove_accents(text.lower())
        for brand in self.brands:
            brand_normalized = self.remove_accents(brand.lower())
            if brand_normalized in text_normalized:
                return brand
        return "Unknown"

    def extract_wheel_size(self, text):
        """Extrae el tamaño de aro del texto."""
        patterns = [r'\b700c?\b', r'\b29\b', r'\b27\.5\b', r'\b26\b', r'\b24\b', r'\b20\b', r'\b16\b']
        for pat in patterns:
            m = re.search(pat, text.lower())
            if m:
                return m.group().strip()
        return None

    def extract_speeds(self, text):
        """Extrae número de velocidades (ej: '21v', '12 velocidades')."""
        m = re.search(r'(\d+)\s*v(?:el|elocidades?)?', text.lower())
        return m.group(1) if m else None

    def match_products(self, prod_a, prod_b):
        """
        Compara dos nombres de productos y retorna un puntaje de confianza (0.0 - 1.0).
        
        Algoritmo:
        1. Si las marcas son distintas (y conocidas) → 0.0 (imposible match)
        2. Si los aros son distintos → 0.0 (son productos diferentes)
        3. Si las velocidades son distintas → penalizar
        4. Similitud de string → score base
        """
        a = self.normalize(prod_a)
        b = self.normalize(prod_b)

        if not a or not b:
            return 0.0

        # 1. Verificar marcas
        brand_a = self.get_brand(a)
        brand_b = self.get_brand(b)
        if brand_a != "Unknown" and brand_b != "Unknown" and brand_a != brand_b:
            return 0.0

        # 2. Verificar tamaño de aro
        aro_a = self.extract_wheel_size(a)
        aro_b = self.extract_wheel_size(b)
        if aro_a and aro_b and aro_a != aro_b:
            return 0.0

        # 3. Similitud base
        similarity = difflib.SequenceMatcher(None, a, b).ratio()

        # 4. Bonus si mismo aro detectado
        if aro_a and aro_a == aro_b:
            similarity = min(1.0, similarity + 0.05)

        # 5. Penalizar si velocidades distintas
        speeds_a = self.extract_speeds(a)
        speeds_b = self.extract_speeds(b)
        if speeds_a and speeds_b and speeds_a != speeds_b:
            similarity *= 0.7

        return round(similarity, 4)

    def is_match(self, prod_a, prod_b):
        """Retorna True si los productos son considerados el mismo modelo."""
        return self.match_products(prod_a, prod_b) >= self.threshold

    def get_canonical_name(self, brand, model):
        """
        Genera un nombre canónico normalizado para uso en la base de datos.
        Se usa para indexar y buscar duplicados.
        """
        combined = f"{brand} {model}"
        normalized = self.normalize(combined)
        # Remover brand aliases
        for alias, replacement in self.brand_aliases.items():
            normalized = normalized.replace(alias, replacement).strip()
        return normalized

    def categorize_by_name(self, name):
        """
        Intenta categorizar una bicicleta por palabras clave en su nombre.
        Útil cuando la tienda no provee categoría explícita.
        """
        name_lower = self.normalize(name)
        
        if any(kw in name_lower for kw in ["montana", "mtb", "trail", "enduro", "xc", "29", "27.5", "26"]):
            return "MTB"
        elif any(kw in name_lower for kw in ["ruta", "road", "gravel", "700c", "700"]):
            return "Ruta"
        elif any(kw in name_lower for kw in ["urbana", "city", "commuter", "hibrida", "28"]):
            return "Urbana"
        elif any(kw in name_lower for kw in ["electrica", "electrico", "ebike", "e-bike"]):
            return "Eléctrica"
        elif any(kw in name_lower for kw in ["infantil", "nino", "junior", "kids", "16", "20", "24"]):
            return "Infantil"
        elif any(kw in name_lower for kw in ["bmx", "freestyle", "street"]):
            return "BMX"
        
        return "MTB"  # Default


# ===== Ejemplo de uso =====
if __name__ == "__main__":
    matcher = ProductMatcher()
    
    tests = [
        ("oxford everest 29", "everest aro 29 oxford"),
        ("trek marlin 5", "trek marlin 5 gen 2"),
        ("specialized rockhopper 29", "rockhopper sport 29 specialized"),
        ("benotto montaña 700 29", "kuwahara 29 pulgadas"),  # Distintas marcas → 0
        ("trek marlin 5 27.5", "trek marlin 5 29"),           # Distinto aro → 0
        ("shimano deore 10v", "shimano deore m4100 10 velocidades"),
    ]
    
    print("=== ProductMatcher v2.0 — Tests ===\n")
    for a, b in tests:
        score = matcher.match_products(a, b)
        result = "✅ MATCH" if score >= matcher.threshold else ("⚠️ POSIBLE" if score > 0.5 else "❌ NO MATCH")
        print(f"{result} ({score:.2f}) | '{a}' vs '{b}'")
