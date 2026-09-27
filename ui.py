# -*- coding: utf-8 -*-
"""
ui.py
การแสดงผลทุกอย่างในเกม:
- เรนเดอร์แผนที่ด้วย Textures & Sprites จริง (หญ้า, ดิน, หิน, อุโมงค์, รอยแตก)
- เรนเดอร์รถขุดพร้อมหัวสว่านหมุน แสงไฟหน้ารถ และเอฟเฟกต์การสั่น
- อาคารบ้านและร้านค้าแบบ Pixel Art
- อนุภาค (Particles) และตัวเลขลอย (Floating Text)
- HUD แสดงพลังงาน ความจุ และเหรียญอย่างสวยงาม
- เมนูต่าง ๆ (หลัก, หยุดเกม, ร้านค้า, จบเกม)
"""
import math
import pygame
import settings as S
import assets

pygame.font.init()
FONT_S = None
FONT_M = None
FONT_L = None
FONT_XL = None


def init_fonts():
    global FONT_S, FONT_M, FONT_L, FONT_XL
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

    FONT_S = pygame.font.Font(thai_font_path, 16)
    FONT_M = pygame.font.Font(thai_font_path, 20)
    FONT_L = pygame.font.Font(thai_font_path, 28)
    FONT_XL = pygame.font.Font(thai_font_path, 42)


def text(surface, s, font, color, pos, center=False, shadow=True):
    if shadow:
        sh = font.render(s, True, (15, 15, 20))
        surface.blit(
            sh,
            (pos[0] + 1, pos[1] + 1) if not center else sh.get_rect(center=(pos[0] + 1, pos[1] + 1))
        )
    surf = font.render(s, True, color)
    rect = surf.get_rect(center=pos) if center else surf.get_rect(topleft=pos)
    surface.blit(surf, rect)
    return rect


# ----------------------------------------------------------------------
# ท้องฟ้าและฉากหลัง
# ----------------------------------------------------------------------
def draw_sky_and_bg(surface, camera_y):
    surface.fill(S.COLOR_SKY_BOTTOM)
    sky_h = S.SURFACE_ROW * S.TILE - camera_y + S.HUD_H
    if sky_h > 0:
        pygame.draw.rect(surface, S.COLOR_SKY_TOP, (0, S.HUD_H, S.SCREEN_W, min(sky_h, S.SCREEN_H)))
        # ก้อนเมฆ
        for i, cx in enumerate([90, 280, 480, 640]):
            cy = 40 + (i * 19) % 35
            _cloud(surface, cx, cy + S.HUD_H - camera_y * 0.25)


def _cloud(surface, x, y):
    if y < S.HUD_H - 40 or y > 240:
        return
    c = (255, 255, 255, 230)
    pygame.draw.circle(surface, c, (int(x), int(y)), 18)
    pygame.draw.circle(surface, c, (int(x) + 18, int(y) + 3), 14)
    pygame.draw.circle(surface, c, (int(x) - 16, int(y) + 4), 13)


