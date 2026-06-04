import requests
from bs4 import BeautifulSoup

def obtener_precio_bicicleta(url):
    # 1. Nos disfrazamos de navegador real para que los sistemas de ciberseguridad de la tienda no nos bloqueen
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print(f"🕵️‍♂️ Enviando robot a: {url}")
    
    try:
        # 2. El robot entra a la página y descarga todo el código fuente
        respuesta = requests.get(url, headers=headers)
        respuesta.raise_for_status() # Verifica que la página no esté caída

        # 3. BeautifulSoup convierte el texto en una estructura HTML navegable
        sopa = BeautifulSoup(respuesta.text, 'html.parser')

        # 4. Buscamos el precio (Aquí aplicas todo tu conocimiento de HTML/CSS)
        # NOTA: En una tienda real, tienes que inspeccionar la página web y cambiar 'precio-oferta' 
        # por la clase real que use la tienda (ej. 'product-price-container')
        
        # Simulamos buscar el título y un span para el precio
        titulo = sopa.find('h1')
        titulo_texto = titulo.text.strip() if titulo else "Bicicleta Desconocida"
        
        # Ejemplo genérico de búsqueda de la etiqueta de precio
        elemento_precio = sopa.find('span', class_='precio-oferta') 
        
        if elemento_precio:
            precio_texto = elemento_precio.text.strip()
            print("✅ ¡Extracción exitosa!")
            print(f"🚲 Modelo: {titulo_texto}")
            print(f"💰 Precio Actual: {precio_texto}")
        else:
            print("⚠️ No se encontró la etiqueta de precio. Revisa la clase CSS de la tienda.")

    except requests.exceptions.RequestException as e:
        print(f"❌ Error de red al conectar con la tienda: {e}")

# 5. Ejecutamos el bot
# (Más adelante reemplazaremos esto por una lista de miles de URLs)
url_tienda = "https://www.ejemplo-tienda-bicis.cl/oxford-everest-29"
obtener_precio_bicicleta(url_tienda)