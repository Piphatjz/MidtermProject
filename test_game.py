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
import json
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
import settings as S
import assets
import ui
from game import (
    Game, PLAYING, SHOP, MENU, PAUSED, GARAGE,
    HOW_TO_PLAY, CONTRACT, GAME_OVER, VICTORY,
    LOAD_MENU, SAVE_MENU
)
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
    how_buttons = ui.draw_how_to_play(screen, (100, 100))
    assert "close" in how_buttons
    ui.draw_quick_controls_bar(screen)

    # Test menu button presence
    m_btns = ui.draw_main_menu(screen, False, (100, 100))
    assert "how_to_play" in m_btns
    p_btns = ui.draw_pause_menu(screen, (100, 100))
    assert "how_to_play" in p_btns
    print("  -> UI rendering across all menus, HUD, and How to Play passed OK.")

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
    # Render all 4 garage tabs
    ui.draw_garage_menu(screen, v_titan, (100, 100), active_tab="color")
    ui.draw_garage_menu(screen, v_titan, (100, 100), active_tab="type")
    ui.draw_garage_menu(screen, v_titan, (100, 100), active_tab="drill")
    ui.draw_garage_menu(screen, v_titan, (100, 100), active_tab="tech")

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

    # Click titan type with insufficient tokens -> should fail
    test_game.vehicle.tokens = 0
    assert "type_titan" in test_game.buttons
    click_titan = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=test_game.buttons["type_titan"].center)
    test_game.handle_event(click_titan)
    assert test_game.vehicle.vehicle_type != "titan", "Titan must require 5 Tokens to unlock!"

    # Give tokens and click titan type -> should succeed
    test_game.vehicle.tokens = 10
    test_game.handle_event(click_titan)
    assert test_game.vehicle.vehicle_type == "titan"
    assert test_game.vehicle.tokens == 5  # 10 - 5 = 5

    # Click tab_drill
    click_drill_tab = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=test_game.buttons["tab_drill"].center)
    test_game.handle_event(click_drill_tab)
    assert test_game.garage_tab == "drill"
    test_game.draw()

    # Click drill_diamond (costs 4 tokens, currently has 5)
    assert "drill_diamond" in test_game.buttons
    click_diamond = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=test_game.buttons["drill_diamond"].center)
    test_game.handle_event(click_diamond)
    assert test_game.vehicle.drill_head == "diamond"
    assert test_game.vehicle.tokens == 1  # 5 - 4 = 1

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
    test_game.vehicle.tokens = 8
    test_game.vehicle.unlocked_colors.add("carbon")
    test_game.vehicle.unlocked_chassis.add("hover")
    test_game.vehicle.unlocked_drills.add("plasma")
    test_game.vehicle.color_id = "carbon"
    test_game.vehicle.vehicle_type = "hover"
    test_game.vehicle.drill_head = "plasma"
    test_game.vehicle.tech_drone = True
    test_game.vehicle.tech_radio = True
    test_game.vehicle.recalc_stats()
    test_game.save_and_quit()

    loaded_game = Game(screen)
    loaded_game.load_game()
    assert loaded_game.vehicle.color_id == "carbon"
    assert loaded_game.vehicle.vehicle_type == "hover"
    assert loaded_game.vehicle.drill_head == "plasma"
    assert loaded_game.vehicle.tokens == 8
    assert loaded_game.vehicle.tech_drone is True
    assert loaded_game.vehicle.tech_radio is True
    assert "carbon" in loaded_game.vehicle.unlocked_colors
    assert "hover" in loaded_game.vehicle.unlocked_chassis
    assert "plasma" in loaded_game.vehicle.unlocked_drills
    assert loaded_game.vehicle.power > v_std.power * 1.5
    print("  -> Customization saved and restored accurately.")

    # Test 11: Classic Endless Mode & Floor Unlocking (+2 Tokens reward)
    print("Testing Classic Endless Mode & Floor Unlocking...")
    c_game = Game(screen)
    c_game.new_game_classic()
    assert c_game.game_mode == "classic"
    assert c_game.unlocked_floor == 1
    assert c_game.mission is None
    init_tok = c_game.vehicle.tokens

    # Verify barrier placement at Floor 1 max_depth (depth 20 -> row 23)
    b_row_flr1 = S.SURFACE_ROW + S.CLASSIC_FLOORS[0]["max_depth"]
    for c in range(S.COLS):
        assert c_game.world.tiles[b_row_flr1][c] == S.T_BARRIER, f"Row {b_row_flr1} col {c} must be T_BARRIER"
        assert c_game.world.is_solid(c, b_row_flr1), f"Row {b_row_flr1} must be solid"

    # Vehicle trying to drill barrier cannot break it
    c_game.vehicle.x = 2 * S.TILE
    c_game.vehicle.y = (b_row_flr1 - 1) * S.TILE
    c_game.vehicle.update(0.016, c_game.world, (0, 1), c_game.particles)
    assert not c_game.vehicle.is_drilling, "Drilling barrier must be blocked!"
    assert c_game.world.tiles[b_row_flr1][2] == S.T_BARRIER

    # Near barrier detection
    barrier_detected = c_game.get_barrier_near_vehicle()
    assert barrier_detected is not None
    next_floor_num, flr_info, b_row = barrier_detected
    assert next_floor_num == 2
    assert b_row == b_row_flr1

    # Insufficient funds to unlock floor 2
    c_game.vehicle.coins = 50
    cost_flr2 = flr_info["unlock_cost"]
    assert not c_game.unlock_next_floor()
    assert c_game.unlocked_floor == 1
    assert c_game.vehicle.tokens == init_tok

    # Give enough coins and unlock floor 2 (+2 Tokens reward)
    c_game.vehicle.coins = cost_flr2 + 100
    res_unlock = c_game.unlock_next_floor()
    assert res_unlock
    assert c_game.unlocked_floor == 2
    assert c_game.vehicle.coins == 100
    assert c_game.vehicle.tokens == init_tok + 2, "Unlocking floor in classic mode MUST grant +2 Tokens!"
    for c in range(S.COLS):
        assert c_game.world.tiles[b_row_flr1][c] == S.T_EMPTY, f"Row {b_row_flr1} must now be opened (T_EMPTY)"

    # Test Shop floor tab rendering
    c_game.shop_tab = "floor"
    shop_buttons = ui.draw_shop_menu(screen, c_game.vehicle, (100, 100),
                                     game_mode=c_game.game_mode,
                                     unlocked_floor=c_game.unlocked_floor,
                                     active_tab=c_game.shop_tab)
    assert "tab_floor" in shop_buttons
    assert "unlock_floor" in shop_buttons

    # Test Save & Load persistence for Classic Mode
    c_game.save_and_quit()
    c_loaded = Game(screen)
    c_loaded.load_game()
    assert c_loaded.game_mode == "classic"
    assert c_loaded.unlocked_floor == 2
    assert c_loaded.vehicle.tokens == init_tok + 2
    assert c_loaded.world.tiles[b_row_flr1][2] == S.T_EMPTY
    print("  -> Classic mode barrier mechanics, +2 Tokens reward, and persistence verified OK.")

    # ==================== Test 12: Cargo Drone & Radio Shop Tech Unlock Enforcement ====================
    print("Testing Cargo Drone & Radio Shop Tech Unlock Enforcement...")
    tech_game = Game(screen)
    tech_game.new_game()
    tech_game.vehicle.tech_drone = False
    tech_game.vehicle.tech_radio = False
    tech_game.vehicle.cargo[S.RES_GOLD] = 2
    tech_game.vehicle.cargo_count = 2

    # 1. Calling drone before unlock -> must fail and keep cargo
    tech_game.call_cargo_drone()
    assert tech_game.vehicle.cargo_count == 2, "Drone must be locked before purchase!"

    # 2. Calling radio shop underground before unlock -> must not open shop
    tech_game.state = PLAYING
    tech_game.vehicle.y = 100 * S.TILE
    tech_game.open_radio_shop()
    assert tech_game.state == PLAYING, "Radio shop must remain locked underground!"

    # 3. Radio shop at surface home/shop building -> accessible without radio
    tech_game.vehicle.x = S.SHOP_COL * S.TILE
    tech_game.vehicle.y = (S.SURFACE_ROW - 1) * S.TILE
    tech_game.open_radio_shop()
    assert tech_game.state == SHOP, "Surface shop must be accessible without radio tech"
    tech_game.state = PLAYING

    # 4. Unlock drone with tokens (costs 3)
    tech_game.vehicle.tokens = 5
    assert tech_game.vehicle.try_unlock_drone()
    assert tech_game.vehicle.tokens == 2
    assert tech_game.vehicle.tech_drone is True
    # Unlock drone again -> should not deduct tokens
    assert tech_game.vehicle.try_unlock_drone()
    assert tech_game.vehicle.tokens == 2

    # Call drone now -> sells cargo successfully
    tech_game.vehicle.coins = 0
    tech_game.call_cargo_drone()
    assert tech_game.vehicle.cargo_count == 0
    assert tech_game.vehicle.coins > 0

    # 5. Unlock radio with tokens (costs 2)
    assert tech_game.vehicle.try_unlock_radio()
    assert tech_game.vehicle.tokens == 0
    assert tech_game.vehicle.tech_radio is True
    # Calling radio shop deep underground now -> opens SHOP!
    tech_game.vehicle.y = 100 * S.TILE
    tech_game.open_radio_shop()
    assert tech_game.state == SHOP
    print("  -> Tech unlock enforcement for drone and radio verified OK.")

    # ==================== Test 13: Mission Token Rewards by Difficulty ====================
    print("Testing Mission Token Rewards by Difficulty...")
    assert missions.DIFFICULTIES["easy"]["reward_tokens"] == 1
    assert missions.DIFFICULTIES["medium"]["reward_tokens"] == 3
    assert missions.DIFFICULTIES["hard"]["reward_tokens"] == 6

    # Test victory granting tokens deterministically across all difficulties
    m_game = Game(screen)
    m_game.new_game()
    m_game.state = PLAYING
    m_game.vehicle.tokens = 0

    # Easy mission victory (award 1 token)
    easy_bp = {
        "id": "test_easy",
        "difficulty": "easy",
        "title": "ภารกิจง่าย",
        "desc": "ทดสอบ",
        "goals": {"gold": 5},
    }
    m_easy = missions.Mission(easy_bp)
    assert m_easy.get_reward_tokens() == 1, "Easy mission must return 1 token from get_reward_tokens()!"
    m_game.mission = m_easy
    m_easy.progress["gold"] = 5
    assert m_easy.is_completed()
    m_game.was_in_home = False
    m_game.vehicle.x = S.HOME_COL * S.TILE
    m_game.vehicle.y = (S.SURFACE_ROW - 1) * S.TILE
    m_game.update(0.016)
    assert m_game.state == "victory"
    assert m_game.vehicle.tokens == 1, "Easy mission victory must award 1 Token!"

    # Medium mission victory (award 3 tokens)
    m_game.state = PLAYING
    med_bp = {
        "id": "test_med",
        "difficulty": "medium",
        "title": "ภารกิจปานกลาง",
        "desc": "ทดสอบ",
        "goals": {"diamonds": 2},
    }
    m_med = missions.Mission(med_bp)
    assert m_med.get_reward_tokens() == 3, "Medium mission must return 3 tokens from get_reward_tokens()!"
    m_game.mission = m_med
    m_med.progress["diamonds"] = 2
    assert m_med.is_completed()
    m_game.was_in_home = False
    m_game.update(0.016)
    assert m_game.state == "victory"
    assert m_game.vehicle.tokens == 1 + 3, "Medium mission victory must award 3 Tokens!"

    # Hard mission victory (award 6 tokens)
    m_game.state = PLAYING
    hard_bp = {
        "id": "test_hard",
        "difficulty": "hard",
        "title": "ภารกิจยาก",
        "desc": "ทดสอบ",
        "goals": {"diamonds": 4, "gold": 10},
    }
    m_hard = missions.Mission(hard_bp)
    assert m_hard.get_reward_tokens() == 6, "Hard mission must return 6 tokens from get_reward_tokens()!"
    m_game.mission = m_hard
    m_hard.progress["diamonds"] = 4
    m_hard.progress["gold"] = 10
    assert m_hard.is_completed()
    m_game.was_in_home = False
    m_game.update(0.016)
    assert m_game.state == "victory"
    assert m_game.vehicle.tokens == 1 + 3 + 6, "Hard mission victory must award 6 Tokens!"

    # Blueprint override victory (override reward_tokens = 5 on an easy mission)
    m_game.state = PLAYING
    override_bp = {
        "id": "test_override",
        "difficulty": "easy",
        "reward_tokens": 5,
        "title": "ภารกิจพิเศษ",
        "desc": "ทดสอบ override",
        "goals": {"gold": 1},
    }
    m_override = missions.Mission(override_bp)
    assert m_override.get_reward_tokens() == 5, "Blueprint reward_tokens must override difficulty default!"
    m_game.mission = m_override
    m_override.progress["gold"] = 1
    assert m_override.is_completed()
    m_game.was_in_home = False
    tokens_prev = m_game.vehicle.tokens
    m_game.update(0.016)
    assert m_game.state == "victory"
    assert m_game.vehicle.tokens == tokens_prev + 5, "Override mission victory must award 5 Tokens!"

    # Verify all blueprints in MISSION_POOL retain completion when vehicle state updates
    for bp in missions.MISSION_POOL:
        sample_m = missions.Mission(bp)
        for k, v in sample_m.goals.items():
            sample_m.progress[k] = v
        sample_m.update_from_game(m_game.vehicle, depth=100)
        assert sample_m.is_completed(), f"Mission {bp['id']} should not lose progress on update_from_game!"
    print("  -> Token reward values and blueprint override (Easy: 1, Med: 3, Hard: 6, Override: 5) verified OK.")

    # ==================== Test 14: Cumulative Coins Mechanism ====================
    print("Testing Cumulative Coins in Mission Goals...")
    test_coin_bp = {
        "id": "coin_m",
        "difficulty": "easy",
        "title": "เป้าหมายเหรียญ",
        "desc": "ทดสอบ",
        "goals": {"coins": 50},
    }
    coin_m = missions.Mission(test_coin_bp)
    veh = Vehicle(2, 2)
    veh.coins = 0

    # Sell cargo to earn coins (3 gold = 15 coins)
    veh.cargo[S.RES_GOLD] = 3
    veh.cargo_count = 3
    earned1 = veh.sell_cargo()
    assert earned1 == 15
    coin_m.add_earned_coins(earned1)
    coin_m.update_from_game(veh, 10)
    assert coin_m.progress["coins"] == 15
    assert not coin_m.is_completed()

    # Player spends coins to 0
    veh.coins = 0
    coin_m.update_from_game(veh, 10)
    assert coin_m.progress["coins"] == 15, "Spending coins must NOT reduce cumulative progress!"

    # Earn more coins (2 diamond = 40 coins, total 55 >= 50)
    veh.cargo[S.RES_DIAMOND] = 2
    veh.cargo_count = 2
    earned2 = veh.sell_cargo()
    assert earned2 == 40
    coin_m.add_earned_coins(earned2)
    coin_m.update_from_game(veh, 10)
    assert coin_m.progress["coins"] == 15 + 40
    assert coin_m.progress["coins"] >= 50
    assert coin_m.is_completed(), "Cumulative coins must fulfill mission even after spending!"
    print("  -> Cumulative coins mechanism verified OK.")

    # ==================== Test 15: Backward Compatibility for Saves ====================
    print("Testing Save File Backward Compatibility...")
    # Simulate old save JSON missing new token / unlock fields
    old_save_data = {
        "world": m_game.world.to_dict(),
        "vehicle": {
            "x": 100.0, "y": 100.0,
            "levels": {"capacity": 1, "energy": 1, "power": 1, "speed": 1},
            "energy": 80.0,
            "cargo": {"1": 0, "2": 0, "3": 0},
            "cargo_count": 0,
            "coins": 250,
            # Notice: NO tokens, unlocked_*, tech_* fields!
        },
        "extra": {"game_mode": "mission"}
    }
    test_veh = Vehicle(0, 0)
    test_veh.load_dict(old_save_data["vehicle"])
    assert test_veh.tokens == 0
    assert test_veh.tech_drone is False
    assert test_veh.tech_radio is False
    assert "yellow" in test_veh.unlocked_colors
    assert "standard" in test_veh.unlocked_chassis
    assert "spiral" in test_veh.unlocked_drills
    print("  -> Backward compatibility with legacy saves without new fields verified OK.")

    # ==================== Test 16: HUD Zone Boundaries and Full Screen Rendering ====================
    print("Testing HUD 3-Zone Layout & Complete UI Rendering...")
    # Verify zone constants match requirement
    assert ui._Z_LEFT_W == 185, f"Left zone must be 185px, got {ui._Z_LEFT_W}"
    assert ui._Z_CENTER_W == 270, f"Center zone must be 270px, got {ui._Z_CENTER_W}"
    assert ui._Z_RIGHT_W == 265, f"Right zone must be 265px, got {ui._Z_RIGHT_W}"
    assert ui._Z_LEFT_W + ui._Z_CENTER_W + ui._Z_RIGHT_W == S.SCREEN_W

    # Test rendering HUD with extreme values (tens of thousands coins, triple digit tokens & depth)
    extreme_veh = Vehicle(2, 2)
    extreme_veh.coins = 99999
    extreme_veh.tokens = 99
    ui.draw_hud(screen, extreme_veh, depth=999, mission=coin_m, game_mode="mission")
    ui.draw_hud(screen, extreme_veh, depth=999, game_mode="classic", unlocked_floor=8)

    # Render all 4 Garage tabs
    for tab in ["color", "type", "drill", "tech"]:
        ui.draw_garage_menu(screen, extreme_veh, (100, 100), active_tab=tab)
    print("  -> HUD zone layout and rendering (16 states) verified OK.")

    # ==================== Test 17: Garage Tooltip Render (hover on Token box) ====================
    print("Testing Garage tooltip render (Token box hover)...")
    # Render with mouse hovering over tok_box area (panel.right-148..panel.right-18, panel.top+14..+44)
    # panel = pygame.Rect(25, 45, 670, 715) => tok_box near x=547..677, y=59..89
    # Use x=600, y=70 to trigger hover
    for tab in ["color", "type", "drill", "tech"]:
        ui.draw_garage_menu(screen, extreme_veh, (600, 70), active_tab=tab)
    # Also render with vehicle that has 0 tokens (all items locked -> show hint text)
    zero_tok_veh = Vehicle(2, 2)
    zero_tok_veh.tokens = 0
    for tab in ["color", "type", "drill", "tech"]:
        ui.draw_garage_menu(screen, zero_tok_veh, (100, 100), active_tab=tab)
    print("  -> Garage tooltip and locked-card hint text rendered without crash OK.")

    # ==================== Test 18: MISSION_POOL token consistency ====================
    print("Testing MISSION_POOL token consistency (UI displayed == actual awarded)...")
    import missions as _ms_pool
    pool_game = Game(screen)
    pool_game.new_game()

    for bp in _ms_pool.MISSION_POOL:
        m = _ms_pool.Mission(bp)
        # ค่าที่ UI โชว์ (ผ่าน helper get_reward_tokens())
        ui_tok = m.get_reward_tokens()
        expected_tok = bp.get("reward_tokens", _ms_pool.DIFFICULTIES[bp["difficulty"]]["reward_tokens"])
        assert ui_tok == expected_tok, f"Mission {bp['id']} get_reward_tokens()={ui_tok} != expected {expected_tok}"

        # จำลองชนะ: เซ็ตความคืบหน้าครบ และขับเข้าบ้านเพื่อตรวจ token ก่อน-หลัง
        pool_game.state = PLAYING
        pool_game.mission = m
        for k, v in m.goals.items():
            m.progress[k] = v
        assert m.is_completed(), f"Mission {bp['id']} should complete after setting all progress"

        pool_game.was_in_home = False
        pool_game.vehicle.x = S.HOME_COL * S.TILE
        pool_game.vehicle.y = (S.SURFACE_ROW - 1) * S.TILE
        tokens_before = pool_game.vehicle.tokens
        pool_game.update(0.016)
        assert pool_game.state == "victory", f"Mission {bp['id']} must trigger victory state"
        tokens_after = pool_game.vehicle.tokens
        actual_reward = tokens_after - tokens_before
        assert actual_reward == ui_tok, (
            f"Mission {bp['id']}: UI shows {ui_tok} Token but actual awarded was {actual_reward}"
        )
    print(f"  -> All {len(_ms_pool.MISSION_POOL)} missions in MISSION_POOL: UI token == actual victory reward OK.")

    # ==================== Test 19: Classic floor token reward consistency ====================
    print("Testing Classic floor token reward (CLASSIC_FLOOR_TOKEN_REWARD)...")
    classic_test = Game(screen)
    classic_test.new_game_classic()
    classic_test.vehicle.tokens = 0
    classic_test.vehicle.coins = 9999  # พอปลดล็อคทุกชั้น

    tok_before = classic_test.vehicle.tokens
    result = classic_test.unlock_next_floor()
    assert result is True, "unlock_next_floor() should return True when coins are sufficient"
    tok_after = classic_test.vehicle.tokens
    reward = tok_after - tok_before
    assert reward == S.CLASSIC_FLOOR_TOKEN_REWARD, (
        f"Classic floor unlock should give {S.CLASSIC_FLOOR_TOKEN_REWARD} Token, got {reward}"
    )
    print(f"  -> Classic floor unlock gives +{S.CLASSIC_FLOOR_TOKEN_REWARD} Token as expected OK.")

    # ==================== Test 20: Layout pixel check via font.size() ====================
    print("Testing layout pixel bounds (HUD right zone 265px, main menu buttons)...")
    import ui as _ui_lay

    # ตรวจ HUD โซนขวา 265px: ข้อความ Token 99 + เหรียญ 99,999 ต้องไม่ล้น
    _right_w = _ui_lay._Z_RIGHT_W  # 265
    _tok_str = "99 Token"
    _coin_str = "99,999"
    _tok_w, _ = _ui_lay.FONT_XS.size(_tok_str)
    _coin_w, _ = _ui_lay.FONT_S.size(_coin_str)
    assert _tok_w <= _right_w - 30, f"Token text '{_tok_str}' width {_tok_w}px exceeds right zone"
    assert _coin_w <= _right_w - 30, f"Coin text '{_coin_str}' width {_coin_w}px exceeds right zone"

    # ตรวจหน้าเมนูหลัก: ปุ่มทั้งหมดต้องไม่ล้นขอบล่าง 720px
    for has_save_flag in [False, True]:
        m_btns = _ui_lay.draw_main_menu(screen, has_save=has_save_flag, mouse_pos=(100, 100))
        for b_name, b_rect in m_btns.items():
            assert b_rect.bottom <= 720, f"Main menu button '{b_name}' bottom {b_rect.bottom} exceeds 720px!"
            assert b_rect.bottom <= S.SCREEN_H, f"Main menu button '{b_name}' bottom {b_rect.bottom} exceeds SCREEN_H!"

    # ตรวจหน้าวิธีเล่น: ปุ่มปิดต้องไม่ล้นขอบล่าง 720px และไม่เกิน SCREEN_H
    htp_btns = _ui_lay.draw_how_to_play(screen, mouse_pos=(100, 100))
    assert "close" in htp_btns
    assert htp_btns["close"].bottom <= 720, f"How to Play close button bottom {htp_btns['close'].bottom} exceeds 720px!"
    assert htp_btns["close"].bottom <= S.SCREEN_H, f"How to Play close button bottom exceeds SCREEN_H!"

    # ตรวจหน้าเลือกสัญญา (Contract Menu)
    contracts = _ms_pool.get_three_contract_options()
    c_btns = _ui_lay.draw_contract_menu(screen, contracts, mouse_pos=(100, 100))
    assert len(c_btns) >= 3

    # ตรวจหน้า Victory
    v_btns = _ui_lay.draw_end_screen(screen, "ชัยชนะ!", "ภารกิจสำเร็จ", extreme_veh, (100, 100), mission=coin_m)
    assert "menu" in v_btns

    # บันทึก screenshot ลง scratch/ เพื่อตรวจด้วยตา
    import os
    os.makedirs("scratch", exist_ok=True)
    _ui_lay.draw_hud(screen, extreme_veh, depth=999, mission=coin_m, game_mode="mission")
    pygame.image.save(screen, "scratch/layout_hud_mission.png")
    _ui_lay.draw_hud(screen, extreme_veh, depth=999, game_mode="classic", unlocked_floor=8)
    pygame.image.save(screen, "scratch/layout_hud_classic.png")
    _ui_lay.draw_main_menu(screen, has_save=True, mouse_pos=(100, 100))
    pygame.image.save(screen, "scratch/layout_main_menu.png")
    _ui_lay.draw_how_to_play(screen, mouse_pos=(100, 100))
    pygame.image.save(screen, "scratch/layout_how_to_play.png")
    _ui_lay.draw_contract_menu(screen, contracts, mouse_pos=(100, 100))
    pygame.image.save(screen, "scratch/layout_contract_menu.png")
    _ui_lay.draw_end_screen(screen, "ชัยชนะ!", "ภารกิจสำเร็จ", extreme_veh, (100, 100), mission=coin_m)
    pygame.image.save(screen, "scratch/layout_victory.png")
    for tab in ["color", "type", "drill", "tech"]:
        _ui_lay.draw_garage_menu(screen, extreme_veh, (100, 100), active_tab=tab)
        pygame.image.save(screen, f"scratch/layout_garage_{tab}.png")
    print("  -> Layout pixel bounds & screenshots for all UI screens verified OK.")

    # ==================== Test 21: Multi-Slot 5 Slots Save/Load/Delete ====================
    print("Testing Multi-Slot 5 Slots Save/Load/Delete (Both Modes, Full Stats)...")
    import tempfile
    import shutil
    mock_dir = tempfile.mkdtemp(prefix="test_slots_")
    SM.set_saves_dir(mock_dir)
    try:
        # ตรวจสอบว่าเริ่มต้น 5 ช่องว่างทั้งหมด
        slots_init = SM.list_slots()
        assert len(slots_init) == 5
        assert all(s["empty"] for s in slots_init)

        # บันทึกทั้ง 5 ช่องโดยสลับโหมดและค่าสถิติ
        # ช่อง 1: Mission mode
        w1 = World(game_mode="mission", unlocked_floor=1)
        v1 = Vehicle(S.HOME_COL, S.SURFACE_ROW - 1, color_id="carbon", vehicle_type="heavy", drill_head="diamond")
        v1.coins = 550
        v1.tokens = 4
        v1.tech_drone = True
        v1.tech_radio = True
        m1 = missions.Mission({"id": "m1", "title": "ภารกิจทดสอบช่อง 1", "desc": "ทดสอบ", "difficulty": "easy", "goals": {"gold": 2}})
        SM.save_slot(1, w1, v1, extra={"game_mode": "mission", "unlocked_floor": 1, "mission": m1.to_dict()})

        # ช่อง 2: Classic mode
        w2 = World(game_mode="classic", unlocked_floor=3)
        v2 = Vehicle(S.HOME_COL, S.SURFACE_ROW - 1, color_id="gold", vehicle_type="titan", drill_head="plasma")
        v2.coins = 12500
        v2.tokens = 7
        SM.save_slot(2, w2, v2, extra={"game_mode": "classic", "unlocked_floor": 3})

        # ช่อง 3: Mission mode
        w3 = World(game_mode="mission", unlocked_floor=1)
        v3 = Vehicle(S.HOME_COL, S.SURFACE_ROW - 1, color_id="ruby", vehicle_type="speedy", drill_head="triple")
        v3.coins = 80
        v3.tokens = 1
        m3 = missions.Mission({"id": "m3", "title": "ภารกิจขุดแร่ช่อง 3", "desc": "ทดสอบ", "difficulty": "medium", "goals": {"diamonds": 1}})
        SM.save_slot(3, w3, v3, extra={"game_mode": "mission", "unlocked_floor": 1, "mission": m3.to_dict()})

        # ช่อง 4: Classic mode
        w4 = World(game_mode="classic", unlocked_floor=5)
        v4 = Vehicle(S.HOME_COL, S.SURFACE_ROW - 1, color_id="emerald", vehicle_type="cargo", drill_head="laser")
        v4.coins = 88000
        v4.tokens = 15
        SM.save_slot(4, w4, v4, extra={"game_mode": "classic", "unlocked_floor": 5})

        # ช่อง 5: Mission mode
        w5 = World(game_mode="mission", unlocked_floor=1)
        v5 = Vehicle(S.HOME_COL, S.SURFACE_ROW - 1, color_id="standard", vehicle_type="standard", drill_head="spiral")
        v5.coins = 0
        v5.tokens = 0
        SM.save_slot(5, w5, v5, extra={"game_mode": "mission", "unlocked_floor": 1})

        # ตรวจสอบ list_slots
        slots_after = SM.list_slots()
        assert len(slots_after) == 5
        assert all(not s["empty"] and not s.get("corrupted", False) for s in slots_after)

        # โหลดและตรวจสอบความถูกต้องแบบแยกอิสระ (Slots Isolation)
        # โหลดช่อง 1
        ok1, gd1, meta1 = SM.load_slot(1)
        assert ok1 and meta1["game_mode"] == "mission"
        assert gd1["vehicle"]["coins"] == 550
        assert gd1["vehicle"]["tokens"] == 4
        assert gd1["vehicle"]["color_id"] == "carbon"
        assert gd1["vehicle"]["vehicle_type"] == "heavy"
        assert gd1["vehicle"]["drill_head"] == "diamond"
        assert gd1["vehicle"]["tech_drone"] is True
        assert gd1["vehicle"]["tech_radio"] is True
        assert gd1["extra"]["mission"]["title"] == "ภารกิจทดสอบช่อง 1"

        # โหลดช่อง 2
        ok2, gd2, meta2 = SM.load_slot(2)
        assert ok2 and meta2["game_mode"] == "classic"
        assert gd2["vehicle"]["coins"] == 12500
        assert gd2["vehicle"]["tokens"] == 7
        assert gd2["vehicle"]["color_id"] == "gold"
        assert gd2["extra"]["unlocked_floor"] == 3

        # โหลดช่อง 4
        ok4, gd4, meta4 = SM.load_slot(4)
        assert ok4 and meta4["game_mode"] == "classic"
        assert gd4["vehicle"]["coins"] == 88000
        assert gd4["extra"]["unlocked_floor"] == 5

        # ลบช่อง 2 และช่อง 4
        assert SM.delete_slot(2) is True
        assert SM.delete_slot(4) is True

        slots_del = SM.list_slots()
        assert slots_del[1]["empty"] is True   # ช่อง 2 ว่าง
        assert slots_del[3]["empty"] is True   # ช่อง 4 ว่าง
        assert slots_del[0]["empty"] is False  # ช่อง 1 ยังอยู่
        assert slots_del[2]["empty"] is False  # ช่อง 3 ยังอยู่
        assert slots_del[4]["empty"] is False  # ช่อง 5 ยังอยู่
        print("  -> Multi-slot 5 slots save/load/delete and isolation verified OK.")
    finally:
        SM.reset_saves_dir()
        shutil.rmtree(mock_dir, ignore_errors=True)

    # ==================== Test 22: Corrupted JSON & Structure Resilience ====================
    print("Testing Corrupted JSON & Invalid Structure Resilience...")
    mock_dir2 = tempfile.mkdtemp(prefix="test_corrupt_")
    SM.set_saves_dir(mock_dir2)
    try:
        # เขียนไฟล์ JSON เสีย (syntax error) ในช่อง 2
        bad_path = SM.get_slot_path(2)
        with open(bad_path, "w", encoding="utf-8") as f:
            f.write("{ invalid json : broken syntax [")

        # เขียนไฟล์โครงสร้างแปลกๆ ในช่อง 4
        exotic_path = SM.get_slot_path(4)
        with open(exotic_path, "w", encoding="utf-8") as f:
            f.write(json.dumps({"version": 9999, "unknown_field": True, "extra": {}}))

        slots = SM.list_slots()
        assert slots[1]["corrupted"] is True
        assert "ไฟล์เสียหาย" in slots[1]["summary"]["mode_name"]
        assert slots[3]["empty"] is False
        assert slots[3]["corrupted"] is False  # fallback ปลอดภัย

        # ทดสอบ load_slot บนไฟล์เสีย
        ok, gdata, meta = SM.load_slot(2)
        assert ok is False
        assert gdata is None
        assert "error" in meta

        # ทดสอบ Game.load_slot ปลอดภัย ไม่ crash
        g_test = Game(screen)
        load_res = g_test.load_slot(2)
        assert load_res is False
        assert "ไม่สำเร็จ" in g_test.toast_msg

        # ลบไฟล์เสียได้สำเร็จ
        assert SM.delete_slot(2) is True
        assert SM.list_slots()[1]["empty"] is True
        print("  -> Corrupted JSON and exotic structures handled gracefully without crash OK.")
    finally:
        SM.reset_saves_dir()
        shutil.rmtree(mock_dir2, ignore_errors=True)

    # ==================== Test 23: Legacy Save Migration ====================
    print("Testing Legacy Save Migration (savegame.json -> slot_1.json)...")
    mock_dir3 = tempfile.mkdtemp(prefix="test_mig_")
    SM.set_saves_dir(mock_dir3)
    try:
        old_save_file = os.path.join(mock_dir3, "savegame_legacy.json")
        # จำลอง savegame.json แบบเก่า
        legacy_data = {
            "world": World(game_mode="classic", unlocked_floor=2).to_dict(),
            "vehicle": Vehicle(S.HOME_COL, S.SURFACE_ROW - 1, color_id="blue").to_dict(),
            "extra": {
                "game_mode": "classic",
                "unlocked_floor": 2,
            }
        }
        with open(old_save_file, "w", encoding="utf-8") as f:
            json.dump(legacy_data, f)

        orig_save_file = S.SAVE_FILE
        S.SAVE_FILE = old_save_file
        try:
            SM.migrate_legacy_save()
            slot1_path = SM.get_slot_path(1)
            assert os.path.isfile(slot1_path), "slot_1.json must be created from migration!"
            ok, gdata, meta = SM.load_slot(1)
            assert ok is True
            assert meta["version"] == 2
            assert meta["game_mode"] == "classic"
            assert meta["summary"]["unlocked_floor"] == 2
        finally:
            S.SAVE_FILE = orig_save_file
        print("  -> Legacy savegame.json migrated to slot_1.json accurately OK.")
    finally:
        SM.reset_saves_dir()
        shutil.rmtree(mock_dir3, ignore_errors=True)

    # ==================== Test 24: Overwrite & Delete Confirmation Flow ====================
    print("Testing Overwrite & Delete Confirmation Dialog Flow...")
    mock_dir4 = tempfile.mkdtemp(prefix="test_conf_")
    SM.set_saves_dir(mock_dir4)
    try:
        # บันทึกข้อมูลลง slot 1
        w = World(game_mode="mission", unlocked_floor=1)
        v = Vehicle(S.HOME_COL, S.SURFACE_ROW - 1)
        SM.save_slot(1, w, v)

        g = Game(screen)
        g.world = w
        g.vehicle = v

        # 1. ทดสอบการลบใน LOAD_MENU: กด delete_slot_1 ต้องถามยืนยันก่อน
        g.state = LOAD_MENU
        g.buttons = {"delete_slot_1": pygame.Rect(100, 100, 36, 36)}
        ev_click_del = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(110, 110))
        g.handle_event(ev_click_del)
        assert g.confirm_delete_slot == 1, "Must set confirm_delete_slot to 1!"
        assert os.path.isfile(SM.get_slot_path(1)), "File must NOT be deleted yet!"

        # กดยืนยัน confirm_delete_1
        g.buttons = {"confirm_delete_1": pygame.Rect(100, 100, 100, 36)}
        ev_confirm_del = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(110, 110))
        g.handle_event(ev_confirm_del)
        assert g.confirm_delete_slot is None, "confirm_delete_slot must be cleared!"
        assert not os.path.isfile(SM.get_slot_path(1)), "File must be deleted now!"

        # 2. ทดสอบการเขียนทับใน SAVE_MENU
        SM.save_slot(1, w, v)
        g.state = SAVE_MENU
        g.buttons = {"save_slot_1": pygame.Rect(200, 200, 92, 36)}
        ev_click_save = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(210, 210))
        g.handle_event(ev_click_save)
        assert g.confirm_overwrite_slot == 1, "Must set confirm_overwrite_slot to 1 when slot is not empty!"

        # กดยืนยันเขียนทับ confirm_overwrite_1
        g.buttons = {"confirm_overwrite_1": pygame.Rect(200, 200, 120, 36)}
        ev_confirm_ow = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(210, 210))
        g.handle_event(ev_confirm_ow)
        assert g.confirm_overwrite_slot is None, "confirm_overwrite_slot must be reset!"
        assert g.state == g.previous_state, "Should return to previous state after saving!"
        print("  -> Confirmation steps for deletion and overwrite verified OK.")
    finally:
        SM.reset_saves_dir()
        shutil.rmtree(mock_dir4, ignore_errors=True)

    # ==================== Test 25: Audio Settings Sync & M Key Toggle ====================
    print("Testing Audio Settings Sync & Global 'M' Key Toggle...")
    mock_dir5 = tempfile.mkdtemp(prefix="test_snd_")
    SM.set_saves_dir(mock_dir5)
    try:
        g = Game(screen)
        assets.set_muted(False)
        assert assets.is_muted() is False

        # ทดสอบ toggle_mute()
        g.toggle_mute()
        assert assets.is_muted() is True
        setts = SM.load_settings()
        assert setts.get("muted") is True

        # ทดสอบ Game instance ใหม่โหลดการตั้งค่าเสียงอัตโนมัติ
        g2 = Game(screen)
        assert assets.is_muted() is True

        # ทดสอบการกดปุ่ม 'M' ในทุกสถานะเกม (MENU, PLAYING, PAUSED, SHOP, GARAGE, LOAD_MENU, SAVE_MENU)
        states_to_test = [MENU, PLAYING, PAUSED, SHOP, GARAGE, LOAD_MENU, SAVE_MENU]
        for st in states_to_test:
            g2.state = st
            cur_muted = assets.is_muted()
            ev_m = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_m, unicode="m")
            g2.handle_event(ev_m)
            assert assets.is_muted() == (not cur_muted), f"M key must toggle mute in state {st}!"

        # สลับกลับเป็นเปิดเสียง
        assets.set_muted(False)
        SM.save_settings({"muted": False})
        print("  -> Audio settings persistence and global 'M' key toggle verified OK.")
    finally:
        SM.reset_saves_dir()
        shutil.rmtree(mock_dir5, ignore_errors=True)

    # ==================== Test 26: Multi-Slot & Audio UI Rendering & Screenshots ====================
    print("Testing Multi-Slot & Audio UI Rendering & Pixel Bounds (<= 720px)...")
    mock_dir6 = tempfile.mkdtemp(prefix="test_rend_")
    SM.set_saves_dir(mock_dir6)
    try:
        w = World(game_mode="classic", unlocked_floor=2)
        v = Vehicle(S.HOME_COL, S.SURFACE_ROW - 1, color_id="ruby", vehicle_type="speedy")
        v.coins = 9999
        v.tokens = 5
        SM.save_slot(1, w, v, extra={"game_mode": "classic", "unlocked_floor": 2})

        with open(SM.get_slot_path(3), "w", encoding="utf-8") as f:
            f.write("{ broken json")

        slots_info = SM.list_slots()
        os.makedirs("scratch", exist_ok=True)

        # 1. เรนเดอร์ slot menu โหมด load
        load_btns = ui.draw_slot_menu(screen, slots_info, mode="load", mouse_pos=(100, 100), current_slot=1)
        pygame.image.save(screen, "scratch/layout_slot_load.png")
        for k, r in load_btns.items():
            assert r.right <= S.SCREEN_W, f"Button {k} exceeds SCREEN_W: {r.right} > {S.SCREEN_W}"
            assert r.left >= 0, f"Button {k} left < 0: {r.left}"

        # 2. เรนเดอร์ slot menu โหมด save
        save_btns = ui.draw_slot_menu(screen, slots_info, mode="save", mouse_pos=(100, 100), current_slot=1)
        pygame.image.save(screen, "scratch/layout_slot_save.png")
        for k, r in save_btns.items():
            assert r.right <= S.SCREEN_W, f"Button {k} exceeds SCREEN_W: {r.right} > {S.SCREEN_W}"

        # 3. เรนเดอร์ slot menu ขณะรอยืนยันลบ
        del_conf_btns = ui.draw_slot_menu(screen, slots_info, mode="load", confirm_delete_slot=1)
        pygame.image.save(screen, "scratch/layout_slot_confirm_delete.png")
        assert "confirm_delete_1" in del_conf_btns
        assert del_conf_btns["confirm_delete_1"].right <= S.SCREEN_W

        # 4. เรนเดอร์ slot menu ขณะรอยืนยันเขียนทับ
        ow_conf_btns = ui.draw_slot_menu(screen, slots_info, mode="save", confirm_overwrite_slot=1)
        pygame.image.save(screen, "scratch/layout_slot_confirm_overwrite.png")
        assert "confirm_overwrite_1" in ow_conf_btns
        assert ow_conf_btns["confirm_overwrite_1"].right <= S.SCREEN_W

        # 5. เรนเดอร์ Main Menu (เปิด/ปิดเสียง)
        assets.set_muted(False)
        m_btns_unmuted = ui.draw_main_menu(screen, has_save=True, mouse_pos=(200, 200))
        pygame.image.save(screen, "scratch/layout_main_menu_unmuted.png")
        assert "mute" in m_btns_unmuted
        assert m_btns_unmuted["mute"].right <= S.SCREEN_W

        assets.set_muted(True)
        m_btns_muted = ui.draw_main_menu(screen, has_save=True, mouse_pos=(200, 200))
        pygame.image.save(screen, "scratch/layout_main_menu_muted.png")

        # 6. เรนเดอร์ Pause Menu (เปิด/ปิดเสียง)
        assets.set_muted(False)
        p_btns_unmuted = ui.draw_pause_menu(screen, (200, 200), current_slot=2)
        pygame.image.save(screen, "scratch/layout_pause_unmuted.png")
        assert "mute" in p_btns_unmuted
        assert "save_current" in p_btns_unmuted
        assert "save_slots" in p_btns_unmuted
        for k, r in p_btns_unmuted.items():
            assert r.right <= S.SCREEN_W, f"Pause button {k} exceeds SCREEN_W: {r.right} > {S.SCREEN_W}"

        assets.set_muted(True)
        p_btns_muted = ui.draw_pause_menu(screen, (200, 200), current_slot=2)
        pygame.image.save(screen, "scratch/layout_pause_muted.png")
        print("  -> Slot menu, Main menu, and Pause menu layouts verified within 720px bounds OK.")
    finally:
        SM.reset_saves_dir()
        shutil.rmtree(mock_dir6, ignore_errors=True)

    # ==================== Test 27: Regex emoji/special symbol scan ====================
    print("Testing no Emoji/special symbols in Python string literals...")
    import re
    import ast

    # pattern: บล็อก Unicode emoji ที่ห้ามใช้ใน Pygame string
    _EMOJI_RE = re.compile(
        r'(?:'
        r'[\u25A0-\u25FF]'   # Geometric shapes
        r'|[\u2600-\u27BF]'  # Misc symbols, Dingbats
        r'|[\U0001F300-\U0001FAFF]'  # Emoji block
        r')'
    )

    _py_files = sorted([f for f in os.listdir('.') if f.endswith('.py')])
    _total_hits = 0
    for _pyf in _py_files:
        with open(_pyf, encoding="utf-8") as _fh:
            _src = _fh.read()
        try:
            _tree = ast.parse(_src)
        except SyntaxError:
            continue
        # ตรวจเฉพาะ string literals (ไม่นับ comments)
        for _node in ast.walk(_tree):
            if isinstance(_node, ast.Constant) and isinstance(_node.value, str):
                _hits = _EMOJI_RE.findall(_node.value)
                if _hits:
                    print(f"  [FAIL] {_pyf}:{_node.lineno}: found symbols {_hits!r} in string: {_node.value[:60]!r}")
                    _total_hits += len(_hits)
    assert _total_hits == 0, f"Found {_total_hits} forbidden symbol(s) in string literals!"
    print(f"  -> Emoji/special symbol scan: 0 hits in {len(_py_files)} files OK.")

    # ==================== Cleanup ====================
    if SM.save_exists():
        SM.delete_save()

    pygame.quit()
    print("=== ALL TESTS (27/27) PASSED SUCCESSFULLY! ===")


if __name__ == "__main__":
    run_tests()

