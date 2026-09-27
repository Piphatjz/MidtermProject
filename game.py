# -*- coding: utf-8 -*-
"""
game.py
สถานะเกมและลอจิกหลัก (state machine): MENU, PLAYING, PAUSED, SHOP, GAME_OVER, VICTORY
ผูกระบบ Particle, เสียงเอฟเฟกต์, การควบคุม และการเปลี่ยนฉากเข้าด้วยกัน
"""
import sys
import pygame
import settings as S
import ui
import assets
from world import World
from vehicle import Vehicle
from particles import ParticleSystem
import save_manager as SM

MENU = "menu"
PLAYING = "playing"
PAUSED = "paused"
SHOP = "shop"
GAME_OVER = "game_over"
VICTORY = "victory"


class Game:
    def __init__(self, screen):
        self.screen = screen
        self.state = MENU
        self.world = None
        self.vehicle = None
        self.particles = ParticleSystem()
        self.camera_y = 0.0
        self.toast_msg = ""
        self.toast_timer = 0.0
        self.was_in_home = False
        self.buttons = {}
        self.end_title = ""
        self.end_sub = ""
        assets.init()

    # ------------------------------------------------------------------
    def new_game(self):
        self.world = World()
        self.vehicle = Vehicle(S.HOME_COL, S.SURFACE_ROW - 1)
        self.particles.clear()
        self.camera_y = 0.0
        self.was_in_home = True
        self.state = PLAYING
        self._toast("เริ่มเกมใหม่! บังคับด้วย WASD/ลูกศร หรือคลิกเมาส์ค้างไว้")

    def load_game(self):
        try:
            data = SM.load_game()
            self.world = World.from_dict(data["world"])
            self.vehicle = Vehicle(S.HOME_COL, S.SURFACE_ROW - 1)
            self.vehicle.load_dict(data["vehicle"])
            self.particles.clear()
            self.camera_y = max(0.0, self.vehicle.y - S.SCREEN_H / 2)
            self.was_in_home = False
            self.state = PLAYING
            self._toast("โหลดเกมสำเร็จ")
        except Exception as e:
            print(f"[Game] Load error: {e}, starting new game.")
            self.new_game()

    def save_and_quit(self):
        SM.save_game(self.world, self.vehicle)
        self.state = MENU
        self._toast("บันทึกเกมแล้ว")

    def _toast(self, msg, dur=2.2):
        self.toast_msg = msg
        self.toast_timer = dur

    # ------------------------------------------------------------------
    def home_zone(self):
        # โซนบ้านสำหรับขายของและเติมพลังงาน (2x2 tiles)
        return pygame.Rect(
            S.HOME_COL * S.TILE,
            (S.SURFACE_ROW - 1) * S.TILE,
            S.TILE * 2,
            S.TILE * 2
        )

    def shop_zone(self):
        # โซนร้านค้าสำหรับกด E อัพเกรด (1x2 tiles)
        return pygame.Rect(
            S.SHOP_COL * S.TILE,
            (S.SURFACE_ROW - 1) * S.TILE,
            S.TILE,
            S.TILE * 2
        )

    # ------------------------------------------------------------------
    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()

        if self.state == MENU:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for key, rect in self.buttons.items():
                    if rect.collidepoint(mouse_pos):
                        if key == "new":
                            self.new_game()
                        elif key == "continue":
                            self.load_game()
                        elif key == "quit":
                            pygame.quit()
                            sys.exit()
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.state == PLAYING:
                    self.state = PAUSED
                elif self.state == PAUSED:
                    self.state = PLAYING
                elif self.state == SHOP:
                    self.state = PLAYING
            elif event.key == pygame.K_e and self.state in (PLAYING, SHOP):
                if self.state == PLAYING and self.vehicle.rect.colliderect(self.shop_zone()):
                    self.state = SHOP
                elif self.state == SHOP:
                    self.state = PLAYING

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.state == PAUSED:
                for key, rect in self.buttons.items():
                    if rect.collidepoint(mouse_pos):
                        if key == "resume":
                            self.state = PLAYING
                        elif key == "save_quit":
                            self.save_and_quit()
                        elif key == "quit_nosave":
                            pygame.quit()
                            sys.exit()
            elif self.state == SHOP:
                for key, rect in self.buttons.items():
                    if rect.collidepoint(mouse_pos):
                        if key == "close":
                            self.state = PLAYING
                        else:
                            self.vehicle.do_upgrade(key)
            elif self.state in (GAME_OVER, VICTORY):
                for key, rect in self.buttons.items():
                    if rect.collidepoint(mouse_pos):
                        if key == "menu":
                            self.state = MENU
                        elif key == "quit":
                            pygame.quit()
                            sys.exit()

    # ------------------------------------------------------------------
    def _input_direction(self):
        keys = pygame.key.get_pressed()
        dx = dy = 0

        # ควบคุมด้วยคีย์บอร์ด
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += 1

        # ควบคุมด้วยเมาส์ (ถ้าไม่ได้กดปุ่มคีย์บอร์ดอยู่)
        if dx == 0 and dy == 0 and pygame.mouse.get_pressed()[0]:
            mx, my = pygame.mouse.get_pos()
            # พิกัดรถขุดบนหน้าจอ
            v_screen_x = self.vehicle.x
            v_screen_y = self.vehicle.y - self.camera_y + S.HUD_H

            diff_x = mx - v_screen_x
            diff_y = my - v_screen_y

            # Deadzone ป้องกันการกระตุกเมื่อเมาส์อยู่ใกล้ตัวรถมากเกินไป
            if abs(diff_x) > 14 or abs(diff_y) > 14:
                dx = diff_x
                dy = diff_y

        return (dx, dy)

    # ------------------------------------------------------------------
    def update(self, dt):
        if self.toast_timer > 0:
            self.toast_timer -= dt

        if self.state != PLAYING:
            return

        direction = self._input_direction()
        self.vehicle.update(dt, self.world, direction, self.particles)
        self.particles.update(dt)

        # การเลื่อนกล้องตามรถขุดในแนวตั้งอย่างนุ่มนวล
        target_cam = max(0.0, self.vehicle.y - S.SCREEN_H / 2.0)
        self.camera_y += (target_cam - self.camera_y) * min(1.0, dt * 7.0)
        self.camera_y = max(0.0, min(self.camera_y, S.WORLD_PIXEL_H - S.SCREEN_H))

        # ตรวจสอบการกลับมาที่บ้าน (ขายของ + เติมพลังงาน)
        in_home = self.vehicle.rect.colliderect(self.home_zone())
        if in_home and not self.was_in_home:
            earned = self.vehicle.sell_cargo()
            self.vehicle.refuel()
            assets.play_sound("refuel", volume=0.7)
            if earned > 0:
                assets.play_sound("sell", volume=0.85)
                self._toast(f"ขายแร่ได้ {earned} เหรียญ! เติมพลังงานเต็มแล้ว")
                hx = (S.HOME_COL + 1) * S.TILE
                hy = (S.SURFACE_ROW - 0.5) * S.TILE
                self.particles.add_floating_text(f"+{earned} เหรียญ!", hx, hy, (255, 230, 80))
            else:
                self._toast("เติมพลังงานเต็มแล้ว")

            if S.END_ON_TARGET_RESOURCE and self.vehicle.coins >= S.VICTORY_COIN_TARGET:
                self.end_title = "ขุดเจอสมบัติมหาศาล!"
                self.end_sub = f"คุณสะสมเหรียญครบ {S.VICTORY_COIN_TARGET} เหรียญแล้ว!"
                self.state = VICTORY
        self.was_in_home = in_home

        # ตรวจสอบพลังงานหมด
        if S.END_ON_ENERGY_EMPTY and self.vehicle.stalled and not in_home:
            self.end_title = "พลังงานหมด!"
            self.end_sub = "รถขุดติดอยู่ใต้ดิน ต้องเริ่มใหม่หรือโหลดเซฟล่าสุด"
            self.state = GAME_OVER

    # ------------------------------------------------------------------
    def draw(self):
        mouse_pos = pygame.mouse.get_pos()
        if self.state == MENU:
            self.buttons = ui.draw_main_menu(self.screen, SM.save_exists(), mouse_pos)
            return

        # วาดฉากเกม
        ui.draw_sky_and_bg(self.screen, self.camera_y)
        ui.draw_world(self.screen, self.world, self.camera_y)
        ui.draw_home_and_shop(self.screen, self.camera_y)
        ui.draw_vehicle(self.screen, self.vehicle, self.camera_y)

        # วาดอนุภาคและข้อความลอย
        self.particles.draw(self.screen, self.camera_y)

        # วาดเป้าหมายเมาส์เมื่อคลิกค้างไว้
        if self.state == PLAYING and pygame.mouse.get_pressed()[0]:
            ui.draw_aim_indicator(self.screen, self.vehicle, mouse_pos, self.camera_y)

        # วาด HUD ด้านบน
        depth = max(0, int(self.vehicle.y // S.TILE) - S.SURFACE_ROW)
        ui.draw_hud(self.screen, self.vehicle, depth)

        # แสดงข้อความคำใบ้ (Hint)
        blocked_by_rock = (
            self.state == PLAYING
            and self.vehicle.drilling_target is not None
            and not self.vehicle.is_drilling
            and not self.vehicle.stalled
        )
        if self.state == PLAYING and self.vehicle.rect.colliderect(self.shop_zone()):
            ui.draw_hint(self.screen, "กด E เพื่อเปิดร้านอัพเกรด")
        elif blocked_by_rock:
            ui.draw_hint(self.screen, f"หินแข็งเกินไป! อัพเกรดหัวขุดถึง Lv.{S.ROCK_MIN_DRILL_LEVEL} ที่ร้านก่อน")
        elif self.vehicle.cargo_full() and self.state == PLAYING:
            ui.draw_hint(self.screen, "ถังเต็มแล้ว! กลับบ้านเพื่อขายของ")
        elif self.vehicle.stalled and self.state == PLAYING:
            ui.draw_hint(self.screen, "พลังงานหมด! รอโดนจบเกม หรือกด ESC")

        ui.draw_toast(self.screen, self.toast_msg, self.toast_timer)

        # วาดเมนูตาม State
        if self.state == PAUSED:
            self.buttons = ui.draw_pause_menu(self.screen, mouse_pos)
        elif self.state == SHOP:
            self.buttons = ui.draw_shop_menu(self.screen, self.vehicle, mouse_pos)
        elif self.state == GAME_OVER:
            self.buttons = ui.draw_end_screen(self.screen, self.end_title, self.end_sub, self.vehicle,
                                               mouse_pos, color=(255, 100, 90))
        elif self.state == VICTORY:
            self.buttons = ui.draw_end_screen(self.screen, self.end_title, self.end_sub, self.vehicle,
                                               mouse_pos, color=(255, 220, 100))
        else:
            self.buttons = {}
