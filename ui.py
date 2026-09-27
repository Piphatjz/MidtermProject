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
# ท้องฟ้า / เมฆ
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


# ─────────────────────────────────────────────────────────────────────────────
# รถขุด
# ─────────────────────────────────────────────────────────────────────────────

def draw_vehicle(surface, vehicle, camera_y):
    vx = vehicle.x + vehicle.vibe_x
    vy = vehicle.y + vehicle.vibe_y - camera_y + S.HUD_H
    rect = pygame.Rect(0, 0, int(vehicle.w), int(vehicle.h))
    rect.center = (int(vx), int(vy))

    body_raw = assets.get_image("vehicle_body")
    body = pygame.transform.smoothscale(body_raw, (rect.w, rect.h))
    if vehicle.facing[0] < 0:
        body = pygame.transform.flip(body, True, False)
    surface.blit(body, rect.topleft)

    fx, fy = vehicle.facing
    drill_name = "drill_down"
    drill_pos = (rect.centerx, rect.bottom + 2)

    if fx > 0:
        drill_name, drill_pos = "drill_right", (rect.right + 2, rect.centery)
    elif fx < 0:
        drill_name, drill_pos = "drill_left",  (rect.left - 2, rect.centery)
    elif fy < 0:
        drill_name, drill_pos = "drill_up",    (rect.centerx, rect.top - 2)
    elif fy > 0:
        drill_name, drill_pos = "drill_down",  (rect.centerx, rect.bottom + 2)

    d_base = assets.get_image(drill_name)
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
# SCREEN_W = 720, HUD_H = 90
_Z_LEFT_W   = 195
_Z_CENTER_W = 250
_Z_RIGHT_W  = S.SCREEN_W - _Z_LEFT_W - _Z_CENTER_W  # 275

def draw_hud(surface, vehicle, depth, mission=None):
    # พื้นหลังแถบ HUD
    hud_surf = pygame.Surface((S.SCREEN_W, S.HUD_H), pygame.SRCALPHA)
    hud_surf.fill((18, 20, 28, 252))
    surface.blit(hud_surf, (0, 0))

    # เส้นแบ่งโซนแนวตั้ง
    pygame.draw.line(surface, (45, 50, 70), (_Z_LEFT_W, 8), (_Z_LEFT_W, S.HUD_H - 8), 1)
    pygame.draw.line(surface, (45, 50, 70), (_Z_LEFT_W + _Z_CENTER_W, 8), (_Z_LEFT_W + _Z_CENTER_W, S.HUD_H - 8), 1)

    # เส้นขอบล่าง HUD
    pygame.draw.line(surface, (55, 62, 85), (0, S.HUD_H - 1), (S.SCREEN_W, S.HUD_H - 1), 2)

    _hud_zone_left(surface, vehicle)
    _hud_zone_center(surface, vehicle, depth)
    _hud_zone_right(surface, vehicle, mission)


