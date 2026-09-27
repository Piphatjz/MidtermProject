# -*- coding: utf-8 -*-
"""
world.py
สร้างและจัดการแผนที่ใต้ดิน (grid), ทรัพยากรในแต่ละช่อง, ความคงทนและการแตกของบล็อก
"""
import random
import settings as S


class World:
    def __init__(self, seed=None):
        self.rng = random.Random(seed)
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

    def _pick_underground_tile(self, depth):
        rock_chance = min(0.10 + depth * 0.0035, 0.45)
        cave_chance = 0.035
        roll = self.rng.random()
        if roll < cave_chance:
            return S.T_EMPTY
        if roll < cave_chance + rock_chance:
            return S.T_ROCK
        return S.T_DIRT

    def _pick_resource(self, depth, tile_type):
        if tile_type not in (S.T_DIRT, S.T_ROCK):
            return S.RES_NONE
        diamond_chance = min(0.015 + depth * 0.0012, 0.12)
        gold_chance = min(0.06 + depth * 0.001, 0.20)
        coin_chance = 0.22
        roll = self.rng.random()
        if roll < diamond_chance:
            return S.RES_DIAMOND
        if roll < diamond_chance + gold_chance:
            return S.RES_GOLD
        if roll < diamond_chance + gold_chance + coin_chance:
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
        """ช่องที่เป็นบล็อกแข็งขวางการเคลื่อนที่"""
        if col < 0 or col >= self.cols or row >= self.rows:
            return True
        if row < 0:
            return False
        return self.tiles[row][col] in (S.T_DIRT, S.T_ROCK, S.T_GRASS)

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
        return w
