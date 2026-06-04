from bicitodo_scraper.spiders.base_spider import BaseBiciSpider
from bicitodo_scraper.items import BicitodoItem

class SatiroSpider(BaseBiciSpider):
    name = "satiro"
    allowed_domains = ["satiro.cl"]
    start_urls = [
        "https://satiro.cl/collections/bicicletas"
    ]

    def parse(self, response):
        products = response.css("li.grid__item")
        for product in products:
            item = BicitodoItem()
            item["name"] = self.clean_text(product.css(".full-unstyled-link::text").get())
            item["url"] = response.urljoin(product.css(".full-unstyled-link::attr(href)").get())
            
            # Precios en Shopify Dawn tema Sátiro
            price_sale = product.css(".price-item--sale::text").get()
            price_regular = product.css(".price-item--regular::text").get()
            
            item["price_normal"] = self.clean_price(price_sale or price_regular)
            
            item["image_url"] = response.urljoin(product.css(".grid__item img::attr(src)").get())
            item["store"] = "Sátiro Bikes"
            item["brand"] = "Sátiro"
            item["timestamp"] = self.get_timestamp()
            
            if item["url"]:
                yield response.follow(item["url"], self.parse_detail, cb_kwargs={'item': item})

        # Paginación Dawn (Shopify standard)
        next_page = response.css(".pagination__next::attr(href)").get()
        if next_page:
            yield response.follow(next_page, self.parse)

    def parse_detail(self, response, item):
        specs = {}
        # Dawn suele usar accordions para specs
        rows = response.css(".product__description table tr")
        for row in rows:
            label = self.clean_text(row.css("td:first-child::text").get())
            value = self.clean_text(row.css("td:last-child::text").get())
            if label and value:
                specs[label] = value
        
        item["specs"] = specs
        item["model"] = item["name"]
        item["sku"] = response.url.split("/")[-1]
        
        yield item
