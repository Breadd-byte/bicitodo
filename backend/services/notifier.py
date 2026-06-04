import os
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

def enviar_alerta_precio(email_usuario, nombre_producto, precio_antiguo, precio_nuevo, url_producto):
    """
    Función para enviar un correo de alerta de precio utilizando la API gratuita de Brevo.
    """
    # 1. Configurar la clave API de Brevo desde variables de entorno o fallback
    api_key = os.environ.get('BREVO_API_KEY', 'TU_CLAVE_API_DE_BREVO_AQUÍ')
    
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = api_key

    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

    # 2. Diseñar el contenido del correo en formato HTML responsivo (Glassmorphic/Limpio)
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Arial', sans-serif; background-color: #0f172a; color: #f8fafc; padding: 20px; }}
            .card {{ background: rgba(30, 41, 59, 0.7); border-radius: 16px; padding: 30px; max-width: 500px; margin: 0 auto; border: 1px solid rgba(255, 255, 255, 0.1); text-align: center; }}
            h1 {{ color: #22c55e; font-size: 24px; margin-bottom: 10px; }}
            p {{ color: #94a3b8; font-size: 16px; line-height: 1.5; }}
            .product-name {{ color: #ffffff; font-weight: bold; font-size: 18px; margin: 15px 0; }}
            .prices {{ margin: 20px 0; font-size: 18px; }}
            .old-price {{ text-decoration: line-through; color: #ef4444; margin-right: 15px; }}
            .new-price {{ color: #22c55e; font-weight: bold; font-size: 22px; }}
            .btn {{ display: inline-block; background-color: #2563eb; color: #ffffff !important; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: bold; margin-top: 15px; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>⚡ ¡Baja de Precios en BiciTodo! ⚡</h1>
            <p>Buenas noticias, el producto que estabas siguiendo en nuestro comparador acaba de caer de precio de forma importante:</p>
            
            <div class="product-name">{nombre_producto}</div>
            
            <div class="prices">
                <span class="old-price">Antes: ${precio_antiguo:,}</span>
                <span class="new-price">Ahora: ${precio_nuevo:,}</span>
            </div>
            
            <p>Aprovecha esta oportunidad antes de que se agote el stock en la tienda correspondiente.</p>
            
            <a href="{url_producto}" class="btn" target="_blank">Ver Oferta en BiciTodo</a>
        </div>
    </body>
    </html>
    """

    # 3. Estructurar el objeto del correo de envío
    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        to=[{"email": email_usuario}],
        sender={"name": "BiciTodo Chile", "email": "alertas@bicitodo.cl"},
        subject=f"⚡ ¡Aviso de oferta! Bajó de precio: {nombre_producto}",
        html_content=html_content
    )

    # 4. Enviar a través de la API
    try:
        api_response = api_instance.send_transac_email(send_smtp_email) # NOTA: en sib_api_v3_sdk la función correcta es send_transac_email (no send_transitional_smtp_email)
        print(f"Correo enviado con éxito a {email_usuario}. ID: {api_response.message_id}")
        return True
    except ApiException as e:
        print(f"Error al enviar el correo mediante Brevo: {e}")
        return False
