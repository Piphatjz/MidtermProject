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


def draw_icon_drone(surface, rect, color=(120, 240, 170)):
    """ไอคอนโดรน/จรวดขนส่งแร่ (Cargo Drone / Rocket Icon)"""
    x, y, w, h = rect
    cx, cy = x + w // 2, y + h // 2
    # ลำตัวจรวด/โดรนพุ่งขึ้น
    pts = [(cx, y + 1), (x + w - 2, cy + 2), (cx + 2, y + h - 2), (cx - 2, y + h - 2), (x + 2, cy + 2)]
    pygame.draw.polygon(surface, color, pts)
    pygame.draw.polygon(surface, (255, 255, 255), pts, 1)
    # ไอพ่นด้านล่าง
    pygame.draw.line(surface, (255, 200, 60), (cx, y + h - 2), (cx, y + h), 2)


def draw_icon_radio(surface, rect, color=(130, 210, 255)):
    """ไอคอนวิทยุสื่อสาร/ร้านค้าดาวเทียม (Radio Antenna Icon)"""
    x, y, w, h = rect
    cx, cy = x + w // 2, y + h // 2
    # ฐานวิทยุ
    pygame.draw.rect(surface, color, (x + 2, cy, w - 4, h // 2 - 1), border_radius=2)
    # เสาอากาศและคลื่นสัญญาณ
    pygame.draw.line(surface, (255, 255, 255), (cx, cy), (cx, y + 2), 2)
    pygame.draw.circle(surface, (255, 220, 80), (cx, y + 2), 2)


def draw_icon_depth(surface, rect, color=(110, 210, 255)):
    """ไอคอนลูกศรวัดระดับความลึก (Depth Arrow Icon)"""
    x, y, w, h = rect
    cx = x + w // 2
    pygame.draw.line(surface, color, (cx, y + 2), (cx, y + h - 4), 2)
    pygame.draw.polygon(surface, color, [(x + 2, y + h - 7), (x + w - 2, y + h - 7), (cx, y + h - 1)])
    pygame.draw.line(surface, (200, 240, 255), (x + 3, y + 2), (x + w - 3, y + 2), 1)


def draw_icon_dive(surface, rect, color=(255, 190, 50)):
    """ไอคอนพุ่งดิ่งกระแทกพื้น (Gravity Slam / Dive Icon)"""
    x, y, w, h = rect
    cx = x + w // 2
    # หัวลูกศรคู่พุ่งลงพร้อมคลื่นกระแทก
    pygame.draw.polygon(surface, color, [(x + 2, y + 2), (x + w - 2, y + 2), (cx, y + h - 4)])
    pygame.draw.polygon(surface, (255, 245, 160), [(x + 4, y + 3), (x + w - 4, y + 3), (cx, y + h - 6)], 1)
    pygame.draw.line(surface, (255, 120, 40), (x + 1, y + h - 2), (x + w - 1, y + h - 2), 2)


def draw_icon_tier(surface, rect, color=(190, 145, 255)):
    """ไอคอนโล่ระดับ Tier รถขุด (Vehicle Tier Shield Icon)"""
    x, y, w, h = rect
    cx = x + w // 2
    pts = [
        (cx, y + 1),
        (x + w - 2, y + 4),
        (x + w - 3, y + h - 6),
        (cx, y + h - 1),
        (x + 3, y + h - 6),
        (x + 2, y + 4),
    ]
    pygame.draw.polygon(surface, color, pts)
    pygame.draw.polygon(surface, (240, 225, 255), pts, 1)


def draw_icon_goal(surface, goal_key, rect):
    """วาดไอคอนประจำเป้าหมายภารกิจทั้ง 8 ชนิด (ใช้ Sprite จริงหรือ Vector Icon ไม่ใช้ Emoji)"""
    x, y, w, h = rect
    sprite_map = {
        "gold": "res_gold",
        "diamonds": "res_diamond",
        "coins": "res_coin",
        "fuel": "res_fuel",
    }
    if goal_key in sprite_map:
        icon_s = pygame.transform.smoothscale(assets.get_image(sprite_map[goal_key]), (w, h))
        surface.blit(icon_s, (x, y))
    elif goal_key == "depth":
        draw_icon_depth(surface, rect, color=(110, 215, 255))
    elif goal_key == "drill_lv":
        draw_icon_power(surface, rect, color=(140, 225, 255))
    elif goal_key == "tier":
        draw_icon_tier(surface, rect, color=(200, 150, 255))
    elif goal_key == "dives":
        draw_icon_dive(surface, rect, color=(255, 195, 55))
    else:
        draw_icon_star(surface, (x + w // 2, y + h // 2), min(w, h))



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
    """โซนซ้าย: ทรัพยากรในถังขุด พร้อมแสดงมูลค่ารวมของแร่ในถัง"""
    draw_icon_cargo(surface, (14, 8, 16, 16), (170, 190, 220))
    text(surface, "แร่ในถัง", FONT_XS, (170, 190, 220), (35, 9))
    val = vehicle.cargo_value()
    if val > 0:
        text(surface, f"+{val:,} G", FONT_XS, (255, 220, 80), (_Z_LEFT_W - 10, 9), right=True)

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
    """โซนกลาง: เหรียญสะสม | ความลึก | หลอดพลังงาน | หลอดความจุถัง"""
    x0 = _Z_LEFT_W + 12
    bar_w = 226

    # แถวบน: เหรียญ (ซ้าย) + ความลึกและระดับ Tier (ขวา)
    coin_icon = pygame.transform.smoothscale(assets.get_image("res_coin"), (18, 18))
    surface.blit(coin_icon, (x0, 7))
    text(surface, f"{vehicle.coins:,} G", FONT_S, (255, 215, 60), (x0 + 22, 8), max_w=125)

    depth_txt = f"{depth}ม. (Tier {vehicle.overall_tier()})"
    dw = FONT_XS.size(depth_txt)[0]
    draw_icon_depth(surface, (x0 + bar_w - dw - 14, 9, 11, 13), color=(140, 215, 245))
    text(surface, depth_txt, FONT_XS, (140, 215, 245), (x0 + bar_w, 8), right=True)

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
    cap_lbl = "ถังเต็ม! กลับฐานขายแร่" if vehicle.cargo_full() else f"ถัง: {vehicle.cargo_count} / {vehicle.max_capacity}"
    cap_col = (255, 140, 130) if vehicle.cargo_full() else (225, 245, 225)
    text(surface, cap_lbl, FONT_XS, cap_col,
         (x0 + bar_w // 2, 70), center=True, shadow=True)


def _hud_zone_right(surface, vehicle, mission=None, game_mode="mission", unlocked_floor=1, depth=0):
    """โซนขวา: ภารกิจผสมประจำตา (Quest Tracker) หรือแถบความคืบหน้าโหมดคลาสสิก (Floor Tracker)"""
    panel = pygame.Rect(_Z_LEFT_W + _Z_CENTER_W + 8, 6, _Z_RIGHT_W - 16, 78)

    # ---------- โหมดคลาสสิก: ติดตามการปลดล็อคชั้นความลึก (Floor Unlock Tracker) ----------
    if game_mode == "classic":
        max_flr = getattr(S, "MAX_CLASSIC_FLOORS", 7)
        # คำนวณชั้นปัจจุบันตามความลึก
        cur_floor = 1
        for fc in getattr(S, "CLASSIC_FLOORS", []):
            if depth >= fc["min_depth"]:
                cur_floor = fc["floor"]

        all_unlocked = (unlocked_floor >= max_flr)

        if all_unlocked:
            _panel(surface, panel, bg=(34, 30, 20), border=(255, 215, 60), alpha=235, radius=10)
            draw_icon_star(surface, (panel.left + 16, panel.top + 16), 16)
            text(surface, f"ชั้นที่ {cur_floor} (ไร้ขีดจำกัด)", FONT_S, (255, 220, 80), (panel.left + 36, panel.top + 7))
            text(surface, "ปลดล็อคครบทุกชั้นแล้ว!", FONT_S, (120, 245, 150), (panel.left + 14, panel.top + 33))
            text(surface, "ขุดสำรวจใต้พิภพได้อย่างไร้สิ้นสุด", FONT_XS, (190, 205, 230), (panel.left + 14, panel.top + 57))
            return

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
        text(surface, f"ปลดล็อคถึงชั้น {unlocked_floor}/{max_flr}", FONT_S, (235, 240, 255), (panel.left + 82, panel.top + 7), max_w=panel.w - 88)

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
        positions = [
            (panel.left + 10,  panel.top + 32),
            (panel.left + 136, panel.top + 32),
            (panel.left + 10,  panel.top + 54),
            (panel.left + 136, panel.top + 54),
        ]
        for idx, (gkey, glabel, is_met, cur, tgt, prog_txt) in enumerate(goals[:4]):
            gx, gy_row = positions[idx]
            col_txt = (100, 240, 125) if is_met else (220, 228, 242)
            if is_met:
                draw_icon_check(surface, (gx + 7, gy_row + 8), 13)
            else:
                draw_icon_goal(surface, gkey, (gx, gy_row + 1, 14, 14))
            text(surface, prog_txt, FONT_XS, col_txt, (gx + 17, gy_row), max_w=104)
        if len(goals) <= 3:
            text(surface, "(ครบแล้วกลับบ้าน)", FONT_XS, (145, 160, 185),
                 (panel.left + 136, panel.top + 54), max_w=118)


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


def draw_toast(surface, msg, timer, y=None):
    if timer <= 0:
        return
    alpha = min(255, int(timer * 255))
    tw, th = FONT_M.size(msg)
    max_w = S.SCREEN_W - 40
    w = min(tw + 48, max_w)
    toast_y = y if y is not None else (S.HUD_H + 34)
    rect = pygame.Rect((S.SCREEN_W - w) // 2, toast_y, w, 40)

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
        ("E", "ร้านค้า / ปลดล็อคชั้น"),
        ("H", "วิธีเล่น"),
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

        # แสดงเป้าหมายแต่ละข้อพร้อมไอคอนเฉพาะตามประเภทเป้าหมายทั้ง 8 ชนิด
        gy = card_y + 146
        for goal_key, target in mission.goals.items():
            label = missions.format_goal_label(goal_key, target)
            draw_icon_goal(surface, goal_key, (card_x + 14, gy + 1, 16, 16))
            text(surface, label, FONT_S, (230, 235, 245), (card_x + 36, gy), max_w=card_w - 46)
            gy += 32

        # ปุ่มเลือกแผน
        btn_rect = pygame.Rect(card_x + 14, card_rect.bottom - 52, card_w - 28, 40)
        button(surface, btn_rect, "รับภารกิจนี้", FONT_M, base=diff_info["border_color"],
               hover=btn_rect.collidepoint(mouse_pos))
        buttons[f"select_{i}"] = btn_rect

    # ปุ่มการทำงานด้านล่าง (3 ปุ่ม จัดวางสมดุล)
    by = panel.bottom - 54
    btn_random = pygame.Rect(panel.left + 24, by, 185, 40)
    button(surface, btn_random, "สุ่มภารกิจ", FONT_S, base=(50, 80, 130),
           hover=btn_random.collidepoint(mouse_pos))
    draw_icon_dice(surface, (btn_random.left + 12, btn_random.centery - 8, 16, 16))
    buttons["random"] = btn_random

    btn_reroll = pygame.Rect(panel.left + 225, by, 185, 40)
    button(surface, btn_reroll, "สุ่มชุดใหม่", FONT_S, base=(75, 65, 110),
           hover=btn_reroll.collidepoint(mouse_pos))
    draw_icon_refresh(surface, (btn_reroll.left + 20, btn_reroll.centery), 16)
    buttons["reroll"] = btn_reroll

    btn_back = pygame.Rect(panel.right - 165, by, 140, 40)
    button(surface, btn_back, "< กลับ", FONT_S, base=(110, 45, 50),
           hover=btn_back.collidepoint(mouse_pos))
    buttons["back"] = btn_back

    return buttons


# ─────────────────────────────────────────────────────────────────────────────
# ไอคอนลำโพง (Speaker Icon Helper)
# ─────────────────────────────────────────────────────────────────────────────

def draw_icon_speaker(surface, center, size=22, muted=False, color=None):
    mcx, mcy = center
    ic = color if color else (255, 255, 255)
    scale = size / 22.0
    pts = [
        (mcx - int(8 * scale), mcy - int(6 * scale)),
        (mcx - int(3 * scale), mcy - int(6 * scale)),
        (mcx + int(2 * scale), mcy - int(11 * scale)),
        (mcx + int(2 * scale), mcy + int(11 * scale)),
        (mcx - int(3 * scale), mcy + int(6 * scale)),
        (mcx - int(8 * scale), mcy + int(6 * scale))
    ]
    pygame.draw.polygon(surface, ic, pts)
    if not muted:
        for r, w in [(int(8 * scale), max(1, int(2 * scale))), (int(13 * scale), max(1, int(2 * scale)))]:
            pygame.draw.arc(surface, ic,
                            pygame.Rect(mcx + int(2 * scale) - r, mcy - r, r * 2, r * 2),
                            math.radians(-50), math.radians(50), w)
    else:
        xc = color if color else (255, 110, 90)
        pygame.draw.line(surface, xc, (mcx + int(5 * scale), mcy - int(9 * scale)),
                         (mcx + int(15 * scale), mcy + int(9 * scale)), max(2, int(3 * scale)))
        pygame.draw.line(surface, xc, (mcx + int(15 * scale), mcy - int(9 * scale)),
                         (mcx + int(5 * scale), mcy + int(9 * scale)), max(2, int(3 * scale)))


# ─────────────────────────────────────────────────────────────────────────────
# เมนูหลัก (Main Menu - 4 Main Buttons: Play, Load, Setting, Exit)
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
    surface.blit(sh, sh.get_rect(center=(cx + 3, 141)))
    text(surface, "DIG & TREASURE", FONT_XL, (255, 215, 60), (cx, 138), center=True)
    text(surface, "ขุดดิน ● หาสมบัติ ● ปลดล็อคชั้นความลึก ● ปรับแต่งรถขุด", FONT_M, (180, 210, 255),
         (cx, 188), center=True)

    pygame.draw.line(surface, (55, 80, 130), (cx - 180, 212), (cx + 180, 212), 1)

    buttons = {}
    btn_w = 340
    btn_h = 52
    gap = 16
    y = 246

    # 1. "Play" (เล่นเกม)
    r_play = pygame.Rect(cx - btn_w // 2, y, btn_w, btn_h)
    button(surface, r_play, "เล่นเกม  (Play)", FONT_L, base=(40, 130, 75),
           hover=r_play.collidepoint(mouse_pos))
    pcx, pcy = r_play.left + 26, r_play.centery
    pygame.draw.polygon(surface, (180, 255, 180), [(pcx - 8, pcy - 10), (pcx + 10, pcy), (pcx - 8, pcy + 10)])
    buttons["play"] = r_play
    y += btn_h + gap

    # 2. "Load" (โหลดเกมจาก 5 สล็อต)
    r_load = pygame.Rect(cx - btn_w // 2, y, btn_w, btn_h)
    base_load = (45, 95, 160) if has_save else (45, 55, 75)
    button(surface, r_load, "โหลดเกม  (Load)", FONT_L, base=base_load,
           hover=r_load.collidepoint(mouse_pos))
    dia_icon = pygame.transform.smoothscale(assets.get_image("res_diamond"), (22, 22))
    surface.blit(dia_icon, (r_load.left + 16, r_load.centery - 11))
    buttons["load"] = r_load
    buttons["load_game"] = r_load
    buttons["continue"] = r_load
    y += btn_h + gap

    # 3. "Setting" (ตั้งค่าเสียง / หน้าจอ / วิธีเล่น)
    r_setting = pygame.Rect(cx - btn_w // 2, y, btn_w, btn_h)
    button(surface, r_setting, "ตั้งค่า  (Setting)", FONT_L, base=(35, 105, 135),
           hover=r_setting.collidepoint(mouse_pos))
    draw_icon_wrench(surface, (r_setting.left + 16, r_setting.centery - 10, 20, 20), color=(180, 235, 255))
    buttons["setting"] = r_setting
    buttons["how_to_play"] = r_setting   # compatibility for automated tests
    y += btn_h + gap

    # 4. "Exit" (ออกจากเกม)
    r_exit = pygame.Rect(cx - btn_w // 2, y, btn_w, btn_h)
    button(surface, r_exit, "ออกจากเกม  (Exit)", FONT_L, base=(125, 45, 50),
           hover=r_exit.collidepoint(mouse_pos))
    draw_icon_cross(surface, (r_exit.left + 26, r_exit.centery), 18, color=(255, 120, 120))
    buttons["exit"] = r_exit
    buttons["quit"] = r_exit

    # ข้อความเวอร์ชัน
    text(surface, "v1.4 — Multi-Slot Save & 4-Button Menu", FONT_XS, (90, 105, 135),
         (S.SCREEN_W - 16, S.SCREEN_H - 14), right=True, max_w=300)

    return buttons


# ─────────────────────────────────────────────────────────────────────────────
# เมนูเลือกโหมดการเล่น (Play Mode Selection Menu)
# ─────────────────────────────────────────────────────────────────────────────

def draw_play_select_menu(surface, mouse_pos):
    dim_overlay(surface, 210)
    cx = S.SCREEN_W // 2

    panel = pygame.Rect(cx - 270, 95, 540, 560)
    _panel(surface, panel, bg=(18, 22, 34), border=(65, 80, 125), alpha=252, radius=18)

    text(surface, "เลือกโหมดการเล่น (Select Game Mode)", FONT_L, (240, 245, 255),
         (cx, panel.top + 26), center=True)
    text(surface, "เลือกรูปแบบการผจญภัยและเป้าหมายของคุณ", FONT_XS, (160, 175, 205),
         (cx, panel.top + 54), center=True)
    pygame.draw.line(surface, (50, 60, 85),
                     (panel.left + 20, panel.top + 76), (panel.right - 20, panel.top + 76), 1)

    buttons = {}
    card_w = 480
    card_h = 170
    x0 = panel.left + 30

    # 1. Card: โหมดภารกิจสัญญา (Mission Contracts)
    y_m = panel.top + 96
    card_m = pygame.Rect(x0, y_m, card_w, card_h)
    is_hov_m = card_m.collidepoint(mouse_pos)
    _panel(surface, card_m, bg=(24, 46, 36) if is_hov_m else (20, 36, 30),
           border=(70, 185, 110) if is_hov_m else (50, 120, 75), alpha=245, radius=12)

    gold_icon = pygame.transform.smoothscale(assets.get_image("res_gold"), (32, 32))
    surface.blit(gold_icon, (card_m.left + 20, card_m.top + 20))
    text(surface, "โหมดภารกิจสัญญา  (Mission Contracts)", FONT_M, (120, 240, 160),
         (card_m.left + 64, card_m.top + 24))
    text(surface, "• สุ่มข้อเสนอสัญญา 3 ระดับความยาก (Easy, Medium, Hard)", FONT_S, (210, 230, 220),
         (card_m.left + 24, card_m.top + 66))
    text(surface, "• สะสมเหรียญรางวัล พิชิตเป้าหมายขุดแร่และดำดิ่งลึก", FONT_S, (210, 230, 220),
         (card_m.left + 24, card_m.top + 94))

    btn_play_m = pygame.Rect(card_m.right - 146, card_m.bottom - 42, 130, 32)
    button(surface, btn_play_m, "เลือกโหมดนี้ >", FONT_XS, base=(40, 130, 75), hover=is_hov_m)
    buttons["mode_mission"] = card_m

    # 2. Card: โหมดคลาสสิก (Classic Endless)
    y_c = card_m.bottom + 20
    card_c = pygame.Rect(x0, y_c, card_w, card_h)
    is_hov_c = card_c.collidepoint(mouse_pos)
    _panel(surface, card_c, bg=(52, 38, 20) if is_hov_c else (40, 28, 16),
           border=(220, 160, 50) if is_hov_c else (150, 105, 35), alpha=245, radius=12)

    dia_icon = pygame.transform.smoothscale(assets.get_image("res_diamond"), (32, 32))
    surface.blit(dia_icon, (card_c.left + 20, card_c.top + 20))
    text(surface, "โหมดคลาสสิก  (Classic Endless)", FONT_M, (255, 215, 60),
         (card_c.left + 64, card_c.top + 24))
    text(surface, "• ขุดลึกไม่จำกัดรอบ อิสระตามใจ ไร้เงื่อนไขเวลา", FONT_S, (240, 230, 205),
         (card_c.left + 24, card_c.top + 66))
    text(surface, "• สะสมเหรียญเพื่อปลดล็อคประตูกั้นชั้นความลึก 4 ชั้น", FONT_S, (240, 230, 205),
         (card_c.left + 24, card_c.top + 94))

    btn_play_c = pygame.Rect(card_c.right - 146, card_c.bottom - 42, 130, 32)
    button(surface, btn_play_c, "เลือกโหมดนี้ >", FONT_XS, base=(170, 110, 25), hover=is_hov_c)
    buttons["mode_classic"] = card_c

    # ปุ่มย้อนกลับ
    back_rect = pygame.Rect(cx - 90, panel.bottom - 44, 180, 34)
    button(surface, back_rect, "< กลับไปเมนูหลัก", FONT_S, base=(95, 45, 55),
           hover=back_rect.collidepoint(mouse_pos))
    buttons["back"] = back_rect

    return buttons


# ─────────────────────────────────────────────────────────────────────────────
# เมนูตั้งค่าระบบ (Settings Menu)
# ─────────────────────────────────────────────────────────────────────────────

def draw_settings_menu(surface, mouse_pos, is_fullscreen=False):
    dim_overlay(surface, 210)
    cx = S.SCREEN_W // 2

    panel = pygame.Rect(cx - 240, 110, 480, 510)
    _panel(surface, panel, bg=(18, 22, 34), border=(65, 80, 125), alpha=252, radius=18)

    text(surface, "ตั้งค่าระบบ (Settings)", FONT_L, (240, 245, 255),
         (cx, panel.top + 26), center=True)
    text(surface, "ปรับแต่งเสียง การแสดงผล และดูวิธีเล่น", FONT_XS, (160, 175, 205),
         (cx, panel.top + 54), center=True)
    pygame.draw.line(surface, (50, 60, 85),
                     (panel.left + 20, panel.top + 76), (panel.right - 20, panel.top + 76), 1)

    buttons = {}
    btn_w = 400
    btn_h = 56
    gap = 18
    y = panel.top + 100

    # 1. Toggle Audio Mute
    muted = assets.is_muted()
    r_mute = pygame.Rect(cx - btn_w // 2, y, btn_w, btn_h)
    _panel(surface, r_mute, bg=(38, 24, 28) if muted else (22, 40, 32),
           border=(180, 65, 65) if muted else (60, 160, 95), alpha=240, radius=10)
    draw_icon_speaker(surface, (r_mute.left + 30, r_mute.centery), size=24, muted=muted,
                      color=(255, 120, 100) if muted else (140, 255, 180))
    status_audio = "ปิดเสียงอยู่ (Muted)" if muted else "เปิดเสียงปกติ (Sound On)"
    status_color = (255, 140, 120) if muted else (120, 240, 160)
    text(surface, "ระบบเสียงเอฟเฟกต์  [คีย์ M]", FONT_M, (240, 245, 255), (r_mute.left + 64, r_mute.top + 10))
    text(surface, f"สถานะ: {status_audio}", FONT_XS, status_color, (r_mute.left + 64, r_mute.top + 34))
    buttons["toggle_mute"] = r_mute
    y += btn_h + gap

    # 2. Toggle Fullscreen
    r_fs = pygame.Rect(cx - btn_w // 2, y, btn_w, btn_h)
    _panel(surface, r_fs, bg=(26, 34, 52), border=(70, 110, 180), alpha=240, radius=10)
    draw_icon_tier(surface, (r_fs.left + 20, r_fs.centery - 10, 20, 20), color=(120, 190, 255))
    status_fs = "เต็มจอ (Fullscreen)" if is_fullscreen else "หน้าต่างปกติ (Windowed)"
    text(surface, "โหมดการแสดงผล  [คีย์ F11]", FONT_M, (240, 245, 255), (r_fs.left + 64, r_fs.top + 10))
    text(surface, f"สถานะ: {status_fs}", FONT_XS, (160, 210, 255), (r_fs.left + 64, r_fs.top + 34))
    buttons["toggle_fullscreen"] = r_fs
    y += btn_h + gap

    # 3. How to Play
    r_how = pygame.Rect(cx - btn_w // 2, y, btn_w, btn_h)
    _panel(surface, r_how, bg=(30, 36, 52), border=(80, 120, 175), alpha=240, radius=10)
    draw_icon_help(surface, (r_how.left + 20, r_how.centery - 10, 20, 20))
    text(surface, "คู่มือวิธีเล่น & ปุ่มควบคุม", FONT_M, (240, 245, 255), (r_how.left + 64, r_how.top + 10))
    text(surface, "ดูคำแนะนำการบังคับรถ ขุดบล็อก และเทคนิค Gravity Slam", FONT_XS, (170, 190, 220), (r_how.left + 64, r_how.top + 34))
    buttons["how_to_play"] = r_how
    y += btn_h + gap + 10

    # ปุ่มย้อนกลับ
    back_rect = pygame.Rect(cx - 90, panel.bottom - 44, 180, 34)
    button(surface, back_rect, "< กลับ", FONT_S, base=(95, 45, 55),
           hover=back_rect.collidepoint(mouse_pos))
    buttons["back"] = back_rect

    return buttons


# ─────────────────────────────────────────────────────────────────────────────
# เมนู Pause (Pause Menu - คลีน กระชับ เป็นระเบียบ ไม่ใช้อีโมจิ)
# ─────────────────────────────────────────────────────────────────────────────

def draw_pause_menu(surface, mouse_pos, is_fullscreen=False, current_slot=1):
    dim_overlay(surface, 195)
    cx = S.SCREEN_W // 2

    panel_w = 340
    panel_h = 370
    panel = pygame.Rect(cx - panel_w // 2, (S.SCREEN_H - panel_h) // 2, panel_w, panel_h)
    _panel(surface, panel, bg=(18, 22, 34), border=(65, 75, 115), alpha=248, radius=16)

    text(surface, "หยุดชั่วคราว (PAUSED)", FONT_L, (240, 245, 255),
         (cx, panel.top + 26), center=True)
    pygame.draw.line(surface, (50, 58, 85),
                     (panel.left + 24, panel.top + 52), (panel.right - 24, panel.top + 52), 1)

    buttons = {}
    btn_w = 280
    btn_h = 44
    gap = 12
    y = panel.top + 66

    # 1. เล่นต่อ (Resume)
    r_resume = pygame.Rect(cx - btn_w // 2, y, btn_w, btn_h)
    button(surface, r_resume, "เล่นต่อ  (Resume)", FONT_M, base=(36, 110, 68),
           hover=r_resume.collidepoint(mouse_pos))
    buttons["resume"] = r_resume
    y += btn_h + gap

    # 2. บันทึกเกม (Save Game)
    r_save = pygame.Rect(cx - btn_w // 2, y, btn_w, btn_h)
    button(surface, r_save, f"บันทึกเกม  (Save Game)", FONT_M, base=(36, 52, 78),
           hover=r_save.collidepoint(mouse_pos))
    buttons["save"] = r_save
    buttons["save_game"] = r_save
    buttons["save_slots"] = r_save
    buttons["save_current"] = r_save
    y += btn_h + gap

    # 3. โหลดเกม (Load Game)
    r_load = pygame.Rect(cx - btn_w // 2, y, btn_w, btn_h)
    button(surface, r_load, "โหลดเกม  (Load Game)", FONT_M, base=(34, 44, 66),
           hover=r_load.collidepoint(mouse_pos))
    buttons["load"] = r_load
    buttons["load_game"] = r_load
    buttons["load_slots"] = r_load
    y += btn_h + gap

    # 4. ตั้งค่าระบบ (Settings)
    r_settings = pygame.Rect(cx - btn_w // 2, y, btn_w, btn_h)
    button(surface, r_settings, "ตั้งค่าระบบ  (Settings)", FONT_M, base=(34, 44, 66),
           hover=r_settings.collidepoint(mouse_pos))
    buttons["settings"] = r_settings
    buttons["how_to_play"] = r_settings   # compatibility for automated tests
    y += btn_h + gap

    # 5. ออกไปเมนูหลัก (Exit to Main Menu)
    r_exit = pygame.Rect(cx - btn_w // 2, y, btn_w, btn_h)
    button(surface, r_exit, "ออกไปเมนูหลัก  (Exit to Menu)", FONT_M, base=(95, 38, 45),
           hover=r_exit.collidepoint(mouse_pos))
    buttons["save_quit"] = r_exit
    buttons["exit_menu"] = r_exit
    buttons["quit_nosave"] = r_exit
    buttons["menu"] = r_exit

    # คำแนะนำปุ่มลัดด้านล่าง
    text(surface, "กด [Esc] เล่นต่อ  •  [M] เปิด/ปิดเสียง", FONT_XS, (140, 155, 185),
         (cx, panel.bottom - 18), center=True)

    return buttons


# ─────────────────────────────────────────────────────────────────────────────
# หน้าต่างจัดการช่องเซฟ 5 สล็อต (Multi-Slot Save/Load Menu)
# ─────────────────────────────────────────────────────────────────────────────

def draw_slot_menu(surface, slots, mode="load", mouse_pos=(0, 0),
                   confirm_delete_slot=None, confirm_overwrite_slot=None, current_slot=1):
    """
    หน้าต่างแสดงช่องบันทึกเกม 5 สล็อต (Slot 1 - 5):
    - mode="load": สำหรับเลือกโหลดเกม หรือลบเซฟ
    - mode="save": สำหรับเลือกสล็อตบันทึกเกม (หากมีข้อมูลแล้วจะถามยืนยันเขียนทับ)
    """
    dim_overlay(surface, 215)
    cx = S.SCREEN_W // 2

    panel = pygame.Rect(30, 20, S.SCREEN_W - 60, 770)
    _panel(surface, panel, bg=(18, 22, 34), border=(65, 80, 125), alpha=252, radius=18)

    # ส่วนหัว
    if mode == "load":
        title_txt = "เลือกช่องบันทึกเพื่อโหลดเกม (Load Game)"
        sub_txt = "เลือกข้อมูลเกมจากช่องบันทึกเพื่อเล่นต่อ (แยกเก็บ 5 สล็อตอิสระ)"
        head_col = (110, 205, 255)
    else:
        title_txt = "เลือกช่องเพื่อบันทึกเกม (Save Game)"
        sub_txt = "เลือกช่องสล็อตที่ต้องการบันทึกข้อมูลเกม (บันทึกทับต้องยืนยัน)"
        head_col = (255, 215, 60)

    text(surface, title_txt, FONT_L, head_col, (cx, panel.top + 16), center=True)
    text(surface, sub_txt, FONT_XS, (175, 190, 220), (cx, panel.top + 42), center=True)
    pygame.draw.line(surface, (50, 60, 85), (panel.left + 20, panel.top + 60), (panel.right - 20, panel.top + 60), 1)

    buttons = {}
    slot_h = 108
    slot_gap = 12
    start_y = panel.top + 72

    for i in range(1, 6):
        s_info = slots[i - 1] if (i - 1) < len(slots) else {"slot_id": i, "empty": True}
        card_rect = pygame.Rect(panel.left + 16, start_y + (i - 1) * (slot_h + slot_gap), panel.w - 32, slot_h)
        is_card_hov = card_rect.collidepoint(mouse_pos)
        is_cur = (current_slot == i)
        is_empty = s_info.get("empty", False)
        is_corrupted = s_info.get("corrupted", False)

        if is_empty:
            card_bg = (20, 24, 36) if not is_card_hov else (28, 34, 48)
            card_border = (48, 56, 75) if not is_card_hov else (75, 90, 125)
            _panel(surface, card_rect, bg=card_bg, border=card_border, alpha=230, radius=10)

            # เลขช่อง
            slot_badge = pygame.Rect(card_rect.left + 14, card_rect.top + 12, 90, 24)
            pygame.draw.rect(surface, (34, 40, 56), slot_badge, border_radius=4)
            pygame.draw.rect(surface, (60, 72, 98), slot_badge, 1, border_radius=4)
            text(surface, f"ช่องที่ {i}", FONT_S, (180, 195, 220), slot_badge.center, center=True)

            text(surface, "(ช่องว่าง - ยังไม่มีข้อมูลเกม)", FONT_M, (130, 145, 170),
                 (card_rect.left + 120, card_rect.top + 12))
            text(surface, "สามารถเลือกบันทึกเกมลงในช่องนี้ได้ตลอดเวลา", FONT_XS, (110, 125, 150),
                 (card_rect.left + 120, card_rect.top + 42))

            if mode == "save":
                btn_save = pygame.Rect(card_rect.right - 150, card_rect.centery - 18, 136, 36)
                button(surface, btn_save, "บันทึกที่นี่", FONT_S, base=(40, 130, 70),
                       hover=btn_save.collidepoint(mouse_pos))
                draw_icon_check(surface, (btn_save.left + 18, btn_save.centery), 14)
                buttons[f"save_slot_{i}"] = btn_save
            buttons[f"card_slot_{i}"] = card_rect
            continue

        if is_corrupted:
            _panel(surface, card_rect, bg=(38, 20, 24), border=(160, 50, 50), alpha=240, radius=10)
            slot_badge = pygame.Rect(card_rect.left + 14, card_rect.top + 12, 90, 24)
            pygame.draw.rect(surface, (56, 24, 28), slot_badge, border_radius=4)
            text(surface, f"ช่องที่ {i}", FONT_S, (255, 120, 120), slot_badge.center, center=True)
            text(surface, "ไฟล์บันทึกมีปัญหา / เสียหาย", FONT_M, (255, 120, 120),
                 (card_rect.left + 120, card_rect.top + 12))
            text(surface, "ไม่สามารถอ่านข้อมูลได้ กรุณาลบแล้วเริ่มใหม่", FONT_XS, (200, 140, 140),
                 (card_rect.left + 120, card_rect.top + 42))

            del_btn = pygame.Rect(card_rect.right - 110, card_rect.centery - 18, 96, 36)
            button(surface, del_btn, "ลบไฟล์", FONT_S, base=(120, 42, 42),
                   hover=del_btn.collidepoint(mouse_pos))
            buttons[f"delete_slot_{i}"] = del_btn
            buttons[f"card_slot_{i}"] = card_rect
            continue

        # มีข้อมูลเซฟปกติ
        summary = s_info.get("summary", {})
        gmode = s_info.get("game_mode", "mission")
        saved_at = s_info.get("saved_at", "")

        card_bg = (24, 28, 42) if not is_card_hov else (32, 38, 56)
        card_border = (80, 140, 220) if is_cur else ((60, 72, 100) if not is_card_hov else (100, 130, 185))
        _panel(surface, card_rect, bg=card_bg, border=card_border, alpha=240, radius=10)

        # ป้ายเลขช่อง
        slot_badge = pygame.Rect(card_rect.left + 14, card_rect.top + 10, 80, 22)
        badge_bg = (40, 70, 120) if is_cur else (32, 40, 58)
        pygame.draw.rect(surface, badge_bg, slot_badge, border_radius=4)
        pygame.draw.rect(surface, (90, 130, 190), slot_badge, 1, border_radius=4)
        text(surface, f"ช่องที่ {i}", FONT_S, (230, 240, 255), slot_badge.center, center=True)

        # ป้ายโหมด
        mode_badge = pygame.Rect(card_rect.left + 100, card_rect.top + 10, 106, 22)
        if gmode == "classic":
            m_bg, m_border, m_tc = (52, 38, 18), (190, 140, 45), (255, 215, 60)
            m_label = "โหมดคลาสสิก"
        else:
            m_bg, m_border, m_tc = (20, 46, 30), (55, 160, 85), (95, 235, 135)
            m_label = "โหมดภารกิจ"
        pygame.draw.rect(surface, m_bg, mode_badge, border_radius=4)
        pygame.draw.rect(surface, m_border, mode_badge, 1, border_radius=4)
        text(surface, m_label, FONT_XS, m_tc, mode_badge.center, center=True)

        if is_cur:
            text(surface, "[ช่องปัจจุบัน]", FONT_XS, (255, 215, 90), (card_rect.left + 214, card_rect.top + 12))

        # ชื่อหัวข้อ / เป้าหมาย
        title_disp = summary.get("title", "ข้อมูลเกม")
        text(surface, title_disp, FONT_M, (255, 255, 255), (card_rect.left + 14, card_rect.top + 38), max_w=280)

        # วันเวลาที่เซฟ
        if saved_at:
            text(surface, f"บันทึก: {saved_at}", FONT_XS, (150, 165, 195), (card_rect.left + 14, card_rect.top + 64))

        # ข้อมูลทรัพยากร: เหรียญ และ ความลึก
        coins_val = summary.get("coins", 0)
        depth_val = summary.get("depth", 0)

        stat_x = card_rect.left + 305
        stat_y = card_rect.top + 28
        coin_img = pygame.transform.smoothscale(assets.get_image("res_coin"), (18, 18))
        surface.blit(coin_img, (stat_x, stat_y))
        text(surface, f"{coins_val:,} G", FONT_S, (255, 220, 80), (stat_x + 22, stat_y))

        # ความลึก
        text(surface, f"ลึก: {depth_val}ม.", FONT_XS, (160, 195, 235), (stat_x + 22, stat_y + 26))

        # ปุ่มการทำงานด้านขวาของการ์ด
        right_btn_x = card_rect.right - 146
        btn_y = card_rect.centery - 18

        if mode == "load":
            if confirm_delete_slot == i:
                btn_del_conf = pygame.Rect(right_btn_x - 30, btn_y, 164, 36)
                button(surface, btn_del_conf, "ยืนยันลบ?", FONT_S, base=(175, 45, 45),
                       hover=btn_del_conf.collidepoint(mouse_pos))
                draw_icon_cross(surface, (btn_del_conf.left + 16, btn_del_conf.centery), 14)
                buttons[f"confirm_delete_{i}"] = btn_del_conf
            else:
                btn_load = pygame.Rect(right_btn_x, btn_y, 92, 36)
                button(surface, btn_load, "โหลด", FONT_S, base=(40, 115, 175),
                       hover=btn_load.collidepoint(mouse_pos))
                buttons[f"load_slot_{i}"] = btn_load

                # ปุ่มลบ
                btn_del = pygame.Rect(card_rect.right - 48, btn_y, 36, 36)
                button(surface, btn_del, "", FONT_S, base=(95, 38, 42),
                       hover=btn_del.collidepoint(mouse_pos))
                draw_icon_cross(surface, btn_del.center, 14, color=(235, 100, 100))
                buttons[f"delete_slot_{i}"] = btn_del
        else:
            # mode == 'save'
            if confirm_overwrite_slot == i:
                btn_ow_conf = pygame.Rect(card_rect.right - 160, btn_y, 148, 36)
                button(surface, btn_ow_conf, "ยืนยันเขียนทับ!", FONT_S, base=(190, 60, 45),
                       hover=btn_ow_conf.collidepoint(mouse_pos))
                buttons[f"confirm_overwrite_{i}"] = btn_ow_conf
            elif confirm_delete_slot == i:
                btn_del_conf = pygame.Rect(right_btn_x - 40, btn_y, 174, 36)
                button(surface, btn_del_conf, "ยืนยันลบ?", FONT_S, base=(175, 45, 45),
                       hover=btn_del_conf.collidepoint(mouse_pos))
                draw_icon_cross(surface, (btn_del_conf.left + 16, btn_del_conf.centery), 14)
                buttons[f"confirm_delete_{i}"] = btn_del_conf
            else:
                btn_save = pygame.Rect(card_rect.right - 146, btn_y, 92, 36)
                button(surface, btn_save, "เขียนทับ", FONT_S, base=(140, 85, 35),
                       hover=btn_save.collidepoint(mouse_pos))
                buttons[f"save_slot_{i}"] = btn_save

                btn_del = pygame.Rect(card_rect.right - 48, btn_y, 36, 36)
                button(surface, btn_del, "", FONT_S, base=(95, 38, 42),
                       hover=btn_del.collidepoint(mouse_pos))
                draw_icon_cross(surface, btn_del.center, 14, color=(235, 100, 100))
                buttons[f"delete_slot_{i}"] = btn_del

        buttons[f"card_slot_{i}"] = card_rect

    # ปุ่มปิด / กลับ
    back_rect = pygame.Rect(cx - 100, panel.bottom - 46, 200, 36)
    button(surface, back_rect, "< กลับ", FONT_M, base=(95, 45, 55),
           hover=back_rect.collidepoint(mouse_pos))
    buttons["back"] = back_rect
    return buttons


# ─────────────────────────────────────────────────────────────────────────────
# ร้านอัพเกรด (Shop)
# ─────────────────────────────────────────────────────────────────────────────

def draw_shop_menu(surface, vehicle, mouse_pos, game_mode="mission", unlocked_floor=1, active_tab="upgrades"):
    dim_overlay(surface, 185)
    cx = S.SCREEN_W // 2

    panel = pygame.Rect(cx - 260, 60, 520, 580)
    _panel(surface, panel, bg=(20, 22, 34), border=(65, 72, 110), alpha=248, radius=16)

    buttons = {}

    # แถบแท็บด้านบน
    if game_mode == "classic":
        tab_w = 152
        tab_gap = 12
        tab_x0 = panel.left + 20

        # แท็บ 1: อัปเกรดสถานะ
        tab_upg = pygame.Rect(tab_x0, panel.top + 16, tab_w, 36)
        is_upg = (active_tab == "upgrades")
        _panel(surface, tab_upg, bg=(50, 95, 155) if is_upg else (38, 42, 60),
               border=(90, 160, 255) if is_upg else (80, 95, 130), alpha=240, radius=8)
        draw_icon_wrench(surface, (tab_upg.left + 12, tab_upg.centery - 9, 18, 18))
        text(surface, "อัปเกรด", FONT_S, (255, 255, 255) if is_upg else (200, 210, 230),
             (tab_upg.centerx + 10, tab_upg.centery), center=True)
        buttons["tab_upgrades"] = tab_upg

        # แท็บ 2: ปลดล็อคชั้นความลึก
        tab_flr = pygame.Rect(tab_x0 + tab_w + tab_gap, panel.top + 16, tab_w, 36)
        is_flr = (active_tab == "floor")
        _panel(surface, tab_flr, bg=(175, 115, 30) if is_flr else (38, 42, 60),
               border=(255, 215, 60) if is_flr else (80, 95, 130), alpha=240, radius=8)
        draw_icon_lock(surface, (tab_flr.left + 12, tab_flr.centery - 9, 18, 18),
                       color=(255, 225, 90) if is_flr else (210, 220, 240))
        text(surface, "ปลดล็อคชั้น", FONT_S, (255, 255, 255) if is_flr else (200, 210, 230),
             (tab_flr.centerx + 10, tab_flr.centery), center=True)
        buttons["tab_floor"] = tab_flr

        # แท็บ 3: อู่แต่งรถ (Garage)
        tab_gar = pygame.Rect(tab_x0 + (tab_w + tab_gap) * 2, panel.top + 16, tab_w, 36)
        _panel(surface, tab_gar, bg=(38, 42, 60) if not tab_gar.collidepoint(mouse_pos) else (50, 55, 80),
               border=(80, 95, 130), alpha=240, radius=8)
        draw_icon_palette(surface, (tab_gar.left + 12, tab_gar.centery - 9, 18, 18))
        text(surface, "อู่แต่งรถ", FONT_S, (200, 210, 230),
             (tab_gar.centerx + 10, tab_gar.centery), center=True)
        buttons["tab_garage"] = tab_gar
    else:
        tab_upg = pygame.Rect(panel.left + 20, panel.top + 16, 232, 36)
        _panel(surface, tab_upg, bg=(50, 95, 155), border=(90, 160, 255), alpha=240, radius=8)
        draw_icon_wrench(surface, (tab_upg.left + 14, tab_upg.centery - 9, 18, 18))
        text(surface, "อัปเกรดสถานะ", FONT_S, (255, 255, 255),
             (tab_upg.centerx + 10, tab_upg.centery), center=True)

        tab_gar = pygame.Rect(panel.right - 252, panel.top + 16, 232, 36)
        _panel(surface, tab_gar, bg=(38, 42, 60) if not tab_gar.collidepoint(mouse_pos) else (50, 55, 80),
               border=(80, 95, 130), alpha=240, radius=8)
        draw_icon_palette(surface, (tab_gar.left + 14, tab_gar.centery - 9, 18, 18))
        text(surface, "อู่แต่งรถ (Garage)", FONT_S,
             (210, 220, 240) if not tab_gar.collidepoint(mouse_pos) else (255, 255, 255),
             (tab_gar.centerx + 10, tab_gar.centery), center=True)
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
        max_classic = getattr(S, "MAX_CLASSIC_FLOORS", 7)
        if unlocked_floor >= max_classic:
            card = pygame.Rect(panel.left + 20, panel.top + 96, panel.w - 40, 160)
            _panel(surface, card, bg=(36, 32, 20), border=(255, 215, 60), alpha=245, radius=12)
            draw_icon_star(surface, (card.left + 24, card.top + 28), 20)
            text(surface, "ปลดล็อคครบทุกชั้นสมบูรณ์แล้ว! (ชั้นที่ 7 - ไร้ขีดจำกัด)", FONT_M, (255, 225, 90),
                 (card.left + 54, card.top + 18), max_w=card.w - 68)
            text(surface, "คุณได้ปลดล็อคทุกประตูกั้นในโลกใต้พิภพครบถ้วนแล้ว!", FONT_S, (120, 245, 140),
                 (card.left + 54, card.top + 48), max_w=card.w - 68)
            text(surface, "หลังจากชั้น 7 เป็นต้นไป จะเป็นชั้นหินและสายแร่ทอดยาวอย่างไม่มีที่สิ้นสุด", FONT_XS, (220, 230, 245),
                 (card.left + 20, card.top + 80), max_w=card.w - 40)
            text(surface, "สามารถขุดสำรวจ ขุดสะสมทองคำและเพชรพลอยได้อย่างอิสระโดยไม่ต้องปลดล็อคอีกต่อไป!", FONT_XS, (190, 205, 230),
                 (card.left + 20, card.top + 106), max_w=card.w - 40)
        else:
            next_floor = unlocked_floor + 1
            next_info = S.get_floor_info(next_floor)
            cur_info = S.get_floor_info(unlocked_floor)
            cost = next_info["unlock_cost"]
            can_unlock = (vehicle.coins >= cost)

            # การ์ดชั้นถัดไป
            card = pygame.Rect(panel.left + 20, panel.top + 96, panel.w - 40, 174)
            _panel(surface, card, bg=(32, 28, 24) if can_unlock else (26, 26, 36),
                   border=(255, 215, 60) if can_unlock else (75, 75, 100), alpha=240, radius=12)

            draw_icon_lock(surface, (card.left + 14, card.top + 13, 22, 22),
                           color=(255, 215, 60) if can_unlock else (210, 95, 95))
            text(surface, f"ชั้นถัดไป: ชั้นที่ {next_floor} - {next_info['name']}", FONT_M, (255, 235, 120),
                 (card.left + 42, card.top + 13), max_w=card.w - 56)

            text(surface, f"ความลึก: {next_info['min_depth']} - {next_info['max_depth']} เมตร  (ชั้นปัจจุบันปลดล็อคถึง {cur_info['max_depth']}ม.)",
                 FONT_S, (120, 215, 255), (card.left + 16, card.top + 44), max_w=card.w - 32)
            text(surface, next_info["desc"], FONT_XS, (200, 210, 230),
                 (card.left + 16, card.top + 70), max_w=card.w - 32)

            cost_col = (255, 215, 60) if can_unlock else (245, 110, 110)
            cost_lbl = f"ค่าปลดล็อค: {cost:,} เหรียญ" if can_unlock else f"ค่าปลดล็อค: {cost:,} เหรียญ  (ขาดอีก {cost - vehicle.coins:,} เหรียญ)"
            text(surface, cost_lbl, FONT_S, cost_col, (card.left + 16, card.top + 95), max_w=card.w - 32)

            # ปุ่มปลดล็อค
            btn_unlock = pygame.Rect(card.left + 16, card.top + 120, card.w - 32, 40)
            if can_unlock:
                button(surface, btn_unlock, f"ปลดล็อคชั้นที่ {next_floor}  ({cost:,} เหรียญ)",
                       FONT_M, base=(40, 150, 75), hover=btn_unlock.collidepoint(mouse_pos))
                draw_icon_star(surface, (btn_unlock.left + 22, btn_unlock.centery), 16)
            else:
                button(surface, btn_unlock, f"เหรียญยังไม่พอ  (ต้องการ {cost:,} เหรียญ)",
                       FONT_M, base=(65, 55, 60), hover=btn_unlock.collidepoint(mouse_pos))
                draw_icon_lock(surface, (btn_unlock.left + 14, btn_unlock.centery - 9, 18, 18), (210, 110, 110))
            buttons["unlock_floor"] = btn_unlock

        # รายการทำเนียบชั้นความลึก
        list_rect = pygame.Rect(panel.left + 20, panel.top + 274, panel.w - 40, 244)
        _panel(surface, list_rect, bg=(24, 26, 38), border=(50, 56, 78), radius=12)
        text(surface, "ทำเนียบชั้นความลึกทั้งหมด (Floor Directory)", FONT_S, (210, 225, 250),
             (list_rect.centerx, list_rect.top + 16), center=True)
        pygame.draw.line(surface, (45, 52, 74),
                         (list_rect.left + 14, list_rect.top + 32), (list_rect.right - 14, list_rect.top + 32), 1)

        for i, fc in enumerate(S.CLASSIC_FLOORS[:7]):
            row_y = list_rect.top + 38 + i * 29
            f_num = fc["floor"]
            is_unlocked = (f_num <= unlocked_floor)

            f_col = (110, 245, 130) if is_unlocked else (160, 170, 190)
            if is_unlocked:
                draw_icon_check(surface, (list_rect.left + 20, row_y + 9), 14)
                status_txt = "ปลดล็อคแล้ว (ชั้นสุดท้าย)" if f_num == max_classic else "ปลดล็อคแล้ว"
                status_col = (110, 245, 130)
            else:
                draw_icon_lock(surface, (list_rect.left + 13, row_y + 2, 14, 14), (170, 150, 120))
                status_txt = f"ล็อค ({fc['unlock_cost']:,} เหรียญ)"
                status_col = (235, 155, 80)

            short_name = fc["name"].split(" (")[0]
            depth_str = f"{fc['min_depth']}ม.+" if f_num == max_classic else f"{fc['min_depth']}-{fc['max_depth']}ม."
            text(surface, f"ชั้น {f_num}: {short_name} ({depth_str})",
                 FONT_XS, f_col, (list_rect.left + 36, row_y + 2), max_w=280)
            text(surface, status_txt, FONT_XS, status_col, (list_rect.right - 16, row_y + 2), right=True)

        close_rect = pygame.Rect(cx - 90, panel.bottom - 48, 180, 36)
        button(surface, close_rect, "ปิดร้าน  (E / ESC)", FONT_S, base=(55, 58, 80),
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

    # แบนเนอร์แจ้งเตือนปลดล็อคชั้น (โหมดคลาสสิก - คลิกเพื่อสลับไปแท็บปลดล็อคชั้นได้ทันที)
    if game_mode == "classic":
        max_classic = getattr(S, "MAX_CLASSIC_FLOORS", 7)
        teaser_rect = pygame.Rect(panel.left + 16, y + 2, panel.w - 32, 36)
        is_t_hov = teaser_rect.collidepoint(mouse_pos)
        if unlocked_floor >= max_classic:
            _panel(surface, teaser_rect, bg=(38, 34, 22), border=(255, 215, 60), radius=8)
            draw_icon_star(surface, (teaser_rect.left + 16, teaser_rect.centery), 14)
            text(surface, "ปลดล็อคครบทุกชั้นแล้ว! ขุดสำรวจชั้น 7 ได้ต่อเนื่องไม่สิ้นสุด", FONT_S, (255, 225, 100),
                 (teaser_rect.left + 36, teaser_rect.centery - 8), max_w=teaser_rect.w - 45)
        else:
            next_floor = unlocked_floor + 1
            next_cost = S.get_floor_info(next_floor)["unlock_cost"]
            can_flr = (vehicle.coins >= next_cost)
            _panel(surface, teaser_rect, bg=(52, 42, 24) if (can_flr and is_t_hov) else ((42, 34, 20) if can_flr else (26, 28, 40)),
                   border=(255, 215, 60) if can_flr else (85, 100, 135), radius=8)
            draw_icon_lock(surface, (teaser_rect.left + 10, teaser_rect.centery - 8, 16, 16),
                           color=(255, 215, 60) if can_flr else (200, 210, 230))
            t_msg = f"ชั้นถัดไป: ชั้น {next_floor} ({next_cost:,} เหรียญ) -> พร้อมปลดล็อค! คลิกที่นี่" if can_flr else f"ชั้นถัดไป: ชั้น {next_floor} ({next_cost:,} เหรียญ) -> คลิกเพื่อดูข้อมูลชั้น"
            t_col = (255, 235, 140) if can_flr else (190, 205, 230)
            text(surface, t_msg, FONT_XS, t_col, (teaser_rect.left + 32, teaser_rect.centery - 7), max_w=teaser_rect.w - 40)
        buttons["teaser_floor"] = teaser_rect

    close_rect = pygame.Rect(cx - 90, panel.bottom - 46, 180, 36)
    button(surface, close_rect, "ปิดร้าน  (E / ESC)", FONT_S, base=(55, 58, 80),
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

    panel = pygame.Rect(25, 24, 670, 762)
    _panel(surface, panel, bg=(18, 22, 34), border=(65, 80, 125), alpha=252, radius=18)

    # ส่วนหัว
    draw_icon_help(surface, (panel.left + 24, panel.top + 18, 28, 28), color=(255, 220, 75))
    text(surface, "วิธีเล่น & ปุ่มควบคุม (How to Play)", FONT_L, (255, 220, 75),
         (cx, panel.top + 20), center=True)
    text(surface, "สรุปวิธีเล่น การควบคุมรถขุด และเป้าหมายเกม", FONT_S,
         (175, 190, 220), (cx, panel.top + 48), center=True)
    pygame.draw.line(surface, (50, 60, 85),
                     (panel.left + 20, panel.top + 70), (panel.right - 20, panel.top + 70), 1)

    buttons = {}

    # ─── การ์ด 1: การบังคับ & ขุดเจาะ ───
    c1 = pygame.Rect(panel.left + 16, panel.top + 78, panel.w - 32, 172)
    _panel(surface, c1, bg=(24, 28, 42), border=(55, 68, 98), alpha=235, radius=12)
    text(surface, "1. การบังคับรถขุด & เจาะดิน (Controls & Digging)", FONT_M, (120, 215, 255),
         (c1.left + 16, c1.top + 10))

    # แถว 1: คีย์บอร์ด & ทิศทาง
    draw_key_badge(surface, "W", c1.left + 16, c1.top + 36, min_w=28, h=24)
    draw_key_badge(surface, "A", c1.left + 50, c1.top + 36, min_w=28, h=24)
    draw_key_badge(surface, "S", c1.left + 84, c1.top + 36, min_w=28, h=24)
    draw_key_badge(surface, "D", c1.left + 118, c1.top + 36, min_w=28, h=24)
    text(surface, "หรือ", FONT_S, (160, 175, 200), (c1.left + 158, c1.top + 39))
    draw_key_badge(surface, "↑", c1.left + 188, c1.top + 36, min_w=26, h=24)
    draw_key_badge(surface, "←", c1.left + 218, c1.top + 36, min_w=26, h=24)
    draw_key_badge(surface, "↓", c1.left + 248, c1.top + 36, min_w=26, h=24)
    draw_key_badge(surface, "→", c1.left + 278, c1.top + 36, min_w=26, h=24)
    text(surface, "หรือ คลิกเมาส์ค้างตามทิศทาง", FONT_S, (190, 210, 235), (c1.left + 316, c1.top + 39))

    # แถว 2: เทอร์โบ
    draw_key_badge(surface, "Shift", c1.left + 16, c1.top + 68, min_w=54, h=24, active=True)
    text(surface, "หรือ", FONT_S, (160, 175, 200), (c1.left + 78, c1.top + 71))
    draw_key_badge(surface, "Space", c1.left + 108, c1.top + 68, min_w=62, h=24, active=True)
    draw_icon_energy(surface, (c1.left + 180, c1.top + 70, 16, 16))
    text(surface, "Turbo Boost: พุ่งไปข้างหน้าเร็ว 2.6x  |  พุ่งดิ่งทุบหินแรง 3.0x (Slam)",
         FONT_S, (255, 215, 110), (c1.left + 204, c1.top + 71))

    # คำอธิบายย่อย: สบายตา ไม่อึดอัด
    text(surface, "• บิน & เจาะ: W / ↑ บินขึ้นผิวดิน  |  A / D เลี้ยวซ้าย-ขวา  |  S / ↓ เจาะลงใต้ดิน",
         FONT_S, (220, 230, 245), (c1.left + 16, c1.top + 106))
    text(surface, "• ขุดอัตโนมัติ: เพียงขับรถเคลื่อนที่ชนบล็อกดินหรือหิน รถจะขุดเจาะทันที!",
         FONT_S, (255, 230, 140), (c1.left + 16, c1.top + 138))

    # ─── การ์ด 2: วงจรเกมเพลย์ 3 ขั้นตอน ───
    c2 = pygame.Rect(panel.left + 16, c1.bottom + 12, panel.w - 32, 184)
    _panel(surface, c2, bg=(30, 28, 38), border=(75, 65, 95), alpha=235, radius=12)
    text(surface, "2. วงจรการเล่นหลัก 3 ขั้นตอน (Core Game Loop)", FONT_M, (255, 195, 60),
         (c2.left + 16, c2.top + 10))

    col_w = 196
    col_h = 132
    col_y = c2.top + 38
    cols_data = [
        ("1. ขุดเจาะ & สะสม", (255, 215, 100), (32, 28, 22), (90, 75, 45),
         ["• เจาะดินและหินลึก", "• เก็บ เหรียญ, ทอง, เพชร", "• สังเกตความจุถังแร่"]),
        ("2. ระวังพลังงาน!", (255, 150, 70), (38, 26, 22), (125, 70, 45),
         ["• พลังงานลดขณะขุด/บิน", "• บินกลับบ้านก่อนหมด!", "• เก็บถังน้ำมันช่วยเติม"]),
        ("3. กลับฐานบ้าน", (110, 235, 180), (22, 34, 30), (45, 115, 95),
         ["• ขับเข้าบ้าน (ผิวดินขวา)", "• ขายแร่ทั้งหมดเป็นเงิน", "• เติมพลังงานฟรี 100%!"]),
    ]

    for i, (col_title, title_c, bg_c, border_c, bullet_list) in enumerate(cols_data):
        col_x = c2.left + 14 + i * (col_w + 10)
        box = pygame.Rect(col_x, col_y, col_w, col_h)
        _panel(surface, box, bg=bg_c, border=border_c, alpha=230, radius=8)

        # ไอคอนประจำกล่อง
        if i == 0:
            draw_icon_power(surface, (box.left + 10, box.top + 9, 16, 16), color=title_c)
        elif i == 1:
            draw_icon_energy(surface, (box.left + 10, box.top + 9, 16, 16), color=title_c)
        else:
            draw_icon_star(surface, (box.left + 18, box.top + 17), size=14, color=title_c)

        text(surface, col_title, FONT_S, title_c, (box.left + 32, box.top + 9))
        pygame.draw.line(surface, border_c, (box.left + 10, box.top + 30), (box.right - 10, box.top + 30), 1)

        for bi, bullet in enumerate(bullet_list):
            tc = (220, 230, 245) if bi < 2 else (175, 215, 235)
            if i == 1 and bi == 1:
                tc = (255, 195, 160)
            elif i == 2 and bi == 2:
                tc = (130, 255, 190)
            text(surface, bullet, FONT_S, tc, (box.left + 10, box.top + 38 + bi * 28))

        # ลูกศรเชื่อมระหว่างกล่อง
        if i < 2:
            text(surface, "→", FONT_M, (160, 175, 200), (box.right + 5, box.centery - 1), center=True)

    # ─── การ์ด 3: ฐานบริการ & คีย์ลัด ───
    c3 = pygame.Rect(panel.left + 16, c2.bottom + 12, panel.w - 32, 196)
    _panel(surface, c3, bg=(22, 32, 38), border=(45, 105, 110), alpha=235, radius=12)
    text(surface, "3. ฐานบริการ, การอัปเกรด & ปุ่มลัด (Base & Shortcuts)", FONT_M, (100, 235, 200),
         (c3.left + 16, c3.top + 10))

    draw_key_badge(surface, "E", c3.left + 16, c3.top + 34, min_w=28, h=24, active=True)
    text(surface, "เปิดร้านค้า & อู่แต่งรถ (หน้าร้านผิวดินซ้าย) หรือกดปลดล็อคประตูกั้นชั้นใต้ดิน",
         FONT_S, (215, 240, 235), (c3.left + 52, c3.top + 37))

    text(surface, "• ร้านค้า & อู่: อัปเกรดพลังขุด, ความจุถัง, พลังงาน และแต่งสี/ซื้อหัวขุดพิเศษ",
         FONT_S, (220, 230, 245), (c3.left + 16, c3.top + 68))
    text(surface, "• เป้าหมาย: ทำสัญญาภารกิจให้ครบ (โหมดภารกิจ) หรือขุดสะสมเงินปลดล็อคทุกชั้น (โหมดคลาสสิก)",
         FONT_S, (255, 230, 140), (c3.left + 16, c3.top + 98))

    # แถบปุ่มลัด
    bar_rect = pygame.Rect(c3.left + 12, c3.top + 134, c3.w - 24, 46)
    _panel(surface, bar_rect, bg=(16, 22, 30), border=(50, 75, 95), alpha=240, radius=8)
    text(surface, "[ESC] เมนูพัก  |  [H / F1] ดูวิธีเล่น  |  [M] ปิด-เปิดเสียง  |  [F11] สลับเต็มจอ",
         FONT_S, (185, 210, 245), (bar_rect.centerx, bar_rect.centery), center=True)

    # ปุ่มปิด
    close_rect = pygame.Rect(cx - 130, c3.bottom + 14, 260, 42)
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

    # ส่วนหัว: วางชิดซ้าย และกล่องเหรียญสะสมวางชิดขวา ป้องกันข้อความทับซ้อนกัน 100%
    text(surface, "อู่แต่งรถขุด (Vehicle Garage)", FONT_L, (240, 245, 255),
         (panel.left + 22, panel.top + 16))
    text(surface, "ปลดล็อคสีตัวถัง โครงสร้างรถ และหัวขุดพิเศษด้วยเหรียญ", FONT_XS,
         (160, 175, 205), (panel.left + 22, panel.top + 45))

    coin_box = pygame.Rect(panel.right - 148, panel.top + 18, 128, 30)
    _panel(surface, coin_box, bg=(28, 32, 48), border=(220, 180, 55), alpha=240, radius=8)
    coin_icon = pygame.transform.smoothscale(assets.get_image("res_coin"), (18, 18))
    surface.blit(coin_icon, (coin_box.left + 8, coin_box.centery - 9))
    text(surface, f"{vehicle.coins:,} G", FONT_S, (255, 215, 60),
         (coin_box.right - 10, coin_box.top + 6), right=True)

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
    draw_icon_star(surface, (ab_rect.left + 12, ab_rect.centery), 12, color=head_cfg["badge_color"])
    text(surface, head_cfg["ability_name"], FONT_XS, (255, 225, 90), (ab_rect.centerx + 6, ab_rect.centery), center=True, max_w=prev_rect.w - 36)

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

    # แสดงสถิติความก้าวหน้าสำหรับปลดล็อค
    prog_box = pygame.Rect(prev_rect.left + 12, sy + 4, prev_rect.w - 24, 48)
    _panel(surface, prog_box, bg=(18, 22, 34), border=(55, 70, 95), alpha=220, radius=8)
    max_d = getattr(vehicle, "max_depth_reached", 0)
    tot_dia = getattr(vehicle, "total_diamonds_collected", 0)
    text(surface, f"ลึกสุดที่เคยถึง: {max_d}ม. | Tier {vehicle.overall_tier()}", FONT_XS, (150, 215, 255),
         (prog_box.centerx, prog_box.top + 14), center=True, max_w=prog_box.w - 10)
    text(surface, f"เพชรสะสม: {tot_dia} เม็ด | หัวขุด Lv.{vehicle.levels.get('power', 1)}", FONT_XS, (255, 220, 110),
         (prog_box.centerx, prog_box.top + 33), center=True, max_w=prog_box.w - 10)

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
            is_unlocked = vehicle.is_item_unlocked("color", cid)
            cond_met, req_desc, cost = vehicle.check_unlock_condition("color", cid)
            can_afford = (vehicle.coins >= cost)
            is_hov = crect.collidepoint(mouse_pos)

            if is_sel:
                border_c = (255, 215, 60)
                bg_c = (35, 42, 60)
            elif is_unlocked:
                border_c = (90, 200, 130) if is_hov else (48, 78, 65)
                bg_c = (24, 34, 32)
            elif cond_met:
                border_c = (255, 195, 50) if (can_afford and is_hov) else ((190, 150, 50) if can_afford else (120, 68, 68))
                bg_c = (32, 28, 22) if can_afford else (26, 22, 26)
            else:
                border_c = (55, 52, 68)
                bg_c = (18, 18, 26)

            _panel(surface, crect, bg=bg_c, border=border_c, alpha=235, radius=10)

            # วงกลมสวอชสีตัวถัง
            swatch_cx = crect.left + 32
            swatch_cy = crect.top + 32
            pygame.draw.circle(surface, c_info["dark"], (swatch_cx, swatch_cy), 20)
            pygame.draw.circle(surface, c_info["primary"], (swatch_cx, swatch_cy), 16)
            pygame.draw.circle(surface, c_info["highlight"], (swatch_cx - 4, swatch_cy - 4), 5)
            pygame.draw.circle(surface, (255, 255, 255), (swatch_cx, swatch_cy), 18, 2)

            # มินิพรีวิวรถ (sprite จริงจาก assets)
            vmini = assets.get_image(f"vehicle_{vehicle.vehicle_type}_{cid}")
            vmini_scaled = pygame.transform.smoothscale(vmini, (34, 34))
            surface.blit(vmini_scaled, (crect.right - 44, crect.top + 14))

            # ชื่อสี
            name_col = (255, 255, 255) if (is_unlocked or cond_met) else (165, 170, 185)
            text(surface, c_info["name"], FONT_S, name_col, (crect.left + 12, crect.top + 58), max_w=crect.w - 24)

            # สถานะ / เงื่อนไข / ราคา
            if is_sel:
                text(surface, "กำลังใช้งาน", FONT_XS, (110, 240, 140), (crect.left + 12, crect.top + 78))
                draw_icon_check(surface, (crect.right - 16, crect.bottom - 14), 15)
            elif is_unlocked:
                text(surface, "ปลดล็อคแล้ว (คลิกใช้)", FONT_XS, (110, 235, 140), (crect.left + 12, crect.top + 78))
            elif cond_met:
                p_col = (255, 215, 60) if can_afford else (245, 110, 110)
                text(surface, f"ซื้อปลดล็อค: {cost:,} G", FONT_XS, p_col, (crect.left + 12, crect.top + 78), max_w=crect.w - 34)
                draw_icon_lock(surface, (crect.right - 22, crect.bottom - 20, 13, 13), color=p_col)
            else:
                text(surface, f"{c_info.get('unlock_desc', req_desc)} ({cost}G)", FONT_XS, (220, 145, 105),
                     (crect.left + 12, crect.top + 78), max_w=crect.w - 32)
                draw_icon_lock(surface, (crect.right - 22, crect.bottom - 20, 13, 13), color=(190, 105, 105))

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
            is_unlocked = vehicle.is_item_unlocked("type", vtid)
            cond_met, req_desc, cost = vehicle.check_unlock_condition("type", vtid)
            can_afford = (vehicle.coins >= cost)
            is_hov = card_rect.collidepoint(mouse_pos)

            if is_sel:
                border_c = t_info["badge_color"]
                bg_c = (32, 40, 58)
            elif is_unlocked:
                border_c = (90, 200, 130) if is_hov else (50, 78, 65)
                bg_c = (22, 32, 30)
            elif cond_met:
                border_c = (255, 195, 50) if (can_afford and is_hov) else ((190, 150, 50) if can_afford else (120, 68, 68))
                bg_c = (30, 26, 22) if can_afford else (24, 20, 26)
            else:
                border_c = (52, 50, 65)
                bg_c = (18, 20, 28)

            _panel(surface, card_rect, bg=bg_c, border=border_c, alpha=235, radius=12)

            # มินิพรีวิวตัวถัง (sprite จริง)
            vmini = assets.get_image(f"vehicle_{vtid}_{vehicle.color_id}")
            vmini_scaled = pygame.transform.smoothscale(vmini, (52, 52))
            surface.blit(vmini_scaled, (card_rect.left + 14, card_rect.top + 16))

            # ชื่อ + ป้ายเด่น
            name_col = (255, 255, 255) if (is_unlocked or cond_met) else (175, 180, 195)
            text(surface, t_info["name"], FONT_M, name_col, (card_rect.left + 76, card_rect.top + 10), max_w=195)
            tag_rect = pygame.Rect(card_rect.left + 76, card_rect.top + 35, 118, 19)
            pygame.draw.rect(surface, (*t_info["badge_color"], 50), tag_rect, border_radius=4)
            pygame.draw.rect(surface, t_info["badge_color"], tag_rect, 1, border_radius=4)
            text(surface, t_info["tag"], FONT_XS, t_info["badge_color"], tag_rect.center, center=True, max_w=112)

            # ป้ายสถานะปลดล็อค/ราคา มุมขวาบนของการ์ด
            if is_sel:
                draw_icon_check(surface, (card_rect.right - 20, card_rect.top + 20), 18)
                text(surface, "ติดตั้งอยู่", FONT_XS, (110, 240, 140), (card_rect.right - 34, card_rect.top + 13), right=True)
            elif is_unlocked:
                text(surface, "ปลดล็อคแล้ว (คลิกใช้)", FONT_XS, (110, 235, 140), (card_rect.right - 12, card_rect.top + 13), right=True)
            elif cond_met:
                p_col = (255, 215, 60) if can_afford else (245, 110, 110)
                draw_icon_lock(surface, (card_rect.right - 24, card_rect.top + 11, 14, 14), color=p_col)
                text(surface, f"ซื้อปลดล็อค {cost:,} G", FONT_XS, p_col, (card_rect.right - 28, card_rect.top + 12), right=True)
            else:
                draw_icon_lock(surface, (card_rect.right - 24, card_rect.top + 11, 14, 14), color=(210, 110, 110))
                text(surface, f"ล็อค ({cost:,} G)", FONT_XS, (220, 130, 110), (card_rect.right - 28, card_rect.top + 12), right=True)

            # คำอธิบายและเงื่อนไข
            text(surface, t_info["desc"], FONT_XS, (180, 195, 220), (card_rect.left + 76, card_rect.top + 59), max_w=card_w - 88)
            if not is_unlocked:
                req_col = (110, 235, 140) if cond_met else (245, 165, 95)
                req_prefix = "ผ่านเงื่อนไขแล้ว! " if cond_met else "ต้องทำ: "
                text(surface, f"{req_prefix}{req_desc}", FONT_XS, req_col, (card_rect.left + 76, card_rect.top + 79), max_w=card_w - 88)

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
            is_unlocked = vehicle.is_item_unlocked("drill", dhid)
            cond_met, req_desc, cost = vehicle.check_unlock_condition("drill", dhid)
            can_afford = (vehicle.coins >= cost)
            is_hov = card_rect.collidepoint(mouse_pos)

            if is_sel:
                border_c = d_info["badge_color"]
                bg_c = (32, 40, 58)
            elif is_unlocked:
                border_c = (90, 200, 130) if is_hov else (50, 78, 65)
                bg_c = (22, 32, 30)
            elif cond_met:
                border_c = (255, 195, 50) if (can_afford and is_hov) else ((190, 150, 50) if can_afford else (120, 68, 68))
                bg_c = (30, 26, 22) if can_afford else (24, 20, 26)
            else:
                border_c = (52, 50, 65)
                bg_c = (18, 20, 28)

            _panel(surface, card_rect, bg=bg_c, border=border_c, alpha=235, radius=10)

            # มินิพรีวิวหัวสว่าน (sprite จริงจาก assets)
            dmini = assets.get_image(f"drill_{dhid}_down")
            dmini_scaled = pygame.transform.smoothscale(dmini, (40, 40))
            surface.blit(dmini_scaled, (card_rect.left + 14, card_rect.top + 14))

            # ชื่อหัวขุด + สถานะมุมขวาบน
            name_col = (255, 255, 255) if (is_unlocked or cond_met) else (175, 180, 195)
            text(surface, d_info["name"], FONT_M, name_col, (card_rect.left + 64, card_rect.top + 8), max_w=185)

            if is_sel:
                draw_icon_check(surface, (card_rect.right - 18, card_rect.top + 18), 16)
                text(surface, "ติดตั้งอยู่", FONT_XS, (110, 240, 140), (card_rect.right - 30, card_rect.top + 10), right=True)
            elif is_unlocked:
                text(surface, "ปลดล็อคแล้ว", FONT_XS, (110, 235, 140), (card_rect.right - 10, card_rect.top + 10), right=True)
            elif cond_met:
                p_col = (255, 215, 60) if can_afford else (245, 110, 110)
                draw_icon_lock(surface, (card_rect.right - 22, card_rect.top + 9, 13, 13), color=p_col)
                text(surface, f"ซื้อ {cost:,} G", FONT_XS, p_col, (card_rect.right - 26, card_rect.top + 10), right=True)
            else:
                draw_icon_lock(surface, (card_rect.right - 22, card_rect.top + 9, 13, 13), color=(210, 110, 110))
                text(surface, f"{cost:,} G", FONT_XS, (220, 130, 110), (card_rect.right - 26, card_rect.top + 10), right=True)

            ab_tag = pygame.Rect(card_rect.left + 64, card_rect.top + 31, 180, 18)
            pygame.draw.rect(surface, (*d_info["badge_color"], 50), ab_tag, border_radius=4)
            pygame.draw.rect(surface, d_info["badge_color"], ab_tag, 1, border_radius=4)
            draw_icon_star(surface, (ab_tag.left + 10, ab_tag.centery), 11, color=d_info["badge_color"])
            text(surface, d_info["ability_name"], FONT_XS, d_info["badge_color"], (ab_tag.left + 18, ab_tag.top + 2), max_w=158)

            # คำอธิบายคุณสมบัติ หรือเงื่อนไขปลดล็อคหากยังไม่ปลดล็อค
            if is_unlocked:
                text(surface, d_info["desc"], FONT_XS, (185, 195, 220), (card_rect.left + 64, card_rect.top + 54), max_w=card_w - 76)
            else:
                text(surface, d_info["desc"], FONT_XS, (165, 175, 195), (card_rect.left + 64, card_rect.top + 51), max_w=card_w - 76)
                req_col = (110, 235, 140) if cond_met else (245, 165, 95)
                req_prefix = "พร้อมซื้อ! " if cond_met else "เงื่อนไข: "
                text(surface, f"{req_prefix}{req_desc}", FONT_XS, req_col, (card_rect.left + 64, card_rect.top + 68), max_w=card_w - 76)

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
            draw_icon_goal(surface, key, (gx + 20, gy_curr + 1, 15, 15))
            text(surface, prog_txt, FONT_S, chk_col, (gx + 39, gy_curr), max_w=m_box.w // 2 - 42)
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

