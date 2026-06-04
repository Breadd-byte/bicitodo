from bicitodo_scraper.spiders.base_spider import BaseBiciSpider
from bicitodo_scraper.items import BicitodoItem

class SpecializedSpider(BaseBiciSpider):
    name = "specialized"
    allowed_domains = ["specialized.com"]
    start_urls = [
        "https://www.specialized.com/cl/es/shop/bikes/c/bikes"
    ]

    def parse(self, response):
        # Specialized usa clases dinámicas de Next.js/CSS Modules.
        # Usamos selectores parciales para mayor robustez.
        products = response.css("div[class*='ProductCard_wrapper']")
        for product in products:
            item = BicitodoItem()
            item["name"] = self.clean_text(product.css("h2::text").get())
            item["url"] = response.urljoin(product.css("a[class*='ProductCard_cardTitle']::attr(href)").get())
            
            # Precios en Specialized CL
            # El precio suele estar en un span o div dentro del card
            price_text = product.css("span[class*='ProductPrice']::text").get()
            item["price_normal"] = self.clean_price(price_text)
            
            raw_image = product.css("img[class*='ProductCard_image']::attr(src)").get()
            item["image_url"] = self.upscale_image_url(raw_image)
            
            item["store"] = "Specialized Chile"
            item["brand"] = "Specialized"
            item["timestamp"] = self.get_timestamp()
            
            if item["url"]:
                yield response.follow(item["url"], self.parse_detail, cb_kwargs={'item': item})

        # Paginación Specialized (a veces es scroll infinito, pero tienen botones de página en algunas vistas)
        next_page = response.css("a[class*='Pagination_next']::attr(href)").get()
        if next_page:
            yield response.follow(next_page, self.parse)

    def parse_detail(self, response, item):
        specs = {}
        # Specialized usa una estructura "Technical Specifications" muy detallada
        # Buscamos la sección de especificaciones técnicas
        sections = response.css("div[class*='ProductTechnicalSpecifications_item']")
        for section in sections:
            label = self.clean_text(section.css("h4::text").get())
            value = self.clean_text(section.css("p::text").get())
            if label and value:
                specs[label] = value
        
        item["specs"] = specs
        item["model"] = item["name"]
        item["sku"] = response.url.split("-")[-1] # Fallback to URL part
        
        yield item
