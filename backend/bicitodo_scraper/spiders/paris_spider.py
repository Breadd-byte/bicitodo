from bicitodo_scraper.spiders.base_spider import BaseBiciSpider
from bicitodo_scraper.items import BicitodoItem

class ParisSpider(BaseBiciSpider):
    """
    Spider para Paris Chile (paris.cl).
    Paris también usa VTEX. Sus selectores son muy similares a Ripley.
    El precio CMR Paris es el precio con tarjeta.
    """
    name = "paris"
    allowed_domains = ["paris.cl", "www.paris.cl"]
    start_urls = [
        "https://www.paris.cl/bicicletas"
    ]

    def parse(self, response):
        products = response.css(
            ".vtex-product-summary-2-x-container, "
            ".product-summary__content"
        )
        
        for product in products:
            item = BicitodoItem()
            
            item["name"] = self.clean_text(
                product.css(
                    ".vtex-product-summary-2-x-productNameContainer::text, "
                    ".vtex-product-summary-2-x-brandName::text"
                ).get()
            )
            
            url = product.css("a::attr(href)").get()
            item["url"] = response.urljoin(url) if url else None
            
            # Precio normal
            price_normal = product.css(
                ".vtex-product-price-1-x-currencyInteger::text, "
                ".vtex-product-price-1-x-sellingPriceValue::text"
            ).get()
            item["price_normal"] = self.clean_price(price_normal)
            
            # Precio CMR Paris (precio con tarjeta)
            price_cmr = product.css(
                ".paris-cmr-price::text, "
                "[class*='cmrPrice']::text, "
                "[class*='cardPrice']::text"
            ).get()
            item["price_card"] = self.clean_price(price_cmr)
            
            raw_image = product.css("img::attr(src), img::attr(data-src)").get()
            item["image_url"] = self.upscale_image_url(raw_image)
            
            item["store"] = "Paris"
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
            "a[aria-label='Siguiente']::attr(href)"
        ).get()
        if next_page:
            yield response.follow(next_page, self.parse)

    def parse_detail(self, response, item):
        specs = {}
        
        # Especificaciones VTEX
        spec_props = response.css(".vtex-product-specifications-1-x-specificationItemProperty")
        spec_vals = response.css(".vtex-product-specifications-1-x-specificationItemValue")
        
        for label, val in zip(spec_props, spec_vals):
            l = self.clean_text(label.css("::text").get())
            v = self.clean_text(val.css("::text").get())
            if l and v:
                specs[l] = v
        
        item["specs"] = specs
        item["brand"] = specs.get("Marca", item.get("brand", "Desconocida"))
        item["model"] = specs.get("Modelo", item.get("name", ""))
        item["sku"] = response.css(
            ".vtex-product-identifier-0-x-product-identifier__value::text"
        ).get() or response.url.split("/")[-1]
        
        yield item
