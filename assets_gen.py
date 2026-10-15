# -*- coding: utf-8 -*-
"""
assets_gen.py
สร้างกราฟิก (PNG) และเสียงเอฟเฟกต์ (WAV) คุณภาพสูงสำหรับเกม Dig & Treasure
ทำงานอัตโนมัติ ไม่ต้องดาวน์โหลดไฟล์ภายนอก
"""
import os
import math
import struct
import wave
import random
from PIL import Image, ImageDraw, ImageFilter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
IMG_DIR = os.path.join(ASSETS_DIR, "images")
SND_DIR = os.path.join(ASSETS_DIR, "sounds")

os.makedirs(IMG_DIR, exist_ok=True)
os.makedirs(SND_DIR, exist_ok=True)

TILE = 48


# ==============================================================================
# 1. GENERATE SPRITES & TEXTURES
# ==============================================================================

def generate_dirt_texture():
    img = Image.new("RGBA", (TILE, TILE), (145, 92, 54, 255))
    draw = ImageDraw.Draw(img)
    rng = random.Random(42)

    # Shading specks and soil layers
    for _ in range(120):
        x = rng.randint(0, TILE - 1)
        y = rng.randint(0, TILE - 1)
        c_var = rng.randint(-25, 25)
        color = (
            max(0, min(255, 145 + c_var)),
            max(0, min(255, 92 + c_var // 2)),
            max(0, min(255, 54 + c_var // 3)),
            255
        )
        r = rng.randint(1, 3)
        draw.ellipse([x - r, y - r, x + r, y + r], fill=color)

    # Small embedded pebbles
    for _ in range(6):
        px = rng.randint(4, TILE - 5)
        py = rng.randint(4, TILE - 5)
        pr = rng.randint(2, 3)
        draw.ellipse([px - pr, py - pr, px + pr, py + pr], fill=(110, 80, 65, 255))
        draw.point((px - 1, py - 1), fill=(160, 130, 110, 255))

    # Subtle beveled border for grid depth
    draw.line([(0, 0), (TILE - 1, 0)], fill=(175, 120, 75, 180), width=1)
    draw.line([(0, 0), (0, TILE - 1)], fill=(175, 120, 75, 180), width=1)
    draw.line([(0, TILE - 1), (TILE - 1, TILE - 1)], fill=(90, 55, 30, 200), width=1)
    draw.line([(TILE - 1, 0), (TILE - 1, TILE - 1)], fill=(90, 55, 30, 200), width=1)

    img.save(os.path.join(IMG_DIR, "dirt.png"))


def generate_grass_texture():
    # Base is dirt with rich grassy top
    img = Image.open(os.path.join(IMG_DIR, "dirt.png")).copy()
    draw = ImageDraw.Draw(img)
    rng = random.Random(101)

    # Lush green top band
    grass_h = 12
    draw.rectangle([0, 0, TILE, grass_h], fill=(76, 175, 80, 255))
    draw.line([(0, 0), (TILE, 0)], fill=(129, 199, 132, 255), width=2)

    # Grass blades hanging down into the dirt
    for x in range(0, TILE, 3):
        h = rng.randint(11, 16)
        c = (rng.randint(60, 90), rng.randint(150, 190), rng.randint(60, 90), 255)
        draw.polygon([(x, 0), (x + 3, 0), (x + 1, h)], fill=c)

    img.save(os.path.join(IMG_DIR, "grass.png"))


def generate_rock_texture():
    img = Image.new("RGBA", (TILE, TILE), (110, 115, 125, 255))
    draw = ImageDraw.Draw(img)
    rng = random.Random(777)

    # Stone grain & facets
    for _ in range(160):
        x = rng.randint(0, TILE - 1)
        y = rng.randint(0, TILE - 1)
        v = rng.randint(-30, 30)
        draw.point((x, y), fill=(max(0, min(255, 110 + v)),
                                 max(0, min(255, 115 + v)),
                                 max(0, min(255, 125 + v)), 255))

    # Chiseled rock cracks & edge facets
    lines = [
        [(8, 6), (22, 18), (38, 14)],
        [(22, 18), (18, 36), (32, 42)],
        [(4, 28), (18, 36)],
        [(38, 14), (44, 30), (32, 42)]
    ]
    for pts in lines:
        draw.line(pts, fill=(55, 60, 68, 220), width=2)
        # Highlight along crack
        hl_pts = [(p[0] + 1, p[1] + 1) for p in pts]
        draw.line(hl_pts, fill=(160, 165, 175, 180), width=1)

    # Border bevel
    draw.line([(0, 0), (TILE - 1, 0)], fill=(165, 170, 180, 200), width=2)
    draw.line([(0, 0), (0, TILE - 1)], fill=(165, 170, 180, 200), width=2)
    draw.line([(0, TILE - 1), (TILE - 1, TILE - 1)], fill=(50, 52, 60, 240), width=2)
    draw.line([(TILE - 1, 0), (TILE - 1, TILE - 1)], fill=(50, 52, 60, 240), width=2)

    img.save(os.path.join(IMG_DIR, "rock.png"))


def generate_tunnel_bg():
    # Dug out cave tunnel background (dark earth & carved rock)
    img = Image.new("RGBA", (TILE, TILE), (36, 26, 22, 255))
    draw = ImageDraw.Draw(img)
    rng = random.Random(88)

    # Cave texture
    for _ in range(80):
        x = rng.randint(0, TILE - 1)
        y = rng.randint(0, TILE - 1)
        v = rng.randint(-10, 10)
        draw.point((x, y), fill=(max(0, min(255, 36 + v)),
                                 max(0, min(255, 26 + v)),
                                 max(0, min(255, 22 + v)), 255))

    # Subtle ambient corner shadow
    for i in range(4):
        alpha = int(40 * (1 - i / 4))
        draw.rectangle([i, i, TILE - 1 - i, TILE - 1 - i], outline=(15, 10, 8, alpha))

    img.save(os.path.join(IMG_DIR, "tunnel.png"))


def generate_barrier_texture():
    """สร้างพื้นผิวประตูกั้นชั้นความลึก (Security Barrier) พร้อมแถบเตือนสะท้อนแสงและไฟสถานะล็อค"""
    img = Image.new("RGBA", (TILE, TILE), (34, 38, 50, 255))
    draw = ImageDraw.Draw(img)

    # Diagonal hazard caution stripes (bright amber/yellow & dark industrial gray)
    stripe_w = 9
    for offset in range(-TILE, TILE * 2, stripe_w * 2):
        pts = [
            (offset, 0),
            (offset + stripe_w, 0),
            (offset + stripe_w - TILE, TILE),
            (offset - TILE, TILE),
        ]
        draw.polygon(pts, fill=(235, 185, 25, 235))

    # Darker border & bevel
    draw.rectangle([0, 0, TILE - 1, TILE - 1], outline=(18, 22, 30, 255), width=2)
    draw.line([(1, 1), (TILE - 2, 1)], fill=(110, 130, 160, 230), width=1)
    draw.line([(1, 1), (1, TILE - 2)], fill=(110, 130, 160, 230), width=1)
    draw.line([(1, TILE - 2), (TILE - 2, TILE - 2)], fill=(15, 18, 24, 250), width=1)
    draw.line([(TILE - 2, 1), (TILE - 2, TILE - 2)], fill=(15, 18, 24, 250), width=1)

    # Steel rivets at 4 corners
    for rx, ry in [(5, 5), (TILE - 6, 5), (5, TILE - 6), (TILE - 6, TILE - 6)]:
        draw.ellipse([rx - 2, ry - 2, rx + 2, ry + 2], fill=(55, 62, 75, 255))
        draw.point((rx - 1, ry - 1), fill=(190, 210, 240, 255))

    # Center horizontal glowing security laser/lock beam
    cy = TILE // 2
    draw.line([(2, cy), (TILE - 3, cy)], fill=(255, 65, 45, 245), width=3)
    draw.line([(3, cy), (TILE - 4, cy)], fill=(255, 225, 140, 255), width=1)

    img.save(os.path.join(IMG_DIR, "barrier.png"))


def generate_cracks():
    # Crack progressive overlays at stages 1, 2, 3
    for stage in [1, 2, 3]:
        img = Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        lines = [
            [(TILE // 2, TILE // 2), (TILE // 2 - 8, TILE // 2 - 12), (10, 8)],
            [(TILE // 2, TILE // 2), (TILE // 2 + 10, TILE // 2 + 8), (TILE - 8, TILE - 10)]
        ]
        if stage >= 2:
            lines.extend([
                [(TILE // 2, TILE // 2), (TILE // 2 + 12, TILE // 2 - 10), (TILE - 6, 12)],
                [(TILE // 2, TILE // 2), (TILE // 2 - 10, TILE // 2 + 10), (12, TILE - 8)]
            ])
        if stage >= 3:
            lines.extend([
                [(TILE // 2 - 8, TILE // 2 - 12), (TILE // 2 - 16, TILE // 2 - 4)],
                [(TILE // 2 + 10, TILE // 2 + 8), (TILE // 2 + 18, TILE // 2 + 16)],
                [(10, 8), (4, 18)],
                [(TILE - 8, TILE - 10), (TILE - 4, TILE // 2)]
            ])

        for line in lines:
            draw.line(line, fill=(20, 15, 10, 230), width=2)
            draw.line([(p[0] + 1, p[1] + 1) for p in line], fill=(255, 255, 255, 70), width=1)

        img.save(os.path.join(IMG_DIR, f"crack_{stage}.png"))


def generate_resources():
    # 1. Coin / Copper Ore
    img_coin = Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img_coin)
    cx, cy = TILE // 2, TILE // 2
    r = 11
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(245, 185, 30, 255), outline=(180, 120, 10, 255), width=2)
    d.ellipse([cx - r + 3, cy - r + 3, cx + r - 3, cy + r - 3], outline=(255, 225, 110, 200), width=1)
    # Specular shine
    d.ellipse([cx - 5, cy - 6, cx - 1, cy - 2], fill=(255, 255, 240, 220))
    img_coin.save(os.path.join(IMG_DIR, "res_coin.png"))

    # 2. Gold Nugget
    img_gold = Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img_gold)
    nuggets = [
        ([(cx - 8, cy + 6), (cx - 2, cy - 8), (cx + 8, cy - 2), (cx + 10, cy + 8), (cx + 1, cy + 10)], (255, 195, 20, 255)),
        ([(cx - 10, cy + 2), (cx - 3, cy - 4), (cx + 2, cy + 4), (cx - 4, cy + 8)], (235, 165, 15, 255)),
        ([(cx + 2, cy - 8), (cx + 11, cy - 5), (cx + 7, cy + 1)], (255, 225, 60, 255))
    ]
    for pts, col in nuggets:
        d.polygon(pts, fill=col, outline=(160, 100, 10, 255))
    # Shiny glint
    d.line([(cx - 3, cy - 6), (cx + 1, cy - 4)], fill=(255, 255, 255, 240), width=2)
    img_gold.save(os.path.join(IMG_DIR, "res_gold.png"))

    # 3. Diamond / Gem
    img_dia = Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img_dia)
    top_w, mid_w, h_top, h_bot = 10, 14, 5, 11
    # Diamond facets
    p_top_l = (cx - top_w, cy - h_top)
    p_top_r = (cx + top_w, cy - h_top)
    p_mid_l = (cx - mid_w, cy)
    p_mid_r = (cx + mid_w, cy)
    p_bot = (cx, cy + h_bot)

    # Facet coloring
    d.polygon([p_top_l, p_top_r, p_mid_r, (cx, cy), p_mid_l], fill=(100, 215, 255, 255))
    d.polygon([p_top_l, (cx, cy - h_top), (cx, cy), p_mid_l], fill=(160, 240, 255, 255))
    d.polygon([p_top_r, (cx, cy - h_top), (cx, cy), p_mid_r], fill=(60, 185, 240, 255))
    d.polygon([p_mid_l, (cx, cy), p_bot], fill=(30, 150, 220, 255))
    d.polygon([p_mid_r, (cx, cy), p_bot], fill=(15, 120, 195, 255))
    d.polygon([p_top_l, p_top_r, p_mid_r, p_bot, p_mid_l], outline=(220, 250, 255, 255), width=1)
    # Bright shine star
    d.line([(cx - 4, cy - 3), (cx + 4, cy - 3)], fill=(255, 255, 255, 255), width=2)
    d.line([(cx, cy - 7), (cx, cy + 1)], fill=(255, 255, 255, 255), width=2)
    # 4. Fuel Canister (High-tech transparent Jerrycan / Battery cell)
    img_fuel = Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0))
    d_fuel = ImageDraw.Draw(img_fuel)
    # Canister metal body
    d_fuel.rounded_rectangle([10, 12, 38, 44], radius=5, fill=(235, 90, 30, 255), outline=(150, 45, 15, 255), width=2)
    # Metallic nozzle and cap
    d_fuel.rounded_rectangle([13, 6, 21, 13], radius=2, fill=(180, 185, 195, 255), outline=(100, 105, 115, 255), width=1)
    # Handle on top
    d_fuel.line([(24, 7), (35, 7)], fill=(160, 50, 20, 255), width=3)
    d_fuel.line([(24, 7), (24, 12)], fill=(160, 50, 20, 255), width=2)
    d_fuel.line([(35, 7), (35, 12)], fill=(160, 50, 20, 255), width=2)
    # Gauge window with glowing amber fuel
    d_fuel.rounded_rectangle([15, 19, 33, 38], radius=3, fill=(40, 25, 18, 255), outline=(160, 60, 20, 255), width=1)
    d_fuel.rounded_rectangle([17, 23, 31, 36], radius=2, fill=(255, 195, 45, 255))
    # Electric lightning decal on canister
    d_fuel.polygon([(24, 25), (20, 30), (24, 30), (23, 35), (28, 28), (24, 28)], fill=(255, 255, 220, 255))
    # Highlights
    d_fuel.line([(12, 16), (12, 40)], fill=(255, 155, 105, 200), width=1)
    img_fuel.save(os.path.join(IMG_DIR, "res_fuel.png"))


def generate_vehicle_sprites():
    import settings as S
    size = 42

    for c_id, c_data in S.VEHICLE_COLORS.items():
        p_col = (*c_data["primary"], 255)
        d_col = (*c_data["dark"], 255)
        h_col = (*c_data["highlight"], 255)
        t_col = (*c_data["tread"], 255)
        g_col = (*c_data["glass"], 255)
        t_rim = (30, 32, 36, 255)

        for vtype in S.VEHICLE_TYPES.keys():
            img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            d = ImageDraw.Draw(img)

            if vtype == "standard":
                # Dual caterpillar treads
                d.rounded_rectangle([2, 4, 10, size - 4], radius=3, fill=t_col, outline=t_rim, width=1)
                for ty in range(8, size - 6, 6):
                    d.line([(3, ty), (9, ty)], fill=h_col, width=1)

                d.rounded_rectangle([size - 10, 4, size - 2, size - 4], radius=3, fill=t_col, outline=t_rim, width=1)
                for ty in range(8, size - 6, 6):
                    d.line([(size - 9, ty), (size - 3, ty)], fill=h_col, width=1)

                # Cabin chassis
                d.rounded_rectangle([8, 6, size - 8, size - 6], radius=5, fill=p_col, outline=d_col, width=2)
                d.rounded_rectangle([10, size - 14, size - 10, size - 8], radius=2, fill=d_col)
                # Hazard stripes
                d.line([(12, size - 10), (16, size - 14)], fill=(40, 40, 40, 255), width=2)
                d.line([(20, size - 10), (24, size - 14)], fill=(40, 40, 40, 255), width=2)
                d.line([(28, size - 10), (32, size - 14)], fill=(40, 40, 40, 255), width=2)
                # Cockpit dome
                d.rounded_rectangle([12, 10, size - 12, 22], radius=4, fill=g_col, outline=(30, 80, 130, 255), width=1)
                d.line([(15, 13), (25, 13)], fill=(220, 245, 255, 220), width=2)

            elif vtype == "scout":
                # 4 Wide racing off-road wheels
                d.rounded_rectangle([1, 4, 9, 15], radius=2, fill=t_col, outline=t_rim, width=1)
                d.rounded_rectangle([size - 9, 4, size - 1, 15], radius=2, fill=t_col, outline=t_rim, width=1)
                d.rounded_rectangle([1, size - 15, 9, size - 4], radius=2, fill=t_col, outline=t_rim, width=1)
                d.rounded_rectangle([size - 9, size - 15, size - 1, size - 4], radius=2, fill=t_col, outline=t_rim, width=1)
                # Aerodynamic wedge frame
                d.polygon([(size // 2, 4), (size - 9, 16), (size - 9, size - 8), (9, size - 8), (9, 16)], fill=p_col, outline=d_col)
                # Fighter canopy
                d.polygon([(size // 2, 8), (size - 13, 20), (13, 20)], fill=g_col, outline=(20, 60, 110, 255))
                d.line([(size // 2, 10), (size // 2 - 4, 18)], fill=(255, 255, 255, 220), width=1)
                # Dual rocket thrusters
                d.rectangle([12, size - 7, 17, size - 2], fill=(255, 120, 30, 255), outline=(180, 60, 10, 255))
                d.rectangle([size - 17, size - 7, size - 12, size - 2], fill=(255, 120, 30, 255), outline=(180, 60, 10, 255))

            elif vtype == "titan":
                # Heavy Quad-treads
                d.rounded_rectangle([1, 2, 10, 18], radius=2, fill=t_col, outline=t_rim, width=1)
                d.rounded_rectangle([size - 10, 2, size - 1, 18], radius=2, fill=t_col, outline=t_rim, width=1)
                d.rounded_rectangle([1, size - 18, 10, size - 2], radius=2, fill=t_col, outline=t_rim, width=1)
                d.rounded_rectangle([size - 10, size - 18, size - 1, size - 2], radius=2, fill=t_col, outline=t_rim, width=1)
                # Massive reinforced hull
                d.rounded_rectangle([7, 4, size - 7, size - 4], radius=4, fill=p_col, outline=d_col, width=2)
                # Armor visor cockpit
                d.rounded_rectangle([11, 7, size - 11, 19], radius=2, fill=(40, 45, 55, 255), outline=(20, 22, 28, 255))
                d.rectangle([14, 11, size - 14, 15], fill=g_col)
                # Heavy Cargo Bed / Hopper
                d.rounded_rectangle([9, 21, size - 9, size - 6], radius=2, fill=d_col, outline=(30, 32, 40, 255))
                d.line([(11, 25), (size - 11, 25)], fill=h_col, width=1)
                d.line([(11, 30), (size - 11, 30)], fill=h_col, width=1)

            elif vtype == "hover":
                # Antigravity repulsor pods with glowing magnetic coils
                for px, py in [(6, 8), (size - 6, 8), (6, size - 8), (size - 6, size - 8)]:
                    d.ellipse([px - 5, py - 5, px + 5, py + 5], fill=(35, 42, 58, 255), outline=(60, 210, 255, 255), width=2)
                    d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=(140, 245, 255, 255))
                # Hover saucer disc chassis
                d.ellipse([6, 5, size - 6, size - 5], fill=p_col, outline=d_col, width=2)
                # Spherical bubble canopy
                d.ellipse([12, 10, size - 12, size - 12], fill=g_col, outline=(30, 80, 140, 255), width=1)
                d.line([(15, 14), (23, 14)], fill=(255, 255, 255, 220), width=2)
                # Rear energy fins
                d.line([(size // 2 - 8, size - 7), (size // 2 + 8, size - 7)], fill=(70, 220, 255, 255), width=2)

            filename = f"vehicle_{vtype}_{c_id}.png"
            img.save(os.path.join(IMG_DIR, filename))

            # Save fallback
            if vtype == "standard" and c_id == "yellow":
                img.save(os.path.join(IMG_DIR, "vehicle_body.png"))


def generate_drill_sprites():
    import settings as S
    angles = [(0, "down"), (90, "right"), (180, "up"), (270, "left")]

    for head_id in S.DRILL_HEADS.keys():
        d_img = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
        dd = ImageDraw.Draw(d_img)

        if head_id == "spiral":
            # Conical steel spiral drill
            drill_pts = [(5, 2), (19, 2), (12, 21)]
            dd.polygon(drill_pts, fill=(185, 195, 205, 255), outline=(90, 100, 110, 255), width=1)
            dd.line([(7, 5), (17, 8)], fill=(120, 130, 140, 255), width=2)
            dd.line([(8, 10), (16, 14)], fill=(120, 130, 140, 255), width=2)
            dd.line([(10, 15), (14, 18)], fill=(120, 130, 140, 255), width=2)
            dd.point((12, 21), fill=(255, 255, 255, 255))

        elif head_id == "diamond":
            # Faceted diamond tungsten cutter with sharp crystal teeth
            drill_pts = [(4, 2), (20, 2), (18, 10), (12, 22), (6, 10)]
            dd.polygon(drill_pts, fill=(90, 210, 245, 255), outline=(30, 110, 170, 255), width=1)
            dd.polygon([(8, 2), (16, 2), (12, 14)], fill=(185, 245, 255, 255))
            dd.line([(12, 2), (12, 22)], fill=(255, 255, 255, 255), width=1)
            dd.point((12, 22), fill=(255, 255, 255, 255))

        elif head_id == "plasma":
            # Dual plasma emitter prongs with superheated flame lance
            dd.rectangle([4, 2, 7, 12], fill=(65, 70, 80, 255), outline=(35, 40, 48, 255))
            dd.rectangle([17, 2, 20, 12], fill=(65, 70, 80, 255), outline=(35, 40, 48, 255))
            # Blazing plasma cone
            dd.polygon([(7, 5), (17, 5), (12, 22)], fill=(255, 95, 20, 255))
            dd.polygon([(9, 5), (15, 5), (12, 18)], fill=(255, 225, 50, 255))
            dd.line([(12, 6), (12, 21)], fill=(255, 255, 255, 255), width=1)

        elif head_id == "vortex":
            # Electromagnetic rotating induction coils
            dd.ellipse([5, 2, 19, 10], outline=(190, 85, 255, 255), width=2)
            dd.ellipse([7, 8, 17, 16], outline=(150, 50, 235, 255), width=2)
            dd.polygon([(10, 14), (14, 14), (12, 22)], fill=(235, 170, 255, 255))
            dd.point((12, 22), fill=(255, 255, 255, 255))

        elif head_id == "seismic":
            # Heavy pneumatic jackhammer with bronze chisel head
            dd.rectangle([6, 2, 18, 7], fill=(85, 90, 100, 255), outline=(45, 50, 58, 255))
            dd.rectangle([9, 7, 15, 14], fill=(195, 140, 65, 255), outline=(130, 85, 30, 255))
            dd.polygon([(7, 14), (17, 14), (12, 22)], fill=(235, 185, 95, 255), outline=(120, 80, 25, 255))
            dd.line([(10, 10), (14, 10)], fill=(45, 50, 58, 255), width=1)

        for angle, dir_name in angles:
            rot = d_img.rotate(angle, resample=Image.BICUBIC)
            rot.save(os.path.join(IMG_DIR, f"drill_{head_id}_{dir_name}.png"))
            if head_id == "spiral":
                rot.save(os.path.join(IMG_DIR, f"drill_{dir_name}.png"))


def generate_buildings():
    # 1. Base Depot / Home (2 tiles wide = 96, 2 tiles high = 96)
    w, h = 96, 96
    img_home = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img_home)

    # Building Body
    wall_col = (190, 75, 65, 255)
    d.rectangle([10, 32, w - 10, h - 4], fill=wall_col, outline=(110, 40, 35, 255), width=2)

    # Roof (Industrial corrugated angle)
    roof_pts = [(4, 32), (w // 2, 8), (w - 4, 32)]
    d.polygon(roof_pts, fill=(145, 35, 30, 255), outline=(85, 20, 18, 255), width=2)
    # Roof ridges
    for rx in range(16, w - 16, 10):
        t = (rx - 4) / (w - 8)
        ry = 32 - math.sin(t * math.pi) * 20
        d.line([(rx, 32), (rx, int(ry))], fill=(175, 55, 50, 255), width=2)

    # Garage Door / Depot entry
    d.rectangle([20, 46, w - 20, h - 4], fill=(70, 75, 85, 255), outline=(45, 48, 55, 255), width=2)
    for sy in range(52, h - 4, 7):
        d.line([(22, sy), (w - 22, sy)], fill=(100, 105, 115, 255), width=1)

    # Neon Sign: "DEPOT - SELL & REFUEL"
    d.rounded_rectangle([18, 18, w - 18, 30], radius=3, fill=(35, 40, 50, 240), outline=(255, 215, 50, 255), width=1)
    # Light indicator
    d.ellipse([22, 22, 26, 26], fill=(50, 255, 80, 255))
    d.ellipse([w - 26, 22, w - 22, 26], fill=(50, 255, 80, 255))

    img_home.save(os.path.join(IMG_DIR, "building_home.png"))

    # 2. Upgrade Shop (1 tile wide = 48, 2 tiles high = 96)
    sw, sh = 48, 96
    img_shop = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    d = ImageDraw.Draw(img_shop)

    # Shop wall (Cobalt / Steel)
    d.rectangle([4, 32, sw - 4, sh - 4], fill=(65, 110, 185, 255), outline=(35, 65, 120, 255), width=2)
    # Roof
    sroof_pts = [(2, 32), (sw // 2, 10), (sw - 2, 32)]
    d.polygon(sroof_pts, fill=(45, 80, 145, 255), outline=(25, 45, 85, 255), width=2)

    # Workshop window with warm glow
    d.rounded_rectangle([10, 42, sw - 10, 68], radius=3, fill=(255, 235, 130, 240), outline=(140, 110, 30, 255), width=2)
    d.line([(sw // 2, 42), (sw // 2, 68)], fill=(120, 95, 20, 255), width=1)
    d.line([(10, 55), (sw - 10, 55)], fill=(120, 95, 20, 255), width=1)

    # Big mechanical gear emblem on sign
    gcx, gcy = sw // 2, 22
    gr = 8
    d.ellipse([gcx - gr, gcy - gr, gcx + gr, gcy + gr], fill=(240, 200, 40, 255), outline=(160, 120, 20, 255), width=1)
    d.ellipse([gcx - 3, gcy - 3, gcx + 3, gcy + 3], fill=(45, 80, 145, 255))

    img_shop.save(os.path.join(IMG_DIR, "building_shop.png"))


# ==============================================================================
# 2. GENERATE CRISP 16-BIT RETRO SOUND EFFECTS (WAV)
# ==============================================================================

def write_wav(filename, samples, sample_rate=22050):
    filepath = os.path.join(SND_DIR, filename)
    with wave.open(filepath, "w") as wav_file:
        n_channels = 1
        sampwidth = 2
        wav_file.setparams((n_channels, sampwidth, sample_rate, len(samples), "NONE", "not compressed"))
        raw_data = bytearray()
        for s in samples:
            val = int(max(-32767, min(32767, s * 32767)))
            raw_data.extend(struct.pack("<h", val))
        wav_file.writeframes(raw_data)


def generate_sound_effects():
    sr = 22050

    # 1. drill.wav - Industrial grinding / rumble
    dur = 0.18
    n = int(sr * dur)
    samples = []
    rng = random.Random(12)
    for i in range(n):
        t = i / sr
        freq1 = 85 + 20 * math.sin(2 * math.pi * 30 * t)
        freq2 = 170 + 35 * math.sin(2 * math.pi * 45 * t)
        noise = (rng.random() * 2 - 1) * 0.25
        wave_val = (0.5 * math.sin(2 * math.pi * freq1 * t) +
                    0.3 * math.sin(2 * math.pi * freq2 * t) + noise)
        env = math.sin(math.pi * (i / n))
        samples.append(wave_val * env * 0.7)
    write_wav("drill.wav", samples, sr)

    # 2. dig_pop.wav - Crunchy earth break
    dur = 0.15
    n = int(sr * dur)
    samples = []
    for i in range(n):
        t = i / sr
        freq = 280 * math.exp(-t * 22)
        noise = (random.random() * 2 - 1) * 0.4 * math.exp(-t * 20)
        wave_val = math.sin(2 * math.pi * freq * t) * 0.6 + noise
        env = math.exp(-t * 20)
        samples.append(wave_val * env * 0.8)
    write_wav("dig_pop.wav", samples, sr)

    # 3. rock_clink.wav - Metallic / hard stone deflection
    dur = 0.20
    n = int(sr * dur)
    samples = []
    for i in range(n):
        t = i / sr
        f1, f2 = 880, 1320
        wave_val = 0.6 * math.sin(2 * math.pi * f1 * t) + 0.4 * math.sin(2 * math.pi * f2 * t)
        env = math.exp(-t * 25)
        samples.append(wave_val * env * 0.7)
    write_wav("rock_clink.wav", samples, sr)

    # 4. coin.wav - Bright retro coin chime (2-step arpeggio)
    dur = 0.22
    n = int(sr * dur)
    samples = []
    for i in range(n):
        t = i / sr
        f = 987.77 if t < 0.08 else 1318.51  # B5 -> E6
        wave_val = math.sin(2 * math.pi * f * t) + 0.3 * math.sin(2 * math.pi * f * 2 * t)
        env = math.exp(-t * 12)
        samples.append(wave_val * env * 0.65)
    write_wav("coin.wav", samples, sr)

    # 5. gem.wav - Sparkly crystal pickup chime (3-step high arpeggio)
    dur = 0.35
    n = int(sr * dur)
    samples = []
    for i in range(n):
        t = i / sr
        if t < 0.09:
            f = 1046.50  # C6
        elif t < 0.18:
            f = 1318.51  # E6
        else:
            f = 2093.00  # C7
        wave_val = math.sin(2 * math.pi * f * t) + 0.25 * math.sin(2 * math.pi * f * 3 * t)
        env = math.exp(-t * 8)
        samples.append(wave_val * env * 0.6)
    write_wav("gem.wav", samples, sr)

    # 6. sell.wav - Cash register jingle
    dur = 0.38
    n = int(sr * dur)
    samples = []
    for i in range(n):
        t = i / sr
        f = 1200 + (300 if (int(t * 40) % 2 == 0) else 0)
        wave_val = math.sin(2 * math.pi * f * t)
        env = math.exp(-t * 9)
        samples.append(wave_val * env * 0.65)
    write_wav("sell.wav", samples, sr)

    # 7. refuel.wav - Power surge swoop
    dur = 0.32
    n = int(sr * dur)
    samples = []
    for i in range(n):
        t = i / sr
        f = 220 + 700 * (t / dur) ** 2
        wave_val = math.sin(2 * math.pi * f * t) + 0.2 * math.sin(2 * math.pi * f * 2 * t)
        env = math.sin(math.pi * (t / dur))
        samples.append(wave_val * env * 0.55)
    write_wav("refuel.wav", samples, sr)

    # 8. upgrade.wav - Major fanfare arpeggio (C - E - G - C)
    dur = 0.45
    n = int(sr * dur)
    samples = []
    notes = [523.25, 659.25, 783.99, 1046.50]
    for i in range(n):
        t = i / sr
        idx = min(len(notes) - 1, int(t / (dur / len(notes))))
        f = notes[idx]
        wave_val = math.sin(2 * math.pi * f * t) + 0.35 * math.sin(2 * math.pi * f * 2 * t)
        local_t = t % (dur / len(notes))
        env = math.exp(-local_t * 8)
        samples.append(wave_val * env * 0.6)
    write_wav("upgrade.wav", samples, sr)

    # 9. low_energy.wav - Warning beep
    dur = 0.16
    n = int(sr * dur)
    samples = []
    for i in range(n):
        t = i / sr
        f = 750
        wave_val = 1.0 if math.sin(2 * math.pi * f * t) > 0 else -1.0  # Square wave
        env = math.exp(-t * 14)
        samples.append(wave_val * env * 0.4)
    write_wav("low_energy.wav", samples, sr)

    # 10. charge.wav - Rising electromagnetic induction whine
    dur = 0.22
    n = int(sr * dur)
    samples = []
    for i in range(n):
        t = i / sr
        f = 240 + 750 * (t / dur) ** 1.3
        wave_val = 0.65 * math.sin(2 * math.pi * f * t) + 0.35 * math.sin(2 * math.pi * f * 2 * t)
        env = math.sin(math.pi * (t / dur))
        samples.append(wave_val * env * 0.5)
    write_wav("charge.wav", samples, sr)

    # 11. boost.wav - Kinetic burst whoosh / rocket blast
    dur = 0.38
    n = int(sr * dur)
    samples = []
    b_rng = random.Random(999)
    for i in range(n):
        t = i / sr
        f = 520 * math.exp(-t * 7.5) + 75
        noise = (b_rng.random() * 2 - 1) * 0.45
        wave_val = 0.6 * math.sin(2 * math.pi * f * t) + noise
        env = math.exp(-t * 4.5)
        samples.append(wave_val * env * 0.7)
    write_wav("boost.wav", samples, sr)

    # 12. click.wav - Crisp UI button click
    dur = 0.06
    n = int(sr * dur)
    samples = []
    for i in range(n):
        t = i / sr
        f = 950 - 350 * (t / dur)
        wave_val = math.sin(2 * math.pi * f * t) + 0.3 * math.sin(2 * math.pi * f * 2 * t)
        env = math.exp(-t * 45)
        samples.append(wave_val * env * 0.45)
    write_wav("click.wav", samples, sr)




def build_all_assets():
    print("Generating game textures and sprites...")
    generate_dirt_texture()
    generate_grass_texture()
    generate_rock_texture()
    generate_tunnel_bg()
    generate_barrier_texture()
    generate_cracks()
    generate_resources()
    generate_vehicle_sprites()
    generate_drill_sprites()
    generate_buildings()
    print("Textures generated.")

    print("Synthesizing audio sound effects...")
    generate_sound_effects()
    print("Audio synthesized.")
    print("All assets successfully created in:", ASSETS_DIR)


if __name__ == "__main__":
    build_all_assets()
