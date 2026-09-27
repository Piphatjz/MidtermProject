# -*- coding: utf-8 -*-
"""
test_game.py
ทดสอบอัตโนมัติ (Automated headless test):
1. ตรวจสอบการโหลด Assets ครบทุกชิ้น
2. ทดสอบ Game Loop, World, Vehicle
3. ทดสอบการเคลื่อนที่ การเจาะบล็อก และการแตกของบล็อก
4. ทดสอบ Particle และระบบเซฟเกม
"""
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
import settings as S
import assets
import ui
from game import Game
from world import World
from vehicle import Vehicle
from particles import ParticleSystem
import save_manager as SM


def run_tests():
    print("=== STARTING AUTOMATED TESTS ===")
    pygame.init()
    assets.init()
    ui.init_fonts()

    screen = pygame.display.set_mode((S.SCREEN_W, S.SCREEN_H))

    # Test 1: Assets Loading
    print("Testing assets loading...")
    for img in ["dirt", "grass", "rock", "tunnel", "crack_1", "crack_2", "crack_3",
                "res_coin", "res_gold", "res_diamond", "vehicle_body",
                "drill_down", "drill_up", "drill_left", "drill_right",
                "building_home", "building_shop"]:
        surf = assets.get_image(img)
        assert surf is not None, f"Failed to load image: {img}"
    print("  -> Assets images loaded OK.")

    for snd in ["drill", "dig_pop", "rock_clink", "coin", "gem", "sell", "refuel", "upgrade", "low_energy"]:
        assets.play_sound(snd)
    print("  -> Assets sounds triggered OK.")

    # Test 2: Game initialization & New Game
    print("Testing Game state & New Game...")
    game = Game(screen)
    game.new_game()
    assert game.vehicle is not None
    assert game.world is not None
    print(f"  -> Vehicle start position: ({game.vehicle.x}, {game.vehicle.y})")
    print(f"  -> Vehicle grid position: {game.vehicle.grid_pos()}")

    # Test 3: Simulation Loop (120 frames)
    print("Testing movement and digging simulation...")
    # Move DOWN into the mine
    for _ in range(30):
        game.vehicle.update(0.016, game.world, (0, 1), game.particles)
        game.particles.update(0.016)
        game.draw()

    print(f"  -> Position after moving down: ({game.vehicle.x:.1f}, {game.vehicle.y:.1f})")

    # Dig into solid dirt to the right
    col, row = game.vehicle.grid_pos()
    dirt_target_col = col + 1
    dirt_target_row = row
    game.world.tiles[dirt_target_row][dirt_target_col] = S.T_DIRT
    game.world.hp[dirt_target_row][dirt_target_col] = 4.0
    game.world.max_hp[dirt_target_row][dirt_target_col] = 4.0
    game.world.resource[dirt_target_row][dirt_target_col] = S.RES_GOLD

    print(f"  -> Starting drill on tile ({dirt_target_col}, {dirt_target_row}), initial HP: {game.world.hp[dirt_target_row][dirt_target_col]}")

    # Simulate pressing RIGHT to drill the tile
    dug = False
    for frame in range(60):
        game.vehicle.update(0.016, game.world, (1, 0), game.particles)
        game.particles.update(0.016)
        game.draw()
        if game.world.tiles[dirt_target_row][dirt_target_col] == S.T_EMPTY:
            dug = True
            print(f"  -> Block broken successfully at frame {frame}! Tile is now T_EMPTY.")
            break

    assert dug, "Block was not broken within 60 frames!"
    assert game.vehicle.cargo[S.RES_GOLD] > 0, "Resource was not collected into cargo!"
    print(f"  -> Cargo collected: {game.vehicle.cargo}")

    # Test 4: Save and Load
    print("Testing Save and Load...")
    SM.save_game(game.world, game.vehicle)
    assert SM.save_exists(), "Save file does not exist!"
    data = SM.load_game()
    assert "world" in data and "vehicle" in data
    print("  -> Save and Load passed OK.")

    # Clean up test save
    if SM.save_exists():
        SM.delete_save()

    pygame.quit()
    print("=== ALL TESTS PASSED SUCCESSFULLY! ===")


if __name__ == "__main__":
    run_tests()
