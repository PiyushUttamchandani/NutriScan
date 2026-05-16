import os
import django
import numpy as np
from PIL import Image, ImageDraw
import io
import random

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NutriScan.settings')
django.setup()

from core.models import TrainingImage
from django.core.files.base import ContentFile

FOOD_PROFILES = {
    'Salad':      {'color': (50, 180, 50),   'noise': 40, 'tex': 'leafy'},
    'Pizza':      {'color': (220, 150, 50),  'noise': 30, 'tex': 'bumpy'},
    'Burger':     {'color': (130, 90, 60),   'noise': 20, 'tex': 'smooth'},
    'Roti Sabji': {'color': (160, 130, 80),  'noise': 25, 'tex': 'grainy'},
    'Dal Chawal': {'color': (200, 180, 100), 'noise': 15, 'tex': 'smooth'},
    'Apple':      {'color': (200, 30, 30),   'noise': 10, 'tex': 'shiny'},
}

def generate_synthetic_food_image(profile):
    img = Image.new('RGB', (128, 128), color=profile['color'])
    draw = ImageDraw.Draw(img)
    
    for _ in range(2000):
        x, y = random.randint(0, 127), random.randint(0, 127)
        c = tuple([max(0, min(255, val + random.randint(-profile['noise'], profile['noise']))) for val in profile['color']])
        draw.point((x, y), fill=c)
        
    if profile['tex'] == 'leafy':
        for _ in range(10):
            x0, y0 = random.randint(0, 60), random.randint(0, 60)
            x1, y1 = random.randint(x0+10, 120), random.randint(y0+10, 120)
            draw.ellipse([x0, y0, x1, y1], outline=(0, 100, 0))
            
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()

def seed():
    print("Generating 120 synthetic training images in database...")
    TrainingImage.objects.all().delete()
    for label, profile in FOOD_PROFILES.items():
        for i in range(20):
            img_data = generate_synthetic_food_image(profile)
            ti = TrainingImage(label=label)
            ti.image.save(f"{label}_{i}.png", ContentFile(img_data), save=True)
    print("Database seeding complete!")

if __name__ == "__main__":
    seed()
