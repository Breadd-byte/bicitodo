from bicitodo_scraper.spiders.base_spider import BaseBiciSpider
from bicitodo_scraper.items import BicitodoItem

class RipleySpider(BaseBiciSpider):
    """
    Spider para Ripley Chile (simple.ripley.cl).
    Ripley usa VTEX como plataforma, igual que Trek Chile.
    La API de VTEX permite búsquedas por categoría con paginación.
    """
    name = "ripley"
    allowed_domains = ["simple.ripley.cl"]
    
    # API VTEX de Ripley — categoría Bicicletas (ID puede variar, se confirma inspeccionando la red)
    start_urls = [
        "https://simple.ripley.cl/bicicletas?map=c,c"
    ]
    
    def parse(self, response):
        # VTEX standard shelves
        products = response.css(".vtex-product-summary-2-x-container, .shelf__item")
        
        for product in products:
            item = BicitodoItem()
            
            # Nombre — VTEX usa productName o brandName
            item["name"] = self.clean_text(
                product.css(".vtex-product-summary-2-x-productNameContainer::text, "
                            ".vtex-product-summary-2-x-brandName::text, "
                            ".product-summary__name::text").get()
            )
            
            # URL del producto
            url = product.css("a::attr(href)").get()
            item["url"] = response.urljoin(url) if url else None
            
            # Precio — VTEX tiene precio normal y precio tarjeta
            price_normal = product.css(
                ".vtex-product-price-1-x-currencyInteger::text, "
                ".vtex-product-price-1-x-sellingPriceValue::text"
            ).get()
            item["price_normal"] = self.clean_price(price_normal)
            
            # Precio tarjeta Ripley (si existe)
            price_card = product.css(".ripley-card-price::text, .club-ripley::text").get()
            item["price_card"] = self.clean_price(price_card)
            
            # Imagen
            raw_image = product.css("img::attr(src), img::attr(data-src)").get()
            item["image_url"] = self.upscale_image_url(raw_image)
            
            item["store"] = "Ripley"
            item["brand"] = self.clean_text(
                product.css(".vtex-product-summary-2-x-brandName::text").get() or "Desconocida"
            )
            item["timestamp"] = self.get_timestamp()
            item["specs"] = {}
            
            if item["url"]:
                yield response.follow(item["url"], self.parse_detail, cb_kwargs={"item": item})
        
        # Paginación VTEX
        next_page = response.css(
            ".vtex-search-result-3-x-buttonShowMore a::attr(href), "
            "a[class*='paginationArrow']:last-child::attr(href)"
        ).get()
        if next_page:
            yield response.follow(next_page, self.parse)
    
    def parse_detail(self, response, item):
        specs = {}
        
        # Tabla de especificaciones VTEX
        spec_items = response.css(
            ".vtex-product-specifications-1-x-specificationItemProperty, "
            ".specification-item__property"
        )
        spec_values = response.css(
            ".vtex-product-specifications-1-x-specificationItemValue, "
            ".specification-item__value"
        )
        
        for label, val in zip(spec_items, spec_values):
            l = self.clean_text(label.css("::text").get())
            v = self.clean_text(val.css("::text").get())
            if l and v:
                specs[l] = v
        
        # Extraer marca y modelo de specs si están disponibles
        item["specs"] = specs
        item["brand"] = specs.get("Marca", item.get("brand", "Desconocida"))
        item["model"] = specs.get("Modelo", item.get("name", ""))
        item["sku"] = response.css(
            ".vtex-product-identifier-0-x-product-identifier__value::text"
        ).get() or response.url.split("/")[-1]
        
        # Categoría
        breadcrumb = response.css(".vtex-breadcrumb-1-x-link::text").getall()
        if "Montaña" in str(breadcrumb):
            item["category_type"] = "MTB"
        elif "Ruta" in str(breadcrumb) or "Gravel" in str(breadcrumb):
            item["category_type"] = "Ruta"
        elif "Urbana" in str(breadcrumb):
            item["category_type"] = "Urbana"
        elif "Infantil" in str(breadcrumb) or "Niño" in str(breadcrumb):
            item["category_type"] = "Infantil"
        elif "Eléctrica" in str(breadcrumb) or "Electrica" in str(breadcrumb):
            item["category_type"] = "Eléctrica"
        
        yield item
