# -*- coding: utf-8 -*-
"""
ui.py
การแสดงผลกราฟิกและ UI ทั้งหมดของเกม:
- HUD 3 โซน (ซ้าย: ทรัพยากรในถัง | กลาง: เหรียญ/ความลึก/หลอดสถานะ | ขวา: ภารกิจประจำตา Quest Tracker)
- หน้าต่างเลือกสัญญาภารกิจประจำตา (Contract Selection Modal: ง่าย / ปานกลาง / ยาก)
- ร้านค้าอัปเกรด (Shop)
- เมนูหยุดชั่วคราว (Pause Menu)
- หน้าจอชนะ / จบเกม (Victory & Game Over Screen)
- เมนูหลัก (Main Menu)
- ระบบ Hint, Toast, และ Aim Indicator
"""
import math
import random
import pygame
import settings as S
import assets
import missions

pygame.font.init()
FONT_XS = None
FONT_S  = None
FONT_M  = None
FONT_L  = None
FONT_XL = None


def init_fonts():
    global FONT_XS, FONT_S, FONT_M, FONT_L, FONT_XL
    thai_font_path = pygame.font.match_font(
        "tahoma,leelawadee,garuda,loma,tlwgtypo,arialunicodems"
    )
    if thai_font_path is None:
        import glob
        candidates = []
        for pattern in [
            "C:/Windows/Fonts/tahoma.ttf",
            "C:/Windows/Fonts/leelawUI.ttf",
            "/usr/share/fonts/**/NotoSansThai*.ttf",
            "/usr/share/fonts/**/Garuda*.ttf",
        ]:
            candidates.extend(glob.glob(pattern, recursive=True))
        thai_font_path = candidates[0] if candidates else None

    FONT_XS = pygame.font.Font(thai_font_path, 12)
    FONT_S  = pygame.font.Font(thai_font_path, 14)
    FONT_M  = pygame.font.Font(thai_font_path, 17)
    FONT_L  = pygame.font.Font(thai_font_path, 24)
    FONT_XL = pygame.font.Font(thai_font_path, 38)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers สำหรับวาด UI
# ─────────────────────────────────────────────────────────────────────────────

def text(surface, s, font, color, pos, center=False, right=False, shadow=True, max_w=None):
    """วาดข้อความ จัด alignment ซ้าย/กลาง/ขวา และตัดทอน ... อัตโนมัติหากเกิน max_w"""
    s = str(s)
    if max_w and font.size(s)[0] > max_w:
        while len(s) > 1 and font.size(s + "…")[0] > max_w:
            s = s[:-1]
        s = s + "…"

    surf = font.render(s, True, color)
    if center:
        rect = surf.get_rect(center=pos)
    elif right:
        rect = surf.get_rect(topright=pos)
    else:
        rect = surf.get_rect(topleft=pos)

    if shadow:
        sh = font.render(s, True, (10, 10, 14))
        surface.blit(sh, rect.move(1, 1))

    surface.blit(surf, rect)
    return rect


def _draw_bar(surface, x, y, w, h, ratio, fg, bg=(45, 40, 50), radius=6, border=(60, 65, 80)):
    """แถบแสดงสถานะขอบมน พร้อมขอบเนียนตา"""
    pygame.draw.rect(surface, bg, (x, y, w, h), border_radius=radius)
    ratio_clamped = max(0.0, min(1.0, float(ratio)))
    filled = int(w * ratio_clamped)
    if filled > 0:
        pygame.draw.rect(surface, fg, (x, y, filled, h), border_radius=radius)
    pygame.draw.rect(surface, border, (x, y, w, h), 1, border_radius=radius)


def _panel(surface, rect, bg=(28, 30, 42), border=(55, 60, 80), alpha=245, radius=12):
    """พาเนลพื้นหลังสี่เหลี่ยมโค้งพร้อมความโปร่งแสง"""
    p = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
    bg_a = (*bg, alpha)
    pygame.draw.rect(p, bg_a, (0, 0, rect.w, rect.h), border_radius=radius)
    pygame.draw.rect(p, (*border, 255), (0, 0, rect.w, rect.h), 1, border_radius=radius)
    surface.blit(p, rect.topleft)


def dim_overlay(surface, alpha=160):
    """ชั้นมืดคลุมฉากหลังเมื่อเปิดเมนูหรือป๊อปอัป"""
    overlay = pygame.Surface((S.SCREEN_W, S.SCREEN_H), pygame.SRCALPHA)
    overlay.fill((8, 10, 16, alpha))
    surface.blit(overlay, (0, 0))


# ─────────────────────────────────────────────────────────────────────────────
# ไอคอนกราฟิกเวกเตอร์คุณภาพสูง (แทนที่ไอคอนสี่เหลี่ยมและฟอนต์ Emoji Tofu)
# ─────────────────────────────────────────────────────────────────────────────

def draw_icon_cargo(surface, rect, color=(240, 185, 60)):
    """ไอคอนถังเก็บแร่ (Cargo Pod) ทรงกระบอกมนพร้อมแถบล็อค"""
    x, y, w, h = rect
    r = min(w, h)
    cx, cy = x + w // 2, y + h // 2
    bw, bh = int(r * 0.76), int(r * 0.64)
    bx, by = cx - bw // 2, cy - bh // 2 + 1
    pygame.draw.rect(surface, color, (bx, by, bw, bh), border_radius=3)
    lw = bw + 2
    pygame.draw.rect(surface, (min(255, color[0] + 35), min(255, color[1] + 35), min(255, color[2] + 35)),
                     (bx - 1, by - 2, lw, 3), border_radius=2)
    pygame.draw.rect(surface, (40, 30, 20), (cx - 2, by + 2, 4, bh - 4), border_radius=1)


def draw_icon_energy(surface, rect, color=(255, 205, 40)):
    """ไอคอนสายฟ้าพลังงาน (Energy Bolt) แวววาว"""
    x, y, w, h = rect
    cx, cy = x + w // 2, y + h // 2
    s = min(w, h) * 0.42
    pts = [
        (cx + s * 0.1, cy - s * 1.1),
        (cx - s * 0.7, cy + s * 0.1),
        (cx - s * 0.05, cy + s * 0.1),
        (cx - s * 0.3, cy + s * 1.1),
        (cx + s * 0.8, cy - s * 0.1),
        (cx + s * 0.15, cy - s * 0.1),
    ]
    pygame.draw.polygon(surface, color, pts)
    pts_in = [
        (cx + s * 0.1, cy - s * 0.8),
        (cx - s * 0.4, cy + s * 0.05),
        (cx, cy + s * 0.05),
        (cx - s * 0.15, cy + s * 0.7),
        (cx + s * 0.5, cy - s * 0.05),
        (cx + s * 0.1, cy - s * 0.05),
    ]
    pygame.draw.polygon(surface, (255, 255, 220), pts_in)


def draw_icon_power(surface, rect, color=(230, 235, 245)):
    """ไอคอนหัวขุด / อีเต็อร์ (Pickaxe / Drill)"""
    x, y, w, h = rect
    cx, cy = x + w // 2, y + h // 2
    s = min(w, h) * 0.42
    pygame.draw.line(surface, (150, 110, 70), (cx - s * 0.7, cy + s * 0.8), (cx + s * 0.3, cy - s * 0.2), 3)
    pts = [
        (cx - s * 0.4, cy - s * 0.8),
        (cx + s * 0.8, cy - s * 0.5),
        (cx + s * 0.6, cy + s * 0.4),
        (cx + s * 0.3, cy - s * 0.1),
    ]
    pygame.draw.polygon(surface, color, pts)


def draw_icon_speed(surface, rect, color=(80, 205, 255)):
    """ไอคอนเทอร์โบสปีด (Speed Turbo Streaks)"""
    x, y, w, h = rect
    cx, cy = x + w // 2, y + h // 2
    s = min(w, h) * 0.45
    pygame.draw.line(surface, color, (cx - s * 0.8, cy - s * 0.5), (cx + s * 0.6, cy - s * 0.5), 2)
    pygame.draw.line(surface, (255, 255, 255), (cx - s * 0.4, cy), (cx + s * 0.9, cy), 3)
    pygame.draw.line(surface, color, (cx - s * 0.7, cy + s * 0.5), (cx + s * 0.5, cy + s * 0.5), 2)


def draw_icon_wrench(surface, rect, color=(210, 220, 240)):
    """ไอคอนประแจช่างกล (Wrench)"""
    x, y, w, h = rect
    cx, cy = x + w // 2, y + h // 2
    s = min(w, h) * 0.4
    pygame.draw.line(surface, (140, 150, 170), (cx - s * 0.6, cy + s * 0.6), (cx + s * 0.4, cy - s * 0.4), 3)
    pygame.draw.circle(surface, color, (int(cx + s * 0.5), int(cy - s * 0.5)), int(s * 0.45), 2)


def draw_icon_palette(surface, rect, color=(255, 140, 180)):
    """ไอคอนจานสี (Color Palette)"""
    x, y, w, h = rect
    cx, cy = x + w // 2, y + h // 2
    r = int(min(w, h) * 0.4)
    pygame.draw.circle(surface, (45, 50, 65), (cx, cy), r)
    pygame.draw.circle(surface, color, (cx, cy), r, 2)
    for ang, dc in [(0.2, (255, 80, 80)), (1.4, (80, 210, 90)), (2.6, (70, 170, 255)), (4.0, (255, 210, 50))]:
        dx = int(cx + math.cos(ang) * (r * 0.55))
        dy = int(cy + math.sin(ang) * (r * 0.55))
        pygame.draw.circle(surface, dc, (dx, dy), 3)


def draw_icon_check(surface, center, size=18, color=(75, 215, 115)):
    """ไอคอนเครื่องหมายถูกวงกลม (Circle Checkmark)"""
    cx, cy = int(center[0]), int(center[1])
    r = size // 2
    pygame.draw.circle(surface, color, (cx, cy), r)
    pygame.draw.circle(surface, (min(255, color[0] + 40), min(255, color[1] + 40), min(255, color[2] + 40)), (cx, cy), r, 1)
    pts = [(cx - r * 0.45, cy), (cx - r * 0.1, cy + r * 0.4), (cx + r * 0.48, cy - r * 0.35)]
    pygame.draw.lines(surface, (255, 255, 255), False, pts, 2)


def draw_icon_cross(surface, center, size=18, color=(235, 75, 75)):
    """ไอคอนกากบาทวงกลม (Circle Cross)"""
    cx, cy = int(center[0]), int(center[1])
    r = size // 2
    pygame.draw.circle(surface, color, (cx, cy), r)
    pygame.draw.circle(surface, (min(255, color[0] + 40), min(255, color[1] + 40), min(255, color[2] + 40)), (cx, cy), r, 1)
    d = r * 0.4
    pygame.draw.line(surface, (255, 255, 255), (cx - d, cy - d), (cx + d, cy + d), 2)
    pygame.draw.line(surface, (255, 255, 255), (cx + d, cy - d), (cx - d, cy + d), 2)


def draw_icon_star(surface, center, size=18, color=(255, 215, 50)):
    """ไอคอนดาว 5 แฉก (5-Point Star)"""
    cx, cy = int(center[0]), int(center[1])
    r_out = size // 2
    r_in = r_out * 0.45
    pts = []
    for i in range(10):
        ang = i * (math.pi / 5) - math.pi / 2
        r = r_out if i % 2 == 0 else r_in
        pts.append((cx + math.cos(ang) * r, cy + math.sin(ang) * r))
    pygame.draw.polygon(surface, color, pts)
    pygame.draw.polygon(surface, (255, 245, 180), pts, 1)


def draw_icon_dice(surface, rect, color=(80, 160, 240)):
    """ไอคอนลูกเต๋าสุ่ม (Dice)"""
    x, y, w, h = rect
    r = min(w, h)
    bx = x + (w - r) // 2
    by = y + (h - r) // 2
    pygame.draw.rect(surface, color, (bx, by, r, r), border_radius=4)
    pygame.draw.rect(surface, (255, 255, 255), (bx, by, r, r), 1, border_radius=4)
    cx, cy = bx + r // 2, by + r // 2
    pygame.draw.circle(surface, (255, 255, 255), (cx, cy), 2)


