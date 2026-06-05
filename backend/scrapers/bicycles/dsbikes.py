# dsbikes.py - DS Bikes Scraper Module
from scrapers.bicycles.run_scrapers import scrape_shopify

def scrape():
    return scrape_shopify(
        "DS Bikes", "dsbikes", "https://www.dsbikes.cl", 
        ["bicicletas", "mountain-bike", "ruta"]
    )
