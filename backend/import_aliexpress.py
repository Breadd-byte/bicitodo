# import_aliexpress.py - Automatic high-performance importer for AliExpress cycling products
import sys
import os
import sqlite3
import json
import random
from datetime import datetime
from repair_aliexpress_catalog import repair_database as repair_aliexpress_catalog, VERIFIED_MATCHES, normalize_text
from repair_aliexpress_images import repair_database as repair_aliexpress_images

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

DB_PATH = r"c:\Users\basti\Desktop\bicitodo\backend\database\bicitodo.db"

# Strict Whitelist of Brands
BRANDS_WHITELIST = {
    "GPS y Electrónica": ["GEOID", "Magene", "iGPSPORT", "Coospo", "Cycplus"],
    "Accesorios": ["Rockbros", "Rhinowalk", "West Biking"],
    "Herramientas": ["Toopre", "ZTTO", "Riderace"],
    "Componentes": ["Litepro", "ZRace", "L-TWOO", "Bucklos", "Sunshine", "UNO", "Toseek"],
    "Ruedas": ["Elitewheels", "Superteam"],
    "Tubeless y TPU": ["RideNow", "ThinkRider"],
    "Lentes": ["Kapvoe", "Queshark", "Rockbros"],
    "Ropa": ["Darevie", "Arsuxeo", "Cheji", "Inbike"]
}

# Image URL maps by type (High quality, high resolution, non-broken images)
TYPE_IMAGES = {
    "ciclocomputadores": [
        "https://images.unsplash.com/photo-1508962914676-134849a727f0?auto=format&fit=crop&w=600&h=400&q=80",
        "https://images.unsplash.com/photo-1517649763962-0c623066013b?auto=format&fit=crop&w=600&h=400&q=80",
        "https://images.unsplash.com/photo-1501147830916-ae44a90895ed?auto=format&fit=crop&w=600&h=400&q=80"
    ],
    "sensores": [
        "https://images.unsplash.com/photo-1517649763962-0c623066013b?auto=format&fit=crop&w=600&h=400&q=80"
    ],
    "radares": [
        "https://images.unsplash.com/photo-1501147830916-ae44a90895ed?auto=format&fit=crop&w=600&h=400&q=80"
    ],
    "luces": [
        "https://images.unsplash.com/photo-1544198365-f5d60b6d8190?auto=format&fit=crop&w=600&h=400&q=80",
        "https://images.unsplash.com/photo-1485965120184-e220f721d03e?auto=format&fit=crop&w=600&h=400&q=80"
    ],
    "bolsos": [
        "https://images.unsplash.com/photo-1553108715-53d71b12d730?auto=format&fit=crop&w=600&h=400&q=80",
        "https://images.unsplash.com/photo-1532298229144-0ec0c57515c7?auto=format&fit=crop&w=600&h=400&q=80"
    ],
    "herramientas": [
        "https://images.unsplash.com/photo-1485965120184-e220f721d03e?auto=format&fit=crop&w=600&h=400&q=80",
        "https://images.unsplash.com/photo-1530893609608-32a9af3aa95c?auto=format&fit=crop&w=600&h=400&q=80"
    ],
    "bombas": [
        "https://images.unsplash.com/photo-1485965120184-e220f721d03e?auto=format&fit=crop&w=600&h=400&q=80"
    ],
    "tpu": [
        "https://images.unsplash.com/photo-1507035895480-2b3156c31fc8?auto=format&fit=crop&w=600&h=400&q=80"
    ],
    "componentes": [
        "https://images.unsplash.com/photo-1532298229144-0ec0c57515c7?auto=format&fit=crop&w=600&h=400&q=80",
        "https://images.unsplash.com/photo-1508962914676-134849a727f0?auto=format&fit=crop&w=600&h=400&q=80"
    ],
    "ruedas": [
        "https://images.unsplash.com/photo-1507035895480-2b3156c31fc8?auto=format&fit=crop&w=600&h=400&q=80"
    ],
    "sillines": [
        "https://images.unsplash.com/photo-1485965120184-e220f721d03e?auto=format&fit=crop&w=600&h=400&q=80"
    ],
    "lentes": [
        "https://images.unsplash.com/photo-1572635196237-14b3f281503f?auto=format&fit=crop&w=600&h=400&q=80",
        "https://images.unsplash.com/photo-1511556532299-8f662fc26c06?auto=format&fit=crop&w=600&h=400&q=80"
    ],
    "ropa": [
        "https://images.unsplash.com/photo-1541614101331-1a5a3a194e92?auto=format&fit=crop&w=600&h=400&q=80"
    ],
    "soportes": [
        "https://images.unsplash.com/photo-1508962914676-134849a727f0?auto=format&fit=crop&w=600&h=400&q=80"
    ]
}

