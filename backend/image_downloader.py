# Legacy compatibility wrapper. Delegates to backend/utils/image_downloader.py
import os
import sys

# Add current directory and utils to path if needed
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from utils.image_downloader import download_image as new_download_image
from utils.image_downloader import clean_filename_part, is_untrusted_image_url, make_absolute_url, validate_image_bytes

def download_image(url, output_dir=None, custom_filename=None, base_url=None, max_size_bytes=5 * 1024 * 1024, brand=None, model=None):
    """
    Legacy wrapper.
    If called with the old signature, maps custom_filename to model.
    """
    if not brand and custom_filename:
        brand = "legacy"
        model = custom_filename
    return new_download_image(url, brand=brand, model=model, base_url=base_url, max_size_bytes=max_size_bytes)
