# -*- coding: utf-8 -*-
"""
game.py
สถานะเกมและลอจิกหลัก (state machine):
MENU, PLAY_SELECT, CONTRACT, PLAYING, PAUSED, SHOP, GARAGE, HOW_TO_PLAY,
LOAD_MENU, SAVE_MENU, SETTINGS_MENU, GAME_OVER, VICTORY
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
PLAY_SELECT = "play_select"
CONTRACT = "contract"
PLAYING = "playing"
PAUSED = "paused"
SHOP = "shop"
GARAGE = "garage"
HOW_TO_PLAY = "how_to_play"
LOAD_MENU = "load_menu"
SAVE_MENU = "save_menu"
SETTINGS_MENU = "settings_menu"
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
        # ตัวแปรระบบอู่แต่งรถขุด (Garage & Customization)
        self.garage_tab = "color"
        self.shop_tab = "upgrades"
        self.game_mode = "mission"  # "mission" หรือ "classic"
        self.unlocked_floor = 1     # ชั้นสูงสุดที่ปลดล็อคแล้วในโหมดคลาสสิก
        self.previous_state = MENU

        # ระบบเซฟ 5 สล็อต (Multi-slot Save System)
        latest_s = SM.get_latest_slot()
        self.current_slot = latest_s if latest_s is not None else 1
        self.confirm_delete_slot = None
        self.confirm_overwrite_slot = None

        assets.init()
        # โหลดการตั้งค่าระบบเสียง
        try:
            settings_data = SM.load_settings()
            assets.set_muted(settings_data.get("muted", False))
        except Exception:
            pass

    # ------------------------------------------------------------------
    def _get_first_available_slot(self):
        """ค้นหาช่องเซฟที่ว่างช่องแรก (1 - 5) เพื่อใช้เป็นสล็อตเริ่มต้นของเกมใหม่"""
        try:
            slots = SM.list_slots()
            for s in slots:
                if s.get("empty", False):
                    return s["slot_id"]
        except Exception:
            pass
        return 1

    def new_game(self, mission=None):
        prev_color = self.vehicle.color_id if self.vehicle else getattr(S, "DEFAULT_VEHICLE_COLOR", "yellow")
        prev_type = self.vehicle.vehicle_type if self.vehicle else getattr(S, "DEFAULT_VEHICLE_TYPE", "standard")
        prev_drill = self.vehicle.drill_head if self.vehicle else getattr(S, "DEFAULT_DRILL_HEAD", "spiral")

        self.current_slot = self._get_first_available_slot()
        self.game_mode = "mission"
        self.unlocked_floor = 1
        self.shop_tab = "upgrades"
        self.world = World(game_mode="mission", unlocked_floor=1)
        self.vehicle = Vehicle(
            S.HOME_COL, S.SURFACE_ROW - 1,
            color_id=prev_color,
            vehicle_type=prev_type,
            drill_head=prev_drill,
        )
        self.vehicle.on_resource_collected = self._on_resource_collected
        self.vehicle.on_dive_performed = self._on_dive_performed
        self.particles.clear()
        self.camera_y = 0.0
        self.was_in_home = True

        self.mission = mission if mission is not None else missions.get_random_mission()
        self.state = PLAYING
        self._toast(f"เริ่มภารกิจ: {self.mission.title} ({self.mission.diff_info['name']}) [ช่อง {self.current_slot}]")

    def new_game_classic(self):
        """เริ่มเล่นโหมดคลาสสิก: เล่นได้ไม่จำกัด (Unlimited) สะสมเงินเพื่อปลดล็อคชั้นความลึก"""
        prev_color = self.vehicle.color_id if self.vehicle else getattr(S, "DEFAULT_VEHICLE_COLOR", "yellow")
        prev_type = self.vehicle.vehicle_type if self.vehicle else getattr(S, "DEFAULT_VEHICLE_TYPE", "standard")
        prev_drill = self.vehicle.drill_head if self.vehicle else getattr(S, "DEFAULT_DRILL_HEAD", "spiral")

        self.current_slot = self._get_first_available_slot()
        self.game_mode = "classic"
        self.unlocked_floor = 1
        self.mission = None
        self.shop_tab = "upgrades"
        self.world = World(game_mode="classic", unlocked_floor=1)
        self.vehicle = Vehicle(
            S.HOME_COL, S.SURFACE_ROW - 1,
            color_id=prev_color,
            vehicle_type=prev_type,
            drill_head=prev_drill,
        )
        self.vehicle.on_resource_collected = self._on_resource_collected
        self.vehicle.on_dive_performed = self._on_dive_performed
        self.particles.clear()
        self.camera_y = 0.0
        self.was_in_home = True

        self.state = PLAYING
        self._toast(f"เริ่มโหมดคลาสสิก! ขุดอิสระไร้ขีดจำกัด [ช่อง {self.current_slot}]", dur=3.5)

    def unlock_next_floor(self):
        """ปลดล็อคชั้นความลึกถัดไปในโหมดคลาสสิก (หักเหรียญและเปิดประตูกั้น)"""
        if self.game_mode != "classic" or self.world is None or self.vehicle is None:
            return False

        next_floor = self.unlocked_floor + 1
        floor_info = S.get_floor_info(next_floor)
        cost = floor_info["unlock_cost"]

        if self.vehicle.coins < cost:
            diff = cost - self.vehicle.coins
            self._toast(f"เหรียญไม่พอ! ปลดล็อคชั้น {next_floor} ต้องใช้ {cost:,} เหรียญ (ขาดอีก {diff:,})", dur=3.0)
            assets.play_sound("rock_clink", volume=0.7)
            return False

        self.vehicle.coins -= cost
        self.unlocked_floor = next_floor
        opened_blocks = self.world.unlock_barrier(next_floor)
        assets.play_sound("upgrade", volume=0.95)

        # Effect: ข้อความลอยและประกายดาวฉลองการเปิดประตู
        prev_info = S.get_floor_info(next_floor - 1)
        target_depth = prev_info["max_depth"]
        bx = (S.COLS // 2) * S.TILE
        by = (S.SURFACE_ROW + target_depth) * S.TILE
        self.particles.add_floating_text(f"ปลดล็อคชั้น {next_floor}!", bx, by - 24, (255, 215, 60))
        self.particles.add_floating_text(f"-{cost:,} เหรียญ", self.vehicle.x, self.vehicle.y - 20, (255, 120, 120))

        for c in range(0, S.COLS, 2):
            self.particles.spawn_spark(c * S.TILE + S.TILE // 2, by + S.TILE // 2, (90, 220, 255))
            self.particles.spawn_diamond_spark(c * S.TILE + S.TILE // 2, by + S.TILE // 2)

        self._toast(f"ปลดล็อค {floor_info['name']} สำเร็จ! เปิดทางสู่ความลึก {floor_info['min_depth']}ม.+", dur=3.8)
        return True

    def get_barrier_near_vehicle(self):
        """คืนค่า (next_floor, floor_info, barrier_row) หากรถขุดอยู่ใกล้ประตูกั้นชั้นที่ล็อคอยู่"""
        if getattr(self, "game_mode", "mission") != "classic" or self.world is None or self.vehicle is None:
            return None
        next_floor = self.unlocked_floor + 1
        prev_floor_info = S.get_floor_info(self.unlocked_floor)
        barrier_depth = prev_floor_info["max_depth"]
        barrier_row = S.SURFACE_ROW + barrier_depth

        v_col, v_row = self.vehicle.grid_pos()
        if 0 <= barrier_row - v_row <= 2:
            return next_floor, S.get_floor_info(next_floor), barrier_row
        return None

    def toggle_mute(self):
        """สลับสถานะเปิด/ปิดเสียงทั้งหมด และบันทึกลง settings.json อัตโนมัติ"""
        assets.toggle_mute()
        muted = assets.is_muted()
        SM.save_settings({"muted": muted})
        if muted:
            self._toast("ปิดเสียงทั้งหมด [M]", dur=1.8)
        else:
            self._toast("เปิดเสียงทั้งหมด [M]", dur=1.8)

    def toggle_fullscreen(self):
        """สลับโหมดเต็มจอโดยส่ง event K_F11"""
        pygame.event.post(pygame.event.Event(
            pygame.KEYDOWN,
            key=pygame.K_F11, mod=0, unicode=""
        ))

    def save_slot(self, slot_id=None):
        """บันทึกข้อมูลเกมลงในสล็อตที่ระบุ (1 - 5) หากไม่ระบุจะใช้ self.current_slot"""
        if slot_id is None:
            slot_id = self.current_slot
        if self.world is None or self.vehicle is None:
            return False

        extra = {
            "mission": self.mission.to_dict() if self.mission else None,
            "game_mode": self.game_mode,
            "unlocked_floor": self.unlocked_floor,
        }
        ok = SM.save_slot(slot_id, self.world, self.vehicle, extra=extra)
        if ok:
            self.current_slot = slot_id
            assets.play_sound("upgrade", volume=0.6)
            return True
        return False

    def load_slot(self, slot_id):
        """โหลดข้อมูลเกมจากสล็อตที่ระบุ (1 - 5) และปรับคืนค่าสถานะเกมตามโหมดที่บันทึก"""
        ok, data, meta = SM.load_slot(slot_id)
        if not ok or not data:
            err = meta.get("error", "ไฟล์มีปัญหาหรือไม่พบไฟล์")
            self._toast(f"โหลดช่อง {slot_id} ไม่สำเร็จ: {err}")
            return False

        try:
            self.world = World.from_dict(data["world"])
            self.vehicle = Vehicle(S.HOME_COL, S.SURFACE_ROW - 1)
            self.vehicle.load_dict(data["vehicle"])
            self.vehicle.on_resource_collected = self._on_resource_collected
            self.vehicle.on_dive_performed = self._on_dive_performed
            self.particles.clear()
            self.camera_y = max(0.0, self.vehicle.y - S.SCREEN_H / 2)
            self.was_in_home = False
            self.shop_tab = "upgrades"

            extra = data.get("extra", {})
            self.game_mode = extra.get("game_mode", "classic" if not extra.get("mission") else "mission")
            self.unlocked_floor = extra.get("unlocked_floor", getattr(self.world, "unlocked_floor", 1))

            if "mission" in extra and extra["mission"]:
                self.mission = missions.Mission.from_dict(extra["mission"])
            else:
                self.mission = None if self.game_mode == "classic" else missions.get_random_mission()

            self.current_slot = slot_id
            self.state = PLAYING
            assets.play_sound("click", volume=0.6)
            if self.game_mode == "classic":
                self._toast(f"โหลดช่อง {slot_id} สำเร็จ: โหมดคลาสสิก (ชั้นที่ {self.unlocked_floor})")
            else:
                self._toast(f"โหลดช่อง {slot_id} สำเร็จ: {self.mission.title if self.mission else 'โหมดภารกิจ'}")
            return True
        except Exception as e:
            self._toast(f"เกิดข้อผิดพลาดในการโหลดช่อง {slot_id}: {e}")
            return False

    def load_game(self, slot_id=None):
        """โหลดเกม (หากไม่ระบุ slot_id จะเลือกโหลดสล็อตที่บันทึกล่าสุด)"""
        target = slot_id
        if target is None:
            target = SM.get_latest_slot() or self.current_slot
        if not self.load_slot(target):
            self.new_game()

    def save_and_quit(self):
        """บันทึกลงช่องปัจจุบันและกลับสู่เมนูหลัก"""
        self.save_slot(self.current_slot)
        self.state = MENU
        self._toast(f"บันทึกเกมลงช่อง {self.current_slot} และออกสู่เมนูหลัก")

    def _toast(self, msg, dur=2.5):
        self.toast_msg = msg
        self.toast_timer = dur

    def _check_mission_notifications(self):
        if not self.mission:
            return
        newly_met = self.mission.pop_newly_completed_goals()
        if newly_met:
            if self.mission.is_completed():
                self._toast("ภารกิจครบทุกข้อแล้ว! ขับกลับฐานบ้านเพื่อรับชัยชนะ!", dur=3.5)
            else:
                self._toast(f"สำเร็จเงื่อนไข: {newly_met[0]}!")

    def _on_resource_collected(self, res):
        if self.mission:
            self.mission.add_mined_resource(res)
            self._check_mission_notifications()

    def _on_dive_performed(self):
        if self.mission:
            self.mission.add_dive()
            self._check_mission_notifications()

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

        # สลับเปิด/ปิดเสียงได้ทุกหน้าด้วยปุ่ม M
        if event.type == pygame.KEYDOWN and event.key == pygame.K_m:
            self.toggle_mute()
            return

        # 1. หน้าต่างเมนูหลัก (Main Menu: Play, Load, Setting, Exit)
        if self.state == MENU:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for key, rect in self.buttons.items():
                    if rect.collidepoint(mouse_pos):
                        if key == "play":
                            self.previous_state = MENU
                            self.state = PLAY_SELECT
                            assets.play_sound("click", volume=0.5)
                        elif key in ("load", "load_game", "continue"):
                            self.previous_state = MENU
                            self.confirm_delete_slot = None
                            self.confirm_overwrite_slot = None
                            self.state = LOAD_MENU
                            assets.play_sound("click", volume=0.5)
                        elif key in ("setting", "how_to_play"):
                            self.previous_state = MENU
                            self.state = SETTINGS_MENU
                            assets.play_sound("click", volume=0.5)
                        elif key in ("exit", "quit"):
                            pygame.quit()
                            sys.exit()
                        elif key == "classic":  # compatibility
                            self.new_game_classic()
                        elif key == "new":      # compatibility
                            self.contract_options = missions.get_three_contract_options()
                            self.state = CONTRACT
            return

        # 2. หน้าต่างเลือกโหมดการเล่น (Play Select: Mission Contracts / Classic Endless)
        if self.state == PLAY_SELECT:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.state = MENU
                assets.play_sound("click", volume=0.5)
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for key, rect in self.buttons.items():
                    if rect.collidepoint(mouse_pos):
                        if key == "mode_mission":
                            self.contract_options = missions.get_three_contract_options()
                            self.previous_state = PLAY_SELECT
                            self.state = CONTRACT
                            assets.play_sound("click", volume=0.5)
                        elif key == "mode_classic":
                            self.new_game_classic()
                            assets.play_sound("click", volume=0.5)
                        elif key == "back":
                            self.state = MENU
                            assets.play_sound("click", volume=0.5)
            return

        # 3. หน้าต่างตั้งค่าระบบ (Settings Menu)
        if self.state == SETTINGS_MENU:
            parent = MENU if self.previous_state not in (PAUSED, MENU) else self.previous_state
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.state = parent
                assets.play_sound("click", volume=0.5)
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for key, rect in self.buttons.items():
                    if rect.collidepoint(mouse_pos):
                        if key == "toggle_mute":
                            self.toggle_mute()
                        elif key == "toggle_fullscreen":
                            self.toggle_fullscreen()
                        elif key == "how_to_play":
                            self.previous_state = SETTINGS_MENU
                            self.state = HOW_TO_PLAY
                            assets.play_sound("click", volume=0.5)
                        elif key == "back":
                            self.state = parent
                            assets.play_sound("click", volume=0.5)
            return

        # 4. หน้าต่างโหลดเกม 5 สล็อต (Load Menu)
        if self.state == LOAD_MENU:
            parent = MENU if self.previous_state not in (PAUSED, MENU) else self.previous_state
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.state = parent
                self.confirm_delete_slot = None
                assets.play_sound("click", volume=0.6)
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for key, rect in self.buttons.items():
                    if rect.collidepoint(mouse_pos):
                        if key == "back":
                            self.state = parent
                            self.confirm_delete_slot = None
                            assets.play_sound("click", volume=0.6)
                            return
                        elif key.startswith("confirm_delete_"):
                            sid = int(key.split("_")[-1])
                            SM.delete_slot(sid)
                            self.confirm_delete_slot = None
                            self._toast(f"ลบข้อมูลช่อง {sid} เรียบร้อยแล้ว")
                            assets.play_sound("rock_clink", volume=0.7)
                            return
                        elif key.startswith("load_slot_"):
                            sid = int(key.split("_")[-1])
                            self.load_slot(sid)
                            return
                        elif key.startswith("delete_slot_"):
                            sid = int(key.split("_")[-1])
                            self.confirm_delete_slot = sid
                            assets.play_sound("click", volume=0.6)
                            return
            return

        # 5. หน้าต่างบันทึกเกม 5 สล็อต (Save Menu จาก Pause)
        if self.state == SAVE_MENU:
            parent = PAUSED if self.previous_state not in (PAUSED, MENU) else self.previous_state
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.state = parent
                self.confirm_delete_slot = None
                self.confirm_overwrite_slot = None
                assets.play_sound("click", volume=0.6)
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for key, rect in self.buttons.items():
                    if rect.collidepoint(mouse_pos):
                        if key == "back":
                            self.state = parent
                            self.confirm_delete_slot = None
                            self.confirm_overwrite_slot = None
                            assets.play_sound("click", volume=0.6)
                            return
                        elif key.startswith("confirm_delete_"):
                            sid = int(key.split("_")[-1])
                            SM.delete_slot(sid)
                            self.confirm_delete_slot = None
                            self._toast(f"ลบข้อมูลช่อง {sid} เรียบร้อยแล้ว")
                            assets.play_sound("rock_clink", volume=0.7)
                            return
                        elif key.startswith("confirm_overwrite_"):
                            sid = int(key.split("_")[-1])
                            self.save_slot(sid)
                            self.confirm_overwrite_slot = None
                            self._toast(f"บันทึกทับช่อง {sid} เรียบร้อย!")
                            self.state = self.previous_state if self.previous_state else PAUSED
                            return
                        elif key.startswith("save_slot_"):
                            sid = int(key.split("_")[-1])
                            slots = SM.list_slots()
                            sinfo = slots[sid - 1] if (sid - 1) < len(slots) else {"empty": True}
                            if sinfo.get("empty", False):
                                self.save_slot(sid)
                                self._toast(f"บันทึกเกมลงช่อง {sid} เรียบร้อย!")
                                self.state = self.previous_state if self.previous_state else PAUSED
                            else:
                                self.confirm_overwrite_slot = sid
                                self.confirm_delete_slot = None
                                assets.play_sound("click", volume=0.6)
                            return
                        elif key.startswith("delete_slot_"):
                            sid = int(key.split("_")[-1])
                            self.confirm_delete_slot = sid
                            self.confirm_overwrite_slot = None
                            assets.play_sound("click", volume=0.6)
                            return
            return

        if self.state == HOW_TO_PLAY:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_e, pygame.K_h, pygame.K_F1, pygame.K_SPACE, pygame.K_RETURN):
                    self.state = self.previous_state if self.previous_state else MENU
                    return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for key, rect in self.buttons.items():
                    if rect.collidepoint(mouse_pos) and key in ("close", "back"):
                        self.state = self.previous_state if self.previous_state else MENU
                        assets.play_sound("click", volume=0.6)
                        return
            return

        if self.state == CONTRACT:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.state = PLAY_SELECT if self.previous_state == PLAY_SELECT else MENU
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
                            self.state = PLAY_SELECT if self.previous_state == PLAY_SELECT else MENU
            return

        if self.state == GARAGE:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_e):
                if self.vehicle:
                    self.vehicle.recalc_stats()
                self.state = self.previous_state
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for key, rect in self.buttons.items():
                    if rect.collidepoint(mouse_pos):
                        if key == "tab_color":
                            self.garage_tab = "color"
                            assets.play_sound("click", volume=0.6)
                        elif key == "tab_type":
                            self.garage_tab = "type"
                            assets.play_sound("click", volume=0.6)
                        elif key == "tab_drill":
                            self.garage_tab = "drill"
                            assets.play_sound("click", volume=0.6)
                        elif key.startswith("color_") or key.startswith("type_") or key.startswith("drill_"):
                            cat, item_id = key.split("_", 1)
                            if self.vehicle:
                                ok, status, msg = self.vehicle.unlock_and_equip(cat, item_id)
                                self._toast(msg, dur=2.6)
                                if status == "purchased":
                                    assets.play_sound("upgrade", volume=0.85)
                                    if self.mission:
                                        depth = max(0, int(self.vehicle.y // S.TILE) - S.SURFACE_ROW)
                                        self.mission.update_from_game(self.vehicle, depth)
                                        self._check_mission_notifications()
                                elif status == "equipped":
                                    assets.play_sound("click", volume=0.65)
                                else:
                                    assets.play_sound("rock_clink", volume=0.65)
                        elif key in ("apply", "back"):
                            if self.vehicle:
                                self.vehicle.recalc_stats()
                            self.state = self.previous_state
                            assets.play_sound("click", volume=0.6)
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.state == PLAYING:
                    self.state = PAUSED
                elif self.state == PAUSED:
                    self.state = PLAYING
                elif self.state == SHOP:
                    self.state = PLAYING
                elif self.state == HOW_TO_PLAY:
                    self.state = self.previous_state
            elif event.key in (pygame.K_h, pygame.K_F1):
                if self.state == HOW_TO_PLAY:
                    self.state = self.previous_state
                elif self.state in (PLAYING, PAUSED, MENU):
                    self.previous_state = self.state
                    self.state = HOW_TO_PLAY
            elif event.key == pygame.K_e and self.state in (PLAYING, SHOP):
                if self.state == PLAYING and self.vehicle.rect.colliderect(self.shop_zone()):
                    self.state = SHOP
                    assets.play_sound("click", volume=0.6)
                elif self.state == PLAYING and getattr(self, "game_mode", "mission") == "classic" and self.get_barrier_near_vehicle() is not None:
                    self.unlock_next_floor()
                elif self.state == SHOP:
                    self.state = PLAYING

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.state == PAUSED:
                for key, rect in self.buttons.items():
                    if rect.collidepoint(mouse_pos):
                        if key == "resume":
                            self.state = PLAYING
                        elif key in ("save", "save_slots", "save_game"):
                            self.previous_state = PAUSED
                            self.confirm_overwrite_slot = None
                            self.confirm_delete_slot = None
                            self.state = SAVE_MENU
                            assets.play_sound("click", volume=0.6)
                        elif key in ("load", "load_slots", "load_game"):
                            self.previous_state = PAUSED
                            self.confirm_delete_slot = None
                            self.confirm_overwrite_slot = None
                            self.state = LOAD_MENU
                            assets.play_sound("click", volume=0.6)
                        elif key in ("settings", "how_to_play"):
                            self.previous_state = PAUSED
                            self.state = SETTINGS_MENU
                            assets.play_sound("click", volume=0.6)
                        elif key in ("save_quit", "exit_menu", "menu", "quit_nosave"):
                            self.save_and_quit()
                        elif key == "save_current":
                            self.save_slot(self.current_slot)
                            self._toast(f"บันทึกเกมลงช่อง {self.current_slot} สำเร็จ!")
                        elif key == "fullscreen":
                            self.toggle_fullscreen()
                        elif key == "mute":
                            self.toggle_mute()
            elif self.state == SHOP:
                for key, rect in self.buttons.items():
                    if rect.collidepoint(mouse_pos):
                        if key == "close":
                            self.state = PLAYING
                        elif key == "tab_upgrades":
                            self.shop_tab = "upgrades"
                        elif key in ("tab_floor", "teaser_floor"):
                            self.shop_tab = "floor"
                            assets.play_sound("click", volume=0.6)
                        elif key == "tab_garage":
                            self.previous_state = SHOP
                            self.state = GARAGE
                            assets.play_sound("click", volume=0.6)
                        elif key == "unlock_floor":
                            self.unlock_next_floor()
                        else:
                            if self.vehicle.do_upgrade(key):
                                if self.mission:
                                    depth = max(0, int(self.vehicle.y // S.TILE) - S.SURFACE_ROW)
                                    self.mission.update_from_game(self.vehicle, depth)
                                    self._check_mission_notifications()
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
        return keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] or keys[pygame.K_SPACE]

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
            self._check_mission_notifications()

        # การเลื่อนกล้องตามรถขุดในแนวตั้งอย่างนุ่มนวล
        target_cam = max(0.0, self.vehicle.y - S.SCREEN_H / 2.0)
        self.camera_y += (target_cam - self.camera_y) * min(1.0, dt * 7.0)
        self.camera_y = max(0.0, self.camera_y)

        # ตรวจสอบการกลับมาที่บ้าน (ขายของ + เติมพลังงาน + ตรวจเงื่อนไขชนะ)
        in_home = self.vehicle.rect.colliderect(self.home_zone())
        if in_home and not self.was_in_home:
            earned = self.vehicle.sell_cargo()
            self.vehicle.refuel()
            self.vehicle.stalled = False
            assets.play_sound("refuel", volume=0.7)
            if self.mission:
                self.mission.update_from_game(self.vehicle, depth)
                self._check_mission_notifications()

            if earned > 0:
                assets.play_sound("sell", volume=0.85)
                self._toast(f"ขายแร่ได้ {earned} เหรียญ! เติมพลังงานเต็มแล้ว")
                hx = (S.HOME_COL + 1) * S.TILE
                hy = (S.SURFACE_ROW - 0.5) * S.TILE
                self.particles.add_floating_text(f"+{earned} เหรียญ!", hx, hy, (255, 230, 80))
            else:
                self._toast("เติมพลังงานเต็มแล้ว")

            # แจ้งเตือนหากเหรียญสะสมเพียงพอสำหรับการปลดล็อคชั้นถัดไปในโหมดคลาสสิก
            if getattr(self, "game_mode", "mission") == "classic":
                next_floor = self.unlocked_floor + 1
                next_cost = S.get_floor_info(next_floor)["unlock_cost"]
                if self.vehicle.coins >= next_cost:
                    self._toast(f"คุณมีเหรียญพอปลดล็อคชั้น {next_floor} แล้ว! ({next_cost:,} เหรียญ)", dur=3.2)

            # ตรวจสอบเงื่อนไขชนะจากภารกิจผสม (เฉพาะโหมดภารกิจ)
            if self.mission and self.mission.is_completed():
                self.end_title = "ภารกิจสำเร็จสมบูรณ์!"
                self.end_sub = f"คุณพิชิตภารกิจ [{self.mission.title}] ระดับ{self.mission.diff_info['name']} สำเร็จครบทุกข้อ!"
                self.state = VICTORY
                assets.play_sound("upgrade", volume=0.95)
            elif getattr(self, "game_mode", "mission") == "mission" and self.mission is None and S.END_ON_TARGET_RESOURCE and self.vehicle.coins >= S.VICTORY_COIN_TARGET:
                self.end_title = "ขุดเจอสมบัติมหาศาล!"
                self.end_sub = f"คุณสะสมเหรียญครบ {S.VICTORY_COIN_TARGET} เหรียญแล้ว!"
                self.state = VICTORY

        self.was_in_home = in_home

        # ตรวจสอบพลังงานหมดเมื่ออยู่นอกฐานบ้าน (แพ้ทั้งโหมดภารกิจและโหมดคลาสสิก)
        if self.vehicle.stalled and not in_home and S.END_ON_ENERGY_EMPTY:
            self.end_title = "พลังงานหมด!"
            self.end_sub = "รถขุดพลังงานหมดกลางทางและไม่สามารถกลับฐานบ้านบนพื้นผิวได้"
            self.state = GAME_OVER

    # ------------------------------------------------------------------
    def draw(self):
        mouse_pos = self._to_game_pos(pygame.mouse.get_pos())

        if self.state == MENU:
            self.buttons = ui.draw_main_menu(self.screen, SM.save_exists(), mouse_pos)
            ui.draw_toast(self.screen, self.toast_msg, self.toast_timer, y=S.SCREEN_H - 68)
            return

        if self.state == PLAY_SELECT:
            ui.draw_main_menu(self.screen, SM.save_exists(), (-1, -1))
            self.buttons = ui.draw_play_select_menu(self.screen, mouse_pos)
            ui.draw_toast(self.screen, self.toast_msg, self.toast_timer, y=S.SCREEN_H - 68)
            return

        if self.state == SETTINGS_MENU:
            if self.previous_state == PAUSED and self.world is not None and self.vehicle is not None:
                ui.draw_sky_and_bg(self.screen, self.camera_y)
                ui.draw_world(self.screen, self.world, self.camera_y)
                ui.draw_home_and_shop(self.screen, self.camera_y)
                ui.draw_vehicle(self.screen, self.vehicle, self.camera_y)
                depth = max(0, int(self.vehicle.y // S.TILE) - S.SURFACE_ROW)
                ui.draw_hud(self.screen, self.vehicle, depth, self.mission,
                            game_mode=self.game_mode, unlocked_floor=self.unlocked_floor)
            else:
                ui.draw_main_menu(self.screen, SM.save_exists(), (-1, -1))
            self.buttons = ui.draw_settings_menu(self.screen, mouse_pos, is_fullscreen=self.is_fullscreen)
            ui.draw_toast(self.screen, self.toast_msg, self.toast_timer, y=S.SCREEN_H - 68)
            return

        if self.state == LOAD_MENU:
            slots = SM.list_slots()
            if self.previous_state == PAUSED and self.world is not None and self.vehicle is not None:
                ui.draw_sky_and_bg(self.screen, self.camera_y)
                ui.draw_world(self.screen, self.world, self.camera_y)
                ui.draw_home_and_shop(self.screen, self.camera_y)
                ui.draw_vehicle(self.screen, self.vehicle, self.camera_y)
                depth = max(0, int(self.vehicle.y // S.TILE) - S.SURFACE_ROW)
                ui.draw_hud(self.screen, self.vehicle, depth, self.mission,
                            game_mode=self.game_mode, unlocked_floor=self.unlocked_floor)
            else:
                ui.draw_main_menu(self.screen, SM.save_exists(), (-1, -1))
            self.buttons = ui.draw_slot_menu(self.screen, slots, mode="load", mouse_pos=mouse_pos,
                                             confirm_delete_slot=self.confirm_delete_slot,
                                             current_slot=self.current_slot)
            ui.draw_toast(self.screen, self.toast_msg, self.toast_timer, y=S.SCREEN_H - 68)
            return

        if self.state == SAVE_MENU:
            slots = SM.list_slots()
            ui.draw_sky_and_bg(self.screen, self.camera_y)
            ui.draw_world(self.screen, self.world, self.camera_y)
            ui.draw_home_and_shop(self.screen, self.camera_y)
            ui.draw_vehicle(self.screen, self.vehicle, self.camera_y)
            depth = max(0, int(self.vehicle.y // S.TILE) - S.SURFACE_ROW)
            ui.draw_hud(self.screen, self.vehicle, depth, self.mission,
                        game_mode=self.game_mode, unlocked_floor=self.unlocked_floor)
            self.buttons = ui.draw_slot_menu(self.screen, slots, mode="save", mouse_pos=mouse_pos,
                                             confirm_delete_slot=self.confirm_delete_slot,
                                             confirm_overwrite_slot=self.confirm_overwrite_slot,
                                             current_slot=self.current_slot)
            ui.draw_toast(self.screen, self.toast_msg, self.toast_timer, y=S.SCREEN_H - 68)
            return

        if self.state == CONTRACT:
            # วาดฉากหลังเมนูแล้วเปิดหน้าต่างเลือกสัญญาภารกิจ
            ui.draw_main_menu(self.screen, SM.save_exists(), (-1, -1))
            self.buttons = ui.draw_contract_menu(self.screen, self.contract_options, mouse_pos)
            ui.draw_toast(self.screen, self.toast_msg, self.toast_timer, y=S.SCREEN_H - 68)
            return

        if self.state == GARAGE:
            if self.previous_state in (MENU, CONTRACT, PLAY_SELECT) or self.world is None:
                ui.draw_main_menu(self.screen, False, mouse_pos)
            else:
                ui.draw_sky_and_bg(self.screen, self.camera_y)
                ui.draw_world(self.screen, self.world, self.camera_y)
                ui.draw_home_and_shop(self.screen, self.camera_y)
                ui.draw_vehicle(self.screen, self.vehicle, self.camera_y)
                depth = max(0, int(self.vehicle.y // S.TILE) - S.SURFACE_ROW)
                ui.draw_hud(self.screen, self.vehicle, depth, self.mission,
                            game_mode=self.game_mode, unlocked_floor=self.unlocked_floor)
            if self.vehicle is None:
                self.vehicle = Vehicle(S.HOME_COL, S.SURFACE_ROW - 1)
            self.buttons = ui.draw_garage_menu(self.screen, self.vehicle, mouse_pos, active_tab=self.garage_tab)
            ui.draw_toast(self.screen, self.toast_msg, self.toast_timer)
            return

        if self.state == HOW_TO_PLAY:
            if self.previous_state in (MENU, CONTRACT, PLAY_SELECT, SETTINGS_MENU) or self.world is None or self.vehicle is None:
                ui.draw_main_menu(self.screen, SM.save_exists(), mouse_pos)
            else:
                ui.draw_sky_and_bg(self.screen, self.camera_y)
                ui.draw_world(self.screen, self.world, self.camera_y)
                ui.draw_home_and_shop(self.screen, self.camera_y)
                ui.draw_vehicle(self.screen, self.vehicle, self.camera_y)
                depth = max(0, int(self.vehicle.y // S.TILE) - S.SURFACE_ROW)
                ui.draw_hud(self.screen, self.vehicle, depth, self.mission,
                            game_mode=self.game_mode, unlocked_floor=self.unlocked_floor)
            self.buttons = ui.draw_how_to_play(self.screen, mouse_pos)
            ui.draw_toast(self.screen, self.toast_msg, self.toast_timer)
            return

        # วาดฉากเกม
        ui.draw_sky_and_bg(self.screen, self.camera_y)
        ui.draw_world(self.screen, self.world, self.camera_y)
        ui.draw_home_and_shop(self.screen, self.camera_y)

        # หากอยู่ในโหมดคลาสสิก วาดป้ายประตูกั้นชั้นถัดไปที่ลอยอยู่เหนือประตู
        if getattr(self, "game_mode", "mission") == "classic":
            next_flr = self.unlocked_floor + 1
            flr_info = S.get_floor_info(next_flr)
            ui.draw_barrier_gate_banner(self.screen, flr_info, self.vehicle.coins, self.camera_y)

        ui.draw_vehicle(self.screen, self.vehicle, self.camera_y)

        # วาดอนุภาคและข้อความลอย
        self.particles.draw(self.screen, self.camera_y)

        # วาดเป้าหมายเมาส์เมื่อคลิกค้างไว้
        if self.state == PLAYING and pygame.mouse.get_pressed()[0]:
            ui.draw_aim_indicator(self.screen, self.vehicle, mouse_pos, self.camera_y)

        # วาด HUD ด้านบน (รวมแถบภารกิจผสม หรือ โหมดคลาสสิก)
        depth = max(0, int(self.vehicle.y // S.TILE) - S.SURFACE_ROW)
        hud_buttons = ui.draw_hud(self.screen, self.vehicle, depth, self.mission,
                                  mouse_pos=mouse_pos,
                                  game_mode=self.game_mode, unlocked_floor=self.unlocked_floor)

        # แสดงข้อความคำใบ้ (Hint)
        diamond_bypass = getattr(self.vehicle, "drill_head", "") == "diamond"
        barrier_near = self.get_barrier_near_vehicle() if getattr(self, "game_mode", "mission") == "classic" else None
        blocked_by_rock = (
            self.state == PLAYING
            and self.vehicle.drilling_target is not None
            and not self.vehicle.is_drilling
            and not self.vehicle.stalled
            and not diamond_bypass
        )
        if self.state == PLAYING and self.vehicle.rect.colliderect(self.shop_zone()):
            ui.draw_hint(self.screen, "กด [E] เพื่อเปิดร้านอัพเกรดและอู่แต่งรถ")
        elif self.state == PLAYING and barrier_near is not None:
            n_flr, n_info, _ = barrier_near
            cost = n_info["unlock_cost"]
            if self.vehicle.coins >= cost:
                ui.draw_hint(self.screen, f"กด [E] เพื่อปลดล็อคชั้น {n_flr} ({cost:,} เหรียญ)")
            else:
                diff = cost - self.vehicle.coins
                ui.draw_hint(self.screen, f"ประตูกั้นชั้น {n_flr} ล็อคอยู่! ต้องใช้ {cost:,} เหรียญ (ขาดอีก {diff:,} เหรียญ)")
        elif blocked_by_rock:
            ui.draw_hint(self.screen, f"หินแข็งเกินไป! อัพเกรดหัวขุดถึง Lv.{S.ROCK_MIN_DRILL_LEVEL} ที่ร้านบนพื้นผิวก่อน")
        elif self.vehicle.cargo_full() and self.state == PLAYING:
            ui.draw_hint(self.screen, "ถังแร่เต็มแล้ว! ขับกลับฐานบ้านบนพื้นผิวเพื่อขายแร่และเติมพลังงาน")

        ui.draw_toast(self.screen, self.toast_msg, self.toast_timer)

        # แถบแนะนำปุ่มลัดด้านล่างหน้าจอขณะเล่น
        if self.state == PLAYING:
            ui.draw_quick_controls_bar(self.screen)

        # วาดเมนูตาม State
        if self.state == PLAYING:
            self.buttons = hud_buttons
        elif self.state == PAUSED:
            self.buttons = ui.draw_pause_menu(self.screen, mouse_pos,
                                              is_fullscreen=self.is_fullscreen,
                                              current_slot=self.current_slot)
        elif self.state == SHOP:
            self.buttons = ui.draw_shop_menu(self.screen, self.vehicle, mouse_pos,
                                             game_mode=self.game_mode,
                                             unlocked_floor=self.unlocked_floor,
                                             active_tab=self.shop_tab)
        elif self.state == GAME_OVER:
            self.buttons = ui.draw_end_screen(self.screen, self.end_title, self.end_sub, self.vehicle,
                                               mouse_pos, mission=self.mission, color=(255, 100, 90))
        elif self.state == VICTORY:
            self.buttons = ui.draw_end_screen(self.screen, self.end_title, self.end_sub, self.vehicle,
                                               mouse_pos, mission=self.mission, color=(255, 220, 100))
        else:
            self.buttons = {}
