#!/usr/bin/env python3
"""
Script pour créer des images placeholder Art Déco pour développement
"""
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("PIL/Pillow requis: pip install Pillow")
    exit(1)

import os
from pathlib import Path

# Palette Art Déco
COLORS = {
    'gold': '#D4AF37',
    'bronze': '#CD7F32', 
    'burgundy': '#800020',
    'cream': '#F5F5DC',
    'charcoal': '#36454F',
    'silver': '#C0C0C0'
}

def hex_to_rgb(hex_color):
    """Convertit hex en RGB"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def create_cocktail_placeholder(name, color, size=(800, 600)):
    """Crée une image placeholder pour cocktail"""
    img = Image.new('RGB', size, hex_to_rgb(COLORS['charcoal']))
    draw = ImageDraw.Draw(img)
    
    # Fond dégradé simulé
    for i in range(size[1]):
        shade = int(54 + (i / size[1]) * 40)  # 54 à 94
        color_fade = (shade, shade, shade + 10)
        draw.line([(0, i), (size[0], i)], fill=color_fade)
    
    # Cadre Art Déco
    border_color = hex_to_rgb(COLORS['gold'])
    draw.rectangle([20, 20, size[0]-20, size[1]-20], outline=border_color, width=5)
    draw.rectangle([30, 30, size[0]-30, size[1]-30], outline=border_color, width=2)
    
    # Verre stylisé au centre
    glass_center = (size[0]//2, size[1]//2)
    glass_color = hex_to_rgb(color)
    
    # Corps du verre
    draw.ellipse([glass_center[0]-60, glass_center[1]-40, 
                  glass_center[0]+60, glass_center[1]+80], 
                 outline=glass_color, width=4)
    
    # Liquide dans le verre
    liquid_color = tuple(int(c * 0.7) for c in glass_color)
    draw.ellipse([glass_center[0]-50, glass_center[1]-20, 
                  glass_center[0]+50, glass_center[1]+60], 
                 fill=liquid_color)
    
    # Texte du nom
    try:
        font = ImageFont.truetype("Arial.ttf", 36)
    except:
        font = ImageFont.load_default()
    
    text_color = hex_to_rgb(COLORS['cream'])
    bbox = draw.textbbox((0, 0), name, font=font)
    text_width = bbox[2] - bbox[0]
    text_x = (size[0] - text_width) // 2
    text_y = size[1] - 80
    
    draw.text((text_x, text_y), name, fill=text_color, font=font)
    
    # Ornements Art Déco dans les coins
    ornament_color = hex_to_rgb(COLORS['bronze'])
    # Coin supérieur gauche
    draw.polygon([(40, 40), (80, 40), (40, 80)], fill=ornament_color)
    # Coin supérieur droit
    draw.polygon([(size[0]-40, 40), (size[0]-80, 40), (size[0]-40, 80)], fill=ornament_color)
    
    return img

def create_thumbnail(name, color, size=(150, 150)):
    """Crée une miniature Art Déco"""
    img = Image.new('RGBA', size, (0, 0, 0, 0))  # Transparent
    draw = ImageDraw.Draw(img)
    
    # Cercle de fond
    bg_color = hex_to_rgb(COLORS['charcoal']) + (230,)
    draw.ellipse([10, 10, size[0]-10, size[1]-10], fill=bg_color)
    
    # Bordure dorée
    border_color = hex_to_rgb(COLORS['gold'])
    draw.ellipse([5, 5, size[0]-5, size[1]-5], outline=border_color, width=3)
    
    # Verre central
    center = (size[0]//2, size[1]//2)
    glass_color = hex_to_rgb(color)
    
    # Verre simplifié
    draw.ellipse([center[0]-25, center[1]-15, center[0]+25, center[1]+25], 
                 fill=glass_color)
    draw.ellipse([center[0]-20, center[1]-10, center[0]+20, center[1]+20], 
                 fill=tuple(int(c * 0.8) for c in glass_color))
    
    return img

def create_default_images():
    """Crée toutes les images par défaut"""
    base_dir = Path("/Users/alexandreseillier/cocktail.bzh/assets/images")
    
    cocktails = [
        ("gin_tonic", COLORS['silver']),
        ("old_fashioned", COLORS['bronze']),
        ("sidecar", COLORS['gold']),
        ("vodka_cranberry", COLORS['burgundy']),
        ("tequila_sunrise", '#FF8C00'),  # Orange
        ("rum_cola", '#8B4513'),  # Saddle brown
    ]
    
    for cocktail_id, color in cocktails:
        # Image principale
        main_img = create_cocktail_placeholder(
            cocktail_id.replace('_', ' ').title(), color
        )
        main_path = base_dir / "cocktails" / f"{cocktail_id}_main.jpg"
        main_img.save(main_path, "JPEG", quality=90)
        
        # Miniature
        thumb_img = create_thumbnail(cocktail_id.replace('_', ' ').title(), color)
        thumb_path = base_dir / "cocktails" / "thumbnails" / f"{cocktail_id}_thumb.png"
        thumb_img.save(thumb_path, "PNG")
        
        print(f"✅ Créé: {cocktail_id}")
    
    # Image par défaut
    default_img = create_cocktail_placeholder("Cocktail", COLORS['gold'])
    default_path = base_dir / "default_cocktail.png"
    default_img.save(default_path, "PNG")
    
    print(f"✅ Images placeholder créées dans {base_dir}")

if __name__ == "__main__":
    create_default_images()