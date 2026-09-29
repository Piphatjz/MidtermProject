# -*- coding: utf-8 -*-
"""
particles.py
ระบบเอฟเฟกต์อนุภาค (เศษดิน, ประกายไฟ, ควันท่อไอเสีย) และข้อความลอย (Floating Text)
"""
import random
import pygame
import settings as S

pygame.font.init()
_FLOAT_FONT = None


def _get_font():
    global _FLOAT_FONT
    if _FLOAT_FONT is None:
        thai_font = pygame.font.match_font("tahoma,leelawadee,garuda,arialunicodems")
        _FLOAT_FONT = pygame.font.Font(thai_font, 18)
    return _FLOAT_FONT


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "size", "color", "gravity")

    def __init__(self, x, y, vx, vy, life, size, color, gravity=180.0):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.size = size
        self.color = color
        self.gravity = gravity

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gravity * dt
        self.life -= dt
        return self.life > 0


class FloatingText:
    __slots__ = ("text", "x", "y", "color", "life", "max_life", "vy")

    def __init__(self, text, x, y, color=(255, 255, 100), life=1.2, vy=-40.0):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.life = life
        self.max_life = life
        self.vy = vy

    def update(self, dt):
        self.y += self.vy * dt
        self.life -= dt
        return self.life > 0