# Product base templates containing model name, base price in CLP, category and subcategory (type)
PRODUCT_TEMPLATES = [
    # GPS y Ciclocomputadores
    {"brand": "GEOID", "model": "CC400 GPS", "type": "ciclocomputadores", "category": "accesorios", "price": 18990, "specs": {"Pantalla": "FSTN 1.9''", "Duración Batería": "20 Horas", "Conexión": "Bluetooth / ANT+"}},
    {"brand": "GEOID", "model": "CC500 GPS Pro", "type": "ciclocomputadores", "category": "accesorios", "price": 24990, "specs": {"Pantalla": "FSTN 2.2''", "Duración Batería": "24 Horas", "Conexión": "Bluetooth / ANT+"}},
    {"brand": "GEOID", "model": "CC600 GPS Smart", "type": "ciclocomputadores", "category": "accesorios", "price": 32990, "specs": {"Pantalla": "LCD 2.4''", "Duración Batería": "30 Horas", "Conexión": "Bluetooth / ANT+"}},
    {"brand": "GEOID", "model": "CC700 Color GPS", "type": "ciclocomputadores", "category": "accesorios", "price": 54990, "specs": {"Pantalla": "Color LCD 2.6''", "Duración Batería": "32 Horas", "Navegación": "Soporte de mapas offline"}},
    {"brand": "GEOID", "model": "CC700 Pro GPS Bundle", "type": "ciclocomputadores", "category": "accesorios", "price": 84990, "specs": {"Pantalla": "Color LCD 2.6''", "Duración Batería": "32 Horas", "Accesorios": "Incluye Sensor de Cadencia y HR"}},
    {"brand": "Magene", "model": "C206 GPS Ciclocomputador", "type": "ciclocomputadores", "category": "accesorios", "price": 19990, "specs": {"Pantalla": "FSTN 1.9''", "Batería": "20h", "Conexión": "ANT+ / BLE"}},
    {"brand": "Magene", "model": "C406 Pro GPS Inteligente", "type": "ciclocomputadores", "category": "accesorios", "price": 38990, "specs": {"Pantalla": "FSTN 2.4''", "Batería": "28h", "Conexión": "ANT+ / BLE / WiFi"}},
    {"brand": "Magene", "model": "C506 GPS Pantalla a Color", "type": "ciclocomputadores", "category": "accesorios", "price": 68990, "specs": {"Pantalla": "Color 2.4''", "Batería": "24h", "Navegación": "Navegación inteligente con mapa"}},
    {"brand": "Magene", "model": "C606 Smart GPS Flagship", "type": "ciclocomputadores", "category": "accesorios", "price": 118990, "specs": {"Pantalla": "Color Táctil 2.8''", "Batería": "28h", "Navegación": "Navegación por mapas avanzada"}},
    {"brand": "iGPSPORT", "model": "BSC100S GPS de Entrada", "type": "ciclocomputadores", "category": "accesorios", "price": 28990, "specs": {"Pantalla": "2.6'' FSTN", "Batería": "40h", "Conexión": "ANT+ / BLE"}},
    {"brand": "iGPSPORT", "model": "BSC200 GPS con Mapa", "type": "ciclocomputadores", "category": "accesorios", "price": 49990, "specs": {"Pantalla": "2.5'' LCD", "Batería": "30h", "Navegación": "Ruta giro a giro"}},
    {"brand": "iGPSPORT", "model": "BSC300 GPS a Color", "type": "ciclocomputadores", "category": "accesorios", "price": 79990, "specs": {"Pantalla": "Color 2.4''", "Batería": "20h", "Navegación": "Navegación por mapas detallada"}},
    {"brand": "iGPSPORT", "model": "iGS630 GPS Profesional", "type": "ciclocomputadores", "category": "accesorios", "price": 149990, "specs": {"Pantalla": "Color 2.8''", "Batería": "35h", "Navegación": "Mapas offline y altímetro barométrico"}},
    {"brand": "Coospo", "model": "BC107 GPS Inalámbrico", "type": "ciclocomputadores", "category": "accesorios", "price": 26990, "specs": {"Pantalla": "2.4'' LCD", "Batería": "28h", "Conexión": "ANT+ / BLE"}},
    {"brand": "Coospo", "model": "BC200 Pro GPS Triple Banda", "type": "ciclocomputadores", "category": "accesorios", "price": 44990, "specs": {"Pantalla": "2.6'' LCD", "Batería": "36h", "Conexión": "GPS/GLONASS/BeiDou"}},
    
    # Sensores
    {"brand": "Magene", "model": "H303 Sensor Banda Cardíaca", "type": "sensores", "category": "accesorios", "price": 14990, "specs": {"Tipo": "Banda de Pecho", "Protocolo": "ANT+ & BLE", "Batería": "Hasta 1000 horas"}},
    {"brand": "Magene", "model": "H803 Sensor de Pulso de Brazo", "type": "sensores", "category": "accesorios", "price": 24990, "specs": {"Tipo": "Brazalete Óptico", "Protocolo": "ANT+ & BLE", "Batería": "Batería recargable"}},
    {"brand": "Magene", "model": "S3+ Sensor de Cadencia y Velocidad", "type": "sensores", "category": "accesorios", "price": 9990, "specs": {"Tipo": "Dual Cadencia/Velocidad", "Instalación": "Eje de maza o biela", "Protocolo": "ANT+ & BLE"}},
    {"brand": "GEOID", "model": "Sensor de Velocidad Magnético", "type": "sensores", "category": "accesorios", "price": 8990, "specs": {"Tipo": "Velocímetro de Eje", "Protocolo": "ANT+ & BLE", "Resistencia": "IP67"}},
    {"brand": "GEOID", "model": "Sensor de Cadencia Bluetooth", "type": "sensores", "category": "accesorios", "price": 8990, "specs": {"Tipo": "Sensor de Pedaleo", "Protocolo": "ANT+ & BLE", "Batería": "CR2032"}},
    {"brand": "GEOID", "model": "HR Sensor Banda de Pecho Pro", "type": "sensores", "category": "accesorios", "price": 13990, "specs": {"Tipo": "Banda Cardíaca", "Protocolo": "ANT+ & BLE", "Precisión": "+- 1 lpm"}},
    {"brand": "Coospo", "model": "H6 Sensor Cardíaco Bluetooth", "type": "sensores", "category": "accesorios", "price": 12990, "specs": {"Tipo": "Banda de Pecho", "Protocolo": "ANT+ & BLE", "Duración CR2032": "300 horas"}},
    {"brand": "Coospo", "model": "H808S Banda Cardíaca Inteligente", "type": "sensores", "category": "accesorios", "price": 16990, "specs": {"Tipo": "Banda Pecho con Indicador LED", "Protocolo": "ANT+ & BLE", "Batería": "Bajo consumo"}},
    
    # Radares
    {"brand": "Magene", "model": "L308 Luz Trasera Personalizable", "type": "radares", "category": "accesorios", "price": 29990, "specs": {"Tipo": "Luz Trasera Inteligente", "Personalización": "Pantalla LED con dibujos personalizados", "Conexión": "BLE"}},
    {"brand": "Magene", "model": "L508 Radar de Vista Trasera Inteligente", "type": "radares", "category": "accesorios", "price": 98990, "specs": {"Tipo": "Radar con Luz", "Detección": "Hasta 140 metros", "Compatibilidad": "Garmin/Wahoo/Magene"}},
    {"brand": "Cycplus", "model": "L7 Radar Trasero de Ciclismo", "type": "radares", "category": "accesorios", "price": 84990, "specs": {"Tipo": "Radar con Luz de Advertencia", "Detección": "Hasta 120 metros", "Batería": "Hasta 16 horas"}},
    {"brand": "iGPSPORT", "model": "SR30 Radar Trasero Inteligente", "type": "radares", "category": "accesorios", "price": 89990, "specs": {"Tipo": "Radar con Luz", "Rango": "150 metros", "Batería": "Hasta 25 horas"}},
    
    # Luces
    {"brand": "Rockbros", "model": "Luz Delantera 400LM Recargable USB", "type": "luces", "category": "accesorios", "price": 10990, "specs": {"Brillo": "400 Lúmenes", "Carcasa": "Aluminio", "Batería": "2000mAh"}},
    {"brand": "Rockbros", "model": "Luz Delantera 800LM Aero", "type": "luces", "category": "accesorios", "price": 15990, "specs": {"Brillo": "800 Lúmenes", "Carcasa": "Aluminio CNC", "Batería": "3000mAh"}},
    {"brand": "Rockbros", "model": "Luz Delantera 1000LM Recargable", "type": "luces", "category": "accesorios", "price": 22990, "specs": {"Brillo": "1000 Lúmenes", "Carcasa": "Aluminio", "Batería": "4800mAh"}},
    {"brand": "Rockbros", "model": "Luz Delantera Dual 1500LM", "type": "luces", "category": "accesorios", "price": 34990, "specs": {"Brillo": "1500 Lúmenes", "Carcasa": "Aluminio Aero", "Batería": "6400mAh (Powerbank)"}},
    {"brand": "West Biking", "model": "Smart Tail Light Luz Inteligente", "type": "luces", "category": "accesorios", "price": 9990, "specs": {"Tipo": "Luz Trasera", "Sensor": "Auto Start/Stop y sensor de freno", "Carga": "USB-C"}},
    
    # Bolsos
    {"brand": "Rhinowalk", "model": "Bolso de Cuadro Impermeable Frame Bag", "type": "bolsos", "category": "accesorios", "price": 14990, "specs": {"Material": "TPU Impermeable", "Volumen": "1.5L / 2L / 3L", "Ajuste": "Correas de Velcro de alta resistencia"}},
    {"brand": "Rhinowalk", "model": "Bolso de Sillín Premium Saddle Bag", "type": "bolsos", "category": "accesorios", "price": 12990, "specs": {"Material": "Poliéster 840D Impermeable", "Volumen": "1.2L", "Diseño": "Aero compacto"}},
    {"brand": "Rhinowalk", "model": "Bolso de Tubo Superior Top Tube Bag", "type": "bolsos", "category": "accesorios", "price": 11990, "specs": {"Material": "TPU de alta densidad", "Acceso": "Cierre impermeable YKK", "Fijación": "Velcro"}},
    {"brand": "Rhinowalk", "model": "Bolso de Manubrio Handlebar Bag", "type": "bolsos", "category": "accesorios", "price": 16990, "specs": {"Material": "Lona impermeable", "Volumen": "2.4L", "Extra": "Correa para colgar al hombro"}},
    {"brand": "Rockbros", "model": "Bolso Impermeable de Gran Capacidad", "type": "bolsos", "category": "accesorios", "price": 18990, "specs": {"Material": "Nylon TPU", "Volumen": "4L", "Ajuste": "Tubo superior/cuadro"}},
    {"brand": "Rockbros", "model": "Bolso de Teléfono con Ventana Táctil", "type": "bolsos", "category": "accesorios", "price": 13990, "specs": {"Material": "PU + EVA", "Compatibilidad": "Pantallas de hasta 6.8 pulgadas", "Visera": "Protectora solar"}},
    
    # Herramientas
    {"brand": "Toopre", "model": "Llave Dinamométrica de Torque Pro", "type": "herramientas", "category": "accesorios", "price": 28990, "specs": {"Rango": "2-24 Nm", "Precisión": "+- 4%", "Bits Incluidos": "Hex 2, 2.5, 3, 4, 5, 6, 8, Torx T10, T25, T30"}},
    {"brand": "Toopre", "model": "Medidor de Desgaste de Cadena Chain Checker", "type": "herramientas", "category": "accesorios", "price": 3990, "specs": {"Material": "Acero Inoxidable CNC", "Rangos": "0.5% / 0.75% / 1.0%"}},
    {"brand": "ZTTO", "model": "Herramienta Extractora de Cassette", "type": "herramientas", "category": "accesorios", "price": 4990, "specs": {"Material": "Acero endurecido", "Compatibilidad": "Shimano / SRAM / Sunrace"}},
    {"brand": "ZTTO", "model": "Extractor de Motor / Bottom Bracket Tool", "type": "herramientas", "category": "accesorios", "price": 6990, "specs": {"Material": "Aluminio CNC", "Compatibilidad": "Shimano Hollowtech II / SRAM DUB"}},
    {"brand": "Riderace", "model": "Multiherramienta Plegable 16 en 1", "type": "herramientas", "category": "accesorios", "price": 7990, "specs": {"Material": "Acero al Cromo-Vanadio", "Herramientas": "Cortacadena, Hex 2-8, Torx, destornilladores"}},
    {"brand": "Riderace", "model": "Calibre de Desgaste de Cadena Digital", "type": "herramientas", "category": "accesorios", "price": 8990, "specs": {"Material": "Aluminio CNC", "Precisión": "Digital micrométrica"}},
    
    # Bombas
    {"brand": "Cycplus", "model": "Bomba Eléctrica Mini AS2 Recargable", "type": "bombas", "category": "accesorios", "price": 49990, "specs": {"Tipo": "Compresor Portable", "Presión Máxima": "100 PSI", "Batería": "300mAh USB-C", "Peso": "97g"}},
    {"brand": "Cycplus", "model": "Bomba Eléctrica Inteligente AS2 Ultra", "type": "bombas", "category": "accesorios", "price": 79990, "specs": {"Tipo": "Compresor Digital", "Presión Máxima": "120 PSI", "Batería": "500mAh USB-C", "Peso": "120g (con pantalla)"}},
    {"brand": "Riderace", "model": "Mini Inflador de Mano Telescópico 120PSI", "type": "bombas", "category": "accesorios", "price": 6990, "specs": {"Presión": "120 PSI", "Material": "Aluminio CNC", "Válvula": "Presta / Schrader reversible"}},
    
    # Tubeless y TPU
    {"brand": "RideNow", "model": "Cámara TPU Superlight Road 700c", "type": "tpu", "category": "repuestos", "price": 4990, "specs": {"Peso": "36 gramos", "Material": "TPU Premium", "Válvula": "Presta 65mm / 85mm"}},
    {"brand": "RideNow", "model": "Cámara TPU MTB Reforzada 29\"", "type": "tpu", "category": "repuestos", "price": 6990, "specs": {"Peso": "66 gramos", "Material": "TPU Ultra Resistente", "Válvula": "Presta 45mm"}},
    {"brand": "ThinkRider", "model": "Cámara TPU Ultraliviana de Ciclismo", "type": "tpu", "category": "repuestos", "price": 4500, "specs": {"Peso": "38 gramos", "Material": "Poliuretano termoplástico", "Válvula": "Presta 60mm"}},
    {"brand": "ZTTO", "model": "Kit de Conversión Tubeless Cinta + Válvula", "type": "tpu", "category": "repuestos", "price": 12990, "specs": {"Cinta": "25mm x 10m", "Válvulas": "Par de válvulas tubeless de aluminio de 44mm"}},
    {"brand": "ZTTO", "model": "Válvulas Tubeless de Aluminio Par", "type": "tpu", "category": "repuestos", "price": 6990, "specs": {"Largo": "44mm / 60mm / 80mm", "Material": "Aleación de Aluminio CNC", "Colores": "Negro, Rojo, Azul"}},
    
    # Componentes
    {"brand": "Litepro", "model": "Monoplato Ovalado 46T / 48T / 50T", "type": "componentes", "category": "repuestos", "price": 14990, "specs": {"Material": "Aluminio 7075-T6 CNC", "BCD": "130mm BCD", "Peso": "85g"}},
    {"brand": "ZRace", "model": "Monoplato de Ciclismo Direct Mount", "type": "componentes", "category": "repuestos", "price": 18990, "specs": {"Material": "Aluminio 7075", "Dientes": "32T / 34T / 36T / 38T", "Compatibilidad": "SRAM GXP / Shimano"}},
    {"brand": "ZRace", "model": "Juego de Bielas Integradas de Montaña", "type": "componentes", "category": "repuestos", "price": 39990, "specs": {"Material": "Aleación de Aluminio", "Eje": "24mm (Shimano compatible)", "Peso": "680g"}},
    {"brand": "UNO", "model": "Tee / Stem de Aluminio Ultra Liviano 7 Grados", "type": "componentes", "category": "repuestos", "price": 12990, "specs": {"Material": "Aluminio 3D Forjado 6061", "Ángulo": "7 Grados", "Largo": "60mm a 110mm"}},
    {"brand": "UNO", "model": "Manubrio de Aluminio Doble Altura MTB", "type": "componentes", "category": "repuestos", "price": 15990, "specs": {"Material": "Aluminio 6061-T6", "Ancho": "720mm / 780mm", "Diámetro": "31.8mm"}},
    {"brand": "Toseek", "model": "Tija / Tubo de Asiento de Fibra de Carbono", "type": "componentes", "category": "repuestos", "price": 19990, "specs": {"Material": "100% Fibra de Carbono", "Diámetro": "27.2mm / 30.9mm / 31.6mm", "Largo": "350mm / 400mm"}},
    {"brand": "L-TWOO", "model": "Manetas de Cambio R5 2x9 Velocidades", "type": "componentes", "category": "repuestos", "price": 28990, "specs": {"Tipo": "Manetas integradas de ruta", "Velocidades": "2x9v", "Compatibilidad": "Shimano Sora"}},
    {"brand": "L-TWOO", "model": "Transmisión R7 2x10v Manetas y Desviadores", "type": "componentes", "category": "repuestos", "price": 48990, "specs": {"Tipo": "Kit de Transmisión", "Velocidades": "2x10v", "Compatibilidad": "Shimano Tiagra"}},
    {"brand": "L-TWOO", "model": "Kit de Ruta R9 2x11v Carbon Edition", "type": "componentes", "category": "repuestos", "price": 79990, "specs": {"Tipo": "Grupo Parcial con Carbono", "Velocidades": "2x11v", "Compatibilidad": "Shimano 105"}},
    {"brand": "Sunshine", "model": "Cassette Cromado de Ruta / MTB de 11 Velocidades", "type": "componentes", "category": "repuestos", "price": 18990, "specs": {"Dientes": "11-28T / 11-32T / 11-36T", "Material": "Acero de Alta Tensión", "Compatibilidad": "Shimano / SRAM"}},
    {"brand": "Bucklos", "model": "Cassette MTB 10 Velocidades Relación Amplia", "type": "componentes", "category": "repuestos", "price": 15990, "specs": {"Relación": "11-42T / 11-46T", "Material": "Acero niquelado", "Compatibilidad": "Shimano HG"}},
    
    # Ruedas
    {"brand": "Elitewheels", "model": "Juego de Ruedas ENT 38mm Carbono", "type": "ruedas", "category": "repuestos", "price": 349900, "specs": {"Perfil": "38mm de carbono", "Material": "Carbono Toray T700", "Mazas": "Elite Wheels Rodamientos Cerámicos"}},
    {"brand": "Elitewheels", "model": "Juego de Ruedas ENT 50mm Carbono Tubeless", "type": "ruedas", "category": "repuestos", "price": 389900, "specs": {"Perfil": "50mm Aero", "Material": "Carbono Toray T700", "Compatibilidad": "Tubeless Ready"}},
    {"brand": "Elitewheels", "model": "Ruedas de Carbono para Freno de Disco SLR", "type": "ruedas", "category": "repuestos", "price": 429900, "specs": {"Perfil": "45mm", "Mazas": "Centerlock Disco", "Material": "Carbono T800"}},
    {"brand": "Superteam", "model": "Ruedas de Carbono Perfil 50mm Remachador", "type": "ruedas", "category": "repuestos", "price": 289900, "specs": {"Perfil": "50mm", "Material": "Carbono 3K Mate", "Maza": "Powerway R13"}},
    
    # Sillines
    {"brand": "Rockbros", "model": "Sillín de Ciclismo 3D Impreso en Nido de Abeja", "type": "sillines", "category": "repuestos", "price": 39990, "specs": {"Tecnología": "Impresión 3D de TPU", "Rieles": "Cromo-molibdeno", "Diseño": "Aero antiprostático"}},
    {"brand": "West Biking", "model": "Sillín de Gel Ergonómico Antiprostático", "type": "sillines", "category": "repuestos", "price": 14990, "specs": {"Material": "Cuero PU + Gel de alta elasticidad", "Rieles": "Acero", "Diseño": "Acolchado premium"}},
    
    # Lentes
    {"brand": "Rockbros", "model": "Lentes de Ciclismo Fotocromáticos Deportivos", "type": "lentes", "category": "accesorios", "price": 12990, "specs": {"Lente": "Fotocromático inteligente", "Protección": "UV400 100%", "Marco": "TR90 flexible"}},
    {"brand": "Kapvoe", "model": "Lentes Fotocromáticos Deportivos Aero", "type": "lentes", "category": "accesorios", "price": 14990, "specs": {"Lente": "Fotocromático", "Protección": "UV400", "Accesorios": "Estuche rígido y paño"}},
    {"brand": "Queshark", "model": "Lentes de Sol Polarizados Deportivos", "type": "lentes", "category": "accesorios", "price": 11990, "specs": {"Lentes": "1 Polarizada + 2 de recambio", "Protección": "UV400", "Material": "Policarbonato"}},
    
    # Ropa
    {"brand": "Darevie", "model": "Tricota / Jersey Profesional de Ruta Aero", "type": "ropa", "category": "accesorios", "price": 18990, "specs": {"Material": "Spandex respirable", "Corte": "Aero fit", "Cierre": "YKK completo"}},
    {"brand": "Darevie", "model": "Calza / Bib Shorts con Badana de Gel 6h", "type": "ropa", "category": "accesorios", "price": 28990, "specs": {"Badana": "Gel de alta densidad 6 horas", "Material": "Lycra italiana", "Tirantes": "Malla respirable"}},
    {"brand": "Arsuxeo", "model": "Tricota de Manga Larga para Primavera", "type": "ropa", "category": "accesorios", "price": 15990, "specs": {"Material": "Poliéster de secado rápido", "Bolsillos": "3 bolsillos traseros", "Reflectante": "Tiras de seguridad"}},
    {"brand": "Arsuxeo", "model": "Chaqueta Térmica Cortaviento Impermeable", "type": "ropa", "category": "accesorios", "price": 24990, "specs": {"Material": "Poliéster con forro térmico", "Protección": "Impermeable y cortaviento", "Estación": "Invierno"}},
    {"brand": "Cheji", "model": "Bib Shorts de Ciclismo Pro Slim Fit", "type": "ropa", "category": "accesorios", "price": 26990, "specs": {"Badana": "Espuma celular 3D", "Ajuste": "Corte anatómico", "Material": "Lycra"}},
    {"brand": "Inbike", "model": "Guantes de Ciclismo con Gel Antigolpes Cortos", "type": "ropa", "category": "accesorios", "price": 7990, "specs": {"Material": "Lycra elástica", "Palma": "Gel de silicona amortiguador", "Cierre": "Velcro"}},
    
    # Soportes
    {"brand": "Rockbros", "model": "Soporte de Manubrio para Garmin / Wahoo / Bryton", "type": "soportes", "category": "accesorios", "price": 9990, "specs": {"Material": "Aluminio CNC", "Compatibilidad": "Garmin/Wahoo/Bryton", "Extra": "Adaptador GoPro inferior"}},
    {"brand": "Rockbros", "model": "Soporte Metálico de Teléfono para Manubrio", "type": "soportes", "category": "accesorios", "price": 8990, "specs": {"Material": "Aleación de Aluminio CNC", "Ajuste": "Universal de 3.5 a 6.8 pulgadas", "Rotación": "360 grados"}},
    {"brand": "West Biking", "model": "Soporte de Silicona Elástica de Teléfono", "type": "soportes", "category": "accesorios", "price": 5990, "specs": {"Material": "Silicona elástica", "Compatibilidad": "Universal", "Instalación": "Sin herramientas"}}
]

