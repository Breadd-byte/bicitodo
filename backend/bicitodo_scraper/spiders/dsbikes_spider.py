from bicitodo_scraper.spiders.base_spider import BaseBiciSpider
from bicitodo_scraper.items import BicitodoItem

class DsbikesSpider(BaseBiciSpider):
    """
    Spider para DS Bikes Chile (dsbikes.cl).
    DS Bikes es una tienda de San Diego que usa Shopify.
    Marcas típicas: Trinx, Twitter, Java, entre otras.
    """
    name = "dsbikes"
    allowed_domains = ["dsbikes.cl", "www.dsbikes.cl"]
    start_urls = [
        "https://www.dsbikes.cl/collections/bicicletas",
        "https://www.dsbikes.cl/collections/bicicletas-de-montana",
        "https://www.dsbikes.cl/collections/bicicletas-de-ruta",
        "https://www.dsbikes.cl/collections/bicicletas-urbanas",
        "https://www.dsbikes.cl/collections/bicicletas-ninos",
    ]

    def parse(self, response):
        products = response.css("li.grid__item, .product-item, .card-wrapper")
        
        for product in products:
            item = BicitodoItem()
            
            # Nombre
            item["name"] = self.clean_text(
                product.css(
                    ".full-unstyled-link::text, "
                    ".card__heading a::text, "
                    ".product-item__title::text"
                ).get()
            )
            
            # URL
            url = product.css(
                ".full-unstyled-link::attr(href), "
                ".card__heading a::attr(href), "
                ".product-item__title::attr(href)"
            ).get()
            item["url"] = response.urljoin(url) if url else None
            
            # Precios
            price_sale = product.css(".price-item--sale::text, .price__sale .price-item::text").get()
            price_regular = product.css(".price-item--regular::text, .price__regular .price-item::text").get()
            item["price_normal"] = self.clean_price(price_sale or price_regular)
            
            # Imagen
            raw_image = product.css("img::attr(src), img::attr(data-src)").get()
            item["image_url"] = response.urljoin(raw_image) if raw_image else None
            
            # Vendor / Marca
            vendor = self.clean_text(product.css(".card__vendor::text, .product-item__vendor::text").get())
            item["brand"] = vendor or "DS Bikes"
            
            item["store"] = "DS Bikes"
            item["timestamp"] = self.get_timestamp()
            item["specs"] = {}
            
            if item["url"]:
                yield response.follow(item["url"], self.parse_detail, cb_kwargs={"item": item})
        
        # Paginación Shopify
        next_page = response.css(".pagination__next::attr(href), a[rel='next']::attr(href)").get()
        if next_page:
            yield response.follow(next_page, self.parse)

    def parse_detail(self, response, item):
        specs = {}
        
        # Shopify standard table specs
        rows = response.css(".product__description table tr, .rte table tr")
        for row in rows:
            cells = row.css("td::text, td span::text, td p::text").getall()
            if len(cells) >= 2:
                label = self.clean_text(cells[0])
                value = self.clean_text(cells[1])
                if label and value:
                    specs[label] = value
        
        item["specs"] = specs
        item["model"] = item.get("name", "")
        item["sku"] = response.url.split("/")[-1].split("?")[0]
        
        yield item
