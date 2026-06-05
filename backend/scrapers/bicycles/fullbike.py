# fullbike.py - Full Bike Scraper Module
from scrapers.bicycles.run_scrapers import scrape_jumpseller

def scrape():
    return scrape_jumpseller(
        "Full Bike", "fullbike", "https://fullbike.cl", 
        ["/bicicletas"]
    )
