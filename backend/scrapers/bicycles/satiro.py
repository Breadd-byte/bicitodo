# satiro.py - Satiro Bikes Scraper Module
from scrapers.bicycles.run_scrapers import scrape_shopify

def scrape():
    return scrape_shopify(
        "Satiro Bikes", "satiro", "https://satirobikes.cl", 
        ["bicicletas", "mountain-bike", "ruta"]
    )
