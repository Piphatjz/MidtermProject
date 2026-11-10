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
WORLD_ROWS = 650                # ความลึกทั้งหมดของโลก (แถว) - ขยายมากพอจนแทบไม่มีจุดสิ้นสุด รองรับโหมดคลาสสิก
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
RES_FUEL = 4       # กระป๋องน้ำมัน – เก็บแล้วเติมพลังงานได้ทันที

RESOURCE_VALUE = {
    RES_COIN: 2,   # ปรับจาก 1 -> 2 ให้คุ้มค่าความจุช่องเก็บของมากขึ้น
    RES_GOLD: 5,
    RES_DIAMOND: 20,
    RES_FUEL: 0,   # ไม่มีมูลค่าเป็นเหรียญ แต่เติมพลังงาน
}
RESOURCE_NAME = {
    RES_COIN: "เหรียญแร่",
    RES_GOLD: "ทองคำ",
    RES_DIAMOND: "เพชรพลอย",
    RES_FUEL: "กระป๋องน้ำมัน",
}

FUEL_CANISTER_RESTORE = 40.0   # พลังงานที่ได้รับจากกระป๋องน้ำมัน 1 กระป๋อง
FUEL_CANISTER_CHANCE = 0.030   # โอกาสสุ่มพบกระป๋องน้ำมันในแต่ละบล็อก

# ---------- ชนิดของช่อง (tile) ----------
T_SKY = 0
T_GRASS = 1
T_DIRT = 2
T_ROCK = 3
T_EMPTY = 4
T_BARRIER = 5     # ประตูกั้นชั้นความลึก (โหมดคลาสสิก ปลดล็อคด้วยเหรียญ)

# ความทนทานของบล็อก (ปรับสมดุลให้ขุดสนุก ไว และไม่หน่วง)
TILE_HARDNESS = {
    T_GRASS: 4.0,   # ขุดประมาณ 0.4 วินาทีที่ Power เริ่มต้น
    T_DIRT: 4.5,    # ขุดประมาณ 0.45 วินาทีที่ Power เริ่มต้น
    T_ROCK: 18.0,   # หินแข็ง ต้องใช้แรงขุดมากขึ้น
    T_BARRIER: 999999.0, # ปลดล็อคด้วยเหรียญเท่านั้น
}
ROCK_MIN_DRILL_LEVEL = 2   # ต้องอัพเกรดหัวขุดถึงระดับนี้ถึงจะเจาะหินได้
ROCK_LAYER_DEPTH = 40       # ความลึกตั้งแต่ 40 ช่องลงไปเป็นชั้นหินล้วน (สำหรับโหมดภารกิจ)

# ---------- โหมดคลาสสิก: ชั้นความลึกและค่าปลดล็อค (Classic Endless Floors) ----------
MAX_CLASSIC_FLOORS = 7  # ชั้น 7 เป็นชั้นสุดท้ายที่ต้องปลดล็อค หลังจากนั้นขุดได้เรื่อยๆ โดยไม่มีประตูกั้นอีก