# ----------------------------------------------------------------------
# แผนที่โลกใต้ดิน (ใช้ Texture PNG + รอยแตกเมื่อถูกเจาะ)
# ----------------------------------------------------------------------
def draw_world(surface, world, camera_y):
    first_row = max(0, int(camera_y // S.TILE) - 1)
    last_row = min(world.rows, first_row + (S.SCREEN_H // S.TILE) + 3)

    img_dirt = assets.get_image("dirt")
    img_grass = assets.get_image("grass")
    img_rock = assets.get_image("rock")
    img_tunnel = assets.get_image("tunnel")
    crack_1 = assets.get_image("crack_1")
    crack_2 = assets.get_image("crack_2")
    crack_3 = assets.get_image("crack_3")

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
    if res == S.RES_COIN:
        img = assets.get_image("res_coin")
    elif res == S.RES_GOLD:
        img = assets.get_image("res_gold")
    elif res == S.RES_DIAMOND:
        img = assets.get_image("res_diamond")
    else:
        return
    surface.blit(img, (sx, sy))


# ----------------------------------------------------------------------
# อาคารบ้าน (Depot) และร้านค้า (Shop)
# ----------------------------------------------------------------------
def draw_home_and_shop(surface, camera_y):
    base_y = S.SURFACE_ROW * S.TILE - camera_y + S.HUD_H - S.TILE * 2

    # บ้าน / คลังสินค้า (2x2 tiles)
    hx = S.HOME_COL * S.TILE
    home_img = assets.get_image("building_home")
    surface.blit(home_img, (hx, base_y))

    # ร้านค้าอัพเกรด (1x2 tiles)
    sx = S.SHOP_COL * S.TILE
    shop_img = assets.get_image("building_shop")
    surface.blit(shop_img, (sx, base_y))


# ----------------------------------------------------------------------
# รถขุด (Vehicle)
# ----------------------------------------------------------------------
def draw_vehicle(surface, vehicle, camera_y):
    vx = vehicle.x + vehicle.vibe_x
    vy = vehicle.y + vehicle.vibe_y - camera_y + S.HUD_H

    # ลำแสงไฟหน้ารถ ส่องไปในทิศที่หันหน้า
    fx, fy = vehicle.facing
    _draw_headlight(surface, vx, vy, fx, fy)

    # ตัวถังรถ
    body_img = assets.get_image("vehicle_body")
    rect = body_img.get_rect(center=(int(vx), int(vy)))
    surface.blit(body_img, rect)

    # หัวสว่านตามทิศทาง
    if fx == 1:
        drill_name = "drill_right"
        drill_pos = (rect.right + 2, rect.centery)
    elif fx == -1:
        drill_name = "drill_left"
        drill_pos = (rect.left - 2, rect.centery)
    elif fy == -1:
        drill_name = "drill_up"
        drill_pos = (rect.centerx, rect.top - 2)
    else:
        drill_name = "drill_down"
        drill_pos = (rect.centerx, rect.bottom + 2)

    drill_img = assets.get_image(drill_name)

    # อนิเมชันการหมุนสว่าน
    if vehicle.is_drilling or vehicle.is_moving:
        # สั่นขยับหัวสว่านเข้าออกเล็กน้อย
        offset = math.sin(vehicle.drill_anim * 2.0) * 2.0
        d_center = (
            int(drill_pos[0] + fx * offset),
            int(drill_pos[1] + fy * offset)
        )
    else:
        d_center = drill_pos

    d_rect = drill_img.get_rect(center=d_center)
    surface.blit(drill_img, d_rect)

    # ถ้ากำลังเจาะ มีประกายแสงสีขาวที่ปลายสว่าน
    if vehicle.is_drilling:
        tip = (d_center[0] + fx * 10, d_center[1] + fy * 10)
        pygame.draw.circle(surface, (255, 255, 230), tip, 5)
        pygame.draw.circle(surface, (255, 200, 50), tip, 8, 1)

    # สัญลักษณ์เตือนพลังงานหมด
    if vehicle.stalled:
        text(surface, "⚠ พลังงานหมด!", FONT_M, (255, 60, 60), (rect.centerx, rect.top - 18), center=True)


def _draw_headlight(surface, vx, vy, fx, fy):
    """วาดโคนแสงไฟหน้ารถ ส่องเข้าไปในความมืด"""
    beam_len = 80
    beam_w = 42
    light_surf = pygame.Surface((S.SCREEN_W, S.SCREEN_H), pygame.SRCALPHA)

    start = (vx + fx * 15, vy + fy * 15)
    if fx != 0:
        p1 = (start[0] + fx * beam_len, start[1] - beam_w / 2)
        p2 = (start[0] + fx * beam_len, start[1] + beam_w / 2)
    else:
        p1 = (start[0] - beam_w / 2, start[1] + fy * beam_len)
        p2 = (start[0] + beam_w / 2, start[1] + fy * beam_len)

    pygame.draw.polygon(light_surf, (255, 250, 200, 35), [start, p1, p2])
    surface.blit(light_surf, (0, 0))


# ----------------------------------------------------------------------
# HUD (แถบสถานะด้านบน)
# ----------------------------------------------------------------------
def draw_hud(surface, vehicle, depth):
    # แถบพื้นหลัง HUD
    pygame.draw.rect(surface, (20, 22, 28), (0, 0, S.SCREEN_W, S.HUD_H))
    pygame.draw.line(surface, (45, 48, 58), (0, S.HUD_H), (S.SCREEN_W, S.HUD_H), 2)

    pad = 12

    # ไอคอนและจำนวนทรัพยากรในถัง (ซ้ายสุด)
    icons = [
        ("res_coin", vehicle.cargo[S.RES_COIN]),
        ("res_gold", vehicle.cargo[S.RES_GOLD]),
        ("res_diamond", vehicle.cargo[S.RES_DIAMOND]),
    ]
    iy = 10
    for img_name, count in icons:
        icon_img = pygame.transform.scale(assets.get_image(img_name), (24, 24))
        surface.blit(icon_img, (pad, iy))
        text(surface, str(count), FONT_M, S.COLOR_WHITE, (pad + 28, iy + 1))
        iy += 25

    # เหรียญและความลึก (ตรงกลางซ้าย)
    text(surface, f"เหรียญ: {vehicle.coins}", FONT_M, (255, 220, 80), (pad + 80, 12))
    text(surface, f"ความลึก: {depth} ม.", FONT_S, (200, 210, 225), (pad + 80, 38))
    cap_col = (255, 90, 90) if vehicle.cargo_full() else (190, 235, 190)
    cap_txt = "เต็ม!" if vehicle.cargo_full() else f"{vehicle.cargo_count}/{vehicle.max_capacity}"
    text(surface, f"ความจุ: {cap_txt}", FONT_S, cap_col, (pad + 80, 62))

    # แถบพลังงาน + ความจุ (ขวา)
    bar_w, bar_h = 190, 16
    bx = S.SCREEN_W - bar_w - pad
    by = 16

    # 1. หลอดพลังงาน
    pygame.draw.rect(surface, S.COLOR_ENERGY_BG, (bx, by, bar_w, bar_h), border_radius=6)
    ratio = max(0.0, vehicle.energy / vehicle.max_energy)
    col = S.COLOR_ENERGY_BAR if ratio > 0.22 else (235, 60, 60)
    pygame.draw.rect(surface, col, (bx, by, int(bar_w * ratio), bar_h), border_radius=6)
    pygame.draw.rect(surface, (60, 65, 80), (bx, by, bar_w, bar_h), 1, border_radius=6)
    text(surface, f"พลังงาน {int(vehicle.energy)}/{int(vehicle.max_energy)}", FONT_S, S.COLOR_WHITE, (bx, by - 18))

    # 2. หลอดความจุถัง
    by2 = by + 30
    pygame.draw.rect(surface, S.COLOR_CARGO_BG, (bx, by2, bar_w, bar_h), border_radius=6)
    cratio = vehicle.cargo_count / vehicle.max_capacity if vehicle.max_capacity else 0.0
    c_col = (240, 70, 70) if vehicle.cargo_full() else S.COLOR_CARGO_BAR
    pygame.draw.rect(surface, c_col, (bx, by2, int(bar_w * cratio), bar_h), border_radius=6)
    pygame.draw.rect(surface, (60, 65, 80), (bx, by2, bar_w, bar_h), 1, border_radius=6)
    text(surface, "ถังเก็บของ", FONT_S, S.COLOR_WHITE, (bx, by2 - 18))

    # เลเวลของหัวขุดและมอเตอร์
    lvl_txt = f"หัวขุด Lv.{vehicle.levels['power']}   มอเตอร์ Lv.{vehicle.levels['speed']}"
    text(surface, lvl_txt, FONT_S, (185, 195, 215), (bx, by2 + 22))


def draw_aim_indicator(surface, vehicle, mouse_pos, camera_y):
    """วาดกรอบเล็งเป้าหมายเวลาคลิกเมาส์"""
    mx, my = mouse_pos
    if my <= S.HUD_H:
        return
    world_y = my - S.HUD_H + camera_y
    t_col = int(mx // S.TILE)
    t_row = int(world_y // S.TILE)
    if 0 <= t_col < S.COLS and 0 <= t_row < S.WORLD_ROWS:
        sx = t_col * S.TILE
        sy = t_row * S.TILE - camera_y + S.HUD_H
        rect = pygame.Rect(sx, sy, S.TILE, S.TILE)
        pygame.draw.rect(surface, (255, 230, 100, 140), rect, 2, border_radius=4)


def draw_hint(surface, msg):
    w = FONT_M.size(msg)[0] + 30
    rect = pygame.Rect((S.SCREEN_W - w) // 2, S.SCREEN_H - 58, w, 36)
    panel = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
    panel.fill((15, 18, 24, 215))
    surface.blit(panel, rect.topleft)
    pygame.draw.rect(surface, (60, 68, 85), rect, 1, border_radius=6)
    text(surface, msg, FONT_M, S.COLOR_WHITE, rect.center, center=True, shadow=False)


# ----------------------------------------------------------------------
# เมนูและปุ่มกด
# ----------------------------------------------------------------------
def button(surface, rect, label, font=None, base=(65, 75, 95), hover=False):
    font = font or FONT_M
    color = tuple(min(255, c + 25) for c in base) if hover else base
    pygame.draw.rect(surface, color, rect, border_radius=10)
    pygame.draw.rect(surface, (30, 32, 42), rect, 2, border_radius=10)
    text(surface, label, font, S.COLOR_WHITE, rect.center, center=True)
    return rect


def dim_overlay(surface, alpha=160):
    ov = pygame.Surface((S.SCREEN_W, S.SCREEN_H), pygame.SRCALPHA)
    ov.fill((10, 12, 18, alpha))
    surface.blit(ov, (0, 0))


def draw_main_menu(surface, has_save, mouse_pos):
    surface.fill((30, 48, 72))
    for i in range(6):
        pygame.draw.circle(surface, (255, 255, 255, 30), (80 + i * 130, 90 + (i % 2) * 40), 24)
    text(surface, "DIG & TREASURE", FONT_XL, S.COLOR_WHITE, (S.SCREEN_W // 2, 170), center=True)
    text(surface, "ขุดดิน หาสมบัติ อัพเกรดรถขุด", FONT_M, (210, 230, 255), (S.SCREEN_W // 2, 218), center=True)

    buttons = {}
    y = 300
    labels = [("new", "เริ่มเกมใหม่")]
    if has_save:
        labels.append(("continue", "เล่นต่อ (Continue)"))
    labels.append(("quit", "ออกจากเกม"))

    for key, label in labels:
        rect = pygame.Rect(S.SCREEN_W // 2 - 140, y, 280, 54)
        button(surface, rect, label, hover=rect.collidepoint(mouse_pos))
        buttons[key] = rect
        y += 70
    return buttons


def draw_pause_menu(surface, mouse_pos):
    dim_overlay(surface)
    text(surface, "หยุดชั่วคราว", FONT_L, S.COLOR_WHITE, (S.SCREEN_W // 2, 220), center=True)
    buttons = {}
    labels = [("resume", "เล่นต่อ"), ("save_quit", "บันทึกและออก"), ("quit_nosave", "ออกโดยไม่บันทึก")]
    y = 290
    for key, label in labels:
        rect = pygame.Rect(S.SCREEN_W // 2 - 150, y, 300, 54)
        button(surface, rect, label, hover=rect.collidepoint(mouse_pos))
        buttons[key] = rect
        y += 66
    return buttons


def draw_shop_menu(surface, vehicle, mouse_pos):
    dim_overlay(surface, 180)
    panel = pygame.Rect(S.SCREEN_W // 2 - 230, 110, 460, 490)
    pygame.draw.rect(surface, S.COLOR_UI_PANEL, panel, border_radius=14)
    pygame.draw.rect(surface, (25, 28, 38), panel, 3, border_radius=14)
    text(surface, "ร้านอัพเกรดรถขุด", FONT_L, S.COLOR_WHITE, (panel.centerx, panel.top + 34), center=True)
    text(surface, f"เหรียญของคุณ: {vehicle.coins}", FONT_M, (255, 220, 80), (panel.centerx, panel.top + 68), center=True)

    buttons = {}
    y = panel.top + 105
    for key in ("capacity", "energy", "power", "speed"):
        cfg = S.UPGRADES[key]
        lv = vehicle.levels[key]
        cost = vehicle.upgrade_cost(key)
        row = pygame.Rect(panel.left + 20, y, panel.w - 40, 78)
        pygame.draw.rect(surface, (35, 38, 50), row, border_radius=10)
        text(surface, f"{cfg['name']}  Lv.{lv}", FONT_M, S.COLOR_WHITE, (row.left + 16, row.top + 12))
        if cost is None:
            info = "อัพเกรดเต็มแล้ว"
        else:
            info = f"ราคา: {cost} เหรียญ  (+{cfg['step']})"
        text(surface, info, FONT_S, (195, 205, 220), (row.left + 16, row.top + 42))

        brect = pygame.Rect(row.right - 96, row.top + 18, 80, 42)
        can = vehicle.can_upgrade(key)
        base_color = (60, 150, 80) if can else (65, 68, 78)
        button(surface, brect, "ซื้อ" if cost is not None else "-", FONT_S, base=base_color,
               hover=can and brect.collidepoint(mouse_pos))
        buttons[key] = brect
        y += 90

    close_rect = pygame.Rect(panel.centerx - 70, panel.bottom - 56, 140, 42)
    button(surface, close_rect, "ปิด (E)", FONT_S, hover=close_rect.collidepoint(mouse_pos))
    buttons["close"] = close_rect
    return buttons


def draw_end_screen(surface, title, subtitle, vehicle, mouse_pos, color=(255, 220, 100)):
    surface.fill((22, 18, 28))
    text(surface, title, FONT_XL, color, (S.SCREEN_W // 2, 200), center=True)
    text(surface, subtitle, FONT_M, S.COLOR_WHITE, (S.SCREEN_W // 2, 250), center=True)

    stats = [
        f"เหรียญทั้งหมด: {vehicle.coins}",
        f"ระดับหัวขุด: Lv.{vehicle.levels['power']}   ระดับถังเก็บ: Lv.{vehicle.levels['capacity']}",
    ]
    y = 310
    for s in stats:
        text(surface, s, FONT_M, (210, 215, 230), (S.SCREEN_W // 2, y), center=True)
        y += 34

    buttons = {}
    labels = [("menu", "กลับเมนูหลัก"), ("quit", "ออกจากเกม")]
    y = 430
    for key, label in labels:
        rect = pygame.Rect(S.SCREEN_W // 2 - 140, y, 280, 54)
        button(surface, rect, label, hover=rect.collidepoint(mouse_pos))
        buttons[key] = rect
        y += 66
    return buttons


def draw_toast(surface, msg, timer):
    if timer <= 0:
        return
    alpha = min(255, int(timer * 255))
    panel = pygame.Surface((440, 44), pygame.SRCALPHA)
    panel.fill((25, 110, 55, min(220, alpha)))
    rect = panel.get_rect(center=(S.SCREEN_W // 2, S.HUD_H + 40))
    surface.blit(panel, rect.topleft)
    pygame.draw.rect(surface, (60, 200, 100, alpha), rect, 1, border_radius=6)
    text(surface, msg, FONT_M, S.COLOR_WHITE, rect.center, center=True, shadow=False)
