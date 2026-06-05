import os
import re
import time
import hashlib
import io
import urllib.parse
import unicodedata
import cloudscraper

try:
    from PIL import Image
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

# Initialize cloudscraper to bypass Cloudflare anti-bot systems
scraper = cloudscraper.create_scraper(
    browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
)

HEADERS = {
    "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
    "Accept-Language": "es-CL,es;q=0.9,en-US;q=0.8,en;q=0.7",
}

UNTRUSTED_IMAGE_MARKERS = (
    "bike_0.",
    "acc_0.",
    "part_0.",
    "placeholder",
    "no-image",
    "sin-imagen",
)

def clean_filename_part(text):
    """Cleans a string to make it safe for filenames (lowercase, no accents, alphanumeric and hyphens)."""
    if not text:
        return ""
    text = text.lower().strip()
    # Normalize accents
    text = "".join(c for c in unicodedata.normalize('NFKD', text) if not unicodedata.combining(c))
    # Replace anything that isn't alphanumeric or spaces/hyphens
    text = re.sub(r'[^a-z0-9\s\-]', '', text)
    # Replace spaces and multiple hyphens with a single hyphen
    text = re.sub(r'[\s\-]+', '-', text).strip('-')
    return text

def is_untrusted_image_url(url):
    """Checks if the URL matches placeholder markers."""
    if not url:
        return True
    url_lower = url.lower()
    return any(marker in url_lower for marker in UNTRUSTED_IMAGE_MARKERS)

def make_absolute_url(url, base_url=None):
    """Converts a relative URL to absolute if base_url is provided."""
    if not url:
        return ""
    url = url.strip()
    if url.startswith("//"):
        return "https:" + url
    if not url.startswith(("http://", "https://")):
        if base_url:
            return urllib.parse.urljoin(base_url, url)
        return ""
    return url

def validate_image_bytes(content):
    """Validates if image bytes match standard formats and exceed minimum size."""
    if not content or len(content) < 1000:
        return False
    
    # Check magic numbers
    head = content[:12]
    is_jpeg = head[:3] == b"\xff\xd8\xff"
    is_png = head[:4] == b"\x89PNG"
    is_webp = head[:4] == b"RIFF" and head[8:12] == b"WEBP"
    is_gif = head[:6] in (b"GIF87a", b"GIF89a")
    
    return is_jpeg or is_png or is_webp or is_gif

def download_image(url, brand=None, model=None, base_url=None, max_size_bytes=5 * 1024 * 1024):
    """
    Downloads an image, validates it, and saves it optimized as WebP in static/images/products/.
    
    Args:
        url (str): Remote URL of the image.
        brand (str, optional): Brand of the bicycle to build a unique name.
        model (str, optional): Model of the bicycle to build a unique name.
        base_url (str, optional): Base URL to resolve relative paths.
        max_size_bytes (int): Maximum allowed file size to download (default 5MB).
        
    Returns:
        str: Relative URL path (e.g., '/static/images/products/brand_model_<hash>.webp') 
             or '/static/images/placeholder-bike.webp' if failed.
    """
    placeholder_fallback = "/static/images/placeholder-bike.webp"
    
    absolute_url = make_absolute_url(url, base_url)
    if not absolute_url or is_untrusted_image_url(absolute_url):
        return placeholder_fallback

    # Determine project directories (relative to this file)
    utils_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(utils_dir)
    project_root = os.path.dirname(backend_dir)
    
    products_dir = os.path.join(project_root, "static", "images", "products")
    os.makedirs(products_dir, exist_ok=True)
    
    # Generate unique filename based on brand, model, and URL hash
    clean_brand = clean_filename_part(brand) or "generica"
    clean_model = clean_filename_part(model) or "producto"
    url_hash = hashlib.md5(absolute_url.encode()).hexdigest()[:8]
    
    filename = f"{clean_brand}_{clean_model}_{url_hash}.webp"
    dest_path = os.path.join(products_dir, filename)
    relative_url = f"/static/images/products/{filename}"

    # If it already exists and is valid, reuse it (Avoid downloading duplicate)
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 1000:
        return relative_url

    # Set referer header from the image URL domain
    custom_headers = HEADERS.copy()
    try:
        parsed_uri = urllib.parse.urlparse(absolute_url)
        custom_headers["Referer"] = f"{parsed_uri.scheme}://{parsed_uri.netloc}/"
    except Exception:
        pass

    # 3 Retries with exponential backoff
    response_bytes = None
    for attempt in range(3):
        try:
            # We fetch in stream mode to verify Content-Length before downloading the full payload
            r = scraper.get(absolute_url, headers=custom_headers, timeout=15, stream=True)
            if r.status_code == 200:
                content_length = r.headers.get('Content-Length')
                if content_length and int(content_length) > max_size_bytes:
                    return placeholder_fallback
                
                # Download chunks
                content = bytearray()
                for chunk in r.iter_content(chunk_size=8192):
                    content.extend(chunk)
                    if len(content) > max_size_bytes:
                        return placeholder_fallback
                
                downloaded_data = bytes(content)
                if validate_image_bytes(downloaded_data):
                    response_bytes = downloaded_data
                    break
        except Exception:
            pass
        
        if attempt < 2:
            time.sleep(2 ** attempt) # Backoff: 1s, 2s
            
    if not response_bytes:
        print(f"  [WARN] Failed to download image: {absolute_url}")
        return placeholder_fallback

    # Optimize and save as WebP
    if HAS_PILLOW:
        try:
            image = Image.open(io.BytesIO(response_bytes))
            # Convert RGBA/P modes to preserve transparency or convert to RGB
            if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
                image.save(dest_path, format="WEBP", quality=80, method=4)
            else:
                image.convert("RGB").save(dest_path, format="WEBP", quality=80, method=4)
            return relative_url
        except Exception as e:
            print(f"  [WARN] PIL conversion to WebP failed: {e}. Falling back to raw save.")
            
    # Fallback: Save original bytes without conversion if PIL fails
    parsed = urllib.parse.urlparse(absolute_url)
    ext = os.path.splitext(parsed.path)[1].lower()
    if ext not in ('.jpg', '.jpeg', '.png', '.webp', '.gif'):
        ext = '.jpg'
    
    fallback_filename = f"{clean_brand}_{clean_model}_{url_hash}{ext}"
    dest_path = os.path.join(products_dir, fallback_filename)
    relative_url = f"/static/images/products/{fallback_filename}"
    
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 1000:
        return relative_url
        
    try:
        with open(dest_path, "wb") as f:
            f.write(response_bytes)
        return relative_url
    except Exception as e:
        print(f"  [ERROR] Failed to save image raw locally: {e}")
        return placeholder_fallback

if __name__ == "__main__":
    # Test downloader with a sample image
    test_url = "https://images.unsplash.com/photo-1485965120184-e220f721d03e"
    print("Testing image downloader...")
    path = download_image(test_url, brand="TestBrand", model="TestBike")
    print(f"Result path: {path}")