CLASSIC_FLOORS = [
    {
        "floor": 1,
        "name": "ผิวดิน & แร่อ่อน (Upper Crust)",
        "min_depth": 0,
        "max_depth": 20,
        "unlock_cost": 0,           # เริ่มต้นปลดล็อคทันที
        "desc": "ดินร่วนซุย เหรียญแร่และทองคำ เหมาะสำหรับสะสมทุนตั้งต้น",
        "theme_color": (95, 205, 120),
    },
    {
        "floor": 2,
        "name": "หินแกรนิต & สายแร่ทอง (Granite Depths)",
        "min_depth": 21,
        "max_depth": 45,
        "unlock_cost": 80,          # ปรับลดจาก 300 -> 80 เหรียญ (ปลดล็อคได้ชัวร์แม้หักค่าอัพเกรดแล้ว)
        "desc": "หินแกรนิตแข็งปานกลาง ทองคำหนาแน่น และเริ่มพบเพชรแท้",
        "theme_color": (245, 195, 50),
    },
    {
        "floor": 3,
        "name": "หุบเหวคริสตัล & อัญมณี (Crystal Caverns)",
        "min_depth": 46,
        "max_depth": 75,
        "unlock_cost": 220,         # ปรับลดจาก 800 -> 220 เหรียญ
        "desc": "ผลึกเพชรน้ำงาม แหล่งรวมอัญมณีล้ำค่าและถังน้ำมันโบราณ",
        "theme_color": (90, 215, 255),
    },
    {
        "floor": 4,
        "name": "ลาวาใต้พิภพ & เพชรบริสุทธิ์ (Magma Bedrock)",
        "min_depth": 76,
        "max_depth": 110,
        "unlock_cost": 500,         # ปรับลดจาก 1800 -> 500 เหรียญ
        "desc": "ชั้นหินหนาแน่น แหล่งเพชรและขุมทรัพย์มูลค่ามหาศาล",
        "theme_color": (255, 115, 55),
    },
    {
        "floor": 5,
        "name": "แกนพิภพลี้ลับ (Core Abyss)",
        "min_depth": 111,
        "max_depth": 150,
        "unlock_cost": 1000,        # ปรับลดจาก 3200 -> 1000 เหรียญ
        "desc": "แกนกลางโลก ทะเลทองคำและเพชรแท้ล้ำค่า",
        "theme_color": (195, 110, 255),
    },
    {
        "floor": 6,
        "name": "มิติใต้พิภพไร้สิ้นสุด (Infinite Depths)",
        "min_depth": 151,
        "max_depth": 200,
        "unlock_cost": 1800,        # ปรับลดจาก 5000 -> 1800 เหรียญ
        "desc": "ความลึกระดับตำนาน ขุมทรัพย์ไร้ขีดจำกัด",
        "theme_color": (255, 80, 140),
    },
    {
        "floor": 7,
        "name": "แกนลึกไร้ที่สิ้นสุด (The Endless Void)",
        "min_depth": 201,
        "max_depth": 999999,
        "unlock_cost": 2800,
        "desc": "ชั้นสุดท้าย! ปลดล็อคแล้วขุดได้เรื่อยๆ ไร้ขีดจำกัด ไม่มีประตูกั้นอีกต่อไป",
        "theme_color": (255, 215, 50),
    },
]


def get_floor_info(floor_num):
    """คืนค่าพารามิเตอร์ของชั้น floor_num (ชั้น 7 เป็นชั้นสุดท้าย หลังจากนั้นเป็นบล็อกต่อเนื่องไม่มีประตูกั้น)"""
    if 1 <= floor_num <= len(CLASSIC_FLOORS):
        return CLASSIC_FLOORS[floor_num - 1]
    return CLASSIC_FLOORS[-1]


# ---------- รถขุด (ค่าเริ่มต้น และการอัพเกรด) ----------
BASE_SPEED = 160.0             # พิกเซล/วินาที (บังคับคล่องตัวขึ้น)
BASE_CAPACITY = 10             # จำนวนช่องเก็บทรัพยากรสูงสุด
BASE_ENERGY = 120.0            # พลังงานสูงสุดเริ่มต้น
BASE_POWER = 10.0              # ความแรงเจาะ/วินาที (ขุดบล็อกละ ~0.4s)
BASE_ENERGY_DRAIN_MOVE = 1.2   # พลังงานที่ใช้ต่อวินาทีตอนเคลื่อนที่
BASE_ENERGY_DRAIN_DIG = 3.5    # พลังงานที่ใช้ต่อวินาทีตอนเจาะ

BASE_VEHICLE_SIZE = 40         # ขนาดรถขุดเริ่มต้น (พิกเซล) เมื่อทุก stat อยู่ที่ Lv.1 (Tier 1)
VEHICLE_SIZE_PER_TIER = 3.2    # ขนาดที่เพิ่มขึ้นต่อ 1 Tier (เมื่ออัพเกรดครบทุกอย่างถึง Lv.2, 3..8 สูงสุด ~62px)

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

# ---------- ระบบฟิสิกส์กฎแรงโน้มถ่วง (Gravitational Potential & Kinetic Energy) ----------
# กฎฟิสิกส์: พลังงานศักย์โน้มถ่วง (Ep = mgh) เมื่อเคลื่อนที่/บินขึ้นไปด้านบน จะสะสมพลังงานศักย์
# และเมื่อพุ่งลงมาด้านล่าง แรงโน้มถ่วงจะเปลี่ยนพลังงานศักย์เป็นพลังงานจลน์ (Ek = 1/2*m*v^2)
# ทำให้ความเร็วตอนพุ่งลงเร็วขึ้นอย่างมาก และพลังเจาะกระแทกพื้น (Ground Slam) รุนแรงขึ้นหลายเท่า
GRAV_CHARGE_MAX = 1.0           # พลังงานศักย์สูงสุด (1.0 = 100%)
GRAV_CHARGE_RATE = 0.95         # อัตราสะสมพลังงานศักย์เมื่อขึ้นสู่ด้านบนต่อวินาที (~1.0s ชาร์จเต็ม)
GRAV_SPEED_MULT = 2.60          # ตัวคูณความเร็วเมื่อพุ่งดิ่งลงด้านล่างตามแรงโน้มถ่วง (เร็วกว่าปกติ 2.6 เท่า)
GRAV_DRILL_MULT = 3.00          # ตัวคูณพลังเจาะกระแทกบล็อกด้านล่าง (ทะลวงบล็อกแรงขึ้น 3 เท่า)
GRAV_DECAY_RATE = 0.65          # อัตราการใช้พลังงานศักย์ขณะพุ่งดิ่งลงมา (ต่อวินาที)

