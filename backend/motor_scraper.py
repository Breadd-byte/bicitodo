# Arquitectura Maestra de Scrapeo (Patrón Estrategia)
# Requiere instalar: pip install playwright
# Luego ejecutar: playwright install

class ArañaOxford:
    """Módulo específico para entender el código de Oxford"""
    def extraer_datos(self, pagina_html):
        # Aquí va la lógica exacta buscando las clases CSS de Oxford
        print("🚲 [Oxford] Extrayendo: Everest 29 - $259.990")
        return {"marca": "Oxford", "modelo": "Everest 29", "precio": 259990}

class ArañaTrek:
    """Módulo específico para entender el código de Trek"""
    def extraer_datos(self, pagina_html):
        # Trek usa otra estructura, la programamos aquí
        print("🚲 [Trek] Extrayendo: Marlin 5 - $499.900")
        return {"marca": "Trek", "modelo": "Marlin 5", "precio": 499900}

class ArañaSparta:
    """Módulo específico para entender el código de Sparta"""
    def extraer_datos(self, pagina_html):
        # Sparta carga con JavaScript, requiere lógica distinta
        print("🚲 [Sparta] Extrayendo: Specialized Rockhopper - $550.000")
        return {"marca": "Specialized", "modelo": "Rockhopper", "precio": 550000}


class MotorCentralBiciCompare:
    """El cerebro que administra a todas las arañas"""
    def __init__(self):
        # Aquí registramos todas las tiendas que el sistema sabe leer
        self.catalogo_tiendas = {
            "oxfordstore.cl": ArañaOxford(),
            "trek.cl": ArañaTrek(),
            "sparta.cl": ArañaSparta()
        }
        self.base_de_datos_final = []

    def procesar_url(self, url):
        print(f"\n🌐 Motor Central analizando link: {url}")
        
        # 1. Identificar de qué tienda es el link
        araña_correcta = None
        for dominio, araña in self.catalogo_tiendas.items():
            if dominio in url:
                araña_correcta = araña
                break
                
        if not araña_correcta:
            print("❌ Error: No tenemos un módulo programado para esta tienda aún.")
            return

        # 2. (Simulación) El motor descarga el HTML usando Playwright
        html_descargado = "<html>...codigo gigante de la tienda...</html>"
        
        # 3. Le pasamos el HTML a la araña experta en esa tienda
        datos_bicicleta = araña_correcta.extraer_datos(html_descargado)
        
        # 4. Guardar en la base de datos central
        self.base_de_datos_final.append(datos_bicicleta)
        print("✅ Guardado exitosamente en BiciCompare.")

# --- EJECUCIÓN DEL SISTEMA ---
if __name__ == "__main__":
    print("🚀 INICIANDO SISTEMA BICI-COMPARE 2026 🚀")
    
    mi_motor = MotorCentralBiciCompare()
    
    # Lista de links de distintas tiendas (En la vida real, esto son miles de links)
    links_a_procesar = [
        "https://www.oxfordstore.cl/bicicleta-oxford-everest-aro-29.html",
        "https://www.trek.cl/marlin-5-gen-2-2023/p",
        "https://www.sparta.cl/ciclismo/specialized-rockhopper.html"
    ]
    
    for link in links_a_procesar:
        mi_motor.procesar_url(link)