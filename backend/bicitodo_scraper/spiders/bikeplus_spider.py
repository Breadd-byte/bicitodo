from bicitodo_scraper.spiders.base_spider import BaseBiciSpider
from bicitodo_scraper.items import BicitodoItem

class BikePlusSpider(BaseBiciSpider):
    """
    Spider para BikePlus Chile (bikeplus.cl).
    BikePlus es una tienda especializada Shopify que vende Giant, Cannondale, Liv, Orbea.
    """
    name = "bikeplus"
    allowed_domains = ["bikeplus.cl"]
    start_urls = [
        "https://bikeplus.cl/collections/bicicletas",
        "https://bikeplus.cl/collections/bicicletas-de-montana",
        "https://bikeplus.cl/collections/bicicletas-de-ruta",
    ]

    def parse(self, response):
        products = response.css("li.grid__item, .product-item, .product-card")
        
        for product in products:
            item = BicitodoItem()
            
            item["name"] = self.clean_text(
                product.css(
                    ".full-unstyled-link::text, "
                    ".product-item__title::text, "
                    ".card__heading a::text"
                ).get()
            )
            
            url = product.css(
                ".full-unstyled-link::attr(href), "
                ".product-item__title::attr(href), "
                ".card__heading a::attr(href)"
            ).get()
            item["url"] = response.urljoin(url) if url else None
            
            price_sale = product.css(".price-item--sale::text").get()
            price_regular = product.css(".price-item--regular::text").get()
            item["price_normal"] = self.clean_price(price_sale or price_regular)
            
            raw_image = product.css("img::attr(src), img::attr(data-src)").get()
            item["image_url"] = response.urljoin(raw_image) if raw_image else None
            
            # Detectar marca por nombre o vendor
            vendor = self.clean_text(product.css(".product-item__vendor::text, .card__vendor::text").get())
            item["brand"] = vendor or self._detect_brand(item.get("name", ""))
            
            item["store"] = "BikePlus"
            item["timestamp"] = self.get_timestamp()
            item["specs"] = {}
            
            if item["url"]:
                yield response.follow(item["url"], self.parse_detail, cb_kwargs={"item": item})
        
        next_page = response.css(".pagination__next::attr(href), a[rel='next']::attr(href)").get()
        if next_page:
            yield response.follow(next_page, self.parse)

    def _detect_brand(self, name):
        """Detecta la marca por palabras clave en el nombre."""
        brands = ["Giant", "Cannondale", "Liv", "Orbea", "Scott", "Trek", "Specialized", "Merida", "Kona"]
        name_lower = (name or "").lower()
        for brand in brands:
            if brand.lower() in name_lower:
                return brand
        return "BikePlus"

    def parse_detail(self, response, item):
        specs = {}
        
        # Specs en tablas o secciones de producto
        rows = response.css(".product__description table tr, .product-tabs__panel table tr")
        for row in rows:
            cells = row.css("td::text").getall()
            if len(cells) >= 2:
                label = self.clean_text(cells[0])
                value = self.clean_text(cells[1])
                if label and value:
                    specs[label] = value
        
        # También buscar en JSON-LD
        json_ld = response.css('script[type="application/ld+json"]::text').get()
        if json_ld:
            try:
                import json
                data = json.loads(json_ld)
                if isinstance(data, dict) and data.get("@type") == "Product":
                    offers = data.get("offers", {})
                    if isinstance(offers, dict):
                        price = offers.get("price")
                        if price and not item.get("price_normal"):
                            item["price_normal"] = self.clean_price(str(price))
            except Exception:
                pass
        
        item["specs"] = specs
        item["model"] = item.get("name", "")
        item["sku"] = response.url.split("/")[-1].split("?")[0]
        
        yield item
