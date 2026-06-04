from bicitodo_scraper.spiders.base_spider import BaseBiciSpider
from bicitodo_scraper.items import BicitodoItem

class TrekSpider(BaseBiciSpider):
    name = "trek"
    allowed_domains = ["trek.cl"]
    start_urls = [
        "https://www.trek.cl/bicicletas"
    ]

    def parse(self, response):
        # VTEX standard often uses vtex-product-summary-2-x-container
        products = response.css(".vtex-product-summary-2-x-container")
        for product in products:
            item = BicitodoItem()
            item["name"] = self.clean_text(product.css(".vtex-product-summary-2-x-brandName::text").get())
            item["url"] = product.css("a::attr(href)").get()
            
            # Precios en VTEX
            price_text = product.css(".vtex-product-price-1-x-currencyInteger::text").get()
            item["price_normal"] = self.clean_price(price_text)
            
            raw_image = product.css("img::attr(src)").get()
            item["image_url"] = self.upscale_image_url(raw_image)
            
            item["store"] = "Trek"
            item["timestamp"] = self.get_timestamp()
            
            if item["url"]:
                yield response.follow(item["url"], self.parse_detail, cb_kwargs={'item': item})

        # Paginación
        # VTEX suele usar botones de "Ver más" o scroll, pero a veces hay enlaces
        next_page = response.css(".vtex-search-result-3-x-buttonShowMore a::attr(href)").get()
        if next_page:
            yield response.follow(next_page, self.parse)

    def parse_detail(self, response, item):
        # Specs en VTEX suelen estar en una tabla o lista de especificaciones
        specs = {}
        spec_items = response.css(".vtex-product-specifications-1-x-specificationItemProperty")
        spec_values = response.css(".vtex-product-specifications-1-x-specificationItemValue")
        
        for label, val in zip(spec_items, spec_values):
            l = self.clean_text(label.css("::text").get())
            v = self.clean_text(val.css("::text").get())
            if l and v:
                specs[l] = v
        
        item["specs"] = specs
        item["brand"] = "Trek"
        item["model"] = item["name"]
        item["sku"] = response.css(".vtex-product-identifier-0-x-product-identifier__value::text").get()
        
        yield item
