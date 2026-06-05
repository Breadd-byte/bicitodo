# copenhague.py - Copenhague Scraper Module
from scrapers.bicycles.run_scrapers import scrape_jumpseller

def scrape():
    return scrape_jumpseller(
        "Copenhague", "copenhague", "https://www.copenhague.cl", 
        ["/bicicletas"]
    )
