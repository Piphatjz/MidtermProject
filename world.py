# -*- coding: utf-8 -*-
"""
world.py
สร้างและจัดการแผนที่ใต้ดิน (grid), ทรัพยากรในแต่ละช่อง, ความคงทนและการแตกของบล็อก
"""
import random
import settings as S


class World:
    def __init__(self, seed=None, game_mode="mission", unlocked_floor=1):
        self.rng = random.Random(seed)
        self.game_mode = game_mode
        self.unlocked_floor = unlocked_floor
        self.cols = S.COLS
        self.rows = S.WORLD_ROWS
        # tile_type[row][col]
        self.tiles = [[S.T_SKY for _ in range(self.cols)] for _ in range(self.rows)]
        # resource[row][col] -> RES_*
        self.resource = [[S.RES_NONE for _ in range(self.cols)] for _ in range(self.rows)]
        # hp remaining ของช่องที่ยังไม่ถูกเจาะ
        self.hp = [[0.0 for _ in range(self.cols)] for _ in range(self.rows)]
        self.max_hp = [[0.0 for _ in range(self.cols)] for _ in range(self.rows)]
        self._generate()

    # ------------------------------------------------------------------
    def _generate(self):
        for r in range(self.rows):
            for c in range(self.cols):
                if r < S.SURFACE_ROW:
                    self.tiles[r][c] = S.T_SKY
                    self.resource[r][c] = S.RES_NONE
                    self.hp[r][c] = 0.0
                    self.max_hp[r][c] = 0.0
                elif r == S.SURFACE_ROW:
                    self.tiles[r][c] = S.T_GRASS
                    self.resource[r][c] = S.RES_NONE
                    hardness = S.TILE_HARDNESS.get(S.T_GRASS, 4.0)
                    self.hp[r][c] = hardness
                    self.max_hp[r][c] = hardness
                else:
                    depth = r - S.SURFACE_ROW
                    t_type = self._pick_underground_tile(depth)
                    self.tiles[r][c] = t_type
                    self.resource[r][c] = self._pick_resource(depth, t_type)
                    hardness = S.TILE_HARDNESS.get(t_type, 0.0)
                    self.hp[r][c] = hardness
                    self.max_hp[r][c] = hardness

        # ลานหน้าบ้านและร้านค้า (แถวที่ 3 ช่วงบ้าน/ร้าน และทางลงเหมือง)
        # ให้มีทางลงเหมืองแนวดิ่งเปิดโล่ง 2 ช่องใต้บ้าน ให้ผู้เล่นลงเหมืองได้สะดวก
        for r in range(S.SURFACE_ROW, S.SURFACE_ROW + 3):
            for c in (S.HOME_COL, S.HOME_COL + 1):
                self.tiles[r][c] = S.T_EMPTY
                self.resource[r][c] = S.RES_NONE
                self.hp[r][c] = 0.0
                self.max_hp[r][c] = 0.0

        # โหมดคลาสสิก: ติดตั้งประตูกั้นชั้นความลึก (Barrier Gates) สำหรับชั้นที่ยังไม่ปลดล็อค
        if getattr(self, "game_mode", "mission") == "classic":
            self._apply_floor_barriers()

    def _apply_floor_barriers(self):
        """วางแถบประตูกั้นชั้นความลึกตามการปลดล็อค"""
        for floor_cfg in getattr(S, "CLASSIC_FLOORS", []):
            floor_num = floor_cfg["floor"]
            max_depth = floor_cfg["max_depth"]
            row = S.SURFACE_ROW + max_depth
            if row >= self.rows:
                continue
            # หากชั้นถัดไป (floor_num + 1) ยังไม่ปลดล็อค ให้กั้นประตูด้านล่างของชั้นนี้
            if (floor_num + 1) > self.unlocked_floor:
                for c in range(self.cols):
                    self.tiles[row][c] = S.T_BARRIER
                    self.resource[row][c] = S.RES_NONE
                    self.hp[row][c] = S.TILE_HARDNESS.get(S.T_BARRIER, 999999.0)
                    self.max_hp[row][c] = S.TILE_HARDNESS.get(S.T_BARRIER, 999999.0)

    def unlock_barrier(self, floor_num):
        """เปิดประตูกั้นเพื่อเข้าสู่ชั้น floor_num (คืนจำนวนบล็อกประตูที่เปิดออก)"""
        prev_floor_info = S.get_floor_info(floor_num - 1)
        target_depth = prev_floor_info["max_depth"]
        barrier_row = S.SURFACE_ROW + target_depth
        opened = 0
        if 0 <= barrier_row < self.rows:
            for c in range(self.cols):
                if self.tiles[barrier_row][c] == getattr(S, "T_BARRIER", 5):
                    self.tiles[barrier_row][c] = S.T_EMPTY
                    self.resource[barrier_row][c] = S.RES_NONE
                    self.hp[barrier_row][c] = 0.0
                    self.max_hp[barrier_row][c] = 0.0
                    opened += 1
        self.unlocked_floor = max(getattr(self, "unlocked_floor", 1), floor_num)
        return opened

    def _pick_underground_tile(self, depth):
        # โหมดภารกิจเดิม: ความลึกตั้งแต่ 40 ช่องลงไปเป็นชั้นหินล้วน (Solid Bedrock Layer)
        if getattr(self, "game_mode", "mission") != "classic":
            if depth >= getattr(S, "ROCK_LAYER_DEPTH", 40):
                return S.T_ROCK
            rock_chance = min(0.10 + depth * 0.0035, 0.45)
            cave_chance = 0.035
            roll = self.rng.random()
            if roll < cave_chance:
                return S.T_EMPTY
            if roll < cave_chance + rock_chance:
                return S.T_ROCK
            return S.T_DIRT

        # โหมดคลาสสิก: สเกลความยากของหินแบบสมดุล พร้อมเปิดโพรงถ้ำและเส้นทางให้ขุดได้ไม่สิ้นสุด
        rock_chance = min(0.12 + depth * 0.0028, 0.55)
        cave_chance = min(0.035 + depth * 0.00015, 0.08)
        roll = self.rng.random()
        if roll < cave_chance:
            return S.T_EMPTY
        if roll < cave_chance + rock_chance:
            return S.T_ROCK
        return S.T_DIRT

    def _pick_resource(self, depth, tile_type):
        if tile_type not in (S.T_DIRT, S.T_ROCK):
            return S.RES_NONE

        # สเกลทรัพยากร: ชั้นลึกพบเพชรและทองคำเข้มข้นยิ่งขึ้นตามความลึก
        diamond_chance = min(0.015 + depth * 0.0016, 0.22)
        gold_chance = min(0.06 + depth * 0.0014, 0.28)
        coin_chance = max(0.10, 0.22 - depth * 0.0008)
        fuel_chance = min(0.05, S.FUEL_CANISTER_CHANCE + depth * 0.0001)

        roll = self.rng.random()
        if roll < fuel_chance:
            return S.RES_FUEL
        if roll < fuel_chance + diamond_chance:
            return S.RES_DIAMOND
        if roll < fuel_chance + diamond_chance + gold_chance:
            return S.RES_GOLD
        if roll < fuel_chance + diamond_chance + gold_chance + coin_chance:
            return S.RES_COIN
        return S.RES_NONE

    # ------------------------------------------------------------------
    def in_bounds(self, col, row):
        return 0 <= col < self.cols and 0 <= row < self.rows

    def get_tile(self, col, row):
        if col < 0 or col >= self.cols or row >= self.rows:
            return S.T_ROCK  # ขอบข้างและก้นโลก = ผนังหินตันเสมอ
        if row < 0:
            return S.T_SKY
        return self.tiles[row][col]

    def is_solid(self, col, row):
        """ช่องที่เป็นบล็อกแข็งขวางการเคลื่อนที่ (รวมประตูกั้นชั้น)"""
        if col < 0 or col >= self.cols or row >= self.rows:
            return True
        if row < 0:
            return False
        return self.tiles[row][col] in (S.T_DIRT, S.T_ROCK, S.T_GRASS, getattr(S, "T_BARRIER", 5))

    def get_resource(self, col, row):
        if not self.in_bounds(col, row):
            return S.RES_NONE
        return self.resource[row][col]

    def get_damage_ratio(self, col, row):
        """คืนค่า 0.0 ถึง 1.0 บ่งบอกว่าบล็อกโดนเจาะไปกี่เปอร์เซ็นต์ (สำหรับวาดรอยแตก)"""
        if not self.in_bounds(col, row):
            return 0.0
        m = self.max_hp[row][col]
        if m <= 0:
            return 0.0
        ratio = (m - self.hp[row][col]) / m
        return max(0.0, min(1.0, ratio))

    def damage_tile(self, col, row, amount):
        """เจาะช่อง คืนค่า True ถ้าช่องนี้ถูกเจาะจนแตกกลายเป็นทางเดิน"""
        if not self.in_bounds(col, row):
            return False
        if not self.is_solid(col, row):
            return False

        self.hp[row][col] -= amount
        if self.hp[row][col] <= 0:
            self.tiles[row][col] = S.T_EMPTY
            self.hp[row][col] = 0.0
            return True
        return False

    def collect_resource(self, col, row):
        """คืนทรัพยากรที่อยู่ในช่องนี้ แล้วเคลียร์ออก"""
        if not self.in_bounds(col, row):
            return S.RES_NONE
        res = self.resource[row][col]
        self.resource[row][col] = S.RES_NONE
        return res

    # ------------------------------------------------------------------
    def to_dict(self):
        return {
            "tiles": self.tiles,
            "resource": self.resource,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "game_mode": getattr(self, "game_mode", "mission"),
            "unlocked_floor": getattr(self, "unlocked_floor", 1),
        }

    @classmethod
    def from_dict(cls, data):
        w = cls.__new__(cls)
        w.rng = random.Random()
        w.rows = len(data["tiles"])
        w.cols = len(data["tiles"][0]) if w.rows else S.COLS
        w.tiles = data["tiles"]
        w.resource = data["resource"]
        w.hp = data["hp"]
        w.max_hp = data.get("max_hp")
        if w.max_hp is None:
            # Fallback for older saves
            w.max_hp = [[S.TILE_HARDNESS.get(t, 0.0) for t in row] for row in w.tiles]
        w.game_mode = data.get("game_mode", "mission")
        w.unlocked_floor = data.get("unlocked_floor", 1)
        return w
