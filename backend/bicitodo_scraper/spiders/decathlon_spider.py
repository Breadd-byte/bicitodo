from bicitodo_scraper.spiders.base_spider import BaseBiciSpider
from bicitodo_scraper.items import BicitodoItem

class DecathlonSpider(BaseBiciSpider):
    """
    Spider para Decathlon Chile (decathlon.cl).
    Decathlon Chile usa Shopify con tema personalizado.
    Sus marcas internas son: Rockrider (MTB), Btwin (urbana), Van Rysel (ruta), Triban (ruta entry).
    """
    name = "decathlon"
    allowed_domains = ["decathlon.cl", "www.decathlon.cl"]
    start_urls = [
        "https://www.decathlon.cl/4786-bicicletas",
        "https://www.decathlon.cl/4538-accesorios-para-bicicletas",
        "https://www.decathlon.cl/4794-repuestos-de-bicicletas"
    ]
    
    # Mapa de marcas internas Decathlon
    BRAND_MAP = {
        "rockrider": "Rockrider (Decathlon)",
        "btwin": "Btwin (Decathlon)",
        "van rysel": "Van Rysel (Decathlon)",
        "triban": "Triban (Decathlon)",
        "elops": "Elops (Decathlon)",
        "b'twin": "Btwin (Decathlon)",
        "domyos": "Domyos (Decathlon)",
        "oxelo": "Oxelo (Decathlon)",
    }

    def parse(self, response):
        # Oneshop uses article.product-card
        products = response.css("article.product-card, .product-card")
        
        for product in products:
            item = BicitodoItem()
            
            # Nombre del producto
            item["name"] = self.clean_text(
                product.css(".product-card_header h2::text, h2::text").get()
            )
            
            # URL
            url = product.css(".product-card_image a::attr(href), .product-card_header a::attr(href)").get()
            item["url"] = response.urljoin(url) if url else None
            
            # Precio
            price = product.css(".price_amount::attr(data-value), .price_amount::text").get()
            item["price_normal"] = self.clean_price(price)
            
            # Imagen
            raw_image = product.css(".product-card_image img::attr(src), img::attr(src)").get()
            item["image_url"] = response.urljoin(raw_image) if raw_image else None
            
            # Determinar marca
            brand = product.css(".product-card_header p::text").get()
            brand_found = self.clean_text(brand) if brand else "Decathlon"
            
            # Fallback a mapa si es genérico
            name_lower = (item["name"] or "").lower()
            for key, brand_name in self.BRAND_MAP.items():
                if key in name_lower:
                    brand_found = brand_name
                    break
            
            item["brand"] = brand_found
            item["store"] = "Decathlon"
            item["timestamp"] = self.get_timestamp()
            item["specs"] = {}
            
            if item["url"]:
                yield response.follow(item["url"], self.parse_detail, cb_kwargs={"item": item})
        
        # Paginación Oneshop
        next_page = response.css(".pagination a[data-testid='pagination-next']::attr(href), .pagination a[aria-label*='next']::attr(href), .pagination a[aria-label*='siguiente']::attr(href)").get()
        if next_page:
            yield response.follow(next_page, self.parse)

    def parse_detail(self, response, item):
        specs = {}
        
        # Decathlon suele tener specs en tablas dentro de la descripción
        # O en secciones de acordeón
        rows = response.css(
            ".product__description table tr, "
            ".product-description table tr, "
            ".rte table tr"
        )
        for row in rows:
            cells = row.css("td::text").getall()
            if len(cells) >= 2:
                label = self.clean_text(cells[0])
                value = self.clean_text(cells[1])
                if label and value:
                    specs[label] = value
        
        # Especificaciones en listas
        spec_items = response.css(
            ".product-specs li, "
            "[class*='technical-specs'] li"
        )
        for si in spec_items:
            text = si.css("::text").getall()
            if len(text) >= 2:
                specs[self.clean_text(text[0])] = self.clean_text(text[1])
        
        # SKU desde la URL o metafield
        sku_el = response.css("[data-product-sku]::attr(data-product-sku)").get()
        item["sku"] = sku_el or response.url.split("/")[-1].split("?")[0]
        
        # Modelo
        item["model"] = item.get("name", "")
        item["specs"] = specs
        
        yield item
