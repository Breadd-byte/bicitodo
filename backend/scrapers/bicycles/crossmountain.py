# crossmountain.py - CrossMountain Scraper Module
from scrapers.bicycles.run_scrapers import scrape_shopify

def scrape():
    return scrape_shopify(
        "CrossMountain", "crossmountain", "https://crossmountain.cl", 
        ["bicicletas"]
    )
