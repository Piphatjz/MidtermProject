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

    # Test 4: UI Rendering (Menu, Contracts, HUD, Shop, Pause, Victory)
    print("Testing UI Rendering for all states...")
    ui.draw_main_menu(screen, False, (100, 100))
    ui.draw_main_menu(screen, True, (100, 100))

    import missions
    contracts = missions.get_three_contract_options()
    assert len(contracts) == 3
    assert contracts[0].difficulty == "easy"
    assert contracts[1].difficulty == "medium"
    assert contracts[2].difficulty == "hard"
    ui.draw_contract_menu(screen, contracts, (100, 100))
    ui.draw_shop_menu(screen, game.vehicle, (100, 100))
    ui.draw_pause_menu(screen, (100, 100))
    ui.draw_end_screen(screen, "ทดสอบ", "คำอธิบาย", game.vehicle, (100, 100), mission=game.mission)
    print("  -> UI rendering across all menus and HUD passed OK.")

    # Test 5: Composite Mission Progression & Victory
    print("Testing Composite Mission Progression and Victory...")
    test_bp = {
        "id": "test_m",
        "difficulty": "easy",
        "title": "ภารกิจทดสอบ",
        "desc": "ทดสอบระบบ",
        "goals": {
            "diamonds": 1,
            "gold": 2,
            "depth": 10,
        },
    }
    m = missions.Mission(test_bp)
    game.mission = m
    assert not game.mission.is_completed()

    # Progress goals
    game.mission.add_mined_resource(S.RES_DIAMOND)
    game.mission.add_mined_resource(S.RES_GOLD)
    game.mission.add_mined_resource(S.RES_GOLD)
    game.mission.update_from_game(game.vehicle, 12)
    assert game.mission.is_completed(), "All goals should be met!"
    print("  -> Composite Mission goals met correctly.")

    # Test 6: Save and Load with Mission
    print("Testing Save and Load with Mission...")
    game.save_and_quit()
    assert SM.save_exists(), "Save file does not exist!"
    game.load_game()
    assert game.mission is not None
    assert game.mission.id == "test_m"
    assert game.mission.is_completed()
    print("  -> Save and Load with Mission passed OK.")

    # Test 7: Customization Assets Verification
    print("Testing Customization Assets (Vehicles, Drills, Non-Square Icons)...")
    assert assets.get_image("res_fuel") is not None
    for vtid in S.VEHICLE_TYPES:
        for cid in S.VEHICLE_COLORS:
            img_key = f"vehicle_{vtid}_{cid}"
            surf = assets.get_image(img_key)
            assert surf is not None, f"Missing vehicle sprite: {img_key}"
            assert surf.get_width() == 42 and surf.get_height() == 42

    for dhid in S.DRILL_HEADS:
        for ddir in ["down", "up", "left", "right"]:
            d_key = f"drill_{dhid}_{ddir}"
            surf = assets.get_image(d_key)
            assert surf is not None, f"Missing drill sprite: {d_key}"
            assert surf.get_width() == 24 and surf.get_height() == 24
    print("  -> All 32 vehicle sprites, 20 drill head sprites, and non-square fuel canister verified OK.")

    # Test 8: Chassis Stat Modifiers & Drill Head Mechanics
    print("Testing Chassis Stat Modifiers & Drill Head Mechanics...")
    v_std = Vehicle(2, 2, vehicle_type="standard", drill_head="spiral")
    v_scout = Vehicle(2, 2, vehicle_type="scout", drill_head="spiral")
    v_titan = Vehicle(2, 2, vehicle_type="titan", drill_head="spiral")
    v_hover = Vehicle(2, 2, vehicle_type="hover", drill_head="spiral")

    # Scout should have higher speed and lower capacity than Standard
    assert v_scout.speed > v_std.speed, "Scout must be faster than Standard!"
    assert v_scout.max_capacity < v_std.max_capacity, "Scout must have smaller capacity!"

    # Titan should have higher capacity and extra energy
    assert v_titan.max_capacity > v_std.max_capacity, "Titan must have larger capacity!"
    assert v_titan.max_energy > v_std.max_energy, "Titan must have extra energy!"

    # Drill Heads Mechanics:
    # 1. Titanium Diamond can dig rock at Level 1 without rock_min_drill_level restriction
    v_spiral = Vehicle(2, 2, drill_head="spiral")
    v_diamond = Vehicle(2, 2, drill_head="diamond")
    assert not v_spiral.can_drill_rock(), "Standard spiral drill at Lv1 cannot drill rock!"
    assert v_diamond.can_drill_rock(), "Titanium Diamond drill MUST bypass rock requirement at Lv1!"

    # 2. Plasma Cutter has +65% drilling power
    v_plasma = Vehicle(2, 2, drill_head="plasma")
    assert v_plasma.power > v_std.power * 1.5, "Plasma cutter must have elevated drilling power!"

    # 3. Magnetic Vortex has bonus sell multiplier
    v_vortex = Vehicle(2, 2, drill_head="vortex")
    v_std.cargo[S.RES_GOLD] = 1
    v_std.cargo_count = 1
    v_vortex.cargo[S.RES_GOLD] = 1
    v_vortex.cargo_count = 1
    earned_std = v_std.sell_cargo()
    earned_vortex = v_vortex.sell_cargo()
    assert earned_vortex > earned_std, "Magnetic Vortex must yield more coins from selling cargo!"

    # 4. Seismic Hammer has reach = 2 immediately
    v_seismic = Vehicle(2, 2, drill_head="seismic")
    assert v_seismic.drill_reach == 2, "Seismic Hammer must have reach 2 from Tier 1!"
    print("  -> Vehicle chassis modifiers and drill head abilities verified OK.")

    # Test 9: Garage Menu UI & Interactive State Transitions
    print("Testing Garage Menu UI & Transitions...")
    # Render all 3 garage tabs
    ui.draw_garage_menu(screen, v_titan, (100, 100), active_tab="color")
    ui.draw_garage_menu(screen, v_titan, (100, 100), active_tab="type")
    ui.draw_garage_menu(screen, v_titan, (100, 100), active_tab="drill")

    # Test state transition MENU -> GARAGE
    test_game = Game(screen)
    assert test_game.state == "menu"
    test_game.draw()
    assert "garage" in test_game.buttons

    # Simulate clicking 'garage' button
    garage_btn = test_game.buttons["garage"]
    click_evt = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=garage_btn.center)
    test_game.handle_event(click_evt)
    assert test_game.state == "garage", "Must transition to GARAGE from menu!"
    test_game.draw()

    # In GARAGE: click tab_type
    assert "tab_type" in test_game.buttons
    click_type_tab = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=test_game.buttons["tab_type"].center)
    test_game.handle_event(click_type_tab)
    assert test_game.garage_tab == "type"
    test_game.draw()

    # Click titan type
    assert "type_titan" in test_game.buttons
    click_titan = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=test_game.buttons["type_titan"].center)
    test_game.handle_event(click_titan)
    assert test_game.vehicle.vehicle_type == "titan"

    # Click tab_drill
    click_drill_tab = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=test_game.buttons["tab_drill"].center)
    test_game.handle_event(click_drill_tab)
    assert test_game.garage_tab == "drill"
    test_game.draw()

    # Click drill_diamond
    assert "drill_diamond" in test_game.buttons
    click_diamond = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=test_game.buttons["drill_diamond"].center)
    test_game.handle_event(click_diamond)
    assert test_game.vehicle.drill_head == "diamond"

    # Click apply
    assert "apply" in test_game.buttons
    click_apply = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=test_game.buttons["apply"].center)
    test_game.handle_event(click_apply)
    assert test_game.state == "menu", "Must return to previous state (MENU) after apply!"

    # New game should inherit selected vehicle customizations
    test_game.new_game()
    assert test_game.vehicle.vehicle_type == "titan"
    assert test_game.vehicle.drill_head == "diamond"
    print("  -> Garage menu navigation, selection, and application verified OK.")

    # Test 10: Customization Save & Load Persistence
    print("Testing Customization Save & Load Persistence...")
    test_game.vehicle.color_id = "carbon"
    test_game.vehicle.vehicle_type = "hover"
    test_game.vehicle.drill_head = "plasma"
    test_game.vehicle.recalc_stats()
    test_game.save_and_quit()

    loaded_game = Game(screen)
    loaded_game.load_game()
    assert loaded_game.vehicle.color_id == "carbon"
    assert loaded_game.vehicle.vehicle_type == "hover"
    assert loaded_game.vehicle.drill_head == "plasma"
    assert loaded_game.vehicle.power > v_std.power * 1.5
    print("  -> Customization saved and restored accurately.")

    # Clean up test save
    if SM.save_exists():
        SM.delete_save()

    pygame.quit()
    print("=== ALL TESTS PASSED SUCCESSFULLY! ===")


if __name__ == "__main__":
    run_tests()

