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
    img_dia.save(os.path.join(IMG_DIR, "res_diamond.png"))


def generate_vehicle_sprites():
    # Mining Vehicle Base Chassis (42x42)
    size = 42
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Caterpillar treads (top & bottom or sides)
    tread_col = (50, 52, 58, 255)
    tread_rim = (30, 32, 36, 255)
    # Left tread
    d.rounded_rectangle([2, 4, 10, size - 4], radius=3, fill=tread_col, outline=tread_rim, width=1)
    for ty in range(8, size - 6, 6):
        d.line([(3, ty), (9, ty)], fill=(80, 84, 92, 255), width=1)

    # Right tread
    d.rounded_rectangle([size - 10, 4, size - 2, size - 4], radius=3, fill=tread_col, outline=tread_rim, width=1)
    for ty in range(8, size - 6, 6):
        d.line([(size - 9, ty), (size - 3, ty)], fill=(80, 84, 92, 255), width=1)

    # Main cabin / chassis (Vibrant Industrial Yellow / Amber)
    body_col = (245, 175, 25, 255)
    body_shadow = (195, 130, 15, 255)
    d.rounded_rectangle([8, 6, size - 8, size - 6], radius=5, fill=body_col, outline=(140, 90, 10, 255), width=2)
    d.rounded_rectangle([10, size - 14, size - 10, size - 8], radius=2, fill=body_shadow)

    # Hazard stripes on back
    d.line([(12, size - 10), (16, size - 14)], fill=(40, 40, 40, 255), width=2)
    d.line([(20, size - 10), (24, size - 14)], fill=(40, 40, 40, 255), width=2)
    d.line([(28, size - 10), (32, size - 14)], fill=(40, 40, 40, 255), width=2)

    # Cockpit dome with glass reflection
    glass_col = (70, 170, 240, 255)
    d.rounded_rectangle([12, 10, size - 12, 22], radius=4, fill=glass_col, outline=(30, 80, 130, 255), width=1)
    d.line([(15, 13), (25, 13)], fill=(220, 245, 255, 220), width=2)

    img.save(os.path.join(IMG_DIR, "vehicle_body.png"))

    # Drill Bits (cone with rotating spiral grooves) for 4 directions
    for angle, name in [(0, "drill_down"), (90, "drill_right"), (180, "drill_up"), (270, "drill_left")]:
        d_img = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
        dd = ImageDraw.Draw(d_img)
        # Pointing down base template
        drill_pts = [(5, 2), (19, 2), (12, 21)]
        dd.polygon(drill_pts, fill=(185, 195, 205, 255), outline=(90, 100, 110, 255), width=1)
        # Spiral grooves
        dd.line([(7, 5), (17, 8)], fill=(120, 130, 140, 255), width=2)
        dd.line([(8, 10), (16, 14)], fill=(120, 130, 140, 255), width=2)
        dd.line([(10, 15), (14, 18)], fill=(120, 130, 140, 255), width=2)
        dd.point((12, 21), fill=(255, 255, 255, 255))

        rot = d_img.rotate(angle, resample=Image.BICUBIC)
        rot.save(os.path.join(IMG_DIR, f"{name}.png"))


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



def build_all_assets():
    print("Generating game textures and sprites...")
    generate_dirt_texture()
    generate_grass_texture()
    generate_rock_texture()
    generate_tunnel_bg()
    generate_cracks()
    generate_resources()
    generate_vehicle_sprites()
    generate_buildings()
    print("Textures generated.")

    print("Synthesizing audio sound effects...")
    generate_sound_effects()
    print("Audio synthesized.")
    print("All assets successfully created in:", ASSETS_DIR)


if __name__ == "__main__":
    build_all_assets()
