from bicitodo_scraper.spiders.base_spider import BaseBiciSpider
from bicitodo_scraper.items import BicitodoItem

class FauconSpider(BaseBiciSpider):
    name = "faucon"
    allowed_domains = ["fauconbikes.cl"]
    start_urls = [
        "https://fauconbikes.cl/collections/bicicletas-1",
        "https://fauconbikes.cl/collections/ruta",
        "https://fauconbikes.cl/collections/mountain-bike",
        "https://fauconbikes.cl/collections/urbanas",
        "https://fauconbikes.cl/collections/bicicletas-de-gravel",
        "https://fauconbikes.cl/collections/bicicletas-electricas"
    ]

    def parse(self, response):
        products = response.css(".product-item")
        for product in products:
            item = BicitodoItem()
            item["name"] = self.clean_text(product.css(".product-item__title::text").get())
            item["url"] = response.urljoin(product.css(".product-item__title::attr(href)").get())
            
            # Precios en Shopify Faucon
            price_text = product.css(".price::text").get()
            item["price_normal"] = self.clean_price(price_text)
            
            item["image_url"] = response.urljoin(product.css(".product-item__image-wrapper img::attr(src)").get())
            item["store"] = "Faucon Bikes"
            item["brand"] = self.clean_text(product.css(".product-item__vendor::text").get()) or "Faucon"
            item["timestamp"] = self.get_timestamp()
            
            if item["url"]:
                yield response.follow(item["url"], self.parse_detail, cb_kwargs={'item': item})

        # Paginación Shopify
        next_page = response.css(".pagination__next::attr(href)").get()
        if next_page:
            yield response.follow(next_page, self.parse)

    def parse_detail(self, response, item):
        # Specs en Shopify suelen estar en .product-tabs o .product-description
        specs = {}
        # Shopify standard block for specs if exists
        rows = response.css(".product-tabs__panel table tr")
        for row in rows:
            label = self.clean_text(row.css("td:first-child::text").get())
            value = self.clean_text(row.css("td:last-child::text").get())
            if label and value:
                specs[label] = value
        
        item["specs"] = specs
        item["model"] = item["name"]
        item["sku"] = response.url.split("/")[-1] # Fallback to URL part
        
        yield item
