# ======================================
# CONFIGURATION (EDIT THESE)
# ======================================

INPUT_FOLDER = "assets/8x8"
OUTPUT_FOLDER = "assets/16x16-randomized-effect"

# Resize settings
TARGET_SIZE = 16     # output size (width = height)

# Random ranges for each effect
HUE_SHIFT_RANGE = (-0.5, 0.5)
BRIGHTNESS_RANGE = (0.9, 1.2)
CONTRAST_RANGE = (0.9, 1.2)
SATURATION_RANGE = (0.9, 1.3)

# ======================================
# SCRIPT START (DO NOT EDIT BELOW)
# ======================================

import os
import random
from PIL import Image, ImageEnhance
import colorsys

def shift_hue(img, hue_shift):
    img = img.convert("RGBA")
    px = img.load()

    for y in range(img.size[1]):
        for x in range(img.size[0]):
            r, g, b, a = px[x, y]
            if a == 0:
                continue

            h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
            h = (h + hue_shift) % 1.0
            r, g, b = colorsys.hsv_to_rgb(h, s, v)
            px[x, y] = (int(r*255), int(g*255), int(b*255), a)

    return img

def random_edit(img):
    hue = random.uniform(*HUE_SHIFT_RANGE)
    bri = random.uniform(*BRIGHTNESS_RANGE)
    con = random.uniform(*CONTRAST_RANGE)
    sat = random.uniform(*SATURATION_RANGE)

    # hue
    if hue != 0:
        img = shift_hue(img, hue)

    # brightness
    img = ImageEnhance.Brightness(img).enhance(bri)
    # contrast
    img = ImageEnhance.Contrast(img).enhance(con)
    # saturation
    img = ImageEnhance.Color(img).enhance(sat)

    return img

# Ensure output directory
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

for file in os.listdir(INPUT_FOLDER):
    if file.lower().endswith(".png"):
        inp = os.path.join(INPUT_FOLDER, file)
        out = os.path.join(OUTPUT_FOLDER, file)

        print(f"Processing: {file}")
        img = Image.open(inp)

        # Apply random color edits
        img = random_edit(img)

        # Resize (same size for all)
        img = img.resize((TARGET_SIZE, TARGET_SIZE), Image.NEAREST)

        img.save(out)

print("Done! All sprites processed and resized.")