# ---------- เงื่อนไขจบเกม ----------
STARTING_COINS = 10000             # เหรียญเริ่มต้นสำหรับเกมใหม่
VICTORY_COIN_TARGET = 1500     # เป้าหมายเหรียญเดิม (สำรอง)
END_ON_ENERGY_EMPTY = True     # พลังงานหมดกลางทาง (ไม่อยู่บ้าน) = จบเกม
END_ON_TARGET_RESOURCE = True  # สำเร็จภารกิจผสมครบทุกข้อ = จบเกม (ชนะ)

SAVE_FILE = "savegame.json"

# ==============================================================================
# ตัวเลือกรถขุด: สีตัวถัง, ประเภทรถขุด และประเภทหัวขุด (Garage Customization)
# ==============================================================================

# ---------- 1. สีตัวถัง (Vehicle Colors) ----------
DEFAULT_VEHICLE_COLOR = "yellow"

VEHICLE_COLORS = {
    "yellow": {
        "name": "เหลืองอำพัน",
        "name_en": "Industrial Amber",
        "primary": (245, 175, 25),
        "dark": (180, 120, 15),
        "highlight": (255, 220, 80),
        "tread": (50, 52, 58),
        "glass": (70, 170, 240),
        "unlock_cost": 0,
        "unlock_req": None,
        "unlock_desc": "ปลดล็อคเริ่มต้น",
    },
    "blue": {
        "name": "ฟ้าไซเบอร์",
        "name_en": "Cyber Cobalt",
        "primary": (45, 140, 245),
        "dark": (25, 80, 175),
        "highlight": (120, 205, 255),
        "tread": (45, 50, 62),
        "glass": (100, 255, 240),
        "unlock_cost": 50,
        "unlock_req": {"type": "depth", "value": 10},
        "unlock_desc": "ลงถึงความลึก 10ม.",
    },
    "red": {
        "name": "แดงเพลิง",
        "name_en": "Crimson Inferno",
        "primary": (230, 55, 55),
        "dark": (155, 25, 25),
        "highlight": (255, 120, 120),
        "tread": (48, 48, 52),
        "glass": (255, 200, 100),
        "unlock_cost": 50,
        "unlock_req": {"type": "depth", "value": 10},
        "unlock_desc": "ลงถึงความลึก 10ม.",
    },
    "green": {
        "name": "เขียวมรกต",
        "name_en": "Emerald Jade",
        "primary": (45, 195, 95),
        "dark": (25, 125, 55),
        "highlight": (125, 245, 160),
        "tread": (45, 52, 46),
        "glass": (255, 240, 110),
        "unlock_cost": 100,
        "unlock_req": {"type": "depth", "value": 25},
        "unlock_desc": "ลงถึงความลึก 25ม.",
    },
    "purple": {
        "name": "ม่วงอเมทิสต์",
        "name_en": "Neon Amethyst",
        "primary": (175, 65, 245),
        "dark": (110, 30, 170),
        "highlight": (225, 145, 255),
        "tread": (48, 45, 56),
        "glass": (100, 230, 255),
        "unlock_cost": 120,
        "unlock_req": {"type": "depth", "value": 30},
        "unlock_desc": "ลงถึงความลึก 30ม.",
    },
    "carbon": {
        "name": "ดำคาร์บอน",
        "name_en": "Stealth Carbon",
        "primary": (60, 65, 75),
        "dark": (32, 35, 42),
        "highlight": (130, 138, 155),
        "tread": (28, 30, 35),
        "glass": (255, 100, 70),
        "unlock_cost": 150,
        "unlock_req": {"type": "depth", "value": 40},
        "unlock_desc": "ลงถึงความลึก 40ม.",
    },
    "white": {
        "name": "ขาวเงินหิมะ",
        "name_en": "Arctic Platinum",
        "primary": (230, 235, 245),
        "dark": (160, 170, 185),
        "highlight": (255, 255, 255),
        "tread": (50, 55, 65),
        "glass": (80, 190, 255),
        "unlock_cost": 180,
        "unlock_req": {"type": "depth", "value": 50},
        "unlock_desc": "ลงถึงความลึก 50ม.",
    },
    "orange": {
        "name": "ส้มเปลวสุริยัน",
        "name_en": "Solar Flare",
        "primary": (255, 115, 25),
        "dark": (185, 65, 10),
        "highlight": (255, 185, 90),
        "tread": (52, 48, 45),
        "glass": (90, 240, 255),
        "unlock_cost": 200,
        "unlock_req": {"type": "depth", "value": 60},
        "unlock_desc": "ลงถึงความลึก 60ม.",
    },
}

