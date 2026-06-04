from bicitodo_scraper.spiders.base_spider import BaseBiciSpider
from bicitodo_scraper.items import BicitodoItem
import json
import urllib.parse

class FalabellaSpider(BaseBiciSpider):
    """
    Spider para Falabella Chile.
    Usa la API REST pública de Falabella para obtener productos por categoría.
    La categoría de bicicletas en Falabella es cat40062 (Deportes > Ciclismo > Bicicletas)
    """
    name = "falabella"
    allowed_domains = ["falabella.com.cl", "www.falabella.com.cl"]
    
    # Categorías de bicicletas en Falabella
    CATEGORY_IDS = [
        "cat40062",   # Bicicletas
        "cat40063",   # Bicicletas de Montaña
        "cat40064",   # Bicicletas de Ruta
        "cat40065",   # Bicicletas Urbanas
        "cat40066",   # Bicicletas Infantiles
        "cat4006401", # Bicicletas Eléctricas
    ]
    
    start_urls = [
        f"https://www.falabella.com.cl/rest/model/falabella/rest/browse/BrowseActor/fetch-product-summary?"
        f"Nrpp=50&No=0&Nr=AND%28product.siteId%3AFALCL%2Ccategory.repositoryId%3Acat40062%29"
        f"&Ns=product.isAvailableInStore%7C1&rankingMechanism=ProductRanking"
    ]
    
    PAGE_SIZE = 50
    
    def parse(self, response):
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.error(f"[Falabella] JSON inválido en: {response.url}")
            return
        
        products_data = data.get("results", {}).get("products", []) or \
                        data.get("products", []) or \
                        data.get("data", {}).get("products", [])

        if not products_data:
            # Intentar estructura alternativa
            results = data.get("results", {})
            products_data = results.get("records", [])

        for product in products_data:
            item = BicitodoItem()
            
            # Extraer datos básicos
            attrs = product.get("attributes", product)
            
            item["name"] = self.clean_text(
                attrs.get("displayName", attrs.get("product.displayName", ""))
            )
            item["brand"] = self.clean_text(
                attrs.get("brand", attrs.get("product.brand", "Desconocida"))
            )
            item["model"] = item["name"]
            
            # Precio
            price_data = attrs.get("prices", attrs.get("skus", [{}]))
            if isinstance(price_data, list) and price_data:
                sku = price_data[0]
                item["price_normal"] = self.clean_price(str(sku.get("price", {}).get("original", "")))
                item["price_card"] = self.clean_price(str(sku.get("price", {}).get("cmr", "")))
            else:
                price_str = str(attrs.get("price", attrs.get("product.price", "")))
                item["price_normal"] = self.clean_price(price_str)
            
            # URL e imagen
            product_id = attrs.get("productId", attrs.get("product.repositoryId", ""))
            slug = attrs.get("slug", attrs.get("product.slug", product_id))
            item["url"] = f"https://www.falabella.com.cl/falabella-cl/product/{product_id}/{slug}"
            
            images = attrs.get("images", attrs.get("product.imageList", []))
            if images and isinstance(images, list):
                item["image_url"] = images[0] if isinstance(images[0], str) else ""
            
            item["store"] = "Falabella"
            item["timestamp"] = self.get_timestamp()
            item["specs"] = {}
            item["sku"] = product_id
            
            if item["name"] and item["price_normal"]:
                yield item
        
        # Paginación
        total = data.get("results", {}).get("totalNumRecs", data.get("total", 0))
        current_params = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(response.url).query))
        current_offset = int(current_params.get("No", 0))
        
        if current_offset + self.PAGE_SIZE < total:
            next_offset = current_offset + self.PAGE_SIZE
            current_params["No"] = str(next_offset)
            base_url = "https://www.falabella.com.cl/rest/model/falabella/rest/browse/BrowseActor/fetch-product-summary?"
            next_url = base_url + urllib.parse.urlencode(current_params)
            yield response.follow(next_url, self.parse)
