from bicitodo_scraper.spiders.base_spider import BaseBiciSpider
from bicitodo_scraper.items import BicitodoItem

class SpartaSpider(BaseBiciSpider):
    name = "sparta"
    allowed_domains = ["sparta.cl"]
    start_urls = [
        "https://www.sparta.cl/ciclismo/bicicletas.html"
    ]

    def parse(self, response):
        products = response.css(".product-item-info")
        for product in products:
            item = BicitodoItem()
            item["name"] = self.clean_text(product.css(".product-item-link::text").get())
            item["url"] = product.css(".product-item-link::attr(href)").get()
            
            # Precios
            price_text = product.css(".price-wrapper .price::text").get()
            item["price_normal"] = self.clean_price(price_text)
            
            raw_image = product.css(".product-image-photo::attr(src)").get()
            item["image_url"] = self.upscale_image_url(raw_image)
            
            item["store"] = "Sparta"
            item["timestamp"] = self.get_timestamp()
            
            if item["url"]:
                yield response.follow(item["url"], self.parse_detail, cb_kwargs={'item': item})

        # Paginación (Magento standard)
        next_page = response.css(".action.next::attr(href)").get()
        if next_page:
            yield response.follow(next_page, self.parse)

    def parse_detail(self, response, item):
        specs = {}
        rows = response.css("#product-attribute-specs-table tr")
        for row in rows:
            label = self.clean_text(row.css("th::text").get())
            value = self.clean_text(row.css("td::text").get())
            if label and value:
                specs[label] = value
        
        item["specs"] = specs
        item["brand"] = specs.get("Marca", "Desconocida")
        item["model"] = specs.get("Modelo", item["name"])
        item["sku"] = response.css(".value[itemprop='sku']::text").get() or specs.get("SKU")
        
        yield item