# ---------- 2. ประเภทรถขุด (Vehicle Types / Chassis) ----------
DEFAULT_VEHICLE_TYPE = "standard"

VEHICLE_TYPES = {
    "standard": {
        "name": "รถขุดมาตรฐาน (MK-1)",
        "name_en": "Standard Excavator",
        "tag": "สมดุลรอบด้าน",
        "desc": "โครงสร้างมาตรฐาน สมดุลทุกความสามารถ คล่องตัวในทุกความลึก",
        "speed_mult": 1.0,
        "capacity_mult": 1.0,
        "energy_add": 0.0,
        "move_drain_mult": 1.0,
        "grav_charge_mult": 1.0,
        "badge_color": (245, 185, 40),
        "unlock_cost": 0,
        "unlock_req": None,
        "unlock_desc": "ปลดล็อคเริ่มต้น",
    },
    "scout": {
        "name": "รถสำรวจความเร็วสูง (Swift Scout)",
        "name_en": "Speed Buggy",
        "tag": "ว่องไว ปราดเปรียว",
        "desc": "ตัวถังน้ำหนักเบา เพิ่มความเร็ว +25% ประหยัดพลังงานวิ่ง -20% (ความจุถัง -20%)",
        "speed_mult": 1.25,
        "capacity_mult": 0.80,
        "energy_add": 0.0,
        "move_drain_mult": 0.80,
        "grav_charge_mult": 1.0,
        "badge_color": (60, 190, 255),
        "unlock_cost": 150,
        "unlock_req": {"type": "depth", "value": 15},
        "unlock_desc": "ลงถึงความลึก 15ม.",
    },
    "titan": {
        "name": "รถขุดยักษ์ไททัน (Titan Colossus)",
        "name_en": "Heavy Hauler",
        "tag": "บรรทุกหนัก แบตเตอรี่สูง",
        "desc": "เกราะหนาบรรทุกหนัก เพิ่มความจุถัง +50% และพลังงาน +30 (ความเร็ว -15%)",
        "speed_mult": 0.85,
        "capacity_mult": 1.50,
        "energy_add": 30.0,
        "move_drain_mult": 1.15,
        "grav_charge_mult": 0.90,
        "badge_color": (255, 120, 50),
        "unlock_cost": 300,
        "unlock_req": {"type": "capacity_or_energy_lv", "value": 3},
        "unlock_desc": "อัปเกรดถัง หรือ พลังงาน ถึง Lv.3",
    },
    "hover": {
        "name": "ยานโฮเวอร์ใต้พิภพ (Aero Hoverpod)",
        "name_en": "Aero Drill Pod",
        "tag": "เจ้าแห่งแรงโน้มถ่วง",
        "desc": "ไอพ่นต้านแรงโน้มถ่วง สะสมชาร์จดิ่งเร็วกว่าเดิม 2 เท่า และลดพลังงานเจาะลงล่าง -30%",
        "speed_mult": 1.08,
        "capacity_mult": 0.95,
        "energy_add": -10.0,
        "move_drain_mult": 0.90,
        "grav_charge_mult": 2.0,
        "badge_color": (160, 90, 255),
        "unlock_cost": 450,
        "unlock_req": {"type": "depth", "value": 35},
        "unlock_desc": "ลงถึงความลึก 35ม.",
    },
}

# ---------- 3. ประเภทหัวขุด (Digging Heads & Special Abilities) ----------
DEFAULT_DRILL_HEAD = "spiral"

