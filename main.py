# -*- coding: utf-8 -*-
"""
main.py
จุดเริ่มต้นของเกม - รัน:  python main.py
"""
import pygame
import settings as S
import ui
# import random
from game import Game


def main():
    pygame.init()
    ui.init_fonts()
    screen = pygame.display.set_mode((S.SCREEN_W, S.SCREEN_H))
    pygame.display.set_caption("Dig & Treasure - ขุดดินหาสมบัติ")
    clock = pygame.time.Clock()

    game = Game(screen)

    running = True
    while running:
        dt = clock.tick(S.FPS) / 1000.0
        dt = min(dt, 0.05)  # กันเฟรมกระตุกแรง ๆ ทำให้ทะลุกำแพง

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                game.handle_event(event)

        game.update(dt)
        game.draw()
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
