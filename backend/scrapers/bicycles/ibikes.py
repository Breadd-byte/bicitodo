# ibikes.py - iBikes Scraper Module
from scrapers.bicycles.run_scrapers import scrape_shopify

def scrape():
    return scrape_shopify(
        "iBikes", "ibikes", "https://ibikes.cl", 
        ["bicicletas", "mountain-bike", "bicicletas-de-ruta", "bicicletas-electricas"]
    )
