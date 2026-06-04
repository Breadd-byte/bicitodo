import cloudscraper
from scrapy.http import HtmlResponse

class CloudscraperMiddleware:
    def __init__(self):
        # Initialize cloudscraper with Chrome on Windows profile
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )

    def process_request(self, request, spider):
        # List of domains that require cloudscraper to bypass protections
        protected_domains = [
            "decathlon.cl",
            "falabella.com",
            "ripley.cl",
            "paris.cl",
            "mercadolibre.cl",
            "trek.cl",
            "specialized.com"
        ]
        
        # Check if the requested URL belongs to a protected domain
        if any(domain in request.url for domain in protected_domains):
            spider.logger.info(f"☁️ Cloudscraper intercepting: {request.url}")
            try:
                # Custom headers matching standard browser requests
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8"
                }
                
                # Fetch page content
                response = self.scraper.get(request.url, headers=headers, timeout=25)
                
                # Copy headers and remove encoding headers to prevent Scrapy from trying to decompress again
                resp_headers = dict(response.headers)
                resp_headers.pop('Content-Encoding', None)
                resp_headers.pop('content-encoding', None)
                resp_headers.pop('Transfer-Encoding', None)
                resp_headers.pop('transfer-encoding', None)
                
                # Return the Scrapy HtmlResponse
                return HtmlResponse(
                    url=response.url,
                    status=response.status_code,
                    headers=resp_headers,
                    body=response.content,
                    encoding='utf-8',
                    request=request
                )
            except Exception as e:
                spider.logger.error(f"❌ Cloudscraper error for {request.url}: {e}")
                # Fallback to default downloader if cloudscraper encounters a transient error
                return None
                
        return None
