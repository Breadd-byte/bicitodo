import scrapy

class BicitodoItem(scrapy.Item):
    # Identificación
    name = scrapy.Field()
    brand = scrapy.Field()
    model = scrapy.Field()
    sku = scrapy.Field()
    
    # Precios
    price_normal = scrapy.Field()    # Precio estándar
    price_card = scrapy.Field()      # Precio con tarjeta (CMR, Ripley Card, etc.)
    
    # Stock
    stock = scrapy.Field()
    
    # Categorización
    category_type = scrapy.Field()   # 'MTB', 'Ruta', 'Urbana', 'Infantil', 'Eléctrica'
    wheel_size = scrapy.Field()      # '26', '27.5', '29', '700c', '20', '24', '16'
    frame_type = scrapy.Field()      # 'Aluminio', 'Carbono', 'Acero', 'Titanio'
    
    # Tienda
    store = scrapy.Field()
    url = scrapy.Field()
    image_url = scrapy.Field()
    
    # Especificaciones técnicas (JSON)
    specs = scrapy.Field()           # Dict con aro, frenos, transmision, etc.
    
    # Metadata
    timestamp = scrapy.Field()
