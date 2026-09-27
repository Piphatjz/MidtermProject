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
    def __init__(self, col, row):
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
        self._dive_particle_timer = 0.0 # จับเวลาพ่นลมต้านพุ่งดิ่ง

        self.recalc_stats()

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

        self.max_capacity = S.BASE_CAPACITY + (cap_lv - 1) * S.UPGRADES["capacity"]["step"]
        old_max_energy = self.max_energy
        self.max_energy = S.BASE_ENERGY + (en_lv - 1) * S.UPGRADES["energy"]["step"]
        # เติมพลังงานส่วนที่เพิ่มขึ้นมาเมื่ออัพเกรด
        self.energy += max(0.0, self.max_energy - old_max_energy)
        self.power = S.BASE_POWER + (pw_lv - 1) * S.UPGRADES["power"]["step"]
        self.speed = S.BASE_SPEED + (sp_lv - 1) * S.UPGRADES["speed"]["step"]

        # ขนาดรถเพิ่มขึ้นเมื่ออัพเกรดครบทุกอย่างถึงระดับใหม่ (Tier)
        # เมื่อทุกสเตตัสอย่างน้อย Lv.2 -> รถใหญ่ขึ้น, Lv.3 -> ใหญ่ขึ้นอีก ... จนถึง Lv.8 ตันสุด (~62px)
        tier = self.overall_tier()
        new_size = round(S.BASE_VEHICLE_SIZE + (tier - 1) * S.VEHICLE_SIZE_PER_TIER)
        self.w = new_size
        self.h = new_size

    def drill_level(self):
        return self.levels["power"]

    @property
    def drill_reach(self):
        """จำนวนบล็อกที่เจาะได้กว้างขึ้นตาม Tier (ทุก 2 Tier เพิ่ม 1 บล็อก, สูงสุด 4)
        Tier 1-2 = 1 บล็อก, Tier 3-4 = 2 บล็อก, Tier 5-6 = 3 บล็อก, Tier 7-8 = 4 บล็อก"""
        tier = self.overall_tier()
        return min(4, (tier + 1) // 2)

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
        return True

    def cargo_value(self):
        return sum(S.RESOURCE_VALUE[t] * n for t, n in self.cargo.items())

    def sell_cargo(self):
        earned = self.cargo_value()
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

        # อัพเดทตัวนับเวลาความเร็วบูสต์ (Boost timer)
        dir_x, dir_y = self._resolve_input_direction(raw_input)

        if (dir_x, dir_y) == (0, 0):
            self.drilling_target = None
            self.is_diving = False
            return

        self.facing = (dir_x, dir_y)
        current_speed = self.speed
        half_w = self.w / 2.0
        half_h = self.h / 2.0

        # --- กฎฟิสิกส์แรงโน้มถ่วง 1: เมื่อเคลื่อนที่ขึ้นไปด้านบน (Up) -> สะสมพลังงานศักย์โน้มถ่วง (Ep = mgh) ---
        if dir_y < 0:
            self.is_diving = False
            self.dive_power = 0.0
            self.grav_charge = min(S.GRAV_CHARGE_MAX, self.grav_charge + dt * S.GRAV_CHARGE_RATE)

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
            current_speed = self.speed

        # เคลื่อนที่แนวนอน (ซ้าย/ขวา) - อนุรักษ์พลังงานศักย์เดิมไว้ (Conservation of Energy)
        else:
            self.is_diving = False
            self.dive_power = 0.0
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
            self.energy = max(0.0, self.energy - S.BASE_ENERGY_DRAIN_MOVE * dt)
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
        """เจาะบล็อกหลัก + บล็อกข้าง ๆ ตาม drill_reach (Tier-based)
        - เคลื่อนที่แนวนอน (ซ้าย/ขวา) → เจาะบล็อกบน/ล่างเพิ่มด้วย
        - เคลื่อนที่แนวตั้ง (ขึ้น/ลง)  → เจาะบล็อกซ้าย/ขวาเพิ่มด้วย
        reach 1 = 1 บล็อก, reach 2 = 3 บล็อก (±1), reach 3 = 5 บล็อก, reach 4 = 7 บล็อก"""
        self.drilling_target = (col, row)
        tile_type = world.get_tile(col, row)
        is_rock = (tile_type == S.T_ROCK)

        # เช็คว่าหินแข็งเกินกว่าหัวขุดปัจจุบันหรือไม่
        if is_rock and self.drill_level() < S.ROCK_MIN_DRILL_LEVEL:
            self.is_drilling = False
            # กระแทกหินแล้วขุดไม่เข้า มีเสียงกระทบ
            self._drill_sound_timer += dt
            if self._drill_sound_timer >= 0.22:
                assets.play_sound("rock_clink", volume=0.5)
                self._drill_sound_timer = 0.0
            return

        self.is_drilling = True
        self.energy = max(0.0, self.energy - S.BASE_ENERGY_DRAIN_DIG * dt)

        # สั่นสะเทือนตอนเจาะ (Juice)
        self.vibe_x = (random.random() * 2.0 - 1.0) * 1.5
        self.vibe_y = (random.random() * 2.0 - 1.0) * 1.5

        # เสียงเจาะ
        self._drill_sound_timer += dt
        if self._drill_sound_timer >= 0.14:
            assets.play_sound("drill", volume=0.55)
            self._drill_sound_timer = 0.0

        # เสกเศษดิน/เศษหินกระจาย
        if particle_system and random.random() < 0.65:
            fx = self.x + self.facing[0] * (self.w / 2.0 + 4)
            fy = self.y + self.facing[1] * (self.h / 2.0 + 4)
            particle_system.spawn_dig_debris(fx, fy, is_rock=is_rock)

        # ทำความเสียหายต่อบล็อก (เมื่อพุ่งดิ่งชนบล็อกด้านล่างตามแรงโน้มถ่วง พลังเจาะจะแรงขึ้นหลายเท่า Ground Slam!)
        drill_mult = 1.0
        if self.is_diving and self.facing == (0, 1):
            drill_mult = 1.0 + (S.GRAV_DRILL_MULT - 1.0) * self.dive_power
            # สั่นสะเทือนพื้นและสร้างคลื่นกระแทก
            self.vibe_x = (random.random() * 2.0 - 1.0) * 3.5 * self.dive_power
            self.vibe_y = (random.random() * 2.0 - 1.0) * 3.5 * self.dive_power
            if particle_system and self.dive_power > 0.2:
                particle_system.spawn_ground_slam_shockwave(self.x, row * S.TILE)
                particle_system.add_floating_text(f"💥 GRAVITY SLAM! (x{drill_mult:.1f})", self.x, self.y - 20, (255, 210, 60))
                if self.on_dive_performed:
                    self.on_dive_performed()
            # สลายพลังงานศักย์ลงเมื่อกระแทกพื้น
            self.grav_charge = max(0.0, self.grav_charge - dt * 2.2)

        damage_amount = self.power * drill_mult * dt
        dug_through = world.damage_tile(col, row, damage_amount)

        if dug_through:
            self._on_block_dug(col, row, world, particle_system, is_rock)
            self.drilling_target = None

        # ---- Drill Reach: เจาะบล็อกข้าง ๆ ตาม Tier ----
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
            half = reach - 1  # reach=2 → half=1 → offset ±1
            side_damage = damage_amount  # บล็อกข้างได้รับความเสียหายเท่ากับบล็อกหลัก (แตกพร้อมกัน)
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
                    # หินข้างก็ต้องเช็ค drill_level ด้วย
                    if side_is_rock and self.drill_level() < S.ROCK_MIN_DRILL_LEVEL:
                        continue
                    side_dug = world.damage_tile(sc, sr, side_damage)
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
        if res == S.RES_FUEL:
            # กระป๋องน้ำมัน: เติมพลังงานทันที ไม่ต้องเก็บในถัง
            restore = min(S.FUEL_CANISTER_RESTORE, self.max_energy - self.energy)
            self.energy = min(self.max_energy, self.energy + S.FUEL_CANISTER_RESTORE)
            assets.play_sound("refuel", volume=0.8)
            if self.on_resource_collected:
                self.on_resource_collected(S.RES_FUEL)
            if particle_system:
                particle_system.add_floating_text(
                    f"⛽ +{int(restore)} พลังงาน!", t_cx, t_cy, (255, 210, 60)
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

    # ------------------------------------------------------------------
    def to_dict(self):
        return {
            "x": self.x, "y": self.y,
            "levels": self.levels,
            "energy": self.energy,
            "cargo": {str(k): v for k, v in self.cargo.items()},
            "cargo_count": self.cargo_count,
            "coins": self.coins,
        }

    def load_dict(self, data):
        self.x = data["x"]
        self.y = data["y"]
        self.levels = {k: int(v) for k, v in data["levels"].items()}
        self.recalc_stats()
        self.energy = data["energy"]
        self.cargo = {int(k): v for k, v in data["cargo"].items()}
        self.cargo_count = data["cargo_count"]
        self.coins = data["coins"]
        self.grav_charge = 0.0
        self.is_diving = False
        self.dive_power = 0.0
