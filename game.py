# -*- coding: utf-8 -*-
"""
game.py
สถานะเกมและลอจิกหลัก (state machine):
MENU, CONTRACT, PLAYING, PAUSED, SHOP, GAME_OVER, VICTORY
ผูกระบบ Particle, เสียงเอฟเฟกต์, ภารกิจผสมประจำตา, การควบคุม และการเปลี่ยนฉากเข้าด้วยกัน
"""
import sys
import pygame
import settings as S
import ui
import assets
import missions
from world import World
from vehicle import Vehicle
from particles import ParticleSystem
import save_manager as SM

MENU = "menu"
CONTRACT = "contract"
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
        self.mission = None
        self.contract_options = []
        self.particles = ParticleSystem()
        self.camera_y = 0.0
        self.toast_msg = ""
        self.toast_timer = 0.0
        self.was_in_home = False
        self.buttons = {}
        self.end_title = ""
        self.end_sub = ""
        self.is_fullscreen = False
        # สำหรับแปลง mouse coordinates เมื่ออยู่ในโหมด fullscreen scaled
        self.display_scale = 1.0
        self.display_offset = (0, 0)
        assets.init()

    # ------------------------------------------------------------------
    def new_game(self, mission=None):
        self.world = World()
        self.vehicle = Vehicle(S.HOME_COL, S.SURFACE_ROW - 1)
        self.vehicle.on_resource_collected = self._on_resource_collected
        self.vehicle.on_dive_performed = self._on_dive_performed
        self.particles.clear()
        self.camera_y = 0.0
        self.was_in_home = True

        self.mission = mission if mission is not None else missions.get_random_mission()
        self.state = PLAYING
        self._toast(f"เริ่มภารกิจ: {self.mission.title} ({self.mission.diff_info['name']})")

    def load_game(self):
        try:
            data = SM.load_game()
            self.world = World.from_dict(data["world"])
            self.vehicle = Vehicle(S.HOME_COL, S.SURFACE_ROW - 1)
            self.vehicle.load_dict(data["vehicle"])
            self.vehicle.on_resource_collected = self._on_resource_collected
            self.vehicle.on_dive_performed = self._on_dive_performed
            self.particles.clear()
            self.camera_y = max(0.0, self.vehicle.y - S.SCREEN_H / 2)
            self.was_in_home = False

            extra = data.get("extra", {})
            if "mission" in extra and extra["mission"]:
                self.mission = missions.Mission.from_dict(extra["mission"])
            else:
                self.mission = missions.get_random_mission()

            self.state = PLAYING
            self._toast(f"โหลดเกมสำเร็จ: {self.mission.title}")
        except Exception as e:
            print(f"[Game] Load error: {e}, starting new game.")
            self.new_game()

    def save_and_quit(self):
        extra = {
            "mission": self.mission.to_dict() if self.mission else None
        }
        SM.save_game(self.world, self.vehicle, extra=extra)
        self.state = MENU
        self._toast("บันทึกเกมแล้ว")

    def _toast(self, msg, dur=2.5):
        self.toast_msg = msg
        self.toast_timer = dur

    def _on_resource_collected(self, res):
        if self.mission:
            self.mission.add_mined_resource(res)
            for key, label, is_met, cur, tgt, prog_txt in self.mission.get_goals_status():
                if is_met and cur == tgt:
                    self._toast(f"🎯 สำเร็จเงื่อนไข: {label}!")
                    break

    def _on_dive_performed(self):
        if self.mission:
            self.mission.add_dive()
            for key, label, is_met, cur, tgt, prog_txt in self.mission.get_goals_status():
                if key == "dives" and is_met and cur == tgt:
                    self._toast(f"🎯 สำเร็จเงื่อนไข: {label}!")

    # ------------------------------------------------------------------
    def _to_game_pos(self, screen_pos):
        """แปลงพิกัด mouse จากหน้าจอจริง → game surface space (รองรับ fullscreen scaling)"""
        sx, sy = screen_pos
        ox, oy = self.display_offset
        scale = self.display_scale
        if scale == 0:
            return screen_pos
        return ((sx - ox) / scale, (sy - oy) / scale)

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
        raw_pos = getattr(event, "pos", pygame.mouse.get_pos())
        mouse_pos = self._to_game_pos(raw_pos)

        if self.state == MENU:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for key, rect in self.buttons.items():
                    if rect.collidepoint(mouse_pos):
                        if key == "new":
                            self.contract_options = missions.get_three_contract_options()
                            self.state = CONTRACT
                        elif key == "continue":
                            self.load_game()
                        elif key == "quit":
                            pygame.quit()
                            sys.exit()
            return

        if self.state == CONTRACT:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.state = MENU
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for key, rect in self.buttons.items():
                    if rect.collidepoint(mouse_pos):
                        if key == "select_0":
                            self.new_game(self.contract_options[0])
                        elif key == "select_1":
                            self.new_game(self.contract_options[1])
                        elif key == "select_2":
                            self.new_game(self.contract_options[2])
                        elif key == "random":
                            self.new_game(missions.get_random_mission())
                        elif key == "reroll":
                            self.contract_options = missions.get_three_contract_options()
                        elif key == "back":
                            self.state = MENU
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
                        elif key == "fullscreen":
                            pygame.event.post(pygame.event.Event(
                                pygame.KEYDOWN,
                                key=pygame.K_F11, mod=0, unicode=""
                            ))
                        elif key == "save_quit":
                            self.save_and_quit()
                        elif key == "quit_nosave":
                            pygame.quit()
                            sys.exit()
                        elif key == "mute":
                            assets.toggle_mute()
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

        if (dx, dy) != (0, 0):
            return (dx, dy)

        # ควบคุมด้วยเมาส์ (คลิกค้างเพื่อเดินตาม)
        if pygame.mouse.get_pressed()[0]:
            mx, my = self._to_game_pos(pygame.mouse.get_pos())
            # หักลบส่วนหัว HUD ออกก่อนคำนวณตำแหน่งในโลก
            world_mouse_y = my - S.HUD_H + self.camera_y
            diff_x = mx - self.vehicle.x
            diff_y = world_mouse_y - self.vehicle.y

            if abs(diff_x) > 14 or abs(diff_y) > 14:
                dx = diff_x
                dy = diff_y

        return (dx, dy)

    def _shift_pressed(self):
        keys = pygame.key.get_pressed()
        return keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]

    # ------------------------------------------------------------------
    def update(self, dt):
        if self.toast_timer > 0:
            self.toast_timer -= dt

        if self.state != PLAYING:
            return

        direction = self._input_direction()
        self.vehicle.update(dt, self.world, direction, self.particles, shift_pressed=self._shift_pressed())
        self.particles.update(dt)

        # คำนวณความลึกและอัปเดตภารกิจ
        depth = max(0, int(self.vehicle.y // S.TILE) - S.SURFACE_ROW)
        if self.mission:
            self.mission.update_from_game(self.vehicle, depth)

        # การเลื่อนกล้องตามรถขุดในแนวตั้งอย่างนุ่มนวล
        target_cam = max(0.0, self.vehicle.y - S.SCREEN_H / 2.0)
        self.camera_y += (target_cam - self.camera_y) * min(1.0, dt * 7.0)
        self.camera_y = max(0.0, self.camera_y)

        # ตรวจสอบการกลับมาที่บ้าน (ขายของ + เติมพลังงาน + ตรวจเงื่อนไขชนะ)
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

            # ตรวจสอบเงื่อนไขชนะจากภารกิจผสม
            if self.mission and self.mission.is_completed():
                self.end_title = "ภารกิจสำเร็จสมบูรณ์!"
                self.end_sub = f"คุณพิชิตภารกิจ [{self.mission.title}] ระดับ{self.mission.diff_info['name']} สำเร็จครบทุกข้อ!"
                self.state = VICTORY
                assets.play_sound("upgrade", volume=0.95)
            elif S.END_ON_TARGET_RESOURCE and self.vehicle.coins >= S.VICTORY_COIN_TARGET:
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
        mouse_pos = self._to_game_pos(pygame.mouse.get_pos())

        if self.state == MENU:
            self.buttons = ui.draw_main_menu(self.screen, SM.save_exists(), mouse_pos)
            return

        if self.state == CONTRACT:
            # วาดฉากหลังเมนูแล้วเปิดหน้าต่างเลือกสัญญาภารกิจ
            ui.draw_main_menu(self.screen, False, mouse_pos)
            self.buttons = ui.draw_contract_menu(self.screen, self.contract_options, mouse_pos)
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

        # วาด HUD ด้านบน (รวมแถบภารกิจผสม)
        depth = max(0, int(self.vehicle.y // S.TILE) - S.SURFACE_ROW)
        ui.draw_hud(self.screen, self.vehicle, depth, self.mission)

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
            self.buttons = ui.draw_pause_menu(self.screen, mouse_pos, is_fullscreen=self.is_fullscreen)
        elif self.state == SHOP:
            self.buttons = ui.draw_shop_menu(self.screen, self.vehicle, mouse_pos)
        elif self.state == GAME_OVER:
            self.buttons = ui.draw_end_screen(self.screen, self.end_title, self.end_sub, self.vehicle,
                                               mouse_pos, mission=self.mission, color=(255, 100, 90))
        elif self.state == VICTORY:
            self.buttons = ui.draw_end_screen(self.screen, self.end_title, self.end_sub, self.vehicle,
                                               mouse_pos, mission=self.mission, color=(255, 220, 100))
        else:
            self.buttons = {}
