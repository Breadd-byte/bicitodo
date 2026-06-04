import scrapy
import re
from datetime import datetime

class BaseBiciSpider(scrapy.Spider):
    def clean_price(self, text):
        if not text:
            return None
        # Elimina símbolos de moneda, puntos y espacios
        clean = re.sub(r'[^\d]', '', text)
        return int(clean) if clean else None

    def clean_text(self, text):
        if not text:
            return ""
        return text.strip().replace('\n', ' ').replace('\r', '')

    def upscale_image_url(self, url):
        if not url: return None
        
        # 1. Oxford: Remove /cache/[HASH]
        if "oxfordstore.cl" in url and "/cache/" in url:
            import re
            return re.sub(r'/cache/[^/]+/', '/', url)
            
        # 2. Trek/Sparta (Magento): Strip query params
        if any(domain in url for domain in ["trekbikeschile.com", "sparta.cl", "trek.cl"]):
            return url.split('?')[0]
            
        # 3. Specialized: wid=2000
        if "specialized.com" in url or "assets.specialized.com" in url:
            base_url = url.split('?')[0]
            if "wid=" not in url:
                return f"{base_url}?wid=2000&fmt=webp"

        return url

    def get_timestamp(self):
        return datetime.now().isoformat()
