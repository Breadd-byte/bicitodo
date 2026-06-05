# faucon.py - Faucon Bikes Scraper Module
from scrapers.bicycles.run_scrapers import scrape_shopify

def scrape():
    return scrape_shopify(
        "Faucon Bikes", "faucon", "https://fauconbikes.cl", 
        ["bicicletas-1", "mountain-bike", "ruta"]
    )