DRILL_HEADS = {
    "spiral": {
        "name": "สว่านเกลียวเหล็กกล้า",
        "name_en": "Steel Spiral Drill",
        "ability_name": "Standard Reliability (สมดุลรอบด้าน)",
        "desc": "หัวสว่านเหล็กกล้ามาตรฐาน ทำงานสม่ำเสมอ ประหยัดพลังงาน ไว้วางใจได้เสมอ",
        "power_mult": 1.0,
        "dig_drain_mult": 1.0,
        "can_drill_rock_always": False,
        "rock_damage_mult": 1.0,
        "aoe_reach": 0,
        "bonus_sell_mult": 1.0,
        "extra_loot_chance": 0.0,
        "badge_color": (185, 195, 205),
        "particle_theme": "dirt",
        "unlock_cost": 0,
        "unlock_req": None,
        "unlock_desc": "ปลดล็อคเริ่มต้น",
    },
    "diamond": {
        "name": "หัวเจาะเพชรไทเทเนียม",
        "name_en": "Titanium Rock-Crusher",
        "ability_name": "Bedrock Breaker (ทะลวงหินผา)",
        "desc": "เจาะทะลุหินแข็งได้ทันทีโดยไม่ต้องรออัปเกรด! ขุดหินรวดเร็วขึ้น +50%",
        "power_mult": 1.15,
        "dig_drain_mult": 1.0,
        "can_drill_rock_always": True,   # เจาะหินแข็งได้ทันทีตั้งแต่เริ่ม
        "rock_damage_mult": 1.5,
        "aoe_reach": 0,
        "bonus_sell_mult": 1.0,
        "extra_loot_chance": 0.0,
        "badge_color": (90, 220, 255),
        "particle_theme": "diamond",
        "unlock_cost": 450,
        "unlock_req": {"type": "diamond_and_drill", "diamonds": 3, "drill_lv": 2},
        "unlock_desc": "เก็บเพชรครบ 3 เม็ด และหัวขุด Lv.2+",
    },
    "plasma": {
        "name": "หัวตัดเลเซอร์พลาสม่า",
        "name_en": "Plasma Laser Cutter",
        "ability_name": "Superheated Melter (หลอมละลายความร้อนสูง)",
        "desc": "ลำแสงความร้อนสูง เพิ่มแรงเจาะทะลวงดิน +65% ขุดไวมาก (ใช้พลังงานเจาะ +20%)",
        "power_mult": 1.65,
        "dig_drain_mult": 1.20,
        "can_drill_rock_always": False,
        "rock_damage_mult": 1.25,
        "aoe_reach": 0,
        "bonus_sell_mult": 1.0,
        "extra_loot_chance": 0.0,
        "badge_color": (255, 95, 40),
        "particle_theme": "plasma",
        "unlock_cost": 350,
        "unlock_req": {"type": "drill_lv", "value": 3},
        "unlock_desc": "อัปเกรดหัวขุดถึง Lv.3",
    },
    "vortex": {
        "name": "หัวสว่านแม่เหล็กดูดแร่",
        "name_en": "Magnetic Vortex Drill",
        "ability_name": "Fortune Attractor (แรงดึงดูดโชคลาภ)",
        "desc": "สนามแม่เหล็กเพิ่มเงินจากการขายแร่ +25% และเพิ่มโอกาสพบกระป๋องน้ำมัน/อัญมณีลึกลับ",
        "power_mult": 0.95,
        "dig_drain_mult": 0.95,
        "can_drill_rock_always": False,
        "rock_damage_mult": 1.0,
        "aoe_reach": 0,
        "bonus_sell_mult": 1.25,        # โบนัสเงินขายแร่ 25%
        "extra_loot_chance": 0.35,      # โอกาสสุ่มเจอแร่/น้ำมันพิเศษ
        "badge_color": (200, 110, 255),
        "particle_theme": "vortex",
        "unlock_cost": 200,
        "unlock_req": {"type": "drill_lv", "value": 2},
        "unlock_desc": "อัปเกรดหัวขุดถึง Lv.2",
    },
    "seismic": {
        "name": "หัวกระแทกคลื่นสั่นสะเทือน",
        "name_en": "Seismic Hammer Head",
        "ability_name": "Seismic Cleave (คลื่นกระแทกวงกว้าง)",
        "desc": "แรงกระแทกสร้างคลื่นสั่นสะเทือน ขุดบล็อกข้างเคียงพร้อมกัน 3 บล็อกตั้งแต่ระดับเริ่มต้น",
        "power_mult": 1.05,
        "dig_drain_mult": 1.10,
        "can_drill_rock_always": False,
        "rock_damage_mult": 1.1,
        "aoe_reach": 2,                 # กว้าง 3 บล็อก (รัศมี ±1) ทันที
        "bonus_sell_mult": 1.0,
        "extra_loot_chance": 0.0,
        "badge_color": (240, 180, 80),
        "particle_theme": "seismic",
        "unlock_cost": 600,
        "unlock_req": {"type": "tier_or_drill", "tier": 2, "drill_lv": 4},
        "unlock_desc": "ถึงระดับรวม Tier 2 หรือหัวขุด Lv.4",
    },
}


