# -*- coding: utf-8 -*-
"""
main.py
จุดเริ่มต้นของเกม - รัน:  python main.py

รองรับ Fullscreen แบบ Scale จริง:
  - เกม render ลง game_surf ขนาดคงที่ (SCREEN_W x SCREEN_H)
  - เมื่อ fullscreen จะ scale game_surf ขึ้นให้เต็มจอพอดี
  - Mouse coordinates จะถูกแปลงกลับไปยัง game-space อัตโนมัติ
"""
import pygame
import settings as S
import ui
from game import Game


def compute_scale_and_offset(game_w, game_h, screen_w, screen_h):
    """คำนวณ scale + offset เพื่อ letterbox/pillarbox game surface ให้พอดีจอจริง"""
    scale = min(screen_w / game_w, screen_h / game_h)
    scaled_w = int(game_w * scale)
    scaled_h = int(game_h * scale)
    off_x = (screen_w - scaled_w) // 2
    off_y = (screen_h - scaled_h) // 2
    return scale, off_x, off_y, scaled_w, scaled_h


def main():
    pygame.init()
    ui.init_fonts()

    # หน้าต่างเริ่มต้นขนาดเกม (Windowed)
    screen = pygame.display.set_mode((S.SCREEN_W, S.SCREEN_H), pygame.RESIZABLE)
    pygame.display.set_caption("Dig & Treasure - ขุดดินหาสมบัติ")
    clock = pygame.time.Clock()

    # Surface คงที่ที่เกมวาดลงตลอด (ไม่เปลี่ยนแปลงตามขนาดจอ)
    game_surf = pygame.Surface((S.SCREEN_W, S.SCREEN_H))

    game = Game(game_surf)

    is_fullscreen = False
    # scale / offset เริ่มต้น (Windowed = 1:1, ไม่มี offset)
    scale, off_x, off_y, scaled_w, scaled_h = 1.0, 0, 0, S.SCREEN_W, S.SCREEN_H

    running = True
    while running:
        dt = clock.tick(S.FPS) / 1000.0
        dt = min(dt, 0.05)  # กันเฟรมกระตุกแรง ๆ ทำให้ทะลุกำแพง

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # จับ F11 ในลูปหลักเพื่อสลับ fullscreen และอัพเดท scale
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                is_fullscreen = not is_fullscreen
                if is_fullscreen:
                    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                else:
                    screen = pygame.display.set_mode((S.SCREEN_W, S.SCREEN_H), pygame.RESIZABLE)
                sw, sh = screen.get_size()
                scale, off_x, off_y, scaled_w, scaled_h = compute_scale_and_offset(
                    S.SCREEN_W, S.SCREEN_H, sw, sh
                )
                # บอก game ว่า scale/offset เป็นอะไร (สำหรับแปลง mouse coordinates)
                game.display_scale = scale
                game.display_offset = (off_x, off_y)
                game.is_fullscreen = is_fullscreen
                continue

            elif event.type == pygame.VIDEORESIZE:
                sw, sh = event.w, event.h
                scale, off_x, off_y, scaled_w, scaled_h = compute_scale_and_offset(
                    S.SCREEN_W, S.SCREEN_H, sw, sh
                )
                game.display_scale = scale
                game.display_offset = (off_x, off_y)

            else:
                game.handle_event(event)

        game.update(dt)
        game.draw()

        # --- Blit game surface ไปหน้าจอจริง (พร้อม scale ถ้า fullscreen) ---
        if scale == 1.0 and off_x == 0 and off_y == 0:
            # Windowed 1:1 — blit ตรง ๆ ไม่ต้อง scale
            screen.blit(game_surf, (0, 0))
        else:
            screen.fill((0, 0, 0))  # letterbox bars
            scaled = pygame.transform.smoothscale(game_surf, (scaled_w, scaled_h))
            screen.blit(scaled, (off_x, off_y))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