def draw_icon_lock(surface, rect, color=(255, 215, 60)):
    """ไอคอนแม่กุญแจล็อค/ปลดล็อค (Lock Gate Icon)"""
    x, y, w, h = rect
    cx, cy = x + w // 2, y + h // 2
    bw, bh = int(w * 0.72), int(h * 0.54)
    bx, by = cx - bw // 2, cy - bh // 2 + 3
    pygame.draw.rect(surface, color, (bx, by, bw, bh), border_radius=3)
    sr = int(w * 0.24)
    pygame.draw.arc(surface, color, (cx - sr, by - sr * 2 + 1, sr * 2, sr * 2), 0, math.pi, 2)
    pygame.draw.circle(surface, (30, 25, 20), (cx, by + bh // 2 - 2), 2)
    pygame.draw.line(surface, (30, 25, 20), (cx, by + bh // 2), (cx, by + bh // 2 + 4), 2)
    pygame.draw.circle(surface, (255, 255, 255), (cx - 4, cy - 4), 2)
    pygame.draw.circle(surface, (255, 255, 255), (cx + 4, cy + 4), 2)


def draw_icon_refresh(surface, center, size=18, color=(140, 120, 220)):
    """ไอคอนหมุนรีเฟรช (Refresh / Cycle)"""
    cx, cy = int(center[0]), int(center[1])
    r = size // 2 - 2
    pygame.draw.arc(surface, color, (cx - r, cy - r, r * 2, r * 2), 0.5, 5.5, 2)
    pygame.draw.polygon(surface, color, [(cx + r - 3, cy - 2), (cx + r + 3, cy - 2), (cx + r, cy + 3)])


def draw_icon_help(surface, rect, color=(255, 220, 80)):
    """ไอคอนคู่มือ/ช่วยเหลือรูปเครื่องหมายคำถาม"""
    r = pygame.Rect(rect)
    cx, cy = r.center
    radius = min(r.w, r.h) // 2
    pygame.draw.circle(surface, color, (cx, cy), radius, 2)
    text(surface, "?", FONT_S, color, (cx, cy), center=True, shadow=False)


def draw_key_badge(surface, key_str, x, y, min_w=30, h=24, active=False):
    """วาดปุ่มคีย์บอร์ดแบบ 3D Keycap"""
    kw, kh = FONT_S.size(key_str)
    w = max(min_w, kw + 12)
    rect = pygame.Rect(x, y, w, h)
    pygame.draw.rect(surface, (12, 14, 20), (x, y + 2, w, h), border_radius=5)
    base_c = (55, 65, 88) if not active else (190, 140, 35)
    pygame.draw.rect(surface, base_c, rect, border_radius=5)
    face_rect = pygame.Rect(x, y, w, h - 2)
    face_c = (34, 40, 56) if not active else (245, 190, 50)
    pygame.draw.rect(surface, face_c, face_rect, border_radius=4)
    border_c = (80, 95, 130) if not active else (255, 235, 130)
    pygame.draw.rect(surface, border_c, face_rect, 1, border_radius=4)
    tc = (245, 250, 255) if not active else (25, 25, 30)
    text(surface, key_str, FONT_S, tc, (face_rect.centerx, face_rect.centery - 1),
         center=True, shadow=not active)
    return rect


def draw_level_pip(surface, cx, cy, size=12, filled=True, color=(255, 205, 50)):
    """พอยต์แสดงระดับรูปเพชร (Diamond Notch Level Pip) แทนกล่องสี่เหลี่ยมเดิม"""
    r = size // 2
    pts = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
    if filled:
        pygame.draw.polygon(surface, color, pts)
        pygame.draw.polygon(surface, (255, 255, 255), pts, 1)
        pygame.draw.circle(surface, (255, 255, 255), (cx, cy), max(1, r // 3))
    else:
        pygame.draw.polygon(surface, (45, 50, 68), pts)
        pygame.draw.polygon(surface, (70, 75, 95), pts, 1)

def _draw_bullseye_icon(surface, cx, cy, radius, color=(255, 70, 70)):
    """ไอคอนเป้าหมายวงแหวนซ้อน (Bullseye target — แทนที่ emoji 🎯)"""
    pygame.draw.circle(surface, color, (int(cx), int(cy)), radius)
    pygame.draw.circle(surface, (255, 255, 255), (int(cx), int(cy)), max(1, int(radius * 0.65)))
    pygame.draw.circle(surface, color, (int(cx), int(cy)), max(1, int(radius * 0.35)))


def _draw_vehicle_silhouette_icon(surface, x, y, color=(200, 210, 230)):
    """ไอคอนเงารถขุดขนาดเล็ก (Mini excavator silhouette — แทนที่ emoji 🚜)"""
    bx, by = int(x), int(y)
    # ตัวถัง
    pygame.draw.rect(surface, color, (bx + 2, by + 4, 14, 8), border_radius=2)
    # แค็บโค้ง
    pygame.draw.rect(surface, color, (bx + 5, by + 1, 7, 5), border_radius=2)
    # แทร็คซ้าย-ขวา
    pygame.draw.rect(surface, (130, 140, 160), (bx, by + 11, 4, 6), border_radius=1)
    pygame.draw.rect(surface, (130, 140, 160), (bx + 14, by + 11, 4, 6), border_radius=1)



# ─────────────────────────────────────────────────────────────────────────────

def draw_sky_and_bg(surface, camera_y):
    surface.fill(S.COLOR_SKY_BOTTOM)
    sky_h = S.SURFACE_ROW * S.TILE - camera_y + S.HUD_H
    if sky_h > 0:
        pygame.draw.rect(surface, S.COLOR_SKY_TOP,
                         (0, S.HUD_H, S.SCREEN_W, min(sky_h, S.SCREEN_H)))
        for i, cx in enumerate([90, 280, 480, 640]):
            cy = 40 + (i * 19) % 35
            _cloud(surface, cx, cy + S.HUD_H - camera_y * 0.25)


def _cloud(surface, x, y):
    if y < S.HUD_H - 40 or y > 240:
        return
    c = (255, 255, 255, 220)
    pygame.draw.ellipse(surface, c, (int(x) - 30, int(y) - 12, 60, 22))
    pygame.draw.ellipse(surface, c, (int(x) - 14, int(y) - 22, 38, 22))
    pygame.draw.ellipse(surface, c, (int(x) + 6, int(y) - 16, 32, 20))


# ─────────────────────────────────────────────────────────────────────────────
# โลกใต้ดิน
# ─────────────────────────────────────────────────────────────────────────────

def draw_world(surface, world, camera_y):
    first_row = max(0, int(camera_y // S.TILE) - 1)
    last_row  = min(world.rows, first_row + (S.SCREEN_H // S.TILE) + 3)

    img_dirt   = assets.get_image("dirt")
    img_grass  = assets.get_image("grass")
    img_rock   = assets.get_image("rock")
    img_tunnel = assets.get_image("tunnel")
    img_barrier = assets.get_image("barrier")
    crack_1    = assets.get_image("crack_1")
    crack_2    = assets.get_image("crack_2")
    crack_3    = assets.get_image("crack_3")

    for row in range(first_row, last_row):
        screen_y = row * S.TILE - camera_y + S.HUD_H
        for col in range(world.cols):
            screen_x = col * S.TILE
            tile = world.tiles[row][col]

            if tile == S.T_SKY:
                continue
            elif tile == S.T_GRASS:
                surface.blit(img_grass, (screen_x, screen_y))
                _draw_cracks(surface, world, col, row, screen_x, screen_y, crack_1, crack_2, crack_3)
            elif tile == S.T_DIRT:
                surface.blit(img_dirt, (screen_x, screen_y))
                _draw_resource_sprite(surface, world.resource[row][col], screen_x, screen_y)
                _draw_cracks(surface, world, col, row, screen_x, screen_y, crack_1, crack_2, crack_3)
            elif tile == S.T_ROCK:
                surface.blit(img_rock, (screen_x, screen_y))
                _draw_resource_sprite(surface, world.resource[row][col], screen_x, screen_y)
                _draw_cracks(surface, world, col, row, screen_x, screen_y, crack_1, crack_2, crack_3)
            elif tile == getattr(S, "T_BARRIER", 5):
                surface.blit(img_barrier, (screen_x, screen_y))
                # ประตูล็อค: วาดไอคอนแม่กุญแจเรืองแสงตรงกลางแถว
                if col == S.COLS // 2:
                    draw_icon_lock(surface, (screen_x + 10, screen_y + 10, 28, 28), color=(255, 215, 60))
            elif tile == S.T_EMPTY:
                surface.blit(img_tunnel, (screen_x, screen_y))


def _draw_cracks(surface, world, col, row, sx, sy, c1, c2, c3):
    ratio = world.get_damage_ratio(col, row)
    if ratio >= 0.70:
        surface.blit(c3, (sx, sy))
    elif ratio >= 0.40:
        surface.blit(c2, (sx, sy))
    elif ratio >= 0.15:
        surface.blit(c1, (sx, sy))


def _draw_resource_sprite(surface, res, sx, sy):
    if res == S.RES_NONE:
        return
    key = {
        S.RES_COIN: "res_coin",
        S.RES_GOLD: "res_gold",
        S.RES_DIAMOND: "res_diamond",
        S.RES_FUEL: "res_fuel",
    }.get(res)
    if key:
        surface.blit(assets.get_image(key), (sx, sy))


# ─────────────────────────────────────────────────────────────────────────────
# อาคาร (บ้าน / ร้านค้า)
# ─────────────────────────────────────────────────────────────────────────────

def draw_home_and_shop(surface, camera_y):
    base_y = S.SURFACE_ROW * S.TILE - camera_y + S.HUD_H - S.TILE * 2
    surface.blit(assets.get_image("building_home"), (S.HOME_COL * S.TILE, base_y))
    surface.blit(assets.get_image("building_shop"), (S.SHOP_COL * S.TILE, base_y))


def draw_barrier_gate_banner(surface, floor_info, player_coins, camera_y):
    """วาดป้ายข้อมูลประตูกั้นชั้นลอยอยู่เหนือประตูในโลกเกม"""
    target_depth = S.get_floor_info(floor_info["floor"] - 1)["max_depth"]
    row = S.SURFACE_ROW + target_depth
    screen_y = row * S.TILE - camera_y + S.HUD_H

    # หากอยู่นอกจอ ไม่ต้องวาด
    if not (-60 <= screen_y <= S.SCREEN_H + 30):
        return

    cx = S.SCREEN_W // 2
    banner_w = 420
    banner_h = 56
    bx = cx - banner_w // 2
    by = int(screen_y - banner_h - 6)

    can_unlock = (player_coins >= floor_info["unlock_cost"])
    border_col = (255, 215, 60) if can_unlock else (220, 80, 80)
    bg_col = (24, 22, 30)

    panel = pygame.Rect(bx, by, banner_w, banner_h)
    _panel(surface, panel, bg=bg_col, border=border_col, alpha=235, radius=12)

    # วาดไอคอนล็อค
    draw_icon_lock(surface, (panel.left + 12, panel.top + 14, 26, 26),
                   color=(255, 215, 60) if can_unlock else (220, 90, 90))

    # ชื่อชั้น
    text(surface, f"ประตูกั้น: {floor_info['name']}", FONT_S, (255, 235, 180),
         (panel.left + 46, panel.top + 7), max_w=panel.w - 55)

    # ข้อความคำสั่งปลดล็อค
    cost = floor_info["unlock_cost"]
    if can_unlock:
        prompt_txt = f"กด [E] เพื่อปลดล็อค  ({cost:,} เหรียญ)"
        prompt_col = (110, 245, 130)
    else:
        diff = cost - player_coins
        prompt_txt = f"ต้องใช้ {cost:,} เหรียญ  (ขาดอีก {diff:,} เหรียญ ขุดแร่ไปขายก่อน)"
        prompt_col = (245, 130, 130)

    text(surface, prompt_txt, FONT_XS, prompt_col,
         (panel.left + 46, panel.top + 31), max_w=panel.w - 55)


# ─────────────────────────────────────────────────────────────────────────────
# รถขุด
# ─────────────────────────────────────────────────────────────────────────────

def draw_vehicle(surface, vehicle, camera_y):
    vx = vehicle.x + vehicle.vibe_x
    vy = vehicle.y + vehicle.vibe_y - camera_y + S.HUD_H
    rect = pygame.Rect(0, 0, int(vehicle.w), int(vehicle.h))
    rect.center = (int(vx), int(vy))

    vtype = getattr(vehicle, "vehicle_type", "standard")
    vcol = getattr(vehicle, "color_id", "yellow")
    dhead = getattr(vehicle, "drill_head", "spiral")

    body_raw = assets.get_image(f"vehicle_{vtype}_{vcol}")
    body = pygame.transform.smoothscale(body_raw, (rect.w, rect.h))
    if vehicle.facing[0] < 0:
        body = pygame.transform.flip(body, True, False)
    surface.blit(body, rect.topleft)

    fx, fy = vehicle.facing
    drill_dir = "down"
    drill_pos = (rect.centerx, rect.bottom + 2)

    if fx > 0:
        drill_dir, drill_pos = "right", (rect.right + 2, rect.centery)
    elif fx < 0:
        drill_dir, drill_pos = "left",  (rect.left - 2, rect.centery)
    elif fy < 0:
        drill_dir, drill_pos = "up",    (rect.centerx, rect.top - 2)
    elif fy > 0:
        drill_dir, drill_pos = "down",  (rect.centerx, rect.bottom + 2)

    drill_key = f"drill_{dhead}_{drill_dir}"
    d_base = assets.get_image(drill_key)
    drill_scale_w = max(18, int(vehicle.w * 0.44))
    drill_scale_h = max(18, int(vehicle.h * 0.44))
    d_scaled = pygame.transform.smoothscale(d_base, (drill_scale_w, drill_scale_h))

    if vehicle.is_drilling:
        angle = math.sin(vehicle.drill_anim) * 16.0
        d_surf = pygame.transform.rotate(d_scaled, angle)
    else:
        d_surf = d_scaled

    d_rect = d_surf.get_rect(center=drill_pos)
    surface.blit(d_surf, d_rect.topleft)

    # เอฟเฟกต์แสงรอบหัวขุดตามคุณสมบัติพิเศษ
    if vehicle.is_drilling:
        if dhead == "plasma":
            heat_rad = int(drill_scale_w * 0.55)
            ps = pygame.Surface((heat_rad * 2 + 4, heat_rad * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(ps, (255, 110, 20, 110), (heat_rad + 2, heat_rad + 2), heat_rad)
            pygame.draw.circle(ps, (255, 220, 80, 180), (heat_rad + 2, heat_rad + 2), heat_rad // 2)
            surface.blit(ps, (drill_pos[0] - heat_rad - 2, drill_pos[1] - heat_rad - 2))
        elif dhead == "vortex":
            v_rad = int(drill_scale_w * 0.65)
            ps = pygame.Surface((v_rad * 2 + 4, v_rad * 2 + 4), pygame.SRCALPHA)
            ang = pygame.time.get_ticks() / 120.0
            pygame.draw.arc(ps, (200, 90, 255, 190), (2, 2, v_rad * 2, v_rad * 2), ang, ang + 3.0, 2)
            surface.blit(ps, (drill_pos[0] - v_rad - 2, drill_pos[1] - v_rad - 2))
        elif dhead == "diamond":
            c_rad = int(drill_scale_w * 0.45)
            ps = pygame.Surface((c_rad * 2 + 4, c_rad * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(ps, (90, 220, 255, 100), (c_rad + 2, c_rad + 2), c_rad)
            surface.blit(ps, (drill_pos[0] - c_rad - 2, drill_pos[1] - c_rad - 2))

    if getattr(vehicle, "grav_charge", 0.0) > 0.05:
        charge_ratio = vehicle.grav_charge / S.GRAV_CHARGE_MAX
        aura_rad = int(vehicle.w * 0.70 + charge_ratio * 10)
        gs = pygame.Surface((aura_rad * 2 + 4, aura_rad * 2 + 4), pygame.SRCALPHA)
        color_aura = (70, 190, 255, int(50 + 90 * charge_ratio))
        pygame.draw.circle(gs, color_aura, (aura_rad + 2, aura_rad + 2), aura_rad, 2)
        surface.blit(gs, (int(vx - aura_rad - 2), int(vy - aura_rad - 2)))

    if getattr(vehicle, "grav_charge", 0.0) > 0.02:
        bar_w = 6
        bar_h = int(vehicle.h * 0.9)
        bx_bar = int(rect.right + 6)
        by_bar = int(rect.centery - bar_h / 2)
        pygame.draw.rect(surface, (20, 30, 45), (bx_bar, by_bar, bar_w, bar_h), border_radius=3)
        ch_h = int(bar_h * min(1.0, vehicle.grav_charge / S.GRAV_CHARGE_MAX))
        if ch_h > 0:
            c_top = by_bar + bar_h - ch_h
            dive_color = (255, 180, 40) if vehicle.is_diving else (60, 210, 255)
            pygame.draw.rect(surface, dive_color, (bx_bar, c_top, bar_w, ch_h), border_radius=3)
        pygame.draw.rect(surface, (80, 140, 200), (bx_bar, by_bar, bar_w, bar_h), 1, border_radius=3)

    if vehicle.stalled:
        text(surface, "พลังงานหมด!", FONT_S, (255, 80, 80),
             (rect.centerx, rect.top - 20), center=True)


# ─────────────────────────────────────────────────────────────────────────────
# HUD  (3 โซน: ซ้าย ทรัพยากร | กลาง เงิน/สถานะ | ขวา ภารกิจผสม)
# ─────────────────────────────────────────────────────────────────────────────
_Z_LEFT_W   = 195
_Z_CENTER_W = 250
_Z_RIGHT_W  = S.SCREEN_W - _Z_LEFT_W - _Z_CENTER_W  # 275

def draw_hud(surface, vehicle, depth, mission=None, game_mode="mission", unlocked_floor=1, mouse_pos=None):
    # พื้นหลังแถบ HUD
    hud_surf = pygame.Surface((S.SCREEN_W, S.HUD_H), pygame.SRCALPHA)
    hud_surf.fill((18, 20, 28, 252))
    surface.blit(hud_surf, (0, 0))

    # เส้นแบ่งโซนแนวตั้ง
    pygame.draw.line(surface, (45, 50, 70), (_Z_LEFT_W, 8), (_Z_LEFT_W, S.HUD_H - 8), 1)
    pygame.draw.line(surface, (45, 50, 70), (_Z_LEFT_W + _Z_CENTER_W, 8), (_Z_LEFT_W + _Z_CENTER_W, S.HUD_H - 8), 1)

    # เส้นขอบล่าง HUD
    pygame.draw.line(surface, (55, 62, 85), (0, S.HUD_H - 1), (S.SCREEN_W, S.HUD_H - 1), 2)

    buttons = {}
    _hud_zone_left(surface, vehicle, buttons=buttons, mouse_pos=mouse_pos)
    _hud_zone_center(surface, vehicle, depth, buttons=buttons, mouse_pos=mouse_pos)
    _hud_zone_right(surface, vehicle, mission, game_mode=game_mode, unlocked_floor=unlocked_floor, depth=depth)
    return buttons


def _hud_zone_left(surface, vehicle, buttons=None, mouse_pos=None):
    """โซนซ้าย: ทรัพยากรในถังขุด พร้อมปุ่มลัดเรียกโดรนขนส่งแร่ [R]"""
    draw_icon_cargo(surface, (14, 8, 16, 16), (170, 190, 220))
    text(surface, "แร่ในถัง", FONT_XS, (170, 190, 220), (35, 9))

    # ปุ่มทางลัดเรียกโดรนขายแร่ (Cargo Drone Shortcut Button)
    btn_drone = pygame.Rect(96, 5, 90, 20)
    has_cargo = vehicle.cargo_count > 0
    is_hover = (mouse_pos is not None and btn_drone.collidepoint(mouse_pos))
    if has_cargo:
        d_bg = (38, 110, 68) if not is_hover else (48, 140, 85)
        d_border = (90, 215, 140)
        d_txt_col = (255, 255, 255)
    else:
        d_bg = (30, 34, 46) if not is_hover else (38, 44, 58)
        d_border = (60, 70, 92)
        d_txt_col = (150, 165, 185)

    pygame.draw.rect(surface, d_bg, btn_drone, border_radius=5)
    pygame.draw.rect(surface, d_border, btn_drone, 1, border_radius=5)
    text(surface, "🚀 โดรน (R)", FONT_XS, d_txt_col, (btn_drone.centerx, btn_drone.centery), center=True)
    if buttons is not None:
        buttons["drone"] = btn_drone
        buttons["drone_sell"] = btn_drone

    items = [
        ("res_coin",    vehicle.cargo[S.RES_COIN],    (255, 220, 80)),
        ("res_gold",    vehicle.cargo[S.RES_GOLD],    (255, 195, 30)),
        ("res_diamond", vehicle.cargo[S.RES_DIAMOND], (120, 220, 255)),
    ]

    slot_w = 52
    slot_h = 54
    y_start = 28
    x_start = 12

    for i, (img_key, count, color) in enumerate(items):
        sx = x_start + i * (slot_w + 6)
        slot_rect = pygame.Rect(sx, y_start, slot_w, slot_h)
        # ช่องโค้งมนสไตล์แคปซูล
        _panel(surface, slot_rect, bg=(26, 28, 40), border=(55, 65, 88), alpha=210, radius=12)

        # วงแหวนนุ่มนวลด้านหลังไอคอนแร่
        pygame.draw.circle(surface, (36, 42, 58), (sx + slot_w // 2, y_start + 18), 14)

        # ไอคอนแร่
        icon = pygame.transform.smoothscale(assets.get_image(img_key), (22, 22))
        surface.blit(icon, (sx + (slot_w - 22) // 2, y_start + 7))

        # ตัวเลขจำนวน
        text(surface, str(count), FONT_S, color,
             (sx + slot_w // 2, y_start + 38), center=True, shadow=True, max_w=slot_w - 6)


def _hud_zone_center(surface, vehicle, depth, buttons=None, mouse_pos=None):
    """โซนกลาง: เหรียญสะสม | ปุ่มร้านค้าดาวเทียม [B] | ความลึก | หลอดพลังงาน | หลอดความจุถัง"""
    x0 = _Z_LEFT_W + 12
    bar_w = 226

    # แถวบน: เหรียญ (ซ้าย) + ปุ่มร้านค้า (กลาง) + ความลึก (ขวา)
    coin_icon = pygame.transform.smoothscale(assets.get_image("res_coin"), (18, 18))
    surface.blit(coin_icon, (x0, 8))
    text(surface, f"{vehicle.coins:,}", FONT_M, (255, 215, 60), (x0 + 22, 6))

    # ปุ่มทางลัดร้านค้าดาวเทียม (Radio Shop Shortcut Button)
    btn_shop = pygame.Rect(x0 + 78, 6, 72, 21)
    is_hover_s = (mouse_pos is not None and btn_shop.collidepoint(mouse_pos))
    s_bg = (42, 75, 130) if not is_hover_s else (55, 95, 165)
    s_border = (85, 145, 240)
    s_txt = (255, 255, 255) if is_hover_s else (215, 230, 255)
    pygame.draw.rect(surface, s_bg, btn_shop, border_radius=5)
    pygame.draw.rect(surface, s_border, btn_shop, 1, border_radius=5)
    text(surface, "📡 ร้าน (B)", FONT_XS, s_txt, (btn_shop.centerx, btn_shop.centery), center=True)
    if buttons is not None:
        buttons["shop"] = btn_shop
        buttons["radio_shop"] = btn_shop

    depth_txt = f"▼ {depth} ม.  T{vehicle.overall_tier()}"
    text(surface, depth_txt, FONT_S, (140, 215, 245), (x0 + bar_w, 8), right=True)

    # แถว 2: หลอดพลังงาน
    en_ratio = max(0.0, vehicle.energy / vehicle.max_energy)
    en_fg    = (255, 145, 35) if en_ratio > 0.22 else (235, 55, 55)
    _draw_bar(surface, x0, 34, bar_w, 20, en_ratio, en_fg,
              bg=(45, 28, 18), radius=6, border=(70, 48, 30))
    draw_icon_energy(surface, (x0 + 6, 36, 16, 16))
    en_txt = f"{int(vehicle.energy)} / {int(vehicle.max_energy)}"
    text(surface, en_txt, FONT_XS, (255, 255, 255),
         (x0 + bar_w // 2, 44), center=True, shadow=True)

    # แถว 3: หลอดความจุถัง
    cratio = vehicle.cargo_count / vehicle.max_capacity if vehicle.max_capacity else 0.0
    c_fg   = (240, 70, 70) if vehicle.cargo_full() else (75, 195, 100)
    _draw_bar(surface, x0, 60, bar_w, 20, cratio, c_fg,
              bg=(24, 38, 25), radius=6, border=(45, 68, 48))
    draw_icon_cargo(surface, (x0 + 6, 62, 16, 16), (220, 245, 220) if not vehicle.cargo_full() else (255, 140, 130))
    cap_lbl = "ถังเต็ม! กด R" if vehicle.cargo_full() else f"ถัง: {vehicle.cargo_count} / {vehicle.max_capacity}"
    cap_col = (255, 140, 130) if vehicle.cargo_full() else (225, 245, 225)
    text(surface, cap_lbl, FONT_XS, cap_col,
         (x0 + bar_w // 2, 70), center=True, shadow=True)


def _hud_zone_right(surface, vehicle, mission=None, game_mode="mission", unlocked_floor=1, depth=0):
    """โซนขวา: ภารกิจผสมประจำตา (Quest Tracker) หรือแถบความคืบหน้าโหมดคลาสสิก (Floor Tracker)"""
    panel = pygame.Rect(_Z_LEFT_W + _Z_CENTER_W + 8, 6, _Z_RIGHT_W - 16, 78)

    # ---------- โหมดคลาสสิก: ติดตามการปลดล็อคชั้นความลึก (Floor Unlock Tracker) ----------
    if game_mode == "classic":
        # คำนวณชั้นปัจจุบันตามความลึก
        cur_floor = 1
        for fc in getattr(S, "CLASSIC_FLOORS", []):
            if depth >= fc["min_depth"]:
                cur_floor = fc["floor"]
        if depth > S.CLASSIC_FLOORS[-1]["max_depth"]:
            cur_floor = len(S.CLASSIC_FLOORS) + 1 + (depth - S.CLASSIC_FLOORS[-1]["max_depth"]) // 50

        next_floor = unlocked_floor + 1
        next_info = S.get_floor_info(next_floor)
        next_cost = next_info["unlock_cost"]
        can_unlock = (vehicle.coins >= next_cost)
        ratio = min(1.0, vehicle.coins / next_cost) if next_cost > 0 else 1.0

        border_col = (255, 215, 60) if can_unlock else (190, 140, 45)
        bg_col = (34, 30, 22) if can_unlock else (26, 26, 36)
        _panel(surface, panel, bg=bg_col, border=border_col, alpha=235, radius=10)

        # แถว 1: ตราสัญลักษณ์โหมดคลาสสิก + ชั้นปัจจุบัน & ปลดล็อค
        draw_icon_lock(surface, (panel.left + 10, panel.top + 9, 16, 16), color=(255, 215, 60))
        text(surface, f"ชั้นที่ {cur_floor}", FONT_XS, (255, 215, 60), (panel.left + 30, panel.top + 8))
        text(surface, f"ปลดล็อคถึงชั้น {unlocked_floor}", FONT_S, (235, 240, 255), (panel.left + 82, panel.top + 7), max_w=panel.w - 88)

        # แถว 2: หลอดความคืบหน้าการปลดล็อคชั้นถัดไป
        bar_w = panel.w - 24
        bar_h = 18
        bar_x = panel.left + 12
        bar_y = panel.top + 33
        bar_fg = (75, 210, 100) if can_unlock else (235, 175, 45)
        _draw_bar(surface, bar_x, bar_y, bar_w, bar_h, ratio, bar_fg,
                  bg=(40, 32, 22), radius=5, border=(70, 56, 35))

        if can_unlock:
            bar_lbl = f"พร้อมปลดล็อคชั้น {next_floor}! (กด E)"
            lbl_col = (255, 255, 255)
        else:
            bar_lbl = f"{vehicle.coins:,} / {next_cost:,} เหรียญ"
            lbl_col = (255, 245, 220)
        text(surface, bar_lbl, FONT_XS, lbl_col, (panel.centerx, bar_y + 9), center=True, shadow=True)

        # แถว 3: คำอธิบายชั้นเป้าหมาย
        text(surface, f"เป้าหมาย: ชั้นที่ {next_floor} ({next_cost:,} เหรียญ)", FONT_XS, (180, 195, 220),
             (panel.centerx, panel.top + 60), center=True, max_w=panel.w - 20)
        return

    if mission is None:
        _panel(surface, panel, bg=(26, 28, 40), border=(50, 56, 78), alpha=210, radius=10)
        text(surface, "โหมดอิสระ", FONT_S, (200, 210, 230), (panel.centerx, panel.top + 24), center=True)
        text(surface, "ขุดแร่และอัปเกรดตามใจชอบ", FONT_XS, (140, 150, 175), (panel.centerx, panel.top + 48), center=True)
        return

    diff_info = mission.diff_info
    all_done = mission.is_completed()

    border_color = (255, 220, 80) if all_done else diff_info["border_color"]
    _panel(surface, panel, bg=diff_info["bg_color"], border=border_color, alpha=235, radius=10)

    # แถว 1: ตราสัญลักษณ์ความยาก (วงกลมสี + ข้อความ) + ชื่อภารกิจ
    dot_col = diff_info.get("dot_color", diff_info["color"])
    pygame.draw.circle(surface, dot_col, (panel.left + 14, panel.top + 17), 7)
    pygame.draw.circle(surface, (255, 255, 255), (panel.left + 14, panel.top + 17), 7, 1)
    text(surface, diff_info["badge"], FONT_XS, diff_info["color"], (panel.left + 26, panel.top + 8))
    text(surface, mission.title, FONT_S, (240, 245, 255), (panel.left + 72, panel.top + 7), max_w=panel.w - 80)

    if all_done:
        draw_icon_star(surface, (panel.centerx - 90, panel.top + 44), 16)
        text(surface, "ภารกิจครบทุกข้อแล้ว!", FONT_S, (255, 225, 80),
             (panel.centerx, panel.top + 34), center=True)
        draw_icon_star(surface, (panel.centerx + 90, panel.top + 44), 16)
        text(surface, "กลับบ้านเพื่อรับชัยชนะ!", FONT_XS, (160, 245, 185),
             (panel.centerx, panel.top + 55), center=True)
    else:
        goals = mission.get_goals_status()
        # แถว 2 (เป้าหมาย 1 & 2)
        if len(goals) > 0:
            c0 = (100, 235, 120) if goals[0][2] else (215, 220, 235)
            if goals[0][2]:
                draw_icon_check(surface, (panel.left + 16, panel.top + 40), 13)
            else:
                pygame.draw.circle(surface, (140, 150, 170), (panel.left + 16, panel.top + 40), 3)
            text(surface, goals[0][5], FONT_XS, c0, (panel.left + 26, panel.top + 32), max_w=108)

        if len(goals) > 1:
            c1 = (100, 235, 120) if goals[1][2] else (215, 220, 235)
            if goals[1][2]:
                draw_icon_check(surface, (panel.left + 140, panel.top + 40), 13)
            else:
                pygame.draw.circle(surface, (140, 150, 170), (panel.left + 140, panel.top + 40), 3)
            text(surface, goals[1][5], FONT_XS, c1, (panel.left + 150, panel.top + 32), max_w=108)

        # แถว 3 (เป้าหมาย 3 & 4)
        if len(goals) > 2:
            c2 = (100, 235, 120) if goals[2][2] else (215, 220, 235)
            if goals[2][2]:
                draw_icon_check(surface, (panel.left + 16, panel.top + 62), 13)
            else:
                pygame.draw.circle(surface, (140, 150, 170), (panel.left + 16, panel.top + 62), 3)
            text(surface, goals[2][5], FONT_XS, c2, (panel.left + 26, panel.top + 54), max_w=108)

        if len(goals) > 3:
            c3 = (100, 235, 120) if goals[3][2] else (215, 220, 235)
            if goals[3][2]:
                draw_icon_check(surface, (panel.left + 140, panel.top + 62), 13)
            else:
                pygame.draw.circle(surface, (140, 150, 170), (panel.left + 140, panel.top + 62), 3)
            text(surface, goals[3][5], FONT_XS, c3, (panel.left + 150, panel.top + 54), max_w=108)
        elif len(goals) <= 2:
            text(surface, "(ทำครบแล้วขับกลับบ้าน)", FONT_XS, (140, 150, 175),
                 (panel.left + 140, panel.top + 54), max_w=115)


# ─────────────────────────────────────────────────────────────────────────────
# เล็งเป้า / Hint / Toast
# ─────────────────────────────────────────────────────────────────────────────

def draw_aim_indicator(surface, vehicle, mouse_pos, camera_y):
    mx, my = mouse_pos
    if my <= S.HUD_H:
        return
    world_y = my - S.HUD_H + camera_y
    t_col = int(mx // S.TILE)
    t_row = int(world_y // S.TILE)
    if 0 <= t_col < S.COLS and 0 <= t_row < S.WORLD_ROWS:
        sx  = t_col * S.TILE
        sy  = t_row * S.TILE - camera_y + S.HUD_H
        rect = pygame.Rect(sx, sy, S.TILE, S.TILE)
        pygame.draw.rect(surface, (255, 230, 100), rect, 2, border_radius=4)


def draw_hint(surface, msg):
    max_w = S.SCREEN_W - 32
    tw, th = FONT_M.size(msg)
    w = min(tw + 36, max_w)
    rect = pygame.Rect((S.SCREEN_W - w) // 2, S.SCREEN_H - 66, w, 36)
    _panel(surface, rect, bg=(18, 22, 32), border=(70, 80, 110), alpha=235, radius=8)
    text(surface, msg, FONT_M, (230, 235, 255), rect.center,
         center=True, shadow=False, max_w=rect.w - 16)


def draw_toast(surface, msg, timer):
    if timer <= 0:
        return
    alpha = min(255, int(timer * 255))
    tw, th = FONT_M.size(msg)
    max_w = S.SCREEN_W - 40
    w = min(tw + 48, max_w)
    rect = pygame.Rect((S.SCREEN_W - w) // 2, S.HUD_H + 34, w, 40)

    panel = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
    pygame.draw.rect(panel, (20, 100, 48, min(220, alpha)),
                     (0, 0, rect.w, rect.h), border_radius=8)
    pygame.draw.rect(panel, (55, 195, 100, min(220, alpha)),
                     (0, 0, rect.w, rect.h), 1, border_radius=8)
    surface.blit(panel, rect.topleft)
    text(surface, msg, FONT_M, (255, 255, 255), rect.center,
         center=True, shadow=False, max_w=rect.w - 16)


def draw_quick_controls_bar(surface):
    """แถบแนะนำปุ่มควบคุมลัดด้านล่างหน้าจอขณะเล่น (In-game Quick Controls Bar)"""
    bar_h = 24
    bar_y = S.SCREEN_H - bar_h

    bar_surf = pygame.Surface((S.SCREEN_W, bar_h), pygame.SRCALPHA)
    bar_surf.fill((14, 16, 24, 220))
    surface.blit(bar_surf, (0, bar_y))
    pygame.draw.line(surface, (45, 55, 78), (0, bar_y), (S.SCREEN_W, bar_y), 1)

    items = [
        ("WASD / ↑↓←→", "เดิน/ขุด"),
        ("Shift", "Turbo"),
        ("R", "โดรนขายแร่"),
        ("B", "วิทยุร้านค้า"),
        ("E", "ปลดล็อคชั้น"),
        ("H", "ช่วย"),
        ("ESC", "เมนู"),
    ]

    total_w = 0
    for k_txt, desc_txt in items:
        kw, _ = FONT_XS.size(k_txt)
        dw, _ = FONT_XS.size(desc_txt)
        total_w += (kw + 10) + 5 + dw + 14

    start_x = max(8, (S.SCREEN_W - total_w) // 2)
    cur_x = start_x
    for i, (k_txt, desc_txt) in enumerate(items):
        kw, kh = FONT_XS.size(k_txt)
        bw = kw + 10
        bh = 17
        by = bar_y + (bar_h - bh) // 2
        brect = pygame.Rect(cur_x, by, bw, bh)
        pygame.draw.rect(surface, (36, 44, 62), brect, border_radius=4)
        pygame.draw.rect(surface, (80, 95, 130), brect, 1, border_radius=4)
        k_col = (255, 225, 105) if k_txt in ("Shift", "R", "B", "E") else (225, 235, 250)
        text(surface, k_txt, FONT_XS, k_col, (brect.centerx, brect.centery), center=True, shadow=False)

        cur_x += bw + 5
        text(surface, desc_txt, FONT_XS, (185, 200, 220), (cur_x, bar_y + 4), shadow=False)
        cur_x += FONT_XS.size(desc_txt)[0]

        if i < len(items) - 1:
            cur_x += 8
            pygame.draw.circle(surface, (65, 75, 100), (cur_x, bar_y + bar_h // 2), 2)
            cur_x += 10


# ─────────────────────────────────────────────────────────────────────────────
# ปุ่มและฟังก์ชัน Button
# ─────────────────────────────────────────────────────────────────────────────

def button(surface, rect, label, font=None, base=(55, 65, 88), hover=False,
           text_color=None):
    font = font or FONT_M
    color = tuple(min(255, c + 30) for c in base) if hover else base
    pygame.draw.rect(surface, color, rect, border_radius=8)
    border_col = tuple(min(255, c + 60) for c in color)
    pygame.draw.rect(surface, border_col, rect, 1, border_radius=8)

    hl_color = tuple(min(255, c + 50) for c in color)
    hl_rect = pygame.Rect(rect.x + 2, rect.y + 2, rect.w - 4, max(4, rect.h // 3))
    hl_surf = pygame.Surface((hl_rect.w, hl_rect.h), pygame.SRCALPHA)
    hl_surf.fill((*hl_color, 70))
    surface.blit(hl_surf, hl_rect.topleft)

    tc = text_color or ((255, 255, 255) if hover else (225, 230, 245))
    text(surface, label, font, tc, rect.center, center=True, max_w=rect.w - 10)


# ─────────────────────────────────────────────────────────────────────────────
# หน้าต่างเลือกสัญญาภารกิจ (Contract Selection Modal: ง่าย / ปานกลาง / ยาก)
# ─────────────────────────────────────────────────────────────────────────────

def draw_contract_menu(surface, contracts, mouse_pos):
    dim_overlay(surface, 210)
    cx = S.SCREEN_W // 2

    panel = pygame.Rect(cx - 335, 110, 670, 560)
    _panel(surface, panel, bg=(18, 20, 30), border=(65, 75, 110), alpha=252, radius=18)

    text(surface, "เลือกสัญญาภารกิจประจำตา (Mission Contract)", FONT_L, (240, 245, 255),
         (cx, panel.top + 30), center=True)
    text(surface, "เลือกแผนภารกิจที่ต้องการพิชิต (ทำครบทุกข้อแล้วกลับบ้านเพื่อชนะ)", FONT_S,
         (160, 175, 205), (cx, panel.top + 60), center=True)

    buttons = {}
    card_w = 204
    card_h = 360
    card_y = panel.top + 90

    for i, mission in enumerate(contracts):
        card_x = panel.left + 18 + i * (card_w + 14)
        card_rect = pygame.Rect(card_x, card_y, card_w, card_h)
        diff_info = mission.diff_info

        is_hover = card_rect.collidepoint(mouse_pos)
        border_col = diff_info["border_color"] if not is_hover else tuple(min(255, c + 50) for c in diff_info["border_color"])
        _panel(surface, card_rect, bg=diff_info["bg_color"], border=border_col, alpha=240, radius=12)

        # ป้ายระดับความยาก — วงกลมสี + ข้อความ (แทน emoji ที่อาจเป็นสี่เหลี่ยม)
        banner_rect = pygame.Rect(card_x + 8, card_y + 8, card_w - 16, 32)
        pygame.draw.rect(surface, (*diff_info["border_color"], 70), banner_rect, border_radius=8)
        dot_col = diff_info.get("dot_color", diff_info["color"])
        pygame.draw.circle(surface, dot_col,
                           (banner_rect.left + 16, banner_rect.centery), 7)
        pygame.draw.circle(surface, (255, 255, 255),
                           (banner_rect.left + 16, banner_rect.centery), 7, 1)
        text(surface, diff_info["badge"], FONT_M, diff_info["color"],
             (banner_rect.centerx + 8, banner_rect.top + 6))

        # ชื่อภารกิจ
        text(surface, mission.title, FONT_M, (255, 255, 255),
             (card_rect.centerx, card_y + 56), center=True, max_w=card_w - 16)

        # คำอธิบายย่อ
        text(surface, mission.desc, FONT_XS, (180, 190, 210),
             (card_rect.centerx, card_y + 82), center=True, max_w=card_w - 20)

        # เส้นคั่น
        pygame.draw.line(surface, (55, 60, 80), (card_x + 12, card_y + 110), (card_x + card_w - 12, card_y + 110), 1)

        # หัวข้อเงื่อนไข — bullseye icon แทน emoji
        _draw_bullseye_icon(surface, card_x + 20, card_y + 124, 8)
        text(surface, "เงื่อนไขที่ต้องพิชิต:", FONT_XS, (255, 215, 60), (card_x + 34, card_y + 120))

        # แสดงเป้าหมายแต่ละข้อพร้อมไอคอนแร่จริง
        _GOAL_ICONS = {
            "gold":     "res_gold",
            "diamonds": "res_diamond",
            "coins":    "res_coin",
            "depth":    None,
            "fuel":     "res_fuel",
        }
        gy = card_y + 146
        for goal_key, target in mission.goals.items():
            label = missions.format_goal_label(goal_key, target)
            icon_key = _GOAL_ICONS.get(goal_key)
            if icon_key:
                icon_s = pygame.transform.smoothscale(assets.get_image(icon_key), (16, 16))
                surface.blit(icon_s, (card_x + 14, gy + 1))
                text(surface, label, FONT_S, (230, 235, 245), (card_x + 34, gy), max_w=card_w - 44)
            else:
                # Depth: draw a down-arrow vector icon
                ax, ay = card_x + 22, gy + 8
                pygame.draw.polygon(surface, (110, 200, 255),
                                    [(ax - 5, ay - 4), (ax + 5, ay - 4), (ax, ay + 5)])
                text(surface, label, FONT_S, (230, 235, 245), (card_x + 34, gy), max_w=card_w - 44)
            gy += 32

        # ปุ่มเลือกแผน
        btn_rect = pygame.Rect(card_x + 14, card_rect.bottom - 52, card_w - 28, 40)
        button(surface, btn_rect, "รับภารกิจนี้", FONT_M, base=diff_info["border_color"],
               hover=btn_rect.collidepoint(mouse_pos))
        buttons[f"select_{i}"] = btn_rect

    # ปุ่มการทำงานด้านล่าง (4 ปุ่ม จัดวางสมดุล)
    by = panel.bottom - 54
    btn_random = pygame.Rect(panel.left + 20, by, 140, 40)
    button(surface, btn_random, "สุ่มภารกิจ", FONT_S, base=(50, 80, 130),
           hover=btn_random.collidepoint(mouse_pos))
    draw_icon_dice(surface, (btn_random.left + 10, btn_random.centery - 8, 16, 16))
    buttons["random"] = btn_random

    btn_reroll = pygame.Rect(panel.left + 172, by, 140, 40)
    button(surface, btn_reroll, "สุ่มชุดใหม่", FONT_S, base=(75, 65, 110),
           hover=btn_reroll.collidepoint(mouse_pos))
    draw_icon_refresh(surface, (btn_reroll.left + 18, btn_reroll.centery), 16)
    buttons["reroll"] = btn_reroll

    btn_garage = pygame.Rect(panel.left + 324, by, 165, 40)
    button(surface, btn_garage, "แต่งรถขุด (Garage)", FONT_S, base=(45, 105, 165),
           hover=btn_garage.collidepoint(mouse_pos))
    draw_icon_palette(surface, (btn_garage.left + 8, btn_garage.centery - 9, 18, 18))
    buttons["garage"] = btn_garage

    btn_back = pygame.Rect(panel.right - 150, by, 130, 40)
    button(surface, btn_back, "< กลับ", FONT_S, base=(110, 45, 50),
           hover=btn_back.collidepoint(mouse_pos))
    buttons["back"] = btn_back

    return buttons


# ─────────────────────────────────────────────────────────────────────────────
# เมนูหลัก (Main Menu)
# ─────────────────────────────────────────────────────────────────────────────

def draw_main_menu(surface, has_save, mouse_pos):
    surface.fill((22, 32, 52))
    for row in range(S.SCREEN_H // 4):
        darkness = int(row / (S.SCREEN_H // 4) * 30)
        c1 = max(0, min(255, 22 - darkness // 2))
        c2 = max(0, min(255, 32 - darkness // 2))
        pygame.draw.line(surface, (c1, c2, 52),
                         (0, row * 4), (S.SCREEN_W, row * 4), 4)

    # ประกายดาว
    for i in range(40):
        sx = (i * 137 + 50) % S.SCREEN_W
        sy = (i * 97 + 30) % (S.SCREEN_H // 2)
        br = 100 + (i * 41) % 100
        pygame.draw.circle(surface, (br, br, min(255, br + 30)), (sx, sy), 1 + (i % 2))

    cx = S.SCREEN_W // 2
    # เงาชื่อเกม
    sh = FONT_XL.render("DIG & TREASURE", True, (15, 35, 70))
    surface.blit(sh, sh.get_rect(center=(cx + 3, 151)))
    text(surface, "DIG & TREASURE", FONT_XL, (255, 215, 60), (cx, 148), center=True)
    text(surface, "ขุดดิน ● หาสมบัติ ● ปลดล็อคชั้นความลึก ● ปรับแต่งรถขุด", FONT_M, (180, 210, 255),
         (cx, 198), center=True)

    pygame.draw.line(surface, (55, 80, 130), (cx - 180, 222), (cx + 180, 222), 1)

    buttons = {}
    y = 226

    # ─── 1. "Classic Mode" (โหมดคลาสสิก ขุดไร้ขีดจำกัด ปลดล็อคชั้นความลึก) ───
    rect_classic = pygame.Rect(cx - 165, y, 330, 46)
    button(surface, rect_classic, "โหมดคลาสสิก  (Classic Endless)", base=(170, 110, 25),
           hover=rect_classic.collidepoint(mouse_pos))
    draw_icon_lock(surface, (rect_classic.left + 10, rect_classic.centery - 10, 20, 20), color=(255, 225, 90))
    buttons["classic"] = rect_classic
    y += 54

    # ─── 2. "Mission Mode" (โหมดภารกิจผสมประจำตา) ───
    rect_new = pygame.Rect(cx - 165, y, 330, 46)
    button(surface, rect_new, "โหมดภารกิจ  (Mission Contracts)", base=(40, 125, 75),
           hover=rect_new.collidepoint(mouse_pos))
    gold_icon = pygame.transform.smoothscale(assets.get_image("res_gold"), (20, 20))
    surface.blit(gold_icon, (rect_new.left + 10, rect_new.centery - 10))
    buttons["new"] = rect_new
    y += 54

    # ─── 3. "Garage" (อู่แต่งรถขุด) ───
    rect_gar = pygame.Rect(cx - 165, y, 330, 46)
    button(surface, rect_gar, "อู่แต่งรถขุด  (Garage)", base=(45, 95, 160),
           hover=rect_gar.collidepoint(mouse_pos))
    draw_icon_palette(surface, (rect_gar.left + 8, rect_gar.centery - 10, 20, 20))
    buttons["garage"] = rect_gar
    y += 54

    # ─── 4. "How to Play" (วิธีเล่น & ปุ่มควบคุม) ───
    rect_how = pygame.Rect(cx - 165, y, 330, 46)
    button(surface, rect_how, "วิธีเล่น & ปุ่มควบคุม  (Controls)", base=(35, 105, 135),
           hover=rect_how.collidepoint(mouse_pos))
    draw_icon_help(surface, (rect_how.left + 10, rect_how.centery - 10, 20, 20))
    buttons["how_to_play"] = rect_how
    y += 54

    if has_save:
        # ─── 5. "Continue" (เล่นต่อจากเซฟ) ───
        rect_cont = pygame.Rect(cx - 165, y, 330, 46)
        button(surface, rect_cont, "เล่นต่อ  (Continue)", base=(55, 75, 140),
               hover=rect_cont.collidepoint(mouse_pos))
        dia_icon = pygame.transform.smoothscale(assets.get_image("res_diamond"), (20, 20))
        surface.blit(dia_icon, (rect_cont.left + 10, rect_cont.centery - 10))
        buttons["continue"] = rect_cont
        y += 54

    # ─── 6. "Quit" (ออกจากเกม) ───
    rect_quit = pygame.Rect(cx - 165, y, 330, 46)
    button(surface, rect_quit, "ออกจากเกม", base=(110, 45, 50),
           hover=rect_quit.collidepoint(mouse_pos))
    draw_icon_cross(surface, (rect_quit.left + 21, rect_quit.centery), 18, color=(220, 60, 60))
    buttons["quit"] = rect_quit

    # ข้อความเวอร์ชันชิดขวาล่าง
    text(surface, "v1.3 — Classic Endless & Floor Unlock Mode", FONT_XS, (85, 95, 120),
         (S.SCREEN_W - 16, S.SCREEN_H - 14), right=True, max_w=300)

    return buttons


# ─────────────────────────────────────────────────────────────────────────────
# เมนู Pause
# ─────────────────────────────────────────────────────────────────────────────

def draw_pause_menu(surface, mouse_pos, is_fullscreen=False):
    dim_overlay(surface, 175)
    cx = S.SCREEN_W // 2

    panel = pygame.Rect(cx - 170, 115, 340, 475)
    _panel(surface, panel, bg=(20, 22, 34), border=(60, 68, 100), alpha=240, radius=16)

    text(surface, "|| หยุดชั่วคราว (PAUSED)", FONT_L, (235, 240, 255),
         (cx, panel.top + 34), center=True)
    pygame.draw.line(surface, (50, 55, 80),
                      (panel.left + 20, panel.top + 60), (panel.right - 20, panel.top + 60), 1)

    buttons = {}
    y = panel.top + 72

    # ─── Pause menu buttons with real icons ───
    # 1. "Resume" — green play triangle icon
    r_resume = pygame.Rect(cx - 140, y, 280, 42)
    button(surface, r_resume, "เล่นต่อ", base=(40, 130, 70),
           hover=r_resume.collidepoint(mouse_pos))
    pcx, pcy = r_resume.left + 22, r_resume.centery
    pygame.draw.polygon(surface, (180, 255, 180), [(pcx - 7, pcy - 8), (pcx + 8, pcy), (pcx - 7, pcy + 8)])
    buttons["resume"] = r_resume
    y += 52

    # 2. "How to Play" — question mark icon
    r_how = pygame.Rect(cx - 140, y, 280, 42)
    button(surface, r_how, "วิธีเล่น & ปุ่มควบคุม  [H]", base=(35, 105, 135),
           hover=r_how.collidepoint(mouse_pos))
    draw_icon_help(surface, (r_how.left + 12, r_how.centery - 10, 20, 20))
    buttons["how_to_play"] = r_how
    y += 52

    # 3. "Fullscreen" — F11 monitor icon
    fs_label = "ออกจากเต็มจอ  [F11]" if is_fullscreen else "เต็มจอ  [F11]"
    r_fs = pygame.Rect(cx - 140, y, 280, 42)
    button(surface, r_fs, fs_label, base=(55, 75, 130),
           hover=r_fs.collidepoint(mouse_pos))
    mx, my2 = r_fs.left + 10, r_fs.centery - 8
    pygame.draw.rect(surface, (200, 215, 240), (mx, my2, 22, 14), border_radius=2)
    pygame.draw.rect(surface, (80, 100, 140), (mx, my2, 22, 14), 1, border_radius=2)
    pygame.draw.rect(surface, (80, 100, 140), (mx + 8, my2 + 14, 6, 4))
    buttons["fullscreen"] = r_fs
    y += 52

    # 4. "Save & Quit" — coin/save icon (coin = value, progress)
    r_sq = pygame.Rect(cx - 140, y, 280, 42)
    button(surface, r_sq, "บันทึกและออก", base=(130, 95, 35),
           hover=r_sq.collidepoint(mouse_pos))
    coin_icon = pygame.transform.smoothscale(assets.get_image("res_coin"), (22, 22))
    surface.blit(coin_icon, (r_sq.left + 10, r_sq.centery - 11))
    buttons["save_quit"] = r_sq
    y += 52

    # 5. "Quit without save" — red cross icon
    r_qn = pygame.Rect(cx - 140, y, 280, 42)
    button(surface, r_qn, "ออกโดยไม่บันทึก", base=(120, 42, 42),
           hover=r_qn.collidepoint(mouse_pos))
    draw_icon_cross(surface, (r_qn.left + 22, r_qn.centery), 18, color=(220, 60, 60))
    buttons["quit_nosave"] = r_qn
    y += 50

    # 6. ปุ่มเปิด/ปิดเสียง
    muted    = assets.is_muted()
    btn_size = 44
    mute_rect = pygame.Rect(cx - btn_size // 2, y + 4, btn_size, btn_size)
    is_hov   = mute_rect.collidepoint(mouse_pos)
    btn_col  = (130, 42, 42) if muted else (40, 110, 65)
    if is_hov:
        btn_col = tuple(min(255, c + 30) for c in btn_col)
    pygame.draw.circle(surface, btn_col, mute_rect.center, btn_size // 2)
    pygame.draw.circle(surface, (40, 44, 60), mute_rect.center, btn_size // 2, 2)

    mcx, mcy = mute_rect.center
    ic = (255, 255, 255)
    pts = [(mcx-8, mcy-6),(mcx-3, mcy-6),(mcx+2, mcy-11),
           (mcx+2, mcy+11),(mcx-3, mcy+6),(mcx-8, mcy+6)]
    pygame.draw.polygon(surface, ic, pts)
    if not muted:
        for r, w in [(8, 2), (13, 2)]:
            pygame.draw.arc(surface, ic,
                            pygame.Rect(mcx+2-r, mcy-r, r*2, r*2),
                            math.radians(-50), math.radians(50), w)
    else:
        xc = (255, 110, 90)
        pygame.draw.line(surface, xc, (mcx+5, mcy-9), (mcx+15, mcy+9), 3)
        pygame.draw.line(surface, xc, (mcx+15, mcy-9), (mcx+5, mcy+9), 3)

    lbl = "ปิดเสียงอยู่" if muted else "เปิดเสียง"
    text(surface, lbl, FONT_XS, (190, 200, 220),
         (mute_rect.centerx, mute_rect.bottom + 8), center=True)
    buttons["mute"] = mute_rect
    return buttons


# ─────────────────────────────────────────────────────────────────────────────
# ร้านอัพเกรด (Shop)
# ─────────────────────────────────────────────────────────────────────────────

def draw_shop_menu(surface, vehicle, mouse_pos, game_mode="mission", unlocked_floor=1, active_tab="upgrades"):
    dim_overlay(surface, 185)
    cx = S.SCREEN_W // 2

    panel = pygame.Rect(cx - 245, 65, 490, 570)
    _panel(surface, panel, bg=(20, 22, 34), border=(65, 72, 110), alpha=248, radius=16)

    buttons = {}

    # แถบแท็บด้านบน
    if game_mode == "classic":
        tab_w = 142
        tab_gap = 8
        tab_x0 = panel.left + 18

        # แท็บ 1: อัปเกรดสถานะ
        tab_upg = pygame.Rect(tab_x0, panel.top + 16, tab_w, 36)
        is_upg = (active_tab == "upgrades")
        _panel(surface, tab_upg, bg=(50, 95, 155) if is_upg else (38, 42, 60),
               border=(90, 160, 255) if is_upg else (80, 95, 130), alpha=240, radius=8)
        draw_icon_wrench(surface, (tab_upg.left + 8, tab_upg.centery - 9, 18, 18))
        text(surface, "อัปเกรด", FONT_S, (255, 255, 255) if is_upg else (200, 210, 230),
             (tab_upg.centerx + 10, tab_upg.top + 9))
        buttons["tab_upgrades"] = tab_upg

        # แท็บ 2: ปลดล็อคชั้นความลึก
        tab_flr = pygame.Rect(tab_x0 + tab_w + tab_gap, panel.top + 16, tab_w, 36)
        is_flr = (active_tab == "floor")
        _panel(surface, tab_flr, bg=(175, 115, 30) if is_flr else (38, 42, 60),
               border=(255, 215, 60) if is_flr else (80, 95, 130), alpha=240, radius=8)
        draw_icon_lock(surface, (tab_flr.left + 8, tab_flr.centery - 9, 18, 18),
                       color=(255, 225, 90) if is_flr else (210, 220, 240))
        text(surface, "ปลดล็อคชั้น", FONT_S, (255, 255, 255) if is_flr else (200, 210, 230),
             (tab_flr.centerx + 10, tab_flr.top + 9))
        buttons["tab_floor"] = tab_flr

        # แท็บ 3: อู่แต่งรถ (Garage)
        tab_gar = pygame.Rect(tab_x0 + (tab_w + tab_gap) * 2, panel.top + 16, tab_w, 36)
        _panel(surface, tab_gar, bg=(38, 42, 60) if not tab_gar.collidepoint(mouse_pos) else (50, 55, 80),
               border=(80, 95, 130), alpha=240, radius=8)
        draw_icon_palette(surface, (tab_gar.left + 8, tab_gar.centery - 9, 18, 18))
        text(surface, "อู่แต่งรถ", FONT_S, (200, 210, 230), (tab_gar.centerx + 10, tab_gar.top + 9))
        buttons["tab_garage"] = tab_gar
    else:
        tab_upg = pygame.Rect(panel.left + 18, panel.top + 16, 218, 36)
        _panel(surface, tab_upg, bg=(50, 95, 155), border=(90, 160, 255), alpha=240, radius=8)
        draw_icon_wrench(surface, (tab_upg.left + 10, tab_upg.centery - 9, 18, 18))
        text(surface, "อัปเกรดสถานะ", FONT_S, (255, 255, 255), (tab_upg.centerx + 6, tab_upg.top + 9))

        tab_gar = pygame.Rect(panel.right - 236, panel.top + 16, 218, 36)
        _panel(surface, tab_gar, bg=(38, 42, 60) if not tab_gar.collidepoint(mouse_pos) else (50, 55, 80),
               border=(80, 95, 130), alpha=240, radius=8)
        draw_icon_palette(surface, (tab_gar.left + 10, tab_gar.centery - 9, 18, 18))
        text(surface, "อู่แต่งรถ (Garage)", FONT_S,
             (210, 220, 240) if not tab_gar.collidepoint(mouse_pos) else (255, 255, 255),
             (tab_gar.centerx + 6, tab_gar.top + 9))
        buttons["tab_garage"] = tab_gar

    pygame.draw.line(surface, (50, 55, 80),
                      (panel.left + 20, panel.top + 60), (panel.right - 20, panel.top + 60), 1)

    # แถวเหรียญของคุณ
    coin_icon = pygame.transform.smoothscale(assets.get_image("res_coin"), (20, 20))
    surface.blit(coin_icon, (cx - 100, panel.top + 68))
    text(surface, f"เหรียญของคุณ: {vehicle.coins:,}", FONT_M, (255, 215, 60),
         (cx - 74, panel.top + 68))

    # ==================== แท็บ 2: ปลดล็อคชั้นความลึก (Classic Floor Unlock) ====================
    if game_mode == "classic" and active_tab == "floor":
        next_floor = unlocked_floor + 1
        next_info = S.get_floor_info(next_floor)
        cur_info = S.get_floor_info(unlocked_floor)
        cost = next_info["unlock_cost"]
        can_unlock = (vehicle.coins >= cost)

        # การ์ดชั้นถัดไป
        card = pygame.Rect(panel.left + 18, panel.top + 98, panel.w - 36, 178)
        _panel(surface, card, bg=(32, 28, 24) if can_unlock else (26, 26, 36),
               border=(255, 215, 60) if can_unlock else (75, 75, 100), alpha=240, radius=12)

        draw_icon_lock(surface, (card.left + 14, card.top + 14, 22, 22),
                       color=(255, 215, 60) if can_unlock else (210, 95, 95))
        text(surface, f"ชั้นถัดไป: ชั้นที่ {next_floor} - {next_info['name']}", FONT_M, (255, 235, 120),
             (card.left + 44, card.top + 14), max_w=card.w - 55)

        text(surface, f"ความลึก: {next_info['min_depth']} - {next_info['max_depth']} เมตร  (ชั้นปัจจุบันปลดล็อคถึง {cur_info['max_depth']}ม.)",
             FONT_S, (120, 215, 255), (card.left + 16, card.top + 46), max_w=card.w - 32)
        text(surface, next_info["desc"], FONT_XS, (200, 210, 230),
             (card.left + 16, card.top + 72), max_w=card.w - 32)

        cost_col = (255, 215, 60) if can_unlock else (245, 110, 110)
        cost_lbl = f"ค่าปลดล็อค: {cost:,} เหรียญ" if can_unlock else f"ค่าปลดล็อค: {cost:,} เหรียญ  (ขาดอีก {cost - vehicle.coins:,} เหรียญ)"
        text(surface, cost_lbl, FONT_S, cost_col, (card.left + 16, card.top + 98), max_w=card.w - 32)

        # ปุ่มปลดล็อค
        btn_unlock = pygame.Rect(card.left + 16, card.top + 122, card.w - 32, 42)
        if can_unlock:
            button(surface, btn_unlock, f"✨ ปลดล็อคชั้นที่ {next_floor}  ({cost:,} เหรียญ)",
                   FONT_M, base=(40, 150, 75), hover=btn_unlock.collidepoint(mouse_pos))
        else:
            button(surface, btn_unlock, f"เหรียญยังไม่พอ  (ต้องการ {cost:,} เหรียญ)",
                   FONT_M, base=(65, 55, 60), hover=btn_unlock.collidepoint(mouse_pos))
        buttons["unlock_floor"] = btn_unlock

        # รายการทำเนียบชั้นความลึก
        list_rect = pygame.Rect(panel.left + 18, panel.top + 288, panel.w - 36, 216)
        _panel(surface, list_rect, bg=(24, 26, 38), border=(50, 56, 78), radius=12)
        text(surface, "ทำเนียบชั้นความลึกทั้งหมด (Floor Directory)", FONT_S, (210, 225, 250),
             (list_rect.centerx, list_rect.top + 10), center=True)

        for i, fc in enumerate(S.CLASSIC_FLOORS[:6]):
            row_y = list_rect.top + 36 + i * 28
            f_num = fc["floor"]
            is_unlocked = (f_num <= unlocked_floor)

            f_col = (110, 245, 130) if is_unlocked else (160, 170, 190)
            if is_unlocked:
                draw_icon_check(surface, (list_rect.left + 20, row_y + 9), 14)
                status_txt = "✓ ปลดล็อคแล้ว"
                status_col = (110, 245, 130)
            else:
                draw_icon_lock(surface, (list_rect.left + 13, row_y + 2, 14, 14), (170, 150, 120))
                status_txt = f"🔒 ล็อค ({fc['unlock_cost']:,} เหรียญ)"
                status_col = (235, 155, 80)

            text(surface, f"ชั้น {f_num}: {fc['name'][:16]} ({fc['min_depth']}-{fc['max_depth']}ม.)",
                 FONT_XS, f_col, (list_rect.left + 36, row_y + 2), max_w=240)
            text(surface, status_txt, FONT_XS, status_col, (list_rect.right - 14, row_y + 2), right=True)

        fuel_cost = 25
        can_refuel = (vehicle.coins >= fuel_cost and vehicle.energy < vehicle.max_energy)
        refuel_rect = pygame.Rect(panel.left + 20, panel.bottom - 46, 240, 36)
        if vehicle.energy >= vehicle.max_energy:
            r_lbl = "⛽ พลังงานเต็มแล้ว"
            r_bg = (40, 48, 55)
        elif vehicle.coins >= fuel_cost:
            r_lbl = f"⛽ แอร์ดรอปน้ำมัน ({fuel_cost} G)"
            r_bg = (30, 110, 145)
        else:
            r_lbl = f"⛽ แอร์ดรอปน้ำมัน ({fuel_cost} G)"
            r_bg = (55, 45, 50)
        button(surface, refuel_rect, r_lbl, FONT_S, base=r_bg,
               hover=can_refuel and refuel_rect.collidepoint(mouse_pos))
        buttons["emergency_refuel"] = refuel_rect

        close_rect = pygame.Rect(panel.right - 180, panel.bottom - 46, 160, 36)
        button(surface, close_rect, "ปิด  (B / ESC)", FONT_S, base=(55, 58, 80),
               hover=close_rect.collidepoint(mouse_pos))
        buttons["close"] = close_rect
        return buttons

    # ==================== แท็บ 1: อัปเกรดสถานะรถขุด (Upgrades) ====================
    y = panel.top + 98

    for key in ("capacity", "energy", "power", "speed"):
        cfg  = S.UPGRADES[key]
        lv   = vehicle.levels[key]
        cost = vehicle.upgrade_cost(key)
        can  = vehicle.can_upgrade(key)

        row_rect = pygame.Rect(panel.left + 16, y, panel.w - 32, 86)
        row_bg = (32, 35, 50) if not can else (28, 40, 38)
        _panel(surface, row_rect, bg=row_bg, border=(55, 60, 82), alpha=230, radius=12)

        ibox = pygame.Rect(row_rect.left + 14, row_rect.top + 12, 36, 36)
        _panel(surface, ibox, bg=(20, 24, 36), border=(55, 64, 88), alpha=220, radius=8)
        if key == "capacity":
            draw_icon_cargo(surface, ibox.inflate(-8, -8), (240, 190, 60))
        elif key == "energy":
            draw_icon_energy(surface, ibox.inflate(-8, -8), (255, 205, 40))
        elif key == "power":
            draw_icon_power(surface, ibox.inflate(-8, -8), (140, 220, 255))
        elif key == "speed":
            draw_icon_speed(surface, ibox.inflate(-8, -8), (90, 230, 140))

        # ชื่ออัปเกรด
        text(surface, cfg["name"], FONT_M, (235, 240, 255),
             (row_rect.left + 58, row_rect.top + 10), max_w=200)

        # จุดแสดงระดับเลเวลทรงเพชร
        max_lv = cfg["max_level"]
        pip_x  = row_rect.left + 58
        pip_y  = row_rect.top + 38
        for i in range(max_lv):
            draw_level_pip(surface, pip_x + i * 18 + 7, pip_y + 4, size=12,
                           filled=(i < lv), color=(255, 205, 50))

        # ราคา / สถานะ
        if cost is None:
            info_txt = "MAX LEVEL"
            info_col = (110, 225, 130)
        elif can:
            info_txt = f"{cost:,} เหรียญ"
            info_col = (255, 215, 60)
        else:
            info_txt = f"{cost:,} เหรียญ  (ไม่พอ)"
            info_col = (210, 110, 110)
        text(surface, info_txt, FONT_S, info_col,
             (row_rect.left + 58, row_rect.top + 56), max_w=200)

        # ปุ่มซื้อ
        base_col = (38, 145, 72) if can else (55, 55, 70)
        brect = pygame.Rect(row_rect.right - 96, row_rect.top + 20, 82, 46)
        btn_lbl = "ซื้อ" if cost is not None else "MAX"
        button(surface, brect, btn_lbl, FONT_M, base=base_col,
               hover=can and brect.collidepoint(mouse_pos))
        buttons[key] = brect
        y += 94

    # แบนเนอร์แจ้งเตือนปลดล็อคชั้น (โหมดคลาสสิก)
    if game_mode == "classic":
        next_floor = unlocked_floor + 1
        next_cost = S.get_floor_info(next_floor)["unlock_cost"]
        can_flr = (vehicle.coins >= next_cost)
        teaser_rect = pygame.Rect(panel.left + 16, y + 4, panel.w - 32, 38)
        _panel(surface, teaser_rect, bg=(42, 34, 20) if can_flr else (26, 28, 40),
               border=(255, 215, 60) if can_flr else (65, 75, 100), radius=8)
        draw_icon_lock(surface, (teaser_rect.left + 10, teaser_rect.centery - 8, 16, 16),
                       color=(255, 215, 60) if can_flr else (200, 210, 230))
        t_msg = f"ชั้นถัดไป: ชั้น {next_floor} ({next_cost:,} เหรียญ) -> พร้อมปลดล็อค! คลิกแท็บ 'ปลดล็อคชั้น'" if can_flr else f"ชั้นถัดไป: ชั้น {next_floor} ({next_cost:,} เหรียญ) -> คลิกแท็บ 'ปลดล็อคชั้น'"
        t_col = (255, 235, 140) if can_flr else (190, 205, 230)
        text(surface, t_msg, FONT_XS, t_col, (teaser_rect.left + 32, teaser_rect.centery - 7), max_w=teaser_rect.w - 40)

    fuel_cost = 25
    can_refuel = (vehicle.coins >= fuel_cost and vehicle.energy < vehicle.max_energy)
    refuel_rect = pygame.Rect(panel.left + 20, panel.bottom - 46, 240, 36)
    if vehicle.energy >= vehicle.max_energy:
        r_lbl = "⛽ พลังงานเต็มแล้ว"
        r_bg = (40, 48, 55)
    elif vehicle.coins >= fuel_cost:
        r_lbl = f"⛽ แอร์ดรอปน้ำมัน ({fuel_cost} G)"
        r_bg = (30, 110, 145)
    else:
        r_lbl = f"⛽ แอร์ดรอปน้ำมัน ({fuel_cost} G)"
        r_bg = (55, 45, 50)
    button(surface, refuel_rect, r_lbl, FONT_S, base=r_bg,
           hover=can_refuel and refuel_rect.collidepoint(mouse_pos))
    buttons["emergency_refuel"] = refuel_rect

    close_rect = pygame.Rect(panel.right - 180, panel.bottom - 46, 160, 36)
    button(surface, close_rect, "ปิด  (B / ESC)", FONT_S, base=(55, 58, 80),
           hover=close_rect.collidepoint(mouse_pos))
    buttons["close"] = close_rect
    return buttons


# ─────────────────────────────────────────────────────────────────────────────
# หน้าต่างวิธีเล่นและปุ่มควบคุม (How to Play & Controls Modal)
# ─────────────────────────────────────────────────────────────────────────────

def draw_how_to_play(surface, mouse_pos):
    """หน้าต่างวิธีเล่นและปุ่มควบคุมทั้งหมด (How to Play & Controls Modal)"""
    dim_overlay(surface, 225)
    cx = S.SCREEN_W // 2

    panel = pygame.Rect(25, 20, 670, 770)
    _panel(surface, panel, bg=(18, 22, 34), border=(65, 80, 125), alpha=252, radius=18)

    # ส่วนหัว
    draw_icon_help(surface, (panel.left + 24, panel.top + 18, 28, 28), color=(255, 220, 75))
    text(surface, "วิธีเล่น & ปุ่มควบคุม (How to Play)", FONT_L, (255, 220, 75),
         (cx, panel.top + 20), center=True)
    text(surface, "คู่มือการควบคุมรถขุด เทคนิคขุดเจาะ และเป้าหมายเกม", FONT_XS,
         (175, 190, 220), (cx, panel.top + 45), center=True)
    pygame.draw.line(surface, (50, 60, 85),
                     (panel.left + 20, panel.top + 64), (panel.right - 20, panel.top + 64), 1)

    buttons = {}

    # ─── การ์ด 1: การเคลื่อนที่ & ขุดเจาะ ───
    c1 = pygame.Rect(panel.left + 16, panel.top + 72, panel.w - 32, 144)
    _panel(surface, c1, bg=(24, 28, 42), border=(55, 68, 98), alpha=235, radius=12)
    text(surface, "1. การเคลื่อนที่ & ขุดเจาะ (Movement & Digging)", FONT_M, (120, 215, 255),
         (c1.left + 16, c1.top + 9))

    # คีย์บอร์ด
    draw_key_badge(surface, "W", c1.left + 16, c1.top + 34, min_w=28, h=24)
    draw_key_badge(surface, "A", c1.left + 50, c1.top + 34, min_w=28, h=24)
    draw_key_badge(surface, "S", c1.left + 84, c1.top + 34, min_w=28, h=24)
    draw_key_badge(surface, "D", c1.left + 118, c1.top + 34, min_w=28, h=24)
    text(surface, "หรือ", FONT_XS, (160, 175, 200), (c1.left + 158, c1.top + 38))
    draw_key_badge(surface, "↑", c1.left + 188, c1.top + 34, min_w=26, h=24)
    draw_key_badge(surface, "←", c1.left + 218, c1.top + 34, min_w=26, h=24)
    draw_key_badge(surface, "↓", c1.left + 248, c1.top + 34, min_w=26, h=24)
    draw_key_badge(surface, "→", c1.left + 278, c1.top + 34, min_w=26, h=24)
    text(surface, "หรือ  🖱️ คลิกเมาส์ค้างตามทิศทาง", FONT_XS, (190, 210, 235), (c1.left + 320, c1.top + 38))

    text(surface, "• W / ↑ : เร่งไอพ่นบินขึ้นสู่ผิวดิน (Thrust Up) และสะสมพลังงานศักย์ Ep สำหรับ Turbo",
         FONT_XS, (220, 230, 245), (c1.left + 16, c1.top + 66))
    text(surface, "• S / ↓ : เจาะลงใต้ดิน (Drill Down) มุ่งสู่ชั้นหินลึกและขุมทรัพย์",
         FONT_XS, (220, 230, 245), (c1.left + 16, c1.top + 86))
    text(surface, "• A / ← และ D / → : เคลื่อนที่ไปทางซ้าย และ ขวา",
         FONT_XS, (220, 230, 245), (c1.left + 16, c1.top + 106))
    text(surface, "💡 การขุด: รถจะเจาะทำลายดินและหินอัตโนมัติเมื่อเคลื่อนที่ชนบล็อก!",
         FONT_XS, (255, 225, 120), (c1.left + 16, c1.top + 125))

    # ─── การ์ด 2: ระบบเทอร์โบ ───
    c2 = pygame.Rect(panel.left + 16, c1.bottom + 8, panel.w - 32, 126)
    _panel(surface, c2, bg=(32, 26, 22), border=(160, 110, 45), alpha=235, radius=12)
    text(surface, "2. ระบบเทอร์โบ & พุ่งดิ่งเจาะแรง (Turbo Boost & Slam)", FONT_M, (255, 195, 60),
         (c2.left + 16, c2.top + 9))

    draw_key_badge(surface, "Shift", c2.left + 16, c2.top + 34, min_w=58, h=24, active=True)
    text(surface, "หรือ", FONT_XS, (160, 175, 200), (c2.left + 82, c2.top + 38))
    draw_key_badge(surface, "Spacebar", c2.left + 112, c2.top + 34, min_w=78, h=24, active=True)
    text(surface, "⚡ กดขณะเคลื่อนที่เพื่อระเบิดพลังเทอร์โบ!", FONT_XS, (255, 235, 140), (c2.left + 202, c2.top + 38))

    text(surface, "• สะสมชาร์จ: บินขึ้นสู่ที่สูงจะสะสมพลังงานศักย์ Ep (หลอดชาร์จรอบตัวรถ)",
         FONT_XS, (240, 225, 210), (c2.left + 16, c2.top + 66))
    text(surface, "• พุ่งทะยานเร็วกว่าเดิม 2.6 เท่า (+160% Speed) ประหยัดเวลาข้ามอุโมงค์ยาว",
         FONT_XS, (240, 225, 210), (c2.left + 16, c2.top + 86))
    text(surface, "• พลังเจาะกระแทกพื้น (Ground Slam) แรงขึ้น 3.0 เท่า ทะลวงหินหนาได้ในพริบตา!",
         FONT_XS, (255, 215, 110), (c2.left + 16, c2.top + 106))

    # ─── การ์ด 3: ระบบโดรน & วิทยุร้านค้า ───
    c3 = pygame.Rect(panel.left + 16, c2.bottom + 8, panel.w - 32, 126)
    _panel(surface, c3, bg=(22, 34, 38), border=(45, 130, 120), alpha=235, radius=12)
    text(surface, "3. โดรนขนส่ง & วิทยุร้านค้า [ R / B / E ]", FONT_M, (100, 235, 200),
         (c3.left + 16, c3.top + 9))

    draw_key_badge(surface, "R", c3.left + 16, c3.top + 34, min_w=28, h=24, active=True)
    text(surface, "โดรนขายแร่", FONT_XS, (255, 225, 110), (c3.left + 50, c3.top + 38))
    draw_key_badge(surface, "B", c3.left + 130, c3.top + 34, min_w=28, h=24, active=True)
    text(surface, "วิทยุร้านค้า", FONT_XS, (140, 225, 255), (c3.left + 164, c3.top + 38))
    draw_key_badge(surface, "E", c3.left + 248, c3.top + 34, min_w=28, h=24, active=True)
    text(surface, "ปลดล็อคชั้น / ร้านค้าบนดิน", FONT_XS, (200, 230, 220), (c3.left + 282, c3.top + 38))

    text(surface, "• กด [R] (หรือคลิกปุ่มจรวดบน HUD): เรียกดโรนมารับแร่ไปขายทันที ได้เงินทันใจโดยไม่ต้องขับกลับขึ้นมา!",
         FONT_XS, (215, 240, 235), (c3.left + 16, c3.top + 66))
    text(surface, "• กด [B] (หรือคลิกปุ่มร้านค้าบน HUD): เปิดวิทยุร้านค้า อัปเกรดรถ, ปลดล็อคชั้น และสั่งแอร์ดรอปน้ำมันฉุกเฉินได้ทุกที่",
         FONT_XS, (215, 240, 235), (c3.left + 16, c3.top + 86))
    text(surface, "• กด [E]: ปลดล็อคชั้นเมื่ออยู่ใกล้ประตู หรือเปิดร้านค้าเมื่อจอดหน้าร้านบนผิวดิน",
         FONT_XS, (215, 240, 235), (c3.left + 16, c3.top + 106))

    # ─── การ์ด 4: เคล็ดลับการเอาชีวิตรอด ───
    c4 = pygame.Rect(panel.left + 16, c3.bottom + 8, panel.w - 32, 150)
    _panel(surface, c4, bg=(26, 26, 38), border=(60, 70, 95), alpha=235, radius=12)
    text(surface, "4. เคล็ดลับการเอาชีวิตรอด & เป้าหมาย (Survival Tips)", FONT_M, (240, 240, 255),
         (c4.left + 16, c4.top + 9))

    text(surface, "⚡ ระวังพลังงานหมด! หากพลังงานหมดใต้ดิน รถจะสตาร์ทไม่ติดและจบเกม (กลับมาเติมที่บ้านฟรี)",
         FONT_XS, (255, 175, 120), (c4.left + 16, c4.top + 36))
    text(surface, "📦 ถังเก็บแร่ (Cargo): เมื่อถังเต็ม ให้นำแร่กลับมาขายที่บ้านเพื่อเปลี่ยนเป็นเหรียญทอง",
         FONT_XS, (220, 230, 245), (c4.left + 16, c4.top + 58))
    text(surface, "⛏️ อัปเกรดหัวขุด: หินแกรนิตในชั้นที่ 2 เป็นต้นไป ต้องใช้หัวขุด Lv.2 ขึ้นไปจึงจะเจาะเข้า",
         FONT_XS, (220, 230, 245), (c4.left + 16, c4.top + 80))
    text(surface, "🎮 คีย์ลัดอื่นๆ: [ESC] พักเกม  |  [H] หรือ [F1] เปิดคู่มือนี้  |  [F11] เต็มหน้าจอ",
         FONT_XS, (185, 205, 235), (c4.left + 16, c4.top + 102))
    text(surface, "🏆 เป้าหมาย: ขุดลึก ปลดล็อคชั้นความลึกไม่รู้จบ และสร้างรถขุดในฝันของคุณ!",
         FONT_XS, (255, 225, 110), (c4.left + 16, c4.top + 124))

    # ปุ่มปิด
    close_rect = pygame.Rect(cx - 130, c4.bottom + 12, 260, 42)
    button(surface, close_rect, "เข้าใจแล้ว  (ปิด E / ESC)", FONT_M, base=(40, 130, 75),
           hover=close_rect.collidepoint(mouse_pos))
    buttons["close"] = close_rect
    return buttons


# ─────────────────────────────────────────────────────────────────────────────
# อู่แต่งรถขุด (Garage & Customization Hangar)
# ─────────────────────────────────────────────────────────────────────────────

def draw_garage_menu(surface, vehicle, mouse_pos, active_tab="color"):
    dim_overlay(surface, 210)
    cx = S.SCREEN_W // 2

    panel = pygame.Rect(25, 45, 670, 715)
    _panel(surface, panel, bg=(18, 20, 32), border=(65, 75, 115), alpha=252, radius=18)

    # ส่วนหัว
    text(surface, "อู่แต่งรถขุด (Vehicle Hangar & Garage)", FONT_L, (240, 245, 255),
         (cx, panel.top + 24), center=True)
    text(surface, "เลือกสีตัวถัง, ประเภทรถขุด และหัวขุดพร้อมความสามารถพิเศษ", FONT_XS,
         (160, 175, 205), (cx, panel.top + 50), center=True)

    buttons = {}
    tab_y = panel.top + 72
    tab_w = 202

    tabs = [
        ("color", "สีตัวถัง (Colors)",    panel.left + 20),
        ("type",  "ตัวถังรถ (Chassis)",   panel.left + 234),
        ("drill", "หัวขุด (Drill Heads)", panel.left + 448),
    ]

    for tid, tlabel, tx in tabs:
        trect = pygame.Rect(tx, tab_y, tab_w, 36)
        is_active = (active_tab == tid)
        base_c = (55, 105, 170) if is_active else (34, 38, 54)
        border_c = (100, 180, 255) if is_active else (60, 68, 90)
        _panel(surface, trect, bg=base_c, border=border_c, alpha=240, radius=8)
        tc = (255, 255, 255) if is_active else (180, 190, 210)
        # Draw a small vector icon on the left of each tab
        icon_rect = (trect.left + 8, trect.centery - 9, 18, 18)
        if tid == "color":
            draw_icon_palette(surface, icon_rect)
        elif tid == "type":
            _draw_vehicle_silhouette_icon(surface, trect.left + 8, trect.centery - 7, tc)
        elif tid == "drill":
            draw_icon_power(surface, icon_rect, color=(200, 230, 255))
        text(surface, tlabel, FONT_S, tc, (trect.left + 30, trect.top + 9))
        buttons[f"tab_{tid}"] = trect

    content_y = tab_y + 46
    content_h = 525

    # ───────────────────────────
    # โซนซ้าย: แท่นโฮโลแกรมแสดงตัวอย่างรถสด + สถานะรวม
    # ───────────────────────────
    prev_w = 230
    prev_rect = pygame.Rect(panel.left + 20, content_y, prev_w, content_h)
    _panel(surface, prev_rect, bg=(14, 16, 25), border=(50, 60, 85), alpha=240, radius=14)

    ped_cx = prev_rect.centerx
    ped_cy = prev_rect.top + 80

    # วงแหวนโฮโลแกรมเรืองแสง
    pygame.draw.ellipse(surface, (25, 55, 90), (ped_cx - 56, ped_cy + 24, 112, 36))
    pygame.draw.ellipse(surface, (60, 170, 245), (ped_cx - 56, ped_cy + 24, 112, 36), 2)
    pygame.draw.circle(surface, (70, 190, 255, 60), (ped_cx, ped_cy + 42), 24, 1)

    # วาดตัวรถขยายใหญ่
    vtype = getattr(vehicle, "vehicle_type", "standard")
    vcol  = getattr(vehicle, "color_id", "yellow")
    dhead = getattr(vehicle, "drill_head", "spiral")

    body_surf = assets.get_image(f"vehicle_{vtype}_{vcol}")
    b_scaled = pygame.transform.smoothscale(body_surf, (70, 70))
    surface.blit(b_scaled, b_scaled.get_rect(center=(ped_cx, ped_cy)))

    # วาดหัวขุด
    drill_surf = assets.get_image(f"drill_{dhead}_down")
    d_scaled = pygame.transform.smoothscale(drill_surf, (36, 36))
    surface.blit(d_scaled, d_scaled.get_rect(center=(ped_cx, ped_cy + 36)))

    vtype_cfg = S.VEHICLE_TYPES.get(vtype, S.VEHICLE_TYPES["standard"])
    head_cfg  = S.DRILL_HEADS.get(dhead, S.DRILL_HEADS["spiral"])
    col_cfg   = S.VEHICLE_COLORS.get(vcol, S.VEHICLE_COLORS["yellow"])

    # ชื่อและป้ายความสามารถ
    text(surface, vtype_cfg["name"], FONT_M, (255, 255, 255), (ped_cx, ped_cy + 68), center=True, max_w=215)
    text(surface, f"สี: {col_cfg['name']}", FONT_XS, col_cfg["primary"], (ped_cx, ped_cy + 92), center=True)
    text(surface, head_cfg["name"], FONT_S, head_cfg["badge_color"], (ped_cx, ped_cy + 114), center=True, max_w=215)

    # แถบแสดงความสามารถพิเศษ
    ab_rect = pygame.Rect(prev_rect.left + 10, ped_cy + 134, prev_rect.w - 20, 26)
    pygame.draw.rect(surface, (*head_cfg["badge_color"], 40), ab_rect, border_radius=6)
    pygame.draw.rect(surface, head_cfg["badge_color"], ab_rect, 1, border_radius=6)
    text(surface, f"★ {head_cfg['ability_name']}", FONT_XS, (255, 225, 90), ab_rect.center, center=True, max_w=prev_rect.w - 24)

    # กล่องสเตตัสรถขุด — แต่ละแถวมีไอคอนเวกเตอร์ด้านซ้าย
    sy = ped_cy + 172
    stat_items = [
        ("energy",   f"{int(vehicle.max_energy)}",       (255, 175, 40)),
        ("cargo",    f"{vehicle.max_capacity} ช่อง",     (100, 215, 120)),
        ("speed",    f"{int(vehicle.speed)} px/s",       (85, 205, 255)),
        ("power",    f"{vehicle.power:.1f}/s",           (240, 220, 110)),
    ]
    stat_labels = {
        "energy": "พลังงาน",
        "cargo":  "ความจุถัง",
        "speed":  "ความเร็ว",
        "power":  "แรงเจาะ",
    }
    for skey, sval, scol in stat_items:
        sbox = pygame.Rect(prev_rect.left + 12, sy, prev_rect.w - 24, 30)
        _panel(surface, sbox, bg=(22, 26, 38), border=(45, 52, 72), alpha=200, radius=6)
        # ไอคอนด้านซ้าย
        ibox = (sbox.left + 4, sbox.top + 5, 20, 20)
        if skey == "energy":
            draw_icon_energy(surface, ibox, color=(255, 185, 40))
        elif skey == "cargo":
            draw_icon_cargo(surface, ibox, color=(100, 215, 120))
        elif skey == "speed":
            draw_icon_speed(surface, ibox, color=(85, 205, 255))
        elif skey == "power":
            draw_icon_power(surface, ibox, color=(230, 230, 240))
        text(surface, stat_labels[skey], FONT_XS, (185, 195, 215), (sbox.left + 28, sbox.top + 7))
        text(surface, sval, FONT_S, scol, (sbox.right - 8, sbox.top + 6), right=True)
        sy += 36

    # ───────────────────────────
    # โซนขวา: ตัวเลือกตามแท็บที่เลือก
    # ───────────────────────────
    right_w = panel.w - prev_w - 60
    right_rect = pygame.Rect(panel.left + 260, content_y, right_w, content_h)
    _panel(surface, right_rect, bg=(14, 16, 25), border=(50, 60, 85), alpha=240, radius=14)

    # 1. แท็บสีตัวถัง (Color)
    if active_tab == "color":
        draw_icon_palette(surface, (right_rect.left + 16, right_rect.top + 14, 20, 20))
        text(surface, "เลือกโทนสีตัวถังรถขุด (Select Vehicle Color)", FONT_M, (240, 245, 255),
             (right_rect.left + 40, right_rect.top + 16))

        c_keys = list(S.VEHICLE_COLORS.keys())
        card_w = 178
        card_h = 98
        start_x = right_rect.left + 14
        start_y = right_rect.top + 50

        for i, cid in enumerate(c_keys):
            c_info = S.VEHICLE_COLORS[cid]
            col_x = start_x + (i % 2) * (card_w + 14)
            col_y = start_y + (i // 2) * (card_h + 14)
            crect = pygame.Rect(col_x, col_y, card_w, card_h)

            is_sel = (vehicle.color_id == cid)
            is_hov = crect.collidepoint(mouse_pos)
            border_c = (255, 215, 60) if is_sel else ((90, 150, 220) if is_hov else (45, 52, 75))
            bg_c = (35, 42, 60) if is_sel else (22, 26, 38)
            _panel(surface, crect, bg=bg_c, border=border_c, alpha=235, radius=10)

            # วงกลมสวอชสีตัวถัง
            swatch_cx = crect.left + 36
            swatch_cy = crect.top + 36
            pygame.draw.circle(surface, c_info["dark"], (swatch_cx, swatch_cy), 22)
            pygame.draw.circle(surface, c_info["primary"], (swatch_cx, swatch_cy), 18)
            pygame.draw.circle(surface, c_info["highlight"], (swatch_cx - 4, swatch_cy - 4), 6)
            pygame.draw.circle(surface, (255, 255, 255), (swatch_cx, swatch_cy), 20, 2)

            # มินิพรีวิวรถ (sprite จริงจาก assets)
            vmini = assets.get_image(f"vehicle_{vehicle.vehicle_type}_{cid}")
            vmini_scaled = pygame.transform.smoothscale(vmini, (34, 34))
            surface.blit(vmini_scaled, (crect.right - 44, crect.top + 18))

            # ชื่อสี
            text(surface, c_info["name"], FONT_M, (255, 255, 255), (crect.left + 14, crect.top + 64))
            text(surface, c_info["name_en"], FONT_XS, (160, 170, 190), (crect.left + 14, crect.top + 80))

            if is_sel:
                draw_icon_check(surface, (crect.right - 18, crect.bottom - 18), 16)

            buttons[f"color_{cid}"] = crect

    # 2. แท็บประเภทตัวถังรถ (Chassis Type)
    elif active_tab == "type":
        _draw_vehicle_silhouette_icon(surface, right_rect.left + 16, right_rect.top + 14, (240, 245, 255))
        text(surface, "เลือกประเภทตัวถังรถขุด (Select Vehicle Chassis)", FONT_M, (240, 245, 255),
             (right_rect.left + 40, right_rect.top + 16))

        t_keys = list(S.VEHICLE_TYPES.keys())
        card_w = right_rect.w - 28
        card_h = 104
        start_y = right_rect.top + 50

        for i, vtid in enumerate(t_keys):
            t_info = S.VEHICLE_TYPES[vtid]
            card_y = start_y + i * (card_h + 12)
            card_rect = pygame.Rect(right_rect.left + 14, card_y, card_w, card_h)

            is_sel = (vehicle.vehicle_type == vtid)
            is_hov = card_rect.collidepoint(mouse_pos)
            border_c = t_info["badge_color"] if is_sel else ((110, 170, 240) if is_hov else (48, 56, 78))
            bg_c = (32, 40, 58) if is_sel else (20, 24, 36)
            _panel(surface, card_rect, bg=bg_c, border=border_c, alpha=235, radius=12)

            # มินิพรีวิวตัวถัง (sprite จริง)
            vmini = assets.get_image(f"vehicle_{vtid}_{vehicle.color_id}")
            vmini_scaled = pygame.transform.smoothscale(vmini, (52, 52))
            surface.blit(vmini_scaled, (card_rect.left + 14, card_rect.top + 16))

            # ชื่อ + ป้ายเด่น
            text(surface, t_info["name"], FONT_M, (255, 255, 255), (card_rect.left + 76, card_rect.top + 12))
            tag_rect = pygame.Rect(card_rect.left + 76, card_rect.top + 36, 120, 20)
            pygame.draw.rect(surface, (*t_info["badge_color"], 50), tag_rect, border_radius=4)
            pygame.draw.rect(surface, t_info["badge_color"], tag_rect, 1, border_radius=4)
            text(surface, t_info["tag"], FONT_XS, t_info["badge_color"], tag_rect.center, center=True)

            # คำอธิบายและโบนัส
            text(surface, t_info["desc"], FONT_XS, (180, 195, 220), (card_rect.left + 76, card_rect.top + 64), max_w=card_w - 90)

            if is_sel:
                draw_icon_check(surface, (card_rect.right - 22, card_rect.top + 24), 20)

            buttons[f"type_{vtid}"] = card_rect

    # 3. แท็บประเภทหัวขุด (Digging Heads & Abilities)
    elif active_tab == "drill":
        draw_icon_power(surface, (right_rect.left + 16, right_rect.top + 14, 20, 20), color=(200, 230, 255))
        text(surface, "เลือกหัวขุดและความสามารถพิเศษ (Drill Heads)", FONT_M, (240, 245, 255),
             (right_rect.left + 40, right_rect.top + 16))

        d_keys = list(S.DRILL_HEADS.keys())
        card_w = right_rect.w - 28
        card_h = 86
        start_y = right_rect.top + 46

        for i, dhid in enumerate(d_keys):
            d_info = S.DRILL_HEADS[dhid]
            card_y = start_y + i * (card_h + 8)
            card_rect = pygame.Rect(right_rect.left + 14, card_y, card_w, card_h)

            is_sel = (vehicle.drill_head == dhid)
            is_hov = card_rect.collidepoint(mouse_pos)
            border_c = d_info["badge_color"] if is_sel else ((110, 170, 240) if is_hov else (48, 56, 78))
            bg_c = (32, 40, 58) if is_sel else (20, 24, 36)
            _panel(surface, card_rect, bg=bg_c, border=border_c, alpha=235, radius=10)

            # มินิพรีวิวหัวสว่าน (sprite จริงจาก assets)
            dmini = assets.get_image(f"drill_{dhid}_down")
            dmini_scaled = pygame.transform.smoothscale(dmini, (40, 40))
            surface.blit(dmini_scaled, (card_rect.left + 16, card_rect.top + 14))

            # ชื่อหัวขุด + ตราความสามารถพิเศษ
            text(surface, d_info["name"], FONT_M, (255, 255, 255), (card_rect.left + 68, card_rect.top + 10))
            ab_tag = pygame.Rect(card_rect.left + 68, card_rect.top + 34, 180, 20)
            pygame.draw.rect(surface, (*d_info["badge_color"], 50), ab_tag, border_radius=4)
            pygame.draw.rect(surface, d_info["badge_color"], ab_tag, 1, border_radius=4)
            # ดาวไอคอนแทน "★" emoji
            draw_icon_star(surface, (ab_tag.left + 10, ab_tag.centery), 12, color=d_info["badge_color"])
            text(surface, d_info["ability_name"], FONT_XS, d_info["badge_color"], (ab_tag.left + 18, ab_tag.top + 3))

            # คำอธิบายคุณสมบัติ
            text(surface, d_info["desc"], FONT_XS, (185, 195, 220), (card_rect.left + 68, card_rect.top + 58), max_w=card_w - 90)

            if is_sel:
                draw_icon_check(surface, (card_rect.right - 22, card_rect.top + 22), 20)

            buttons[f"drill_{dhid}"] = card_rect

    # ปุ่มแถบล่างสุด
    by = panel.bottom - 46
    btn_apply = pygame.Rect(cx - 165, by, 155, 38)
    button(surface, btn_apply, "บันทึกและใช้", FONT_S, base=(40, 135, 75),
           hover=btn_apply.collidepoint(mouse_pos))
    draw_icon_check(surface, (btn_apply.left + 22, btn_apply.centery), 16)
    buttons["apply"] = btn_apply

    btn_back = pygame.Rect(cx + 10, by, 155, 38)
    button(surface, btn_back, "< กลับ", FONT_S, base=(110, 48, 55),
           hover=btn_back.collidepoint(mouse_pos))
    buttons["back"] = btn_back

    return buttons


# ─────────────────────────────────────────────────────────────────────────────
# หน้าจอจบเกม / ชนะ (Victory & Game Over)
# ─────────────────────────────────────────────────────────────────────────────

def draw_end_screen(surface, title, subtitle, vehicle, mouse_pos,
                    mission=None, color=(255, 215, 100)):
    surface.fill((18, 14, 26))
    for i in range(60):
        sx = (i * 113 + 20) % S.SCREEN_W
        sy = (i * 83 + 10) % S.SCREEN_H
        br = 80 + (i * 37) % 120
        pygame.draw.circle(surface, (br, br, min(255, br + 20)), (sx, sy), 1)

    cx = S.SCREEN_W // 2

    panel = pygame.Rect(cx - 260, 95, 520, 545)
    _panel(surface, panel, bg=(22, 18, 34), border=(80, 65, 120), alpha=245, radius=18)

    text(surface, title, FONT_XL, color, (cx, panel.top + 46), center=True)
    pygame.draw.line(surface, (65, 55, 95),
                      (panel.left + 30, panel.top + 76), (panel.right - 30, panel.top + 76), 1)
    text(surface, subtitle, FONT_M, (210, 215, 235),
         (cx, panel.top + 98), center=True, max_w=panel.w - 40)

    # กล่องสรุปภารกิจผสม
    y = panel.top + 130
    if mission:
        m_box = pygame.Rect(panel.left + 24, y, panel.w - 48, 114)
        _panel(surface, m_box, bg=mission.diff_info["bg_color"], border=mission.diff_info["border_color"], alpha=220, radius=10)

        # วงกลมสี = ระดับความยาก + ชื่อภารกิจ (แทน emoji badge)
        end_dot_col = mission.diff_info.get("dot_color", mission.diff_info["color"])
        pygame.draw.circle(surface, end_dot_col, (m_box.left + 18, m_box.top + 20), 7)
        pygame.draw.circle(surface, (255, 255, 255), (m_box.left + 18, m_box.top + 20), 7, 1)
        text(surface, f"ภารกิจ: {mission.title} ({mission.diff_info['badge']})",
             FONT_M, (255, 255, 255), (m_box.left + 32, m_box.top + 10), max_w=m_box.w - 40)

        # รายการเงื่อนไข
        gy = m_box.top + 38
        goals = mission.get_goals_status()
        for i, (key, label, is_met, cur, tgt, prog_txt) in enumerate(goals):
            gx = m_box.left + 14 if i % 2 == 0 else m_box.centerx + 4
            gy_curr = gy + (i // 2) * 28
            chk_col = (100, 240, 120) if is_met else (240, 90, 90)
            if is_met:
                draw_icon_check(surface, (gx + 8, gy_curr + 8), 14)
            else:
                draw_icon_cross(surface, (gx + 8, gy_curr + 8), 14)
            text(surface, prog_txt, FONT_S, chk_col, (gx + 22, gy_curr), max_w=m_box.w // 2 - 24)
        y += 128

    # สถิติรถขุด
    vtype_name = S.VEHICLE_TYPES.get(vehicle.vehicle_type, S.VEHICLE_TYPES["standard"])["name"]
    dhead_name = S.DRILL_HEADS.get(vehicle.drill_head, S.DRILL_HEADS["spiral"])["name"]

    stats = [
        f"เหรียญที่ครอบครอง: {vehicle.coins:,}",
        f"รถขุด: {vtype_name}   หัวขุด: {dhead_name}",
        f"หัวขุด Lv.{vehicle.levels['power']}   ถัง Lv.{vehicle.levels['capacity']}   พลังงาน Lv.{vehicle.levels['energy']}",
    ]
    for s in stats:
        text(surface, s, FONT_S, (195, 205, 225), (cx, y), center=True, max_w=panel.w - 40)
        y += 28

    buttons = {}
    y = panel.bottom - 105

    # "Back to menu" — diamond icon (treasure = victory theme)
    r_menu = pygame.Rect(cx - 150, y, 300, 44)
    button(surface, r_menu, "กลับเมนูหลัก", base=(40, 90, 160),
           hover=r_menu.collidepoint(mouse_pos))
    dia_icon = pygame.transform.smoothscale(assets.get_image("res_diamond"), (22, 22))
    surface.blit(dia_icon, (r_menu.left + 10, r_menu.centery - 11))
    buttons["menu"] = r_menu
    y += 52

    # "Quit" — red cross icon
    r_quit = pygame.Rect(cx - 150, y, 300, 44)
    button(surface, r_quit, "ออกจากเกม", base=(120, 42, 42),
           hover=r_quit.collidepoint(mouse_pos))
    draw_icon_cross(surface, (r_quit.left + 22, r_quit.centery), 18, color=(220, 60, 60))
    buttons["quit"] = r_quit

    return buttons

