from bicitodo_scraper.spiders.base_spider import BaseBiciSpider
from bicitodo_scraper.items import BicitodoItem

class BikeshopSpider(BaseBiciSpider):
    """
    Spider para Bikeshop Chile (bikeshop.cl).
    Bikeshop.cl usa Magento 2, idéntica lógica a Oxford Store y Sparta.
    Vende marcas: Kona, Merida, GT, Haro, Yeti, entre otras.
    """
    name = "bikeshop"
    allowed_domains = ["bikeshop.cl", "www.bikeshop.cl"]
    start_urls = [
        "https://www.bikeshop.cl/ciclismo/bicicletas.html",
        "https://www.bikeshop.cl/ciclismo/bicicletas-de-montana.html",
        "https://www.bikeshop.cl/ciclismo/bicicletas-ruta.html",
        "https://www.bikeshop.cl/ciclismo/bicicletas-urbanas.html",
    ]

    def parse(self, response):
        # Magento 2 standard
        products = response.css(".product-item-info, .product-item")
        
        for product in products:
            item = BicitodoItem()
            
            item["name"] = self.clean_text(
                product.css(".product-item-link::text, .product-item-name a::text").get()
            )
            url = product.css(".product-item-link::attr(href), .product-item-name a::attr(href)").get()
            item["url"] = url
            
            # Precio Magento 2
            price_special = product.css(".special-price .price-wrapper .price::text").get()
            price_regular = product.css(".price-wrapper .price::text").get()
            item["price_normal"] = self.clean_price(price_special or price_regular)
            
            raw_image = product.css(".product-image-photo::attr(src), img::attr(src)").get()
            item["image_url"] = self.upscale_image_url(raw_image)
            
            item["store"] = "Bikeshop"
            item["timestamp"] = self.get_timestamp()
            item["specs"] = {}
            
            if item["url"]:
                yield response.follow(item["url"], self.parse_detail, cb_kwargs={"item": item})
        
        # Paginación Magento 2
        next_page = response.css(".action.next::attr(href)").get()
        if next_page:
            yield response.follow(next_page, self.parse)

    def parse_detail(self, response, item):
        specs = {}
        
        # Tabla de atributos Magento 2
        rows = response.css("#product-attribute-specs-table tr, .data.table.additional-attributes tr")
        for row in rows:
            label = self.clean_text(row.css("th::text, th span::text").get())
            value = self.clean_text(row.css("td::text, td span::text").get())
            if label and value:
                specs[label] = value
        
        item["specs"] = specs
        item["brand"] = specs.get("Marca", specs.get("Brand", "Desconocida"))
        item["model"] = specs.get("Modelo", specs.get("Model", item.get("name", "")))
        item["sku"] = (
            response.css(".value[itemprop='sku']::text").get()
            or specs.get("SKU")
            or specs.get("Código")
            or response.url.split("/")[-1].replace(".html", "")
        )
        
        # Precio de oferta si existe
        promo_price = response.css(".special-price .price-wrapper .price::text").get()
        if promo_price:
            normal_price = response.css(".old-price .price-wrapper .price::text").get()
            item["price_normal"] = self.clean_price(promo_price)
        
        yield item