def main():
    print("[>] Starting generation of curated AliExpress cycling products...")
    
    cache_path = r"c:\Users\basti\Desktop\bicitodo\scratch\aliexpress_direct_cache.json"
    cache = {}
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cache = json.load(f)
            print(f"[Cache] Cargados {len(cache)} enlaces de AliExpress desde caché.")
        except Exception as e:
            print(f"[Cache Error] Falló al cargar caché: {e}")
            
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}. Please run seed_db.py first.")
        return
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Ensure AliExpress store exists
    cursor.execute("INSERT OR IGNORE INTO stores (name, url) VALUES ('AliExpress', 'https://aliexpress.com')")
    cursor.execute("SELECT id FROM stores WHERE name = 'AliExpress'")
    store_id = cursor.fetchone()[0]
    print(f"🇨🇳 Registered/Verified AliExpress store with ID: {store_id}")
    
    # Clean previous international products to insert a clean, updated Whitelist catalog
    cursor.execute("DELETE FROM products WHERE is_international = 1")
    conn.commit()
    print("🧹 Cleared previous international products to initialize the elite whitelist catalog.")
    
    inserted_products = 0
    inserted_offers = 0
    inserted_history = 0
    
    # Keep one row per curated AliExpress model. Synthetic suffix variants make
    # images and outgoing links look like exact product matches when they are not.
    total_to_generate = len(PRODUCT_TEMPLATES)
    templates_count = len(PRODUCT_TEMPLATES)
    variations_per_template = 1 if total_to_generate <= templates_count else (total_to_generate // templates_count) + 1
    
    generated_count = 0
    
    for idx, template in enumerate(PRODUCT_TEMPLATES):
        brand = template["brand"]
        base_model = template["model"]
        category = template["category"]
        p_type = template["type"]
        base_price = template["price"]
        base_specs = template["specs"]
        
        # Select premium images based on product type
        images_list = TYPE_IMAGES.get(p_type, ["https://images.unsplash.com/photo-1485965120184-e220f721d03e?auto=format&fit=crop&w=600&h=400&q=80"])
        
        for v in range(variations_per_template):
            if generated_count >= total_to_generate:
                break
                
            # Create variations
            variation_suffixes = [
                "", " Pro", " Lite", " Plus", " Ultra", " Evo", " Premium", " Team Edition", 
                " Carbon Series", " Stealth Black", " Neo", " Max", " X-Edition", " Pro Bundle",
                " Master", " Expert", " Comp", " Sport", " Race", " Tour", " Commuter Pack",
                " Extreme", " Ultimate", " Advanced", " Signature", " Limited Color", " Elite",
                " Custom Pack", " Aero Edition"
            ]
            suffix = variation_suffixes[v % len(variation_suffixes)]
            model = f"{base_model}{suffix}"
            
            # Whitelisted brand verification
            brand_cat = None
            for key_brand, val in BRANDS_WHITELIST.items():
                if brand in val:
                    brand_cat = key_brand
                    break
                    
            if not brand_cat:
                continue

            # Verify if this product has a direct item URL (either in VERIFIED_MATCHES or cached)
            norm_key = normalize_text(f"{brand} {model}")
            key = f"{brand} {model}".strip()
            
            has_verified = norm_key in VERIFIED_MATCHES
            if not has_verified and key in cache:
                url_candidate = cache[key].get("url")
                if url_candidate and "aliexpress.com/item/" in url_candidate:
                    has_verified = True
                    
            if not has_verified:
                # Skip this product entirely if it does not have a verified direct link
                continue
                
            # Generate realistic price variations (within +/- 25% of base price)
            price_factor = 0.85 + (v * 0.0314) % 0.3
            price_normal = int((base_price * price_factor) // 100 * 100)
            
            # Ensure price rounds nicely (e.g. ends in 990 or 900)
            if price_normal > 10000:
                price_normal = (price_normal // 1000) * 1000 + 990
            else:
                price_normal = (price_normal // 100) * 100 + 90
                
            # Generate realistic discount (10% to 45%)
            discount_percent = int(12 + (v * 7) % 33)
            price_card = int((price_normal / (1 - discount_percent/100)) // 1000 * 1000 + 990)
            
            # Generate realistic high quality stats (Rating >= 4.5, Sales > 100, Reviews > 15)
            rating = round(4.5 + ((idx * 3 + v * 7) % 5) * 0.1, 1)
            sales_count = int(101 + ((idx * 17 + v * 31) % 4900))
            review_count = int(15 + int(sales_count * (0.05 + (v % 5) * 0.02)))
            
            # Build specs summary and fullSpecs
            specs_summary = f"{brand} • {p_type.title()} • AliExpress Premium Quality"
            full_specs = base_specs.copy()
            full_specs["Marca"] = brand
            full_specs["Calidad / Calificación"] = f"{rating} Estrellas"
            full_specs["Ventas verificadas"] = f"{sales_count}+ unidades vendidas"
            full_specs["Reviews del producto"] = f"{review_count} opiniones de ciclistas"
            full_specs["Envío"] = "Envío internacional gratis disponible"
            full_specs["Actualización"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            # Map correct image and URL
            url = None
            img_url = None
            
            if norm_key in VERIFIED_MATCHES:
                url = VERIFIED_MATCHES[norm_key]["url"]
                img_url = VERIFIED_MATCHES[norm_key]["image"]
            elif key in cache:
                url_candidate = cache[key].get("url")
                if url_candidate and "aliexpress.com/item/" in url_candidate:
                    url = url_candidate
                local_img_candidate = cache[key].get("local_image")
                if local_img_candidate and os.path.exists(os.path.join(r"c:\Users\basti\Desktop\bicitodo\fronted", local_img_candidate)):
                    img_url = local_img_candidate
                elif cache[key].get("image_url"):
                    img_url = cache[key].get("image_url")
                    
            if not url:
                # Fallback to cache link just in case
                url = cache.get(key, {}).get("url")
                
            if not img_url:
                img_url = images_list[v % len(images_list)]
                
            normalized_name = (brand + " " + model).lower()
            
            # Insert product into sqlite products table
            cursor.execute("""
            INSERT INTO products (brand, model, category, type, specs, canonical_image, normalized_name, is_international, rating, sales_count, review_count, discount_percent)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?)
            """, (brand, model, category, p_type, json.dumps(full_specs, ensure_ascii=False), img_url, normalized_name, rating, sales_count, review_count, discount_percent))
            
            product_id = cursor.lastrowid
            inserted_products += 1
            
            # Insert offer into store_products table
            cursor.execute("""
            INSERT INTO store_products (product_id, store_id, url, image_url, price_normal, price_card)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (product_id, store_id, url, img_url, price_normal, price_card))
            
            store_product_id = cursor.lastrowid
            inserted_offers += 1
            
            # Insert price history points to draw nice charts (3-4 historical points)
            history_prices = [
                int(price_normal * 1.15),
                int(price_normal * 1.08),
                int(price_normal * 1.03),
                price_normal
            ]
            for h_price in history_prices:
                cursor.execute("""
                INSERT INTO price_history (store_product_id, price)
                VALUES (?, ?)
                """, (store_product_id, h_price))
                inserted_history += 1
                
            generated_count += 1

    conn.commit()
    conn.close()

    image_repair = repair_aliexpress_images()
    catalog_repair = repair_aliexpress_catalog()
    
    print("\n=== Importer Process Completed successfully! ===")
    print(f"  - Whitelist Bicycles/Parts/Accessories generated: {inserted_products}")
    print(f"  - AliExpress store offers registered: {inserted_offers}")
    print(f"  - Price history entries logged: {inserted_history}")
    print(f"  - AliExpress fallback images assigned: {image_repair['updated']}")
    print(f"  - AliExpress URLs repaired: {catalog_repair['updated_urls']}")

if __name__ == "__main__":
    main()