class ParticleSystem:
    def __init__(self):
        self.particles = []
        self.floating_texts = []
        self.rng = random.Random()

    def clear(self):
        self.particles.clear()
        self.floating_texts.clear()

    def spawn_dig_debris(self, x, y, is_rock=False):
        """เสกเศษหินหรือเศษดินกระจายออกมาจากการเจาะ"""
        count = 4 if not is_rock else 6
        for _ in range(count):
            angle = self.rng.uniform(0, 6.283)
            speed = self.rng.uniform(30, 95)
            vx = speed * self.rng.uniform(-1, 1)
            vy = self.rng.uniform(-70, -20)
            life = self.rng.uniform(0.25, 0.45)
            size = self.rng.uniform(2.5, 4.5)
            if is_rock:
                # Stone gray / spark bright yellow
                c = self.rng.choice([
                    (180, 185, 195),
                    (130, 135, 145),
                    (255, 230, 120),  # Spark
                ])
            else:
                # Dirt brown specks
                c = self.rng.choice([
                    (160, 105, 65),
                    (135, 85, 50),
                    (110, 70, 40),
                ])
            self.particles.append(Particle(x, y, vx, vy, life, size, c, gravity=240.0))

    def spawn_block_break(self, cx, cy, is_rock=False):
        """เสกการระเบิดแตกกระจายของบล็อกเมื่อขุดเสร็จ"""
        count = 14 if not is_rock else 18
        for _ in range(count):
            vx = self.rng.uniform(-80, 80)
            vy = self.rng.uniform(-120, -10)
            life = self.rng.uniform(0.35, 0.6)
            size = self.rng.uniform(3.0, 6.0)
            c = (140, 90, 55) if not is_rock else (150, 155, 165)
            self.particles.append(Particle(cx, cy, vx, vy, life, size, c, gravity=300.0))

    def spawn_exhaust_smoke(self, x, y):
        """ควันท่อไอเสียเบา ๆ จากรถขุด"""
        vx = self.rng.uniform(-8, 8)
        vy = self.rng.uniform(-15, -5)
        life = self.rng.uniform(0.3, 0.5)
        size = self.rng.uniform(3.0, 5.0)
        c = (180, 180, 190)
        self.particles.append(Particle(x, y, vx, vy, life, size, c, gravity=-10.0))

    def spawn_charge_spark(self, x, y):
        """ประกายไฟฟ้าระหว่างชาร์จพลังงานศักย์ขึ้นสู่ด้านบน (Gravitational potential spark)"""
        for _ in range(2):
            vx = self.rng.uniform(-30, 30)
            vy = self.rng.uniform(10, 45) # ประกายพ่นลงด้านล่าง
            life = self.rng.uniform(0.15, 0.3)
            size = self.rng.uniform(2.0, 3.5)
            c = self.rng.choice([
                (80, 225, 255),   # Cyan electric
                (255, 240, 110),  # Yellow spark
                (170, 255, 250),  # Bright white-blue
            ])
            self.particles.append(Particle(x, y, vx, vy, life, size, c, gravity=0.0))

    def spawn_gravity_dive_trail(self, x, y):
        """เส้นลมพุ่งดิ่งและความเร็วสูงตามแรงโน้มถ่วง (Gravitational dive air streaks)"""
        for _ in range(3):
            vx = self.rng.uniform(-10, 10)
            vy = self.rng.uniform(-130, -60) # พุ่งสวนขึ้นไปด้านบนเหมือนลมต้านความเร็วสูง
            life = self.rng.uniform(0.16, 0.30)
            size = self.rng.uniform(2.5, 4.5)
            c = self.rng.choice([
                (100, 230, 255),  # Cyan gravity air
                (255, 255, 255),  # White sonic trail
                (255, 200, 60),   # Kinetic friction yellow
            ])
            self.particles.append(Particle(x, y, vx, vy, life, size, c, gravity=40.0))

    def spawn_ground_slam_shockwave(self, cx, cy):
        """คลื่นกระแทกดินกระจายเมื่อพุ่งดิ่งชนพื้นดินด้วยแรงโน้มถ่วง (Ground Slam Impact)"""
        for _ in range(16):
            vx = self.rng.uniform(-150, 150)
            vy = self.rng.uniform(-90, 15)
            life = self.rng.uniform(0.28, 0.50)
            size = self.rng.uniform(3.5, 6.5)
            c = self.rng.choice([
                (240, 195, 110),  # Shockwave dust
                (150, 110, 70),   # Earth brown
                (255, 245, 180),  # Impact flash
            ])
            self.particles.append(Particle(cx, cy, vx, vy, life, size, c, gravity=200.0))

    def spawn_plasma_spark(self, x, y):
        """สะเก็ดประกายไฟพลาสม่าร้อนแรงสูง (Plasma Melter)"""
        for _ in range(4):
            vx = self.rng.uniform(-75, 75)
            vy = self.rng.uniform(-75, 75)
            life = self.rng.uniform(0.18, 0.38)
            size = self.rng.uniform(3.0, 6.0)
            c = self.rng.choice([
                (255, 235, 80),   # Bright yellow core
                (255, 110, 20),   # Incandescent orange
                (255, 50, 20),    # Fiery red
                (255, 255, 240),  # White heat
            ])
            self.particles.append(Particle(x, y, vx, vy, life, size, c, gravity=-30.0))

    def spawn_diamond_spark(self, x, y):
        """ประกายเพชรและเกล็ดคริสตัลระยิบระยับ (Titanium Diamond)"""
        for _ in range(4):
            vx = self.rng.uniform(-65, 65)
            vy = self.rng.uniform(-80, 20)
            life = self.rng.uniform(0.20, 0.42)
            size = self.rng.uniform(2.5, 5.0)
            c = self.rng.choice([
                (140, 240, 255),  # Cyan sparkle
                (210, 250, 255),  # Crystal glint
                (60, 180, 245),   # Deep blue diamond
                (255, 255, 255),  # Bright white flash
            ])
            self.particles.append(Particle(x, y, vx, vy, life, size, c, gravity=120.0))

    def spawn_vortex_spark(self, x, y):
        """อนุภาคคลื่นแม่เหล็กไฟฟ้าสีม่วงนีออน (Magnetic Vortex)"""
        for _ in range(3):
            vx = self.rng.uniform(-60, 60)
            vy = self.rng.uniform(-60, 60)
            life = self.rng.uniform(0.25, 0.45)
            size = self.rng.uniform(3.0, 5.5)
            c = self.rng.choice([
                (200, 95, 255),   # Neon purple
                (240, 160, 255),  # Lavender flux
                (120, 50, 235),   # Deep violet
                (80, 220, 255),   # Magnetic cyan arc
            ])
            self.particles.append(Particle(x, y, vx, vy, life, size, c, gravity=0.0))

    def spawn_seismic_shock(self, x, y):
        """ฝุ่นและเศษหินคลื่นกระแทกสั่นสะเทือน (Seismic Hammer)"""
        for _ in range(5):
            vx = self.rng.uniform(-110, 110)
            vy = self.rng.uniform(-90, 30)
            life = self.rng.uniform(0.22, 0.45)
            size = self.rng.uniform(3.5, 6.5)
            c = self.rng.choice([
                (225, 180, 110),  # Seismic sand
                (140, 95, 55),    # Heavy earth
                (255, 220, 140),  # Impact dust
            ])
            self.particles.append(Particle(x, y, vx, vy, life, size, c, gravity=180.0))

    def spawn_spark(self, x, y, color=(255, 220, 80)):
        """ประกายไฟหรือดาวแสงสว่างพร้อมกำหนดสีได้"""
        for _ in range(4):
            vx = self.rng.uniform(-70, 70)
            vy = self.rng.uniform(-80, 20)
            life = self.rng.uniform(0.25, 0.50)
            size = self.rng.uniform(2.5, 5.0)
            self.particles.append(Particle(x, y, vx, vy, life, size, color, gravity=100.0))

    def add_floating_text(self, text, x, y, color=(255, 255, 100)):
        self.floating_texts.append(FloatingText(text, x, y, color))

    def update(self, dt):
        self.particles = [p for p in self.particles if p.update(dt)]
        self.floating_texts = [ft for ft in self.floating_texts if ft.update(dt)]

    def draw(self, surface, camera_y):
        # วาด particles เป็นทรงกลมนุ่มนวล ไร้เหลี่ยมมุม (Smooth circular particles)
        for p in self.particles:
            py_screen = p.y - camera_y + S.HUD_H
            if -10 <= py_screen <= S.SCREEN_H + 10:
                s = max(1, int(p.size * (p.life / p.max_life)))
                r = max(1, s // 2)
                pygame.draw.circle(surface, p.color, (int(p.x), int(py_screen)), r)

        # วาด floating text
        font = _get_font()
        for ft in self.floating_texts:
            fy_screen = ft.y - camera_y + S.HUD_H
            if -20 <= fy_screen <= S.SCREEN_H + 20:
                alpha = max(0, min(255, int(255 * (ft.life / ft.max_life))))
                text_surf = font.render(ft.text, True, ft.color)
                # Shadow
                sh_surf = font.render(ft.text, True, (10, 10, 10))
                surface.blit(sh_surf, (int(ft.x - text_surf.get_width() / 2 + 1), int(fy_screen + 1)))
                surface.blit(text_surf, (int(ft.x - text_surf.get_width() / 2), int(fy_screen)))
