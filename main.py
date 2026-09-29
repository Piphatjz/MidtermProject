# -*- coding: utf-8 -*-
"""
main.py  (Pygbag/WebAssembly build)
แปลง game loop ให้เป็น async สำหรับรันบนเว็บผ่าน Pygbag
"""
import asyncio
import pygame
import settings as S
import ui
from game import Game


def compute_scale_and_offset(game_w, game_h, screen_w, screen_h):
    scale = min(screen_w / game_w, screen_h / game_h)
    scaled_w = int(game_w * scale)
    scaled_h = int(game_h * scale)
    off_x = (screen_w - scaled_w) // 2
    off_y = (screen_h - scaled_h) // 2
    return scale, off_x, off_y, scaled_w, scaled_h


async def main():
    pygame.init()
    ui.init_fonts()

    screen = pygame.display.set_mode((S.SCREEN_W, S.SCREEN_H))
    pygame.display.set_caption("Dig & Treasure")
    clock = pygame.time.Clock()

    game_surf = pygame.Surface((S.SCREEN_W, S.SCREEN_H))
    game = Game(game_surf)

    scale, off_x, off_y, scaled_w, scaled_h = 1.0, 0, 0, S.SCREEN_W, S.SCREEN_H

    running = True
    while running:
        dt = clock.tick(S.FPS) / 1000.0
        dt = min(dt, 0.05)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                sw, sh = event.w, event.h
                scale, off_x, off_y, scaled_w, scaled_h = compute_scale_and_offset(
                    S.SCREEN_W, S.SCREEN_H, sw, sh
                )
                game.display_scale = scale
                game.display_offset = (off_x, off_y)
            else:
                result = game.handle_event(event)
                if result == "QUIT":
                    running = False

        game.update(dt)
        game.draw()

        if scale == 1.0 and off_x == 0 and off_y == 0:
            screen.blit(game_surf, (0, 0))
        else:
            screen.fill((0, 0, 0))
            scaled = pygame.transform.smoothscale(game_surf, (scaled_w, scaled_h))
            screen.blit(scaled, (off_x, off_y))

        pygame.display.flip()
        await asyncio.sleep(0)

    pygame.quit()


asyncio.run(main())
