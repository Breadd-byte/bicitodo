from bicitodo_scraper.spiders.base_spider import BaseBiciSpider
from bicitodo_scraper.items import BicitodoItem
import json

class MercadoLibreSpider(BaseBiciSpider):
    """
    Spider para MercadoLibre Chile usando la API oficial pública.
    MLA = Argentina, MLB = Brasil, MLC = Chile
    Categoría Bicicletas en ML Chile: MLC1276
    Subcategorías:
      - MLC1278: Bicicletas de Montaña
      - MLC1279: Bicicletas de Ruta
      - MLC1280: Bicicletas Urbanas  
      - MLC1281: Bicicletas Infantiles
      - MLC439041: Bicicletas Eléctricas
    
    La API pública retorna JSON sin necesidad de autenticación.
    Límite: 50 items por request, offset máximo 1000.
    Solo mostramos vendedores oficiales (condición 'new').
    """
    name = "mercadolibre"
    allowed_domains = ["api.mercadolibre.com", "mercadolibre.cl"]
    
    CATEGORIES = {
        "MLC1278": "MTB",
        "MLC1279": "Ruta",
        "MLC1280": "Urbana",
        "MLC1281": "Infantil",
        "MLC439041": "Eléctrica",
    }
    
    PAGE_SIZE = 50
    MAX_OFFSET = 950  # API limit: 1000 results max (offset 0-950 with size 50)
    
    start_urls = [
        f"https://api.mercadolibre.com/sites/MLC/search?category={cat_id}&condition=new&offset=0&limit=50"
        for cat_id in ["MLC1278", "MLC1279", "MLC1280", "MLC1281", "MLC439041"]
    ]

    def parse(self, response):
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.error(f"[MercadoLibre] JSON inválido: {response.url}")
            return
        
        results = data.get("results", [])
        paging = data.get("paging", {})
        
        # Determinar categoría del URL
        import urllib.parse
        params = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(response.url).query))
        cat_id = params.get("category", "MLC1278")
        category_type = self.CATEGORIES.get(cat_id, "MTB")
        
        for product in results:
            item = BicitodoItem()
            
            item["name"] = self.clean_text(product.get("title", ""))
            item["url"] = product.get("permalink", "")
            item["price_normal"] = int(product.get("price", 0))
            
            # Imagen (thumbnail de ML)
            thumbnail = product.get("thumbnail", "")
            # Obtener imagen en alta calidad (reemplazar -I por -O o -W)
            item["image_url"] = thumbnail.replace("-I.", "-O.") if thumbnail else None
            
            # Marca y modelo desde atributos
            attributes = {a.get("id"): a.get("value_name") for a in product.get("attributes", [])}
            item["brand"] = attributes.get("BRAND", "Desconocida")
            item["model"] = attributes.get("MODEL", item["name"])
            
            # SKU
            item["sku"] = product.get("id", "")
            item["store"] = "MercadoLibre"
            item["timestamp"] = self.get_timestamp()
            
            # Specs desde atributos ML
            specs = {}
            for attr in product.get("attributes", []):
                key = attr.get("name")
                val = attr.get("value_name")
                if key and val and key not in ["BRAND", "MODEL"]:
                    specs[key] = val
            
            # Atributos importantes para bicicletas
            if attributes.get("WHEEL_SIZE"):
                specs["Aro"] = attributes["WHEEL_SIZE"]
            if attributes.get("FRAME_MATERIAL"):
                specs["Material Marco"] = attributes["FRAME_MATERIAL"]
            if attributes.get("BRAKE_TYPE"):
                specs["Frenos"] = attributes["BRAKE_TYPE"]
            if attributes.get("SPEEDS"):
                specs["Velocidades"] = attributes["SPEEDS"]
            
            item["specs"] = specs
            item["category_type"] = category_type
            
            # Solo incluir si tiene precio válido y es nuevo
            condition = product.get("condition", "")
            if item["price_normal"] > 0 and condition == "new":
                yield item
        
        # Paginación de la API ML
        total = paging.get("total", 0)
        current_offset = paging.get("offset", 0)
        next_offset = current_offset + self.PAGE_SIZE
        
        if next_offset <= min(total - 1, self.MAX_OFFSET):
            params["offset"] = str(next_offset)
            base_url = "https://api.mercadolibre.com/sites/MLC/search?"
            next_url = base_url + urllib.parse.urlencode(params)
            yield response.follow(next_url, self.parse)
