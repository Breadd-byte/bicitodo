# pipelines.py - Scrapy to PostgreSQL Pipeline
import psycopg2
from psycopg2.extras import RealDictCursor

class BicitodoPipeline:
    def __init__(self, db_settings=None):
        self.db_settings = db_settings or {
            'host': 'localhost',
            'database': 'bicitodo',
            'user': 'postgres',
            'password': 'password'
        }
        self.connection = None
        self.cursor = None

    def open_spider(self, spider):
        # En producción: self.connection = psycopg2.connect(**self.db_settings)
        # self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)
        pass

    def close_spider(self, spider):
        # if self.connection:
        #    self.connection.close()
        pass

    def process_item(self, item, spider):
        # 1. Normalizar nombre para el Matcher
        normalized_name = self.normalize_name(item['brand'], item['model'])
        
        # 2. Buscar o crear producto base (Cerebro del Matcher)
        # product_id = self.get_or_create_product(item, normalized_name)
        
        # 3. Guardar precio actual en store_products
        # self.save_store_product(item, product_id)
        
        # 4. Registrar en historial de precios
        # self.log_price_history(item)
        
        return item

    def normalize_name(self, brand, model):
        # Lógica básica: minúsculas, sin espacios extra, remover "Bicicleta" redundante
        name = f"{brand} {model}".lower()
        name = name.replace("bicicleta", "").strip()
        # Remover "aro 29", "29 pulgadas", etc para matching genérico
        # (Esto se refina en el Matcher Service)
        return name