def _hud_zone_left(surface, vehicle):
    """โซนซ้าย: ทรัพยากรในถังขุด (3 ช่องแสดงตัวเลขกึ่งกลางไม่ล้นขอบ)"""
    text(surface, "📦 แร่ในถัง", FONT_XS, (160, 175, 205), (14, 8))

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
        _panel(surface, slot_rect, bg=(28, 30, 42), border=(50, 56, 76), alpha=200, radius=8)

        # ไอคอนแร่
        icon = pygame.transform.smoothscale(assets.get_image(img_key), (20, 20))
        surface.blit(icon, (sx + (slot_w - 20) // 2, y_start + 6))

        # ตัวเลขจำนวน
        text(surface, str(count), FONT_S, color,
             (sx + slot_w // 2, y_start + 38), center=True, shadow=True, max_w=slot_w - 6)


def _hud_zone_center(surface, vehicle, depth):
    """โซนกลาง: เหรียญสะสม | ความลึก | หลอดพลังงาน | หลอดความจุถัง"""
    x0 = _Z_LEFT_W + 12
    bar_w = 226

    # แถวบน: เหรียญ (ซ้าย) + ความลึก (ขวา)
    coin_icon = pygame.transform.smoothscale(assets.get_image("res_coin"), (18, 18))
    surface.blit(coin_icon, (x0, 8))
    text(surface, f"{vehicle.coins:,}", FONT_M, (255, 215, 60), (x0 + 22, 6))

    depth_txt = f"⬇ {depth} ม.  T{vehicle.overall_tier()}"
    text(surface, depth_txt, FONT_S, (140, 215, 245), (x0 + bar_w, 8), right=True)

    # แถว 2: หลอดพลังงาน (สูง 20px ข้อความ FONT_XS พอดีเป๊ะ)
    en_ratio = max(0.0, vehicle.energy / vehicle.max_energy)
    en_fg    = (255, 145, 35) if en_ratio > 0.22 else (235, 55, 55)
    _draw_bar(surface, x0, 34, bar_w, 20, en_ratio, en_fg,
              bg=(45, 28, 18), radius=6, border=(70, 48, 30))
    en_txt = f"⚡ {int(vehicle.energy)}/{int(vehicle.max_energy)}"
    text(surface, en_txt, FONT_XS, (255, 255, 255),
         (x0 + bar_w // 2, 44), center=True, shadow=True)

    # แถว 3: หลอดความจุถัง (สูง 20px ข้อความ FONT_XS พอดีเป๊ะ)
    cratio = vehicle.cargo_count / vehicle.max_capacity if vehicle.max_capacity else 0.0
    c_fg   = (240, 70, 70) if vehicle.cargo_full() else (75, 195, 100)
    _draw_bar(surface, x0, 60, bar_w, 20, cratio, c_fg,
              bg=(24, 38, 25), radius=6, border=(45, 68, 48))
    cap_lbl = "ถังเต็ม!" if vehicle.cargo_full() else f"ถัง: {vehicle.cargo_count}/{vehicle.max_capacity}"
    cap_col = (255, 140, 130) if vehicle.cargo_full() else (225, 245, 225)
    text(surface, f"📦 {cap_lbl}", FONT_XS, cap_col,
         (x0 + bar_w // 2, 70), center=True, shadow=True)


def _hud_zone_right(surface, vehicle, mission=None):
    """โซนขวา: ภารกิจผสมประจำตา (Quest Tracker) ตรวจสอบเงื่อนไขแบบเรียลไทม์"""
    panel = pygame.Rect(_Z_LEFT_W + _Z_CENTER_W + 8, 6, _Z_RIGHT_W - 16, 78)

    if mission is None:
        # กรณีไม่มีภารกิจ แสดงสถานะการขับขี่
        _panel(surface, panel, bg=(26, 28, 40), border=(50, 56, 78), alpha=210, radius=10)
        text(surface, "🎯 โหมดอิสระ", FONT_S, (200, 210, 230), (panel.centerx, panel.top + 24), center=True)
        text(surface, "ขุดแร่และอัปเกรดตามใจชอบ", FONT_XS, (140, 150, 175), (panel.centerx, panel.top + 48), center=True)
        return

    diff_info = mission.diff_info
    all_done = mission.is_completed()

    # กรอบพาเนลภารกิจตามระดับความยาก
    border_color = (255, 220, 80) if all_done else diff_info["border_color"]
    _panel(surface, panel, bg=diff_info["bg_color"], border=border_color, alpha=235, radius=10)

    # แถว 1: ตราสัญลักษณ์ความยาก + ชื่อภารกิจ
    text(surface, diff_info["badge"], FONT_XS, diff_info["color"], (panel.left + 8, panel.top + 8))
    text(surface, mission.title, FONT_S, (240, 245, 255), (panel.left + 72, panel.top + 7), max_w=panel.w - 80)

    if all_done:
        # แจ้งเตือนเมื่อครบทุกข้อ
        text(surface, "⭐ ภารกิจครบทุกข้อแล้ว! ⭐", FONT_S, (255, 225, 80),
             (panel.centerx, panel.top + 34), center=True)
        text(surface, "🏠 ขับกลับบ้านเพื่อรับชัยชนะ!", FONT_XS, (160, 245, 185),
             (panel.centerx, panel.top + 55), center=True)
    else:
        # แสดงรายการเป้าหมายพร้อมเครื่องหมายถูก
        goals = mission.get_goals_status()
        # แถว 2 (เป้าหมาย 1 & 2)
        if len(goals) > 0:
            c0 = (100, 235, 120) if goals[0][2] else (215, 220, 235)
            chk0 = "✓" if goals[0][2] else "•"
            text(surface, f"{chk0} {goals[0][5]}", FONT_XS, c0, (panel.left + 10, panel.top + 32), max_w=120)
        if len(goals) > 1:
            c1 = (100, 235, 120) if goals[1][2] else (215, 220, 235)
            chk1 = "✓" if goals[1][2] else "•"
            text(surface, f"{chk1} {goals[1][5]}", FONT_XS, c1, (panel.left + 134, panel.top + 32), max_w=120)

        # แถว 3 (เป้าหมาย 3 & 4)
        if len(goals) > 2:
            c2 = (100, 235, 120) if goals[2][2] else (215, 220, 235)
            chk2 = "✓" if goals[2][2] else "•"
            text(surface, f"{chk2} {goals[2][5]}", FONT_XS, c2, (panel.left + 10, panel.top + 54), max_w=120)
        if len(goals) > 3:
            c3 = (100, 235, 120) if goals[3][2] else (215, 220, 235)
            chk3 = "✓" if goals[3][2] else "•"
            text(surface, f"{chk3} {goals[3][5]}", FONT_XS, c3, (panel.left + 134, panel.top + 54), max_w=120)
        elif len(goals) <= 2:
            text(surface, "(ครบทุกข้อแล้วกลับบ้าน)", FONT_XS, (140, 150, 175),
                 (panel.left + 134, panel.top + 54), max_w=120)


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
    rect = pygame.Rect((S.SCREEN_W - w) // 2, S.SCREEN_H - 58, w, 38)
    _panel(surface, rect, bg=(18, 22, 32), border=(70, 80, 110), alpha=225, radius=8)
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

    text(surface, "📋  เลือกสัญญาภารกิจประจำตา", FONT_L, (240, 245, 255),
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

        # ป้ายระดับความยาก
        banner_rect = pygame.Rect(card_x + 8, card_y + 8, card_w - 16, 32)
        pygame.draw.rect(surface, (*diff_info["border_color"], 70), banner_rect, border_radius=8)
        text(surface, diff_info["badge"], FONT_M, diff_info["color"], banner_rect.center, center=True)

        # ชื่อภารกิจ
        text(surface, mission.title, FONT_M, (255, 255, 255),
             (card_rect.centerx, card_y + 56), center=True, max_w=card_w - 16)

        # คำอธิบายย่อ
        text(surface, mission.desc, FONT_XS, (180, 190, 210),
             (card_rect.centerx, card_y + 82), center=True, max_w=card_w - 20)

        # เส้นคั่น
        pygame.draw.line(surface, (55, 60, 80), (card_x + 12, card_y + 110), (card_x + card_w - 12, card_y + 110), 1)

        # หัวข้อเงื่อนไข
        text(surface, "🎯 เงื่อนไขที่ต้องพิชิต:", FONT_XS, (255, 215, 60), (card_x + 14, card_y + 120))

        gy = card_y + 146
        for key, target in mission.goals.items():
            label = missions.format_goal_label(key, target)
            text(surface, f"• {label}", FONT_S, (230, 235, 245), (card_x + 14, gy), max_w=card_w - 24)
            gy += 32

        # ปุ่มเลือกแผน
        btn_rect = pygame.Rect(card_x + 14, card_rect.bottom - 52, card_w - 28, 40)
        button(surface, btn_rect, "รับภารกิจนี้", FONT_M, base=diff_info["border_color"],
               hover=btn_rect.collidepoint(mouse_pos))
        buttons[f"select_{i}"] = btn_rect

    # ปุ่มการทำงานด้านล่าง
    by = panel.bottom - 54
    btn_random = pygame.Rect(cx - 240, by, 150, 40)
    button(surface, btn_random, "🎲 สุ่มภารกิจ", FONT_S, base=(50, 80, 130),
           hover=btn_random.collidepoint(mouse_pos))
    buttons["random"] = btn_random

    btn_reroll = pygame.Rect(cx - 75, by, 150, 40)
    button(surface, btn_reroll, "🔄 สุ่มชุดใหม่", FONT_S, base=(75, 65, 110),
           hover=btn_reroll.collidepoint(mouse_pos))
    buttons["reroll"] = btn_reroll

    btn_back = pygame.Rect(cx + 90, by, 150, 40)
    button(surface, btn_back, "✕ กลับ", FONT_S, base=(110, 45, 50),
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
    surface.blit(sh, sh.get_rect(center=(cx + 3, 163)))
    text(surface, "DIG & TREASURE", FONT_XL, (255, 215, 60), (cx, 160), center=True)
    text(surface, "ขุดดิน ● หาสมบัติ ● พิชิตภารกิจผสม", FONT_M, (180, 210, 255),
         (cx, 215), center=True)

    pygame.draw.line(surface, (55, 80, 130), (cx - 180, 240), (cx + 180, 240), 1)

    buttons = {}
    y = 265
    labels = [("new", "🚀  เริ่มเกมใหม่ (เลือกภารกิจ)", (45, 130, 75))]
    if has_save:
        labels.append(("continue", "📂  เล่นต่อ (Continue)", (45, 85, 155)))
    labels.append(("quit", "✕  ออกจากเกม", (110, 45, 50)))

    for key, label, base_col in labels:
        rect = pygame.Rect(cx - 165, y, 330, 52)
        button(surface, rect, label, base=base_col,
               hover=rect.collidepoint(mouse_pos))
        buttons[key] = rect
        y += 68

    # ข้อความเวอร์ชันชิดขวาล่างไม่ล้นจอ
    text(surface, "v1.1 — Composite Missions Edition", FONT_XS, (85, 95, 120),
         (S.SCREEN_W - 16, S.SCREEN_H - 14), right=True, max_w=280)

    return buttons


# ─────────────────────────────────────────────────────────────────────────────
# เมนู Pause
# ─────────────────────────────────────────────────────────────────────────────

def draw_pause_menu(surface, mouse_pos, is_fullscreen=False):
    dim_overlay(surface, 175)
    cx = S.SCREEN_W // 2

    panel = pygame.Rect(cx - 170, 150, 340, 410)
    _panel(surface, panel, bg=(20, 22, 34), border=(60, 68, 100), alpha=240, radius=16)

    text(surface, "⏸  หยุดชั่วคราว", FONT_L, (235, 240, 255),
         (cx, panel.top + 34), center=True)
    pygame.draw.line(surface, (50, 55, 80),
                      (panel.left + 20, panel.top + 60), (panel.right - 20, panel.top + 60), 1)

    buttons = {}
    fs_label = "🖥  ออกจากเต็มจอ" if is_fullscreen else "🖥  เต็มจอ (F11)"
    labels = [
        ("resume",      "▶  เล่นต่อ",           (40, 130, 70)),
        ("fullscreen",  fs_label,               (55, 75, 130)),
        ("save_quit",   "💾  บันทึกและออก",     (130, 95, 35)),
        ("quit_nosave", "✕  ออกโดยไม่บันทึก",   (120, 42, 42)),
    ]
    y = panel.top + 80
    for key, label, base_col in labels:
        rect = pygame.Rect(cx - 140, y, 280, 44)
        button(surface, rect, label, base=base_col,
               hover=rect.collidepoint(mouse_pos))
        buttons[key] = rect
        y += 56

    # ปุ่มเปิด/ปิดเสียง
    muted    = assets.is_muted()
    btn_size = 46
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

def draw_shop_menu(surface, vehicle, mouse_pos):
    dim_overlay(surface, 185)
    cx = S.SCREEN_W // 2

    panel = pygame.Rect(cx - 240, 80, 480, 540)
    _panel(surface, panel, bg=(20, 22, 34), border=(65, 72, 110), alpha=248, radius=16)

    text(surface, "🔧  ร้านอัพเกรดรถขุด", FONT_L, (235, 240, 255),
         (cx, panel.top + 28), center=True)
    pygame.draw.line(surface, (50, 55, 80),
                      (panel.left + 20, panel.top + 54), (panel.right - 20, panel.top + 54), 1)
    text(surface, f"🪙  เหรียญของคุณ: {vehicle.coins:,}", FONT_M, (255, 215, 60),
         (cx, panel.top + 72), center=True)

    buttons = {}
    y = panel.top + 98

    upgrade_icons = {"capacity": "📦", "energy": "⚡", "power": "⛏", "speed": "🏎"}
    for key in ("capacity", "energy", "power", "speed"):
        cfg  = S.UPGRADES[key]
        lv   = vehicle.levels[key]
        cost = vehicle.upgrade_cost(key)
        can  = vehicle.can_upgrade(key)

        row_rect = pygame.Rect(panel.left + 16, y, panel.w - 32, 84)
        row_bg = (32, 35, 50) if not can else (28, 40, 38)
        _panel(surface, row_rect, bg=row_bg, border=(55, 60, 82), alpha=230, radius=10)

        # ไอคอน + ชื่อ
        icon_s = upgrade_icons.get(key, "●")
        name_txt = f"{icon_s}  {cfg['name']}"
        text(surface, name_txt, FONT_M, (230, 235, 255),
             (row_rect.left + 14, row_rect.top + 10), max_w=220)

        # จุดบอกระดับเลเวล (Pip dots)
        max_lv = cfg["max_level"]
        pip_x  = row_rect.left + 14
        pip_y  = row_rect.top + 38
        for i in range(max_lv):
            pip_col = (255, 200, 50) if i < lv else (45, 48, 62)
            pygame.draw.rect(surface, pip_col,
                             (pip_x + i * 18, pip_y, 14, 8), border_radius=3)

        # ราคา / สถานะ
        if cost is None:
            info_txt = "✓ MAX"
            info_col = (110, 220, 130)
        elif can:
            info_txt = f"{cost:,} 🪙"
            info_col = (255, 215, 60)
        else:
            info_txt = f"{cost:,} 🪙  (ไม่พอ)"
            info_col = (200, 110, 110)
        text(surface, info_txt, FONT_S, info_col,
             (row_rect.left + 14, row_rect.top + 56), max_w=220)

        # ปุ่มซื้อ
        base_col = (38, 145, 72) if can else (55, 55, 70)
        brect = pygame.Rect(row_rect.right - 96, row_rect.top + 18, 82, 46)
        btn_lbl = "ซื้อ" if cost is not None else "MAX"
        button(surface, brect, btn_lbl, FONT_M, base=base_col,
               hover=can and brect.collidepoint(mouse_pos))
        buttons[key] = brect
        y += 94

    close_rect = pygame.Rect(cx - 80, panel.bottom - 48, 160, 38)
    button(surface, close_rect, "ปิด  (E)", FONT_S, base=(55, 58, 80),
           hover=close_rect.collidepoint(mouse_pos))
    buttons["close"] = close_rect
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

    panel = pygame.Rect(cx - 260, 110, 520, 520)
    _panel(surface, panel, bg=(22, 18, 34), border=(80, 65, 120), alpha=245, radius=18)

    text(surface, title, FONT_XL, color, (cx, panel.top + 46), center=True)
    pygame.draw.line(surface, (65, 55, 95),
                      (panel.left + 30, panel.top + 76), (panel.right - 30, panel.top + 76), 1)
    text(surface, subtitle, FONT_M, (210, 215, 235),
         (cx, panel.top + 98), center=True, max_w=panel.w - 40)

    # กล่องสรุปภารกิจผสม
    y = panel.top + 130
    if mission:
        m_box = pygame.Rect(panel.left + 24, y, panel.w - 48, 112)
        _panel(surface, m_box, bg=mission.diff_info["bg_color"], border=mission.diff_info["border_color"], alpha=220, radius=10)

        text(surface, f"🎯 ภารกิจ: {mission.title} ({mission.diff_info['badge']})",
             FONT_M, (255, 255, 255), (m_box.left + 14, m_box.top + 10), max_w=m_box.w - 28)

        # รายการเงื่อนไข
        gy = m_box.top + 38
        goals = mission.get_goals_status()
        for i, (key, label, is_met, cur, tgt, prog_txt) in enumerate(goals):
            gx = m_box.left + 14 if i % 2 == 0 else m_box.centerx + 4
            gy_curr = gy + (i // 2) * 28
            chk_icon = "✓" if is_met else "✗"
            chk_col = (100, 240, 120) if is_met else (240, 90, 90)
            text(surface, f"{chk_icon} {prog_txt}", FONT_S, chk_col, (gx, gy_curr), max_w=m_box.w // 2 - 10)
        y += 126

    # สถิติรถขุด
    stats = [
        f"🪙  เหรียญที่ครอบครอง: {vehicle.coins:,}",
        f"⛏  หัวขุด Lv.{vehicle.levels['power']}    📦  ถัง Lv.{vehicle.levels['capacity']}",
        f"⚡  พลังงาน Lv.{vehicle.levels['energy']}    🏎  มอเตอร์ Lv.{vehicle.levels['speed']}",
    ]
    for s in stats:
        text(surface, s, FONT_S, (195, 205, 225), (cx, y), center=True, max_w=panel.w - 40)
        y += 30

    buttons = {}
    labels = [
        ("menu", "🏠  กลับเมนูหลัก", (40, 90, 160)),
        ("quit", "✕  ออกจากเกม",     (120, 42, 42)),
    ]
    y = panel.bottom - 110
    for key, label, base_col in labels:
        rect = pygame.Rect(cx - 150, y, 300, 46)
        button(surface, rect, label, base=base_col,
               hover=rect.collidepoint(mouse_pos))
        buttons[key] = rect
        y += 54
    return buttons
