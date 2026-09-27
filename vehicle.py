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
        self.coins = 0

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

        self.recalc_stats()

    # ------------------------------------------------------------------
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

    def drill_level(self):
        return self.levels["power"]

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
    def update(self, dt, world, raw_input, particle_system=None):
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

        if (dir_x, dir_y) == (0, 0):
            self.drilling_target = None
            return

        self.facing = (dir_x, dir_y)

        col, row = self.grid_pos()
        cell_cx = col * S.TILE + S.TILE / 2.0
        cell_cy = row * S.TILE + S.TILE / 2.0

        # อัตราการเคลื่อนที่เฟรมนี้
        move_dist = self.speed * dt
        half_w = self.w / 2.0
        half_h = self.h / 2.0

        # -----------------------------
        # 1. การเคลื่อนที่แนวนอน (ซ้าย / ขวา)
        # -----------------------------
        if dir_x != 0:
            # ดึงรถให้อยู่ตรงกลางเลนแนวนอนอย่างนุ่มนวล
            self.y += (cell_cy - self.y) * min(1.0, dt * 14.0)

            if dir_x > 0:  # ไปทางขวา
                target_col = col + 1
                target_row = row
                is_solid = world.is_solid(target_col, target_row)
                block_edge = target_col * S.TILE

                if is_solid and (self.x + half_w + move_dist) >= block_edge:
                    # ชนบล็อกทางขวา - หยุดชิดขอบและเริ่มเจาะบล็อกนี้
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
                    # ชนบล็อกทางซ้าย - หยุดชิดขอบและเริ่มเจาะบล็อกนี้
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
            # ดึงรถให้อยู่ตรงกลางเลนแนวตั้งอย่างนุ่มนวล
            self.x += (cell_cx - self.x) * min(1.0, dt * 14.0)

            if dir_y > 0:  # ลงล่าง
                target_col = col
                target_row = row + 1
                is_solid = world.is_solid(target_col, target_row)
                block_edge = target_row * S.TILE

                if is_solid and (self.y + half_h + move_dist) >= block_edge:
                    # ชนบล็อกข้างล่าง - หยุดชิดขอบและเริ่มเจาะบล็อกนี้
                    self.y = block_edge - half_h
                    self._handle_drilling(target_col, target_row, world, dt, particle_system)
                else:
                    self.y += move_dist
                    self.is_moving = True
                    self.drilling_target = None

            elif dir_y < 0:  # ขึ้นบน
                target_col = col
                target_row = row - 1
                is_solid = world.is_solid(target_col, target_row)
                block_edge = (target_row + 1) * S.TILE

                if is_solid and (self.y - half_h - move_dist) <= block_edge:
                    # ชนบล็อกข้างบน - หยุดชิดขอบและเริ่มเจาะ
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

        # ลดพลังงานเมื่อวิ่ง
        if self.is_moving:
            self.energy = max(0.0, self.energy - S.BASE_ENERGY_DRAIN_MOVE * dt)
            self._smoke_timer += dt
            if particle_system and self._smoke_timer >= 0.12:
                # ปล่อยควันออกจากท้ายรถ
                bx = self.x - self.facing[0] * half_w
                by = self.y - self.facing[1] * half_h
                particle_system.spawn_exhaust_smoke(bx, by)
                self._smoke_timer = 0.0

        # อัพเดทอนิเมชันหัวสว่านหมุน
        rot_speed = 36.0 if self.is_drilling else (16.0 if self.is_moving else 0.0)
        self.drill_anim += dt * rot_speed

    # ------------------------------------------------------------------
    def _handle_drilling(self, col, row, world, dt, particle_system):
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

        # ทำความเสียหายต่อบล็อก
        damage_amount = self.power * dt
        dug_through = world.damage_tile(col, row, damage_amount)

        if dug_through:
            # บล็อกแตกสำเร็จ!
            t_cx = col * S.TILE + S.TILE / 2.0
            t_cy = row * S.TILE + S.TILE / 2.0
            assets.play_sound("dig_pop" if not is_rock else "rock_clink", volume=0.75)

            if particle_system:
                particle_system.spawn_block_break(t_cx, t_cy, is_rock=is_rock)

            res = world.collect_resource(col, row)
            if res != S.RES_NONE:
                if self.add_cargo(res):
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

            self.drilling_target = None

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
