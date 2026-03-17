#!/usr/bin/env python3
"""Generate simple Simpsons-style pixel art scenes using Pillow,
then save as images that chafa can convert to ASCII."""

import os
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "screenshots")
os.makedirs(OUT_DIR, exist_ok=True)

# Simpsons palette
YELLOW = (255, 217, 15)       # Simpsons skin
DARK_YELLOW = (230, 190, 10)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (45, 100, 245)         # Marge hair / sky
SKY_BLUE = (135, 206, 235)
BROWN = (139, 90, 43)
GREEN = (76, 153, 0)
RED = (220, 50, 50)
ORANGE = (255, 165, 0)
PINK = (255, 182, 193)
GRAY = (169, 169, 169)
DARK_GRAY = (80, 80, 80)
LIGHT_BLUE = (100, 149, 237)
COUCH_BROWN = (139, 69, 19)
FLOOR = (180, 140, 100)
WALL = (200, 180, 160)
TV_GRAY = (120, 120, 120)


def scene_homer_doh(w=320, h=240):
    """Homer saying D'oh! - simple pixel art."""
    img = Image.new("RGB", (w, h), SKY_BLUE)
    draw = ImageDraw.Draw(img)

    # Background - living room wall
    draw.rectangle([0, h//2, w, h], fill=FLOOR)
    draw.rectangle([0, 0, w, h//2 + 20], fill=WALL)

    # Homer's body (sitting on couch)
    cx, cy = w//2, h//2 + 30

    # Couch
    draw.rectangle([cx-90, cy-10, cx+90, cy+50], fill=COUCH_BROWN)
    draw.rectangle([cx-95, cy-30, cx-70, cy+50], fill=COUCH_BROWN)  # armrest

    # Body (white shirt)
    draw.ellipse([cx-35, cy-30, cx+25, cy+40], fill=WHITE)

    # Head (big round yellow)
    hx, hy = cx-5, cy-65
    draw.ellipse([hx-35, hy-30, hx+35, hy+35], fill=YELLOW)

    # Eyes
    draw.ellipse([hx-15, hy-15, hx+5, hy+5], fill=WHITE)
    draw.ellipse([hx+5, hy-15, hx+25, hy+5], fill=WHITE)
    draw.ellipse([hx-8, hy-10, hx+0, hy+0], fill=BLACK)
    draw.ellipse([hx+12, hy-10, hx+20, hy+0], fill=BLACK)

    # Mouth (open - D'oh!)
    draw.ellipse([hx-10, hy+8, hx+20, hy+28], fill=BROWN)
    draw.ellipse([hx-6, hy+10, hx+16, hy+24], fill=RED)

    # Hair strands (zigzag on top)
    for i in range(3):
        x = hx - 10 + i * 12
        draw.line([(x, hy-28), (x+6, hy-38), (x+12, hy-28)], fill=YELLOW, width=3)

    # 5 o'clock shadow
    draw.arc([hx-20, hy+5, hx+5, hy+30], 90, 270, fill=DARK_YELLOW, width=2)

    return img


def scene_bart_eat_shorts(w=320, h=240):
    """Bart on skateboard - pixel art."""
    img = Image.new("RGB", (w, h), SKY_BLUE)
    draw = ImageDraw.Draw(img)

    # Ground
    draw.rectangle([0, h - 50, w, h], fill=GRAY)
    draw.line([(0, h-50), (w, h-50)], fill=DARK_GRAY, width=2)

    # Bart position
    bx, by = w//2, h - 90

    # Skateboard
    draw.ellipse([bx-30, by+35, bx+30, by+45], fill=RED)
    draw.rectangle([bx-25, by+33, bx+25, by+40], fill=RED)
    # Wheels
    draw.ellipse([bx-22, by+40, bx-14, by+48], fill=BLACK)
    draw.ellipse([bx+14, by+40, bx+22, by+48], fill=BLACK)

    # Body (red shirt)
    draw.rectangle([bx-12, by-5, bx+12, by+25], fill=RED)

    # Shorts (blue)
    draw.rectangle([bx-14, by+20, bx+14, by+35], fill=BLUE)

    # Legs
    draw.rectangle([bx-10, by+32, bx-4, by+38], fill=YELLOW)
    draw.rectangle([bx+4, by+32, bx+10, by+38], fill=YELLOW)

    # Head
    hx, hy = bx, by - 30
    draw.ellipse([hx-18, hy-20, hx+18, hy+18], fill=YELLOW)

    # Spiky hair
    spikes = [(-18, -20), (-10, -35), (-2, -20), (4, -38), (10, -20), (16, -32), (20, -18)]
    for i in range(len(spikes)-1):
        x1, y1 = spikes[i]
        x2, y2 = spikes[i+1]
        draw.polygon([(hx+x1, hy+y1), (hx+(x1+x2)//2, hy+min(y1,y2)-5), (hx+x2, hy+y2)], fill=YELLOW)

    # Eyes
    draw.ellipse([hx-10, hy-8, hx+0, hy+4], fill=WHITE)
    draw.ellipse([hx+2, hy-8, hx+12, hy+4], fill=WHITE)
    draw.ellipse([hx-6, hy-4, hx-2, hy+2], fill=BLACK)
    draw.ellipse([hx+6, hy-4, hx+10, hy+2], fill=BLACK)

    # Grin
    draw.arc([hx-8, hy+2, hx+10, hy+14], 0, 180, fill=BLACK, width=2)

    # Arm extended
    draw.line([(bx+12, by+5), (bx+35, by-10)], fill=YELLOW, width=5)

    return img


def scene_moe_tavern(w=320, h=240):
    """Moe's Tavern bar scene."""
    img = Image.new("RGB", (w, h), (60, 40, 30))
    draw = ImageDraw.Draw(img)

    # Bar counter
    draw.rectangle([0, h//2, w, h//2+15], fill=(100, 60, 30))
    draw.rectangle([0, h//2+15, w, h], fill=(70, 40, 20))

    # Shelves with bottles in background
    for shelf_y in [30, 80]:
        draw.rectangle([20, shelf_y, w-20, shelf_y+5], fill=(80, 50, 30))
        # Bottles
        colors = [GREEN, RED, (180, 120, 60), BLUE, ORANGE, (160, 32, 240), GREEN, RED]
        for i, c in enumerate(colors):
            bx = 35 + i * 35
            draw.rectangle([bx, shelf_y-30, bx+12, shelf_y], fill=c)
            draw.rectangle([bx+2, shelf_y-35, bx+10, shelf_y-30], fill=c)

    # Beer mug on counter
    mx = w//2 - 40
    my = h//2 - 25
    draw.rectangle([mx, my, mx+25, my+25], fill=(200, 180, 50))
    draw.rectangle([mx-2, my+2, mx, my+20], fill=(200, 180, 50))  # handle area
    draw.ellipse([mx-8, my+5, mx, my+18], fill=(200, 180, 50))  # handle
    # Foam
    draw.ellipse([mx-2, my-5, mx+27, my+5], fill=WHITE)

    # Homer at bar (simplified)
    hx = w//2 + 30
    hy = h//2 - 20
    # Body
    draw.ellipse([hx-20, hy-10, hx+20, hy+15], fill=WHITE)
    # Head
    draw.ellipse([hx-18, hy-45, hx+18, hy-5], fill=YELLOW)
    # Eyes
    draw.ellipse([hx-8, hy-32, hx+2, hy-20], fill=WHITE)
    draw.ellipse([hx+4, hy-32, hx+14, hy-20], fill=WHITE)
    draw.ellipse([hx-4, hy-28, hx, hy-22], fill=BLACK)
    draw.ellipse([hx+8, hy-28, hx+12, hy-22], fill=BLACK)
    # Mouth
    draw.arc([hx-5, hy-18, hx+10, hy-8], 0, 180, fill=BLACK, width=2)

    # Duff beer sign
    draw.rectangle([w-80, 20, w-15, 55], fill=RED)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
        draw.text((w-72, 25), "DUFF", fill=WHITE, font=font)
    except Exception:
        draw.text((w-70, 28), "DUFF", fill=WHITE)

    return img


# Generate all scenes
scenes = [
    ("homer_doh", scene_homer_doh),
    ("bart_skateboard", scene_bart_eat_shorts),
    ("moes_tavern", scene_moe_tavern),
]

for name, func in scenes:
    img = func()
    path = os.path.join(OUT_DIR, f"{name}.png")
    img.save(path)
    print(f"Saved {path}")
