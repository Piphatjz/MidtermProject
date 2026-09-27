# -*- coding: utf-8 -*-
"""
settings.py
ค่าคงที่และพารามิเตอร์ทั้งหมดของเกม (Game Balance, Controls, Colors, Tiles)
"""

# ---------- หน้าจอ / กริด ----------
TILE = 48                     # ขนาดของ 1 ช่อง (พิกเซล)
COLS = 15                      # จำนวนคอลัมน์ในโลก (กว้างพอดีจอ 720px)
SCREEN_W = TILE * COLS         # 720
HUD_H = 90                     # พื้นที่แถบ HUD ด้านบน
SCREEN_H = 720 + HUD_H         # 810
FPS = 60

SURFACE_ROW = 3                 # แถวพื้นดิน (หญ้า) - เหนือแถวนี้คือท้องฟ้า/ลานหน้าบ้าน
WORLD_ROWS = 140                # ความลึกทั้งหมดของโลก (แถว)
WORLD_PIXEL_H = WORLD_ROWS * TILE

HOME_COL = 2                    # ตำแหน่งคอลัมน์ของบ้าน/ฐาน
SHOP_COL = 5                    # ตำแหน่งคอลัมน์ของร้านอัพเกรด

# ---------- สีพื้นฐาน ----------
COLOR_SKY_TOP = (110, 180, 245)
COLOR_SKY_BOTTOM = (195, 225, 250)
COLOR_GRASS = (76, 175, 80)
COLOR_DIRT = (145, 92, 54)
COLOR_DIRT_DARK = (115, 70, 38)
COLOR_ROCK = (110, 115, 125)
COLOR_ROCK_DARK = (65, 70, 78)
COLOR_EMPTY = (36, 26, 22)       # ช่องที่ขุดแล้ว (อุโมงค์)
COLOR_HOME = (190, 75, 65)
COLOR_HOME_ROOF = (145, 35, 30)
COLOR_SHOP = (65, 110, 185)
COLOR_SHOP_ROOF = (45, 80, 145)

COLOR_COIN = (245, 185, 30)
COLOR_GOLD = (255, 195, 20)
COLOR_DIAMOND = (100, 215, 255)

COLOR_VEHICLE = (245, 175, 25)
COLOR_VEHICLE_DARK = (180, 120, 15)

COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (15, 15, 20)
COLOR_UI_BG = (25, 25, 35, 220)
COLOR_UI_PANEL = (45, 48, 62)
COLOR_ENERGY_BAR = (255, 150, 40)
COLOR_ENERGY_BG = (65, 40, 20)
COLOR_CARGO_BAR = (100, 200, 85)
COLOR_CARGO_BG = (35, 50, 30)

# ---------- ทรัพยากร ----------
RES_NONE = 0
RES_COIN = 1
RES_GOLD = 2
RES_DIAMOND = 3

RESOURCE_VALUE = {
    RES_COIN: 1,
    RES_GOLD: 5,
    RES_DIAMOND: 20,
}
RESOURCE_NAME = {
    RES_COIN: "เหรียญแร่",
    RES_GOLD: "ทองคำ",
    RES_DIAMOND: "เพชรพลอย",
}

# ---------- ชนิดของช่อง (tile) ----------
T_SKY = 0
T_GRASS = 1
T_DIRT = 2
T_ROCK = 3
T_EMPTY = 4

# ความทนทานของบล็อก (ปรับสมดุลให้ขุดสนุก ไว และไม่หน่วง)
TILE_HARDNESS = {
    T_GRASS: 4.0,   # ขุดประมาณ 0.4 วินาทีที่ Power เริ่มต้น
    T_DIRT: 4.5,    # ขุดประมาณ 0.45 วินาทีที่ Power เริ่มต้น
    T_ROCK: 18.0,   # หินแข็ง ต้องใช้แรงขุดมากขึ้น
}
ROCK_MIN_DRILL_LEVEL = 2   # ต้องอัพเกรดหัวขุดถึงระดับนี้ถึงจะเจาะหินได้

# ---------- รถขุด (ค่าเริ่มต้น และการอัพเกรด) ----------
BASE_SPEED = 160.0             # พิกเซล/วินาที (บังคับคล่องตัวขึ้น)
BASE_CAPACITY = 10             # จำนวนช่องเก็บทรัพยากรสูงสุด
BASE_ENERGY = 120.0            # พลังงานสูงสุดเริ่มต้น
BASE_POWER = 10.0              # ความแรงเจาะ/วินาที (ขุดบล็อกละ ~0.4s)
BASE_ENERGY_DRAIN_MOVE = 1.2   # พลังงานที่ใช้ต่อวินาทีตอนเคลื่อนที่
BASE_ENERGY_DRAIN_DIG = 3.5    # พลังงานที่ใช้ต่อวินาทีตอนเจาะ

UPGRADES = {
    "capacity": {
        "name": "ถังเก็บของ",
        "base_cost": 25,
        "cost_growth": 1.6,
        "step": 5,          # เพิ่มความจุ +5 ต่อระดับ
        "max_level": 8,
    },
    "energy": {
        "name": "ถังพลังงาน",
        "base_cost": 30,
        "cost_growth": 1.6,
        "step": 30,         # เพิ่มพลังงานสูงสุด +30 ต่อระดับ
        "max_level": 8,
    },
    "power": {
        "name": "หัวขุด",
        "base_cost": 40,
        "cost_growth": 1.75,
        "step": 3.0,        # เพิ่มแรงเจาะ +3.0/วินาที ต่อระดับ (เจาะไวขึ้นเรื่อย ๆ)
        "max_level": 8,
    },
    "speed": {
        "name": "มอเตอร์",
        "base_cost": 35,
        "cost_growth": 1.7,
        "step": 20.0,       # เพิ่มความเร็ว +20 px/s ต่อระดับ
        "max_level": 8,
    },
}

# ---------- เงื่อนไขจบเกม ----------
VICTORY_COIN_TARGET = 1500     # เก็บมูลค่ารวม (เหรียญ) ครบเท่านี้ = ชนะ
END_ON_ENERGY_EMPTY = True     # พลังงานหมดกลางทาง (ไม่อยู่บ้าน) = จบเกม
END_ON_TARGET_RESOURCE = True  # เก็บทรัพยากรครบเป้าหมาย = จบเกม (ชนะ)

SAVE_FILE = "savegame.json"
