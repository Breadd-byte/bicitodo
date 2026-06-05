import os
import base64

def create_gradient_placeholder(output_path):
    """Generates a stylish dark gradient placeholder with text as PNG and WebP if Pillow is available."""
    try:
        from PIL import Image, ImageDraw
        # Create a dark gradient image (600x400)
        width, height = 600, 400
        base = Image.new("RGB", (width, height), "#111827") # Dark gray/slate
        draw = ImageDraw.Draw(base)
        
        # Draw a subtle border
        draw.rectangle([0, 0, width-1, height-1], outline="#374151", width=2)
        
        # Draw placeholder bicycle-like icon (a simple double circle connection)
        # Left wheel
        draw.ellipse([150, 160, 230, 240], outline="#ec4899", width=4)
        # Right wheel
        draw.ellipse([370, 160, 450, 240], outline="#ec4899", width=4)
        # Frame lines
        draw.line([190, 200, 290, 120], fill="#8b5cf6", width=4) # chainstay to seat joint
        draw.line([290, 120, 410, 200], fill="#8b5cf6", width=4) # seat joint to front wheel
        draw.line([190, 200, 330, 200], fill="#8b5cf6", width=4) # chainstay
        draw.line([330, 200, 290, 120], fill="#8b5cf6", width=4) # seat tube
        draw.line([290, 120, 270, 90], fill="#8b5cf6", width=4)  # seatpost
        draw.line([250, 90, 290, 90], fill="#8b5cf6", width=4)   # saddle
        draw.line([410, 200, 390, 120], fill="#8b5cf6", width=4) # fork/headtube
        draw.line([370, 120, 410, 120], fill="#8b5cf6", width=4) # handlebars

        # Add text
        try:
            draw.text((width//2, 280), "BiciTodo", fill="#ffffff", anchor="mm")
            draw.text((width//2, 310), "Imagen no disponible", fill="#9ca3af", anchor="mm")
        except Exception:
            pass
            
        # Save as PNG
        png_path = output_path.replace(".webp", ".png")
        base.save(png_path, "PNG")
        print(f"[OK] Generated high-quality Pillow placeholder (PNG) at {png_path}")
        
        # Save as WEBP
        webp_path = output_path.replace(".png", ".webp")
        base.save(webp_path, "WEBP")
        print(f"[OK] Generated high-quality Pillow placeholder (WEBP) at {webp_path}")
        
        return True
    except Exception as e:
        print(f"[WARN] Pillow generation failed: {e}. Writing minimal base64 fallback.")
        return write_fallback_placeholders(output_path)

def write_fallback_placeholders(output_path):
    # Minimal 1x1 base64 values
    png_b64 = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8"
        "AAAAASUVORK5CYII="
    )
    # 1x1 transparent WebP base64
    webp_b64 = (
        "UklGRkoAAABXRUJQVlA4WAoAAAAQAAAAAAAAAAAAQUxQSAwAAAARBxAR/Q9ERP8DAABWUDggGAAA"
        "ADQBAJ0BKgEAAQAAQDcyJAwAA3AAPgAA"
    )
    try:
        png_path = output_path.replace(".webp", ".png")
        webp_path = output_path.replace(".png", ".webp")
        
        with open(png_path, "wb") as f:
            f.write(base64.b64decode(png_b64))
        with open(webp_path, "wb") as f:
            f.write(base64.b64decode(webp_b64))
            
        print(f"[OK] Generated minimal fallback placeholders at {png_path} and {webp_path}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to write fallback placeholders: {e}")
        return False

if __name__ == "__main__":
    target_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "images")
    os.makedirs(target_dir, exist_ok=True)
    target_path = os.path.join(target_dir, "placeholder-bike.webp")
    create_gradient_placeholder(target_path)
