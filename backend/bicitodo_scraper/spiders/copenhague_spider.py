from bicitodo_scraper.spiders.base_spider import BaseBiciSpider
from bicitodo_scraper.items import BicitodoItem

class CopenhagueSpider(BaseBiciSpider):
    """
    Spider para Copenhague (copenhague.cl).
    Tienda ubicada en San Diego. Usa la plataforma Jumpseller.
    """
    name = "copenhague"
    allowed_domains = ["copenhague.cl", "www.copenhague.cl"]
    start_urls = [
        "https://www.copenhague.cl/bicicletas"
    ]

    def parse(self, response):
        # Jumpseller standard products grid
        products = response.css(".product-block, .item")
        
        for product in products:
            item = BicitodoItem()
            
            # Nombre
            item["name"] = self.clean_text(
                product.css(".product-block__name::text, .name a::text, .product-name a::text, .title a::text").get()
            )
            
            # URL
            url = product.css(".product-block__name::attr(href), .product-block__anchor::attr(href), .name a::attr(href), .product-name a::attr(href), .title a::attr(href), .image a::attr(href)").get()
            item["url"] = response.urljoin(url) if url else None
            
            # Precios en Jumpseller
            price = product.css(".product-block__price::text, .price::text, .product-price::text, .current-price::text").get()
            item["price_normal"] = self.clean_price(price)
            
            # Imagen
            raw_image = product.css("img.product-block__image::attr(src), img::attr(src), img::attr(data-src)").get()
            item["image_url"] = response.urljoin(raw_image) if raw_image else None
            
            # Marca (a veces en span.brand)
            brand = product.css(".product-block__brand::text, .brand::text, .product-brand::text").get()
            item["brand"] = self.clean_text(brand) if brand else "Copenhague"
            
            item["store"] = "Copenhague"
            item["timestamp"] = self.get_timestamp()
            item["specs"] = {}
            
            if item["url"] and item["name"]:
                yield response.follow(item["url"], self.parse_detail, cb_kwargs={"item": item})
        
        # Paginación Jumpseller
        next_page = response.css("ul.pager li.next a::attr(href), .pager a[rel='next']::attr(href), .next-page a::attr(href), .pagination .next a::attr(href)").get()
        if next_page:
            yield response.follow(next_page, self.parse)

    def parse_detail(self, response, item):
        specs = {}
        
        # Extraer specs de tabla o listas (Jumpseller usa .description)
        rows = response.css(".description table tr, #description table tr, .page-content table tr")
        for row in rows:
            cells = row.css("td::text, td span::text, td p::text").getall()
            if len(cells) >= 2:
                label = self.clean_text(cells[0])
                value = self.clean_text(cells[1])
                if label and value:
                    specs[label] = value
        
        item["specs"] = specs
        item["model"] = item.get("name", "")
        item["sku"] = response.url.split("/")[-1]
        
        yield item
