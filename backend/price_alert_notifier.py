import json
import os
import sys
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Paths
BASE_DIR = r"c:\Users\basti\Desktop\bicitodo"
FRONTED_DIR = os.path.join(BASE_DIR, "fronted")
DATA_PATH = os.path.join(FRONTED_DIR, "data.json")
SCRATCH_DIR = os.path.join(BASE_DIR, "scratch")
EMAIL_PREVIEW_PATH = os.path.join(SCRATCH_DIR, "email_alert_preview.html")
FIREBASE_KEY_PATH = os.path.join(BASE_DIR, "backend", "firebase-key.json")

os.makedirs(SCRATCH_DIR, exist_ok=True)

# SMTP Config (Change with your credentials when ready, completely free SMTP)
SMTP_CONFIG = {
    "server": "smtp.gmail.com",
    "port": 587,
    "email": "tu-alerta@bicitodo.cl",
    "password": "tu-contraseña-aplicacion-gmail"
}

def format_clp(val):
    return f"${val:,.0f}".replace(",", ".")

def generate_email_html(user_name, product_title, brand, old_price, new_price, product_url, image_url):
    discount = int((1 - new_price / old_price) * 100) if old_price else 0
    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>¡Alerta de Descuento en BiciTodo!</title>
        <style>
            body {{
                font-family: 'Poppins', 'Helvetica Neue', Helvetica, Arial, sans-serif;
                background-color: #020617;
                color: #f8fafc;
                margin: 0;
                padding: 0;
            }}
            .email-container {{
                max-width: 600px;
                margin: 2rem auto;
                background: linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(30, 41, 59, 0.95) 100%);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 16px;
                overflow: hidden;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.6);
            }}
            .header {{
                background-color: rgba(15, 23, 42, 0.6);
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
                padding: 1.5rem 2rem;
                text-align: center;
            }}
            .logo-text {{
                font-size: 1.5rem;
                font-weight: 800;
                color: #22c55e;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            .logo-text span {{
                color: #fff;
            }}
            .content {{
                padding: 2.5rem 2rem;
                text-align: center;
            }}
            .greeting {{
                font-size: 1.25rem;
                font-weight: 700;
                margin-bottom: 0.5rem;
                color: #fff;
            }}
            .product-box {{
                background: rgba(0, 0, 0, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.04);
                border-radius: 12px;
                padding: 1.5rem;
                margin: 1.5rem 0;
                display: flex;
                flex-direction: column;
                align-items: center;
            }}
            .product-image-container {{
                width: 160px;
                height: 120px;
                background: #ffffff;
                border-radius: 8px;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 0.5rem;
                margin-bottom: 1rem;
            }}
            .product-image {{
                max-width: 100%;
                max-height: 100%;
                object-fit: contain;
            }}
            .brand-badge {{
                font-size: 0.65rem;
                font-weight: 800;
                color: #22c55e;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 0.25rem;
            }}
            .product-title {{
                font-size: 1.1rem;
                font-weight: 700;
                color: #fff;
                margin-bottom: 1rem;
                line-height: 1.3;
            }}
            .pricing-row {{
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 1.2rem;
                margin-bottom: 0.5rem;
            }}
            .old-price {{
                font-size: 0.95rem;
                color: #64748b;
                text-decoration: line-through;
            }}
            .new-price {{
                font-size: 1.6rem;
                font-weight: 900;
                color: #22c55e;
            }}
            .discount-badge {{
                background: #ef4444;
                color: #fff;
                font-size: 0.75rem;
                font-weight: 800;
                padding: 0.15rem 0.5rem;
                border-radius: 4px;
            }}
            .btn-buy {{
                display: inline-block;
                background-color: #22c55e;
                color: #020617;
                text-decoration: none;
                font-weight: 800;
                font-size: 0.9rem;
                padding: 0.8rem 2rem;
                border-radius: 99px;
                box-shadow: 0 4px 15px rgba(34, 197, 94, 0.35);
                margin-top: 1rem;
                transition: transform 0.2s ease;
            }}
            .footer {{
                background-color: rgba(15, 23, 42, 0.6);
                border-top: 1px solid rgba(255, 255, 255, 0.05);
                padding: 1.5rem 2rem;
                text-align: center;
                font-size: 0.72rem;
                color: #64748b;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <div class="logo-text">Bici<span>Todo</span></div>
            </div>
            <div class="content">
                <div class="greeting">¡Hola, {user_name}!</div>
                <p style="color: #94a3b8; font-size: 0.9rem; margin-top: 0;">Un producto que agregaste a tus favoritos de BiciTodo acaba de bajar de precio.</p>
                
                <div class="product-box">
                    <div class="product-image-container">
                        <img class="product-image" src="{image_url}" alt="{product_title}">
                    </div>
                    <div class="brand-badge">{brand}</div>
                    <div class="product-title">{product_title}</div>
                    
                    <div class="pricing-row">
                        <span class="old-price">{format_clp(old_price)}</span>
                        <span class="new-price">{format_clp(new_price)}</span>
                        <span class="discount-badge">-{discount}% OFF</span>
                    </div>
                </div>
                
                <a class="btn-buy" href="{product_url}" target="_blank">¡Ver Oferta y Comprar Ahora!</a>
            </div>
            <div class="footer">
                <p>BiciTodo Chile — El comparador de ciclismo más completo de Chile.</p>
                <p style="margin-top: 0.35rem;">Si no deseas recibir más alertas de precios, puedes eliminarlas en tu perfil de BiciTodo.</p>
            </div>
        </div>
    </body>
    </html>
    """

def send_alert_email(to_email, user_name, product_title, brand, old_price, new_price, product_url, image_url):
    # Setup SMTP client
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"¡Alerta de Caída de Precio! {brand} {product_title} a {format_clp(new_price)}"
    msg['From'] = SMTP_CONFIG["email"]
    msg['To'] = to_email
    
    html = generate_email_html(user_name, product_title, brand, old_price, new_price, product_url, image_url)
    msg.attach(MIMEText(html, 'html'))
    
    try:
        server = smtplib.SMTP(SMTP_CONFIG["server"], SMTP_CONFIG["port"])
        server.starttls()
        server.login(SMTP_CONFIG["email"], SMTP_CONFIG["password"])
        server.sendmail(SMTP_CONFIG["email"], to_email, msg.as_string())
        server.quit()
        print(f"[OK] Email alert successfully sent to {to_email}")
        return True
    except Exception as e:
        print(f"[WARNING] Failed to send SMTP email to {to_email}: {e}")
        return False

def main():
    print("=" * 60)
    print("[Price Alert Notifier] STARTING PRICE ANALYSIS & EMAIL DISPATCHER")
    print("=" * 60)

    # 1. Load active data.json
    if not os.path.exists(DATA_PATH):
        print(f"Error: data.json not found at {DATA_PATH}")
        return
        
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        database = json.load(f)
        
    all_products = []
    for cat in ["bicicletas", "accesorios", "repuestos"]:
        all_products.extend(database.get(cat, []))
        
    print(f"Loaded {len(all_products)} total products from active database.")
    
    # 2. Check Firebase Admin SDK setup
    firebase_ready = False
    alerts = []
    
    if os.path.exists(FIREBASE_KEY_PATH):
        try:
            import firebase_admin
            from firebase_admin import credentials
            from firebase_admin import firestore
            
            cred = credentials.Certificate(FIREBASE_KEY_PATH)
            firebase_admin.initialize_app(cred)
            db = firestore.client()
            firebase_ready = True
            print("[OK] Connected to Firebase Admin SDK successfully!")
            
            # Fetch alerts from Cloud Firestore
            users_ref = db.collection('bicitodo_users')
            docs = users_ref.stream()
            for doc in docs:
                user_data = doc.to_dict()
                email = user_data.get("email")
                name = user_data.get("displayName") or email.split("@")[0]
                favs = user_data.get("favorites", [])
                for f in favs:
                    if f.get("alertPrice"):
                        alerts.append({
                            "email": email,
                            "name": name,
                            "productId": f.get("id"),
                            "alertPrice": f.get("alertPrice")
                        })
            print(f"Fetched {len(alerts)} price alerts from live Cloud Firestore database.")
        except Exception as e:
            print(f"Firebase Admin SDK initialization skipped or failed: {e}")
    
    if not firebase_ready:
        print("\n[Notification Mode: Mock/Dry-Run Mode]")
        print("To fetch cloud alerts from Firestore, download a Service Account JSON key from Firebase Console,")
        print(f"name it 'firebase-key.json', and place it in the 'backend/' directory.")
        print(f"Generating a beautiful mock email preview at '{EMAIL_PREVIEW_PATH}' so you can review it.")
        
        # Find a product that has a real discount in its history to make a gorgeous realistic preview
        demo_product = None
        for p in all_products:
            history = p.get("history", [])
            offers = sorted(p["offers"], key=lambda o: o["price"])
            if not offers: continue
            current_price = offers[0]["price"]
            old_price = history[-2] if len(history) >= 2 else (current_price * 1.15)
            if current_price < old_price:
                demo_product = p
                break
                
        # Fallback to the first product if none has a discount
        if not demo_product and all_products:
            demo_product = all_products[0]
            
        demo_id = demo_product["id"] if demo_product else 2047
        demo_alert_price = int(demo_product["offers"][0]["price"] * 1.1) if demo_product else 250000
        
        alerts = [
            {
                "email": "test-bicitodo@bastian.com",
                "name": "Bastián Medina",
                "productId": demo_id,
                "alertPrice": demo_alert_price
            }
        ]
        
    # 3. Analyze products for price drops
    notified_count = 0
    
    for alert in alerts:
        p_id = alert["productId"]
        alert_price = alert["alertPrice"]
        
        # Find product in database
        product = next((p for p in all_products if p["id"] == p_id), None)
        if not product:
            continue
            
        # Get active lowest price
        offers = sorted(product["offers"], key=lambda o: o["price"])
        best_offer = offers[0]
        current_price = best_offer["price"]
        
        # Price drop conditions:
        # A: Current price is lower than or equal to user's targeted alertPrice
        # B: Current price is lower than previous price in history
        history = product.get("history", [])
        old_price = history[-2] if len(history) >= 2 else (current_price * 1.15)
        
        is_drop = current_price <= alert_price or current_price < old_price
        
        if is_drop:
            print(f"\n[Price Drop Detected] ID={p_id} | '{product['brand']} {product['model']}'")
            print(f"  Alert Price Target: {format_clp(alert_price)}")
            print(f"  Old/Prev Price:     {format_clp(old_price)}")
            print(f"  New Active Price:   {format_clp(current_price)} at {best_offer['store']}")
            
            image_url = product["image"]
            if image_url.startswith("assets/"):
                # Make relative asset path absolute for email visual integrity
                image_url = "https://raw.githubusercontent.com/bmedina/bicitodo/main/fronted/" + image_url
            
            if firebase_ready:
                send_alert_email(
                    to_email=alert["email"],
                    user_name=alert["name"],
                    product_title=product["model"],
                    brand=product["brand"],
                    old_price=int(old_price),
                    new_price=int(current_price),
                    product_url=best_offer["url"],
                    image_url=image_url
                )
            else:
                # Mock write local preview
                html = generate_email_html(
                    user_name=alert["name"],
                    product_title=product["model"],
                    brand=product["brand"],
                    old_price=int(old_price),
                    new_price=int(current_price),
                    product_url=best_offer["url"],
                    image_url=image_url
                )
                with open(EMAIL_PREVIEW_PATH, "w", encoding="utf-8") as f_out:
                    f_out.write(html)
                print(f"[OK] Mock email html template exported to {EMAIL_PREVIEW_PATH}")
                print("Open the HTML file in any browser to inspect the visual style of BiciTodo alerts!")
                
            notified_count += 1

    print("\n" + "=" * 60)
    print(f"[OK] Price alert analyzer completed! Total notifications triggered: {notified_count}")
    print("=" * 60)

if __name__ == "__main__":
    main()
