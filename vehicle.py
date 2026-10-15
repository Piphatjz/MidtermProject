# -*- coding: utf-8 -*-
"""
vehicle.py
รถขุด: ตำแหน่ง, การเคลื่อนที่แบบฟิสิกส์เนียนตา, การเจาะบล็อกที่แม่นยำ ไม่ข้ามบล็อก,
การจัดการความจุ พลังงาน และระบบอัพเกรด
"""
import math
import random
import pygame
import settings as S
import assets


class Vehicle:
    def __init__(self, col, row, color_id=None, vehicle_type=None, drill_head=None):
        self.w = 40
        self.h = 40
        self.x = col * S.TILE + S.TILE / 2.0
        self.y = row * S.TILE + S.TILE / 2.0

        # ระดับอัพเกรด
        self.levels = {"capacity": 1, "energy": 1, "power": 1, "speed": 1}

        self.max_energy = S.BASE_ENERGY
        self.energy = self.max_energy
        self.max_capacity = S.BASE_CAPACITY
        self.power = S.BASE_POWER
        self.speed = S.BASE_SPEED

        self.cargo = {S.RES_COIN: 0, S.RES_GOLD: 0, S.RES_DIAMOND: 0}
        self.cargo_count = 0
        self.coins = getattr(S, "STARTING_COINS", 0)

        # คอลแบ็กแจ้งเตือนเมื่อเก็บแร่หรือทำ Gravity Dive สำหรับระบบภารกิจ
        self.on_resource_collected = None
        self.on_dive_performed = None

        self.facing = (0, 1)        # (dx, dy) ใน { (0,1), (0,-1), (1,0), (-1,0) }
        self.drilling_target = None # (col, row) ที่กำลังเจาะอยู่
        self.is_moving = False
        self.is_drilling = False
        self.stalled = False        # พลังงานหมด

        # ตัวแปรเสริมอนิเมชันและความรู้สึกในการเล่น (Juice)
        self.drill_anim = 0.0
        self.vibe_x = 0.0
        self.vibe_y = 0.0
        self._drill_sound_timer = 0.0
        self._smoke_timer = 0.0
        self._low_energy_timer = 0.0
        # ระบบฟิสิกส์กฎแรงโน้มถ่วง (Gravitational Potential & Kinetic Energy)
        self.grav_charge = 0.0          # พลังงานศักย์โน้มถ่วงที่สะสมจากการขึ้นด้านบน (0.0 ถึง S.GRAV_CHARGE_MAX)
        self.is_diving = False          # กำลังพุ่งดิ่งลงด้านล่างตามแรงโน้มถ่วงหรือไม่
        self.dive_power = 0.0           # อัตราความแรงขณะพุ่งดิ่ง
        self._grav_sound_timer = 0.0    # จับเวลาเล่นเสียงชาร์จศักย์
        self._dive_particle_timer = 0.0 # จับเวลาสร้างอนุภาคลมขณะพุ่งดิ่ง
        # ตัวเลือกการปรับแต่งรถขุด (Customization) และสถานะการปลดล็อค
        self.color_id = color_id or getattr(S, "DEFAULT_VEHICLE_COLOR", "yellow")
        self.vehicle_type = vehicle_type or getattr(S, "DEFAULT_VEHICLE_TYPE", "standard")
        self.drill_head = drill_head or getattr(S, "DEFAULT_DRILL_HEAD", "spiral")

        # สถิติความก้าวหน้าและรายการอุปกรณ์ที่ปลดล็อคแล้ว (Progression Unlocks)
        self.max_depth_reached = 0
        self.total_diamonds_collected = 0
        self.unlocked_colors = {"yellow", self.color_id}
        self.unlocked_types = {"standard", self.vehicle_type}
        self.unlocked_drills = {"spiral", self.drill_head}

        self.recalc_stats()

    # ------------------------------------------------------------------
    def _get_category_info(self, category, item_id):
        if category == "color":
            return S.VEHICLE_COLORS.get(item_id, {}), self.unlocked_colors
        elif category == "type":
            return S.VEHICLE_TYPES.get(item_id, {}), self.unlocked_types
        elif category == "drill":
            return S.DRILL_HEADS.get(item_id, {}), self.unlocked_drills
        return {}, set()

    def is_item_unlocked(self, category, item_id):
        """ตรวจสอบว่าไอเทมในหมวดหมู่ (color / type / drill) ถูกซื้อปลดล็อคแล้วหรือยัง"""
        _, unlocked_set = self._get_category_info(category, item_id)
        return item_id in unlocked_set

    def check_unlock_condition(self, category, item_id):
        """ตรวจสอบเงื่อนไขความก้าวหน้าในการปลดล็อคไอเทม
        คืนค่า (cond_met: bool, req_desc: str, cost: int)"""
        cfg, unlocked_set = self._get_category_info(category, item_id)
        cost = int(cfg.get("unlock_cost", 0))
        req = cfg.get("unlock_req", None)
        desc = cfg.get("unlock_desc", "ปลดล็อคเริ่มต้น")

        if item_id in unlocked_set or req is None:
            return True, desc, cost

        rtype = req.get("type")
        if rtype == "depth":
            target = req.get("value", 0)
            return self.max_depth_reached >= target, f"{desc} ({self.max_depth_reached}/{target}ม.)", cost
        elif rtype == "drill_lv":
            target = req.get("value", 1)
            cur = self.levels.get("power", 1)
            return cur >= target, f"{desc} (ปัจจุบัน Lv.{cur})", cost
        elif rtype == "capacity_or_energy_lv":
            target = req.get("value", 1)
            cap_lv = self.levels.get("capacity", 1)
            en_lv = self.levels.get("energy", 1)
            return (cap_lv >= target or en_lv >= target), f"{desc} (ถัง Lv.{cap_lv}/พลังงาน Lv.{en_lv})", cost
        elif rtype == "diamond_and_drill":
            t_dia = req.get("diamonds", 3)
            t_drl = req.get("drill_lv", 2)
            cur_drl = self.levels.get("power", 1)
            met = (self.total_diamonds_collected >= t_dia and cur_drl >= t_drl)
            return met, f"เพชร {self.total_diamonds_collected}/{t_dia} เม็ด & หัวขุด Lv.{cur_drl}/{t_drl}", cost
        elif rtype == "tier_or_drill":
            t_tier = req.get("tier", 2)
            t_drl = req.get("drill_lv", 4)
            cur_tier = self.overall_tier()
            cur_drl = self.levels.get("power", 1)
            met = (cur_tier >= t_tier or cur_drl >= t_drl)
            return met, f"Tier {cur_tier}/{t_tier} หรือ หัวขุด Lv.{cur_drl}/{t_drl}", cost

        return True, desc, cost

    def unlock_and_equip(self, category, item_id):
        """พยายามปลดล็อค (หักเหรียญหากผ่านเงื่อนไข) และสวมใส่ไอเทม
        คืนค่า (success: bool, status: str, message: str)"""
        cfg, unlocked_set = self._get_category_info(category, item_id)
        if not cfg:
            return False, "invalid", "ไม่พบข้อมูลอุปกรณ์"

        item_name = cfg.get("name", item_id)

        # หากปลดล็อคแล้ว สวมใส่ได้ทันที
        if item_id in unlocked_set:
            if category == "color":
                self.color_id = item_id
            elif category == "type":
                self.vehicle_type = item_id
            elif category == "drill":
                self.drill_head = item_id
            self.recalc_stats()
            return True, "equipped", f"ติดตั้ง: {item_name}"

        # ยังไม่ปลดล็อค -> ตรวจเงื่อนไขความก้าวหน้าก่อน
        cond_met, req_desc, cost = self.check_unlock_condition(category, item_id)
        if not cond_met:
            return False, "locked_cond", f"ยังไม่ผ่านเงื่อนไข: {req_desc}"

        # ผ่านเงื่อนไขแล้ว -> ตรวจเหรียญ
        if self.coins < cost:
            diff = cost - self.coins
            return False, "locked_coins", f"เหรียญไม่พอซื้อ {item_name}! ต้องใช้ {cost:,} G (ขาดอีก {diff:,} G)"

        # หักเหรียญ ปลดล็อค และสวมใส่ทันที
        self.coins -= cost
        unlocked_set.add(item_id)
        if category == "color":
            self.color_id = item_id
        elif category == "type":
            self.vehicle_type = item_id
        elif category == "drill":
            self.drill_head = item_id
        self.recalc_stats()
        return True, "purchased", f"ปลดล็อคและติดตั้ง {item_name} สำเร็จ! (-{cost:,} G)"

    # ------------------------------------------------------------------
    def overall_tier(self):
        """ระดับรวมต่ำสุดของทุกอัพเกรด (จะเพิ่มขึ้นเมื่อทุกสเตตัสถึงระดับนั้น 1..8)"""
        return min(
            self.levels.get("capacity", 1),
            self.levels.get("energy", 1),
            self.levels.get("power", 1),
            self.levels.get("speed", 1),
        )

    def recalc_stats(self):
        cap_lv = self.levels["capacity"]
        en_lv = self.levels["energy"]
        pw_lv = self.levels["power"]
        sp_lv = self.levels["speed"]

        vtype_cfg = S.VEHICLE_TYPES.get(self.vehicle_type, S.VEHICLE_TYPES["standard"])
        head_cfg = S.DRILL_HEADS.get(self.drill_head, S.DRILL_HEADS["spiral"])

        # ความจุถังคำนวณตามเลเวลและประเภทตัวถัง
        base_cap = S.BASE_CAPACITY + (cap_lv - 1) * S.UPGRADES["capacity"]["step"]
        self.max_capacity = max(1, int(round(base_cap * vtype_cfg.get("capacity_mult", 1.0))))

        old_max_energy = getattr(self, "max_energy", S.BASE_ENERGY)
        base_en = S.BASE_ENERGY + (en_lv - 1) * S.UPGRADES["energy"]["step"]
        self.max_energy = max(30.0, base_en + vtype_cfg.get("energy_add", 0.0))
        # เติมพลังงานส่วนที่เพิ่มขึ้นมาเมื่ออัพเกรด
        if hasattr(self, "energy"):
            self.energy += max(0.0, self.max_energy - old_max_energy)
            self.energy = min(self.max_energy, self.energy)

        # พลังเจาะคำนวณตามเลเวลและประเภทหัวขุด
        base_pw = S.BASE_POWER + (pw_lv - 1) * S.UPGRADES["power"]["step"]
        self.power = base_pw * head_cfg.get("power_mult", 1.0)

        # ความเร็วคำนวณตามเลเวลและประเภทตัวถัง
        base_sp = S.BASE_SPEED + (sp_lv - 1) * S.UPGRADES["speed"]["step"]
        self.speed = base_sp * vtype_cfg.get("speed_mult", 1.0)

        # ขนาดรถเพิ่มขึ้นตาม Tier
        tier = self.overall_tier()
        new_size = round(S.BASE_VEHICLE_SIZE + (tier - 1) * S.VEHICLE_SIZE_PER_TIER)
        self.w = new_size
        self.h = new_size

    def drill_level(self):
        return self.levels["power"]

    def can_drill_rock(self):
        head_cfg = S.DRILL_HEADS.get(self.drill_head, S.DRILL_HEADS["spiral"])
        return head_cfg.get("can_drill_rock_always", False) or (self.drill_level() >= S.ROCK_MIN_DRILL_LEVEL)

    @property
    def drill_reach(self):
        """จำนวนบล็อกที่เจาะได้กว้างขึ้นตาม Tier หรือความสามารถของหัวขุด
        (เช่น หัว Seismic Hammer เริ่มต้นที่รัศมี 2 บล็อก = กว้าง 3 ช่องทันที)"""
        tier = self.overall_tier()
        base_reach = min(4, (tier + 1) // 2)
        head_cfg = S.DRILL_HEADS.get(self.drill_head, S.DRILL_HEADS["spiral"])
        return max(base_reach, head_cfg.get("aoe_reach", 0))

    @property
    def rect(self):
        return pygame.Rect(
            int(self.x - self.w / 2.0),
            int(self.y - self.h / 2.0),
            self.w,
            self.h
        )

    def grid_pos(self):
        return int(self.x // S.TILE), int(self.y // S.TILE)

    # ------------------------------------------------------------------
    def cargo_full(self):
        return self.cargo_count >= self.max_capacity

    def add_cargo(self, res_type):
        if res_type == S.RES_NONE:
            return False
        if self.cargo_full():
            return False
        self.cargo[res_type] += 1
        self.cargo_count += 1
        if res_type == S.RES_DIAMOND:
            self.total_diamonds_collected = getattr(self, "total_diamonds_collected", 0) + 1
        return True

    def cargo_value(self):
        return sum(S.RESOURCE_VALUE[t] * n for t, n in self.cargo.items())

    def sell_cargo(self):
        head_cfg = S.DRILL_HEADS.get(self.drill_head, S.DRILL_HEADS["spiral"])
        bonus = head_cfg.get("bonus_sell_mult", 1.0)
        earned = int(self.cargo_value() * bonus)
        self.coins += earned
        for k in self.cargo:
            self.cargo[k] = 0
        self.cargo_count = 0
        return earned

    def refuel(self):
        self.energy = self.max_energy

    # ------------------------------------------------------------------
    def upgrade_cost(self, key):
        cfg = S.UPGRADES[key]
        lv = self.levels[key]
        if lv >= cfg["max_level"]:
            return None
        return int(cfg["base_cost"] * (cfg["cost_growth"] ** (lv - 1)))

    def can_upgrade(self, key):
        cost = self.upgrade_cost(key)
        return cost is not None and self.coins >= cost

    def do_upgrade(self, key):
        cost = self.upgrade_cost(key)
        if cost is None or self.coins < cost:
            return False
        self.coins -= cost
        self.levels[key] += 1
        self.recalc_stats()
        assets.play_sound("upgrade", volume=0.8)
        return True

    # ------------------------------------------------------------------
    def _resolve_input_direction(self, raw_input):
        """แปลง input ให้เป็นทิศทางหลักแกนเดียวอย่างสเถียร ไร้การสั่นไหว"""
        dx, dy = raw_input
        if dx == 0 and dy == 0:
            return (0, 0)

        # ใช้ Hysteresis เพื่อป้องกันการกระพริบสลับแกนเวลากดเมาส์เฉียง
        abs_x, abs_y = abs(dx), abs(dy)
        if abs_x > abs_y * 1.15:
            return (1 if dx > 0 else -1, 0)
        elif abs_y > abs_x * 1.15:
            return (0, 1 if dy > 0 else -1)
        else:
            # ถ้าใกล้เคียงกัน ให้ยึดตามแกนที่หันอยู่เดิม
            if self.facing[0] != 0:
                return (1 if dx > 0 else -1, 0)
            else:
                return (0, 1 if dy > 0 else -1)

    # ------------------------------------------------------------------
    def update(self, dt, world, raw_input, particle_system=None, shift_pressed=False):
        self.is_moving = False
        self.is_drilling = False
        self.vibe_x = 0.0
        self.vibe_y = 0.0

        # --- Safety guards: ensure all timer/physics attributes exist for saves
        #     loaded from before these fields were added (backward compatibility)
        if not hasattr(self, "_dive_particle_timer"): self._dive_particle_timer = 0.0
        if not hasattr(self, "_grav_sound_timer"):    self._grav_sound_timer = 0.0
        if not hasattr(self, "_low_energy_timer"):    self._low_energy_timer = 0.0
        if not hasattr(self, "_smoke_timer"):         self._smoke_timer = 0.0
        if not hasattr(self, "grav_charge"):          self.grav_charge = 0.0
        if not hasattr(self, "is_diving"):            self.is_diving = False
        if not hasattr(self, "dive_power"):           self.dive_power = 0.0
        if not hasattr(self, "_slam_triggered"):      self._slam_triggered = False
        if not hasattr(self, "color_id"):             self.color_id = "yellow"
        if not hasattr(self, "vehicle_type"):         self.vehicle_type = "standard"
        if not hasattr(self, "drill_head"):           self.drill_head = "spiral"
        if not hasattr(self, "max_depth_reached"):    self.max_depth_reached = 0
        if not hasattr(self, "total_diamonds_collected"): self.total_diamonds_collected = 0
        if not hasattr(self, "unlocked_colors"):      self.unlocked_colors = {"yellow", self.color_id}
        if not hasattr(self, "unlocked_types"):       self.unlocked_types = {"standard", self.vehicle_type}
        if not hasattr(self, "unlocked_drills"):      self.unlocked_drills = {"spiral", self.drill_head}

        cur_depth = max(0, int(self.y // S.TILE) - S.SURFACE_ROW)
        if cur_depth > self.max_depth_reached:
            self.max_depth_reached = cur_depth

        if self.energy <= 0:
            self.stalled = True
            self.energy = 0.0
            return
        self.stalled = False

        # เสียงเตือนพลังงานต่ำ
        if self.energy / self.max_energy < 0.20:
            self._low_energy_timer += dt
            if self._low_energy_timer >= 2.0:
                assets.play_sound("low_energy", volume=0.4)
                self._low_energy_timer = 0.0
        else:
            self._low_energy_timer = 1.8

        dir_x, dir_y = self._resolve_input_direction(raw_input)

        if (dir_x, dir_y) == (0, 0):
            self.drilling_target = None
            self.is_diving = False
            self._slam_triggered = False
            return

        self.facing = (dir_x, dir_y)
        current_speed = self.speed
        half_w = self.w / 2.0
        half_h = self.h / 2.0

        # --- กฎฟิสิกส์แรงโน้มถ่วง 1: เมื่อเคลื่อนที่ขึ้นไปด้านบน (Up) -> สะสมพลังงานศักย์โน้มถ่วง (Ep = mgh) ---
        if dir_y < 0:
            self.is_diving = False
            self.dive_power = 0.0
            self._slam_triggered = False
            vtype_cfg = S.VEHICLE_TYPES.get(self.vehicle_type, S.VEHICLE_TYPES["standard"])
            charge_rate = S.GRAV_CHARGE_RATE * vtype_cfg.get("grav_charge_mult", 1.0)
            self.grav_charge = min(S.GRAV_CHARGE_MAX, self.grav_charge + dt * charge_rate)

            # เสียงและเอฟเฟกต์ประจุไอพ่นต้านแรงโน้มถ่วง
            self._grav_sound_timer += dt
            if self._grav_sound_timer >= 0.22:
                charge_vol = 0.30 + 0.35 * (self.grav_charge / S.GRAV_CHARGE_MAX)
                assets.play_sound("charge", volume=charge_vol)
                self._grav_sound_timer = 0.0
            if particle_system and random.random() < 0.45:
                particle_system.spawn_charge_spark(self.x, self.y + half_h)

            current_speed = self.speed

        # --- กฎฟิสิกส์แรงโน้มถ่วง 2: กด Shift เพื่อ ปลดปล่อยพลังงานศักย์เป็นพลังงานจลน์ในทิศที่กำลังเดิน ---
        elif shift_pressed and self.grav_charge > 0.04:
            self.is_diving = True
            self.dive_power = self.grav_charge / S.GRAV_CHARGE_MAX
            grav_speed_boost = 1.0 + (S.GRAV_SPEED_MULT - 1.0) * self.dive_power
            current_speed = self.speed * grav_speed_boost

            # เส้นลมความเร็วสูงพุ่งดิ่ง
            self._dive_particle_timer += dt
            if particle_system and self._dive_particle_timer >= 0.04:
                particle_system.spawn_gravity_dive_trail(self.x, self.y - half_h)
                self._dive_particle_timer = 0.0

            # เสียงหวีดพุ่งดิ่ง
            if self._grav_sound_timer <= 0.0:
                assets.play_sound("boost", volume=0.75)
                self._grav_sound_timer = 0.4
            else:
                self._grav_sound_timer -= dt

            # ค่อย ๆ ใช้พลังงานศักย์ขณะพุ่งดิ่ง
            self.grav_charge = max(0.0, self.grav_charge - dt * S.GRAV_DECAY_RATE)

        # --- เคลื่อนที่ปกติ (ไม่ได้กด Shift หรือไม่มีชาร์จ) ---
        elif dir_y > 0:
            self.is_diving = False
            self.dive_power = 0.0
            self._slam_triggered = False
            current_speed = self.speed

        # เคลื่อนที่แนวนอน (ซ้าย/ขวา) - อนุรักษ์พลังงานศักย์เดิมไว้ (Conservation of Energy)
        else:
            self.is_diving = False
            self.dive_power = 0.0
            self._slam_triggered = False
            current_speed = self.speed

        col, row = self.grid_pos()
        cell_cx = col * S.TILE + S.TILE / 2.0
        cell_cy = row * S.TILE + S.TILE / 2.0

        move_dist = current_speed * dt

        # -----------------------------
        # 1. การเคลื่อนที่แนวนอน (ซ้าย / ขวา)
        # -----------------------------
        if dir_x != 0:
            self.y += (cell_cy - self.y) * min(1.0, dt * 14.0)

            if dir_x > 0:  # ไปทางขวา
                target_col = col + 1
                target_row = row
                is_solid = world.is_solid(target_col, target_row)
                block_edge = target_col * S.TILE

                if is_solid and (self.x + half_w + move_dist) >= block_edge:
                    self.x = block_edge - half_w
                    self._handle_drilling(target_col, target_row, world, dt, particle_system)
                else:
                    self.x += move_dist
                    self.is_moving = True
                    self.drilling_target = None

            elif dir_x < 0:  # ไปทางซ้าย
                target_col = col - 1
                target_row = row
                is_solid = world.is_solid(target_col, target_row)
                block_edge = (target_col + 1) * S.TILE

                if is_solid and (self.x - half_w - move_dist) <= block_edge:
                    self.x = block_edge + half_w
                    self._handle_drilling(target_col, target_row, world, dt, particle_system)
                else:
                    self.x -= move_dist
                    self.is_moving = True
                    self.drilling_target = None

        # -----------------------------
        # 2. การเคลื่อนที่แนวตั้ง (ขึ้น / ลง)
        # -----------------------------
        elif dir_y != 0:
            self.x += (cell_cx - self.x) * min(1.0, dt * 14.0)

            if dir_y > 0:  # ลงล่าง (Down)
                target_col = col
                target_row = row + 1
                is_solid = world.is_solid(target_col, target_row)
                block_edge = target_row * S.TILE

                if is_solid and (self.y + half_h + move_dist) >= block_edge:
                    self.y = block_edge - half_h
                    self._handle_drilling(target_col, target_row, world, dt, particle_system)
                else:
                    self.y += move_dist
                    self.is_moving = True
                    self.drilling_target = None

            elif dir_y < 0:  # ขึ้นบน (Up)
                target_col = col
                target_row = row - 1
                is_solid = world.is_solid(target_col, target_row)
                block_edge = (target_row + 1) * S.TILE

                if is_solid and (self.y - half_h - move_dist) <= block_edge:
                    self.y = block_edge + half_h
                    self._handle_drilling(target_col, target_row, world, dt, particle_system)
                else:
                    # เพดานด้านบนสุดของท้องฟ้า
                    if self.y - half_h - move_dist >= S.TILE * 1.2:
                        self.y -= move_dist
                        self.is_moving = True
                    self.drilling_target = None

        # ขอบเขตด้านซ้ายและขวาของแผนที่
        min_x = half_w
        max_x = S.SCREEN_W - half_w
        self.x = max(min_x, min(max_x, self.x))

        # ลดพลังงานเมื่อวิ่ง (เมื่อพุ่งดิ่งลงด้านล่างตามแรงโน้มถ่วง ไม่ต้องใช้พลังงานเครื่องยนต์!)
        if self.is_moving and not self.is_diving:
            vtype_cfg = S.VEHICLE_TYPES.get(self.vehicle_type, S.VEHICLE_TYPES["standard"])
            move_drain = S.BASE_ENERGY_DRAIN_MOVE * vtype_cfg.get("move_drain_mult", 1.0)
            self.energy = max(0.0, self.energy - move_drain * dt)
            self._smoke_timer += dt
            if particle_system and self._smoke_timer >= 0.12:
                bx = self.x - self.facing[0] * half_w
                by = self.y - self.facing[1] * half_h
                particle_system.spawn_exhaust_smoke(bx, by)
                self._smoke_timer = 0.0

        # อัพเดทอนิเมชันหัวสว่านหมุน
        rot_speed = 36.0 if self.is_drilling else (16.0 if self.is_moving else 0.0)
        self.drill_anim += dt * rot_speed

    # ------------------------------------------------------------------
    def _handle_drilling(self, col, row, world, dt, particle_system):
        """เจาะบล็อกหลัก + บล็อกข้าง ๆ ตาม drill_reach (Tier-based และความสามารถของหัวขุด)
        - เคลื่อนที่แนวนอน (ซ้าย/ขวา) → เจาะบล็อกบน/ล่างเพิ่มด้วย
        - เคลื่อนที่แนวตั้ง (ขึ้น/ลง)  → เจาะบล็อกซ้าย/ขวาเพิ่มด้วย
        reach 1 = 1 บล็อก, reach 2 = 3 บล็อก (±1), reach 3 = 5 บล็อก, reach 4 = 7 บล็อก"""
        self.drilling_target = (col, row)
        tile_type = world.get_tile(col, row)
        is_rock = (tile_type == S.T_ROCK)

        head_cfg = S.DRILL_HEADS.get(self.drill_head, S.DRILL_HEADS["spiral"])
        can_mine_rock = head_cfg.get("can_drill_rock_always", False) or (self.drill_level() >= S.ROCK_MIN_DRILL_LEVEL)

        # เช็คว่าเป็นประตูกั้นชั้นความลึกที่ยังล็อคอยู่หรือไม่
        if tile_type == getattr(S, "T_BARRIER", 5):
            self.is_drilling = False
            self._drill_sound_timer += dt
            if self._drill_sound_timer >= 0.22:
                assets.play_sound("rock_clink", volume=0.55)
                self._drill_sound_timer = 0.0
            return

        # เช็คว่าหินแข็งเกินกว่าหัวขุดปัจจุบันหรือไม่
        if is_rock and not can_mine_rock:
            self.is_drilling = False
            # กระแทกหินแล้วขุดไม่เข้า มีเสียงกระทบ
            self._drill_sound_timer += dt
            if self._drill_sound_timer >= 0.22:
                assets.play_sound("rock_clink", volume=0.5)
                self._drill_sound_timer = 0.0
            return

        self.is_drilling = True
        dig_drain = S.BASE_ENERGY_DRAIN_DIG * head_cfg.get("dig_drain_mult", 1.0)
        # โบนัสยาน Aero Hoverpod: ขุดดิ่งลงล่างประหยัดพลังงานลง 30%
        if self.vehicle_type == "hover" and self.facing == (0, 1):
            dig_drain *= 0.70
        self.energy = max(0.0, self.energy - dig_drain * dt)

        # สั่นสะเทือนตอนเจาะ (Juice)
        self.vibe_x = (random.random() * 2.0 - 1.0) * 1.5
        self.vibe_y = (random.random() * 2.0 - 1.0) * 1.5

        # เสียงเจาะ
        self._drill_sound_timer += dt
        if self._drill_sound_timer >= 0.14:
            assets.play_sound("drill", volume=0.55)
            self._drill_sound_timer = 0.0

        # เสกเศษดิน/เศษหิน/เอฟเฟกต์ตามชนิดหัวขุด
        if particle_system and random.random() < 0.65:
            fx = self.x + self.facing[0] * (self.w / 2.0 + 4)
            fy = self.y + self.facing[1] * (self.h / 2.0 + 4)
            theme = head_cfg.get("particle_theme", "dirt")
            if theme == "plasma":
                particle_system.spawn_plasma_spark(fx, fy)
            elif theme == "diamond":
                particle_system.spawn_diamond_spark(fx, fy)
            elif theme == "vortex":
                particle_system.spawn_vortex_spark(fx, fy)
            elif theme == "seismic":
                particle_system.spawn_seismic_shock(fx, fy)
            else:
                particle_system.spawn_dig_debris(fx, fy, is_rock=is_rock)

        # ทำความเสียหายต่อบล็อก (เมื่อพุ่งดิ่งชนบล็อกด้านล่างตามแรงโน้มถ่วง พลังเจาะจะแรงขึ้นหลายเท่า Ground Slam!)
        drill_mult = 1.0
        if self.is_diving and self.facing == (0, 1):
            drill_mult = 1.0 + (S.GRAV_DRILL_MULT - 1.0) * self.dive_power
            # สั่นสะเทือนพื้นและสร้างคลื่นกระแทก
            self.vibe_x = (random.random() * 2.0 - 1.0) * 3.5 * self.dive_power
            self.vibe_y = (random.random() * 2.0 - 1.0) * 3.5 * self.dive_power
            if self.dive_power > 0.2 and not getattr(self, "_slam_triggered", False):
                self._slam_triggered = True
                if particle_system:
                    particle_system.spawn_ground_slam_shockwave(self.x, row * S.TILE)
                    particle_system.add_floating_text(f"GRAVITY SLAM! (x{drill_mult:.1f})", self.x, self.y - 20, (255, 210, 60))
                if self.on_dive_performed:
                    self.on_dive_performed()
            # สลายพลังงานศักย์ลงเมื่อกระแทกพื้น
            self.grav_charge = max(0.0, self.grav_charge - dt * 2.2)

        damage_amount = self.power * drill_mult * dt
        if is_rock:
            damage_amount *= head_cfg.get("rock_damage_mult", 1.0)

        dug_through = world.damage_tile(col, row, damage_amount)

        if dug_through:
            self._on_block_dug(col, row, world, particle_system, is_rock)
            self.drilling_target = None

        # ---- Drill Reach: เจาะบล็อกข้าง ๆ ตาม Tier และชนิดหัวขุด ----
        reach = self.drill_reach  # 1..4
        if reach > 1:
            # ทิศที่เคลื่อนที่แนวนอน (left/right) → เจาะบล็อกบน/ล่างของเป้าหมาย
            # ทิศที่เคลื่อนที่แนวตั้ง (up/down)   → เจาะบล็อกซ้าย/ขวาของเป้าหมาย
            fx, fy = self.facing
            if fx != 0:
                perp_axis = "y"  # เคลื่อนที่แนวนอน → เจาะแนวตั้ง
            else:
                perp_axis = "x"  # เคลื่อนที่แนวตั้ง → เจาะแนวนอน

            # สร้างรายการ offset (-reach+1 .. reach-1, ไม่รวม 0 ซึ่งเป็นบล็อกหลัก)
            half = reach - 1
            side_damage = damage_amount
            for off in range(-half, half + 1):
                if off == 0:
                    continue
                if perp_axis == "y":
                    sc, sr = col, row + off
                else:
                    sc, sr = col + off, row

                if world.is_solid(sc, sr):
                    side_tile = world.get_tile(sc, sr)
                    side_is_rock = (side_tile == S.T_ROCK)
                    side_can_mine = head_cfg.get("can_drill_rock_always", False) or (self.drill_level() >= S.ROCK_MIN_DRILL_LEVEL)
                    if side_is_rock and not side_can_mine:
                        continue
                    side_dmg = side_damage
                    if side_is_rock:
                        side_dmg *= head_cfg.get("rock_damage_mult", 1.0)
                    side_dug = world.damage_tile(sc, sr, side_dmg)
                    if side_dug:
                        self._on_block_dug(sc, sr, world, particle_system, side_is_rock)

    def _on_block_dug(self, col, row, world, particle_system, is_rock):
        """ประมวลผลเมื่อบล็อกแตกสำเร็จ (เก็บทรัพยากร + เสียง + อนุภาค)"""
        t_cx = col * S.TILE + S.TILE / 2.0
        t_cy = row * S.TILE + S.TILE / 2.0
        assets.play_sound("dig_pop" if not is_rock else "rock_clink", volume=0.75)

        if particle_system:
            particle_system.spawn_block_break(t_cx, t_cy, is_rock=is_rock)

        res = world.collect_resource(col, row)
        head_cfg = S.DRILL_HEADS.get(self.drill_head, S.DRILL_HEADS["spiral"])

        if res == S.RES_FUEL:
            # กระป๋องน้ำมัน: เติมพลังงานทันที ไม่ต้องเก็บในถัง
            restore = min(S.FUEL_CANISTER_RESTORE, self.max_energy - self.energy)
            self.energy = min(self.max_energy, self.energy + S.FUEL_CANISTER_RESTORE)
            assets.play_sound("refuel", volume=0.8)
            if self.on_resource_collected:
                self.on_resource_collected(S.RES_FUEL)
            if particle_system:
                particle_system.add_floating_text(
                    f"+{int(restore)} พลังงาน!", t_cx, t_cy, (255, 210, 60)
                )
        elif res != S.RES_NONE:
            if self.add_cargo(res):
                if self.on_resource_collected:
                    self.on_resource_collected(res)
                name = S.RESOURCE_NAME.get(res, "สมบัติ")
                val = S.RESOURCE_VALUE.get(res, 1)
                if res == S.RES_COIN:
                    assets.play_sound("coin", volume=0.7)
                    color = (255, 220, 80)
                elif res == S.RES_GOLD:
                    assets.play_sound("coin", volume=0.85)
                    color = (255, 195, 30)
                else:  # Diamond
                    assets.play_sound("gem", volume=0.9)
                    color = (120, 230, 255)

                if particle_system:
                    particle_system.add_floating_text(f"+1 {name} (+{val})", t_cx, t_cy, color)
            else:
                # ถังเต็ม เก็บไม่ได้
                if particle_system:
                    particle_system.add_floating_text("ถังเต็ม!", t_cx, t_cy, (255, 80, 80))
        elif res == S.RES_NONE and head_cfg.get("extra_loot_chance", 0.0) > 0:
            # หัวขุดแม่เหล็ก (Magnetic Vortex): โอกาสดูดแร่หรือพลังงานพิเศษขึ้นมาจากชั้นดินว่าง
            if random.random() < head_cfg["extra_loot_chance"] * 0.12:
                bonus_res = random.choice([S.RES_COIN, S.RES_COIN, S.RES_GOLD, S.RES_FUEL])
                if bonus_res == S.RES_FUEL:
                    self.energy = min(self.max_energy, self.energy + S.FUEL_CANISTER_RESTORE)
                    if particle_system:
                        particle_system.add_floating_text("แรงดึงดูด: +เชื้อเพลิง!", t_cx, t_cy - 16, (255, 210, 60))
                else:
                    if self.add_cargo(bonus_res):
                        if self.on_resource_collected:
                            self.on_resource_collected(bonus_res)
                        bname = S.RESOURCE_NAME.get(bonus_res, "แร่")
                        if particle_system:
                            particle_system.add_floating_text(f"ดูดแร่พิเศษ! +1 {bname}", t_cx, t_cy - 16, (210, 130, 255))

    # ------------------------------------------------------------------
    def to_dict(self):
        return {
            "x": self.x, "y": self.y,
            "levels": self.levels,
            "energy": self.energy,
            "cargo": {str(k): v for k, v in self.cargo.items()},
            "cargo_count": self.cargo_count,
            "coins": self.coins,
            "color_id": self.color_id,
            "vehicle_type": self.vehicle_type,
            "drill_head": self.drill_head,
            "max_depth_reached": getattr(self, "max_depth_reached", 0),
            "total_diamonds_collected": getattr(self, "total_diamonds_collected", 0),
            "unlocked_colors": sorted(list(getattr(self, "unlocked_colors", {"yellow", self.color_id}))),
            "unlocked_types": sorted(list(getattr(self, "unlocked_types", {"standard", self.vehicle_type}))),
            "unlocked_drills": sorted(list(getattr(self, "unlocked_drills", {"spiral", self.drill_head}))),
        }

    def load_dict(self, data):
        self.x = data["x"]
        self.y = data["y"]
        self.levels = {k: int(v) for k, v in data["levels"].items()}
        self.color_id = data.get("color_id", getattr(S, "DEFAULT_VEHICLE_COLOR", "yellow"))
        self.vehicle_type = data.get("vehicle_type", getattr(S, "DEFAULT_VEHICLE_TYPE", "standard"))
        self.drill_head = data.get("drill_head", getattr(S, "DEFAULT_DRILL_HEAD", "spiral"))
        self.max_depth_reached = int(data.get("max_depth_reached", max(0, int(self.y // S.TILE) - S.SURFACE_ROW)))
        self.total_diamonds_collected = int(data.get("total_diamonds_collected", 0))
        self.unlocked_colors = set(data.get("unlocked_colors", ["yellow"])) | {"yellow", self.color_id}
        self.unlocked_types = set(data.get("unlocked_types", ["standard"])) | {"standard", self.vehicle_type}
        self.unlocked_drills = set(data.get("unlocked_drills", ["spiral"])) | {"spiral", self.drill_head}
        self.recalc_stats()
        self.energy = data["energy"]
        self.cargo = {int(k): v for k, v in data["cargo"].items()}
        self.cargo_count = data["cargo_count"]
        self.coins = data["coins"]
        self.grav_charge = 0.0
        self.is_diving = False
        self.dive_power = 0.0

